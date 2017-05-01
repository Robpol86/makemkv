"""Test hooks in bash scripts."""

import contextlib
import re
import subprocess

import pytest


@contextlib.contextmanager
def build_image(root):
    """Build a new Docker image with any file in root coped to /.

    :param py.path.local root: Root directory of files to copy.

    :return: Same root variable and Docker image ID in a list.
    :rtype: iter
    """
    images = list()
    yield root, images

    # Create Dockerfile.
    docker_file = root.join('Dockerfile')
    if not docker_file.check():
        docker_file.write('FROM robpol86/makemkv\n')
    docker_file.write('\n', 'a')

    # Append to Dockerfile.
    for path in (p for p in root.listdir() if p.isfile() and p.basename != 'Dockerfile'):
        docker_file.write('COPY {0} /{0}\n'.format(path.basename), 'a')

    # Build.
    stdout = pytest.run(['docker', 'build', '.'], cwd=root)[0]
    matches = re.compile(br'^Successfully built ([a-f0-9]+)$', re.MULTILINE).findall(stdout)
    assert matches
    images.extend(m.decode('utf8') for m in matches)


@pytest.mark.usefixtures('cdemu')
def test_success(tmpdir):
    """Test most hooks in one test during a successful rip.

    :param py.path.local tmpdir: pytest fixture.
    """
    hooks = ('post-env', 'pre-prepare', 'post-prepare', 'pre-rip', 'post-rip', 'end')
    with build_image(tmpdir.join('root')) as (root, image_ids):
        for hook in hooks:
            root.join('hook-{}.sh'.format(hook)).write('echo HOOK FIRED: {}\n'.format(hook.upper()), ensure=True)

    # Docker run.
    output = tmpdir.ensure_dir('output')
    stdout = pytest.run(output=output, image_id=image_ids[0])[0]

    # Verify.
    for hook in hooks:
        assert hook.upper().encode('utf8') in stdout
    assert stdout.count(b'HOOK FIRED: ') == len(hooks)  # Verify no other hooks fired.
    pytest.verify(output)


@pytest.mark.usefixtures('cdemu_truncated')
def test_failed(tmpdir):
    """Test most hooks in one test during a successful rip.

    :param py.path.local tmpdir: pytest fixture.
    """
    hooks = ('pre-on-err', 'post-on-err', 'pre-on-err-touch', 'post-on-err-touch')
    with build_image(tmpdir.join('root')) as (root, image_ids):
        for hook in hooks:
            root.join('hook-{}.sh'.format(hook)).write('echo HOOK FIRED: {}\n'.format(hook.upper()), ensure=True)

    # Docker run.
    with pytest.raises(subprocess.CalledProcessError) as exc:
        pytest.run(image_id=image_ids[0])
    stdout = exc.value.output

    # Verify.
    for hook in hooks:
        assert hook.upper().encode('utf8') in stdout
    assert stdout.count(b'HOOK FIRED: ') == len(hooks)  # Verify no other hooks fired.


@pytest.mark.parametrize('no_eject', [False, True])
@pytest.mark.usefixtures('cdemu')
def test_eject_success(tmpdir, no_eject):
    """Test post and pre eject hooks.

    :param py.path.local tmpdir: pytest fixture.
    :param bool no_eject: Set environment variable to 'true' or 'false'.
    """
    hooks = ('pre-success-eject', 'post-success-eject')
    with build_image(tmpdir.join('root')) as (root, image_ids):
        for hook in hooks:
            root.join('hook-{}.sh'.format(hook)).write('echo HOOK FIRED: {}\n'.format(hook.upper()), ensure=True)

    # Docker run.
    args = ['-e', 'NO_EJECT=true'] if no_eject else None
    output = tmpdir.ensure_dir('output')
    stdout = pytest.run(args=args, output=output, image_id=image_ids[0])[0]

    # Verify.
    if no_eject:
        for hook in hooks:
            assert hook.upper().encode('utf8') not in stdout
        assert stdout.count(b'HOOK FIRED: ') == 0
    else:
        for hook in hooks:
            assert hook.upper().encode('utf8') in stdout
        assert stdout.count(b'HOOK FIRED: ') == len(hooks)  # Verify no other hooks fired.
    pytest.verify(output)


@pytest.mark.parametrize('failed_eject', [False, True])
@pytest.mark.usefixtures('cdemu_truncated')
def test_eject_failed(tmpdir, failed_eject):
    """Test post and pre eject hooks.

    :param py.path.local tmpdir: pytest fixture.
    :param bool failed_eject: Set environment variable to 'true' or 'false'.
    """
    hooks = ('pre-failed-eject', 'post-failed-eject')
    with build_image(tmpdir.join('root')) as (root, image_ids):
        for hook in hooks:
            root.join('hook-{}.sh'.format(hook)).write('echo HOOK FIRED: {}\n'.format(hook.upper()), ensure=True)

    # Docker run.
    args = ['-e', 'FAILED_EJECT=true'] if failed_eject else None
    output = tmpdir.ensure_dir('output')
    with pytest.raises(subprocess.CalledProcessError) as exc:
        pytest.run(args=args, output=output, image_id=image_ids[0])
    stdout = exc.value.output

    # Verify.
    if failed_eject:
        for hook in hooks:
            assert hook.upper().encode('utf8') in stdout
        assert stdout.count(b'HOOK FIRED: ') == len(hooks)  # Verify no other hooks fired.
    else:
        for hook in hooks:
            assert hook.upper().encode('utf8') not in stdout
        assert stdout.count(b'HOOK FIRED: ') == 0
    pytest.verify_failed_file(output)
