"""Test hooks in bash scripts."""

import contextlib
import re
import subprocess

import pytest


@contextlib.contextmanager
def build_image(root):
    """Build a new Docker image with any file in root coped to /.

    :param py.path.local root: Root directory of files to copy.

    :return: Same root variable, Dockerfile path, and Docker image ID in a list.
    :rtype: iter
    """
    images = list()

    # Create Dockerfile.
    docker_file = root.ensure('Dockerfile')
    docker_file.write('FROM robpol86/makemkv\n')

    # Let caller add files or modify Dockerfile.
    yield root, docker_file, images

    # Append to Dockerfile.
    for path in (p for p in root.listdir() if p.isfile() and p.basename != 'Dockerfile'):
        docker_file.write('COPY {} /\n'.format(path.basename), 'a')

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
    hooks = ('post-env', 'pre-prepare', 'post-prepare', 'pre-rip', 'post-title', 'post-rip', 'end')
    with build_image(tmpdir.join('root')) as (root, _, image_ids):
        for hook in hooks:
            root.ensure('hook-{}.sh'.format(hook)).write('env |sort')

    # Docker run.
    output = tmpdir.ensure_dir('output')
    stdout, stderr = pytest.run(output=output, image_id=image_ids[0])

    # Verify.
    for hook in hooks:
        assert b'FIRING HOOK: /hook-%s.sh' % hook.encode('utf8') in stderr
        assert b'_HOOK_SCRIPT=/hook-%s.sh' % hook.encode('utf8') in stdout
        assert b'END OF HOOK: /hook-%s.sh' % hook.encode('utf8') in stderr
        if hook == 'post-title':
            assert re.compile(br'^TITLE_PATH=/output/Sample[a-zA-Z0-9_/.-]+/title00\.mkv$', re.MULTILINE).search(stdout)
    assert stderr.count(b'\nEND OF HOOK: ') == len(hooks)  # Verify no other hooks fired.
    pytest.verify(output)


@pytest.mark.usefixtures('cdemu_truncated')
def test_failed(tmpdir):
    """Test most hooks in one test during a successful rip.

    :param py.path.local tmpdir: pytest fixture.
    """
    hooks = ('pre-on-err', 'post-on-err', 'pre-on-err-touch', 'post-on-err-touch')
    with build_image(tmpdir.join('root')) as (root, _, image_ids):
        for hook in hooks:
            root.ensure('hook-{}.sh'.format(hook)).write('env |sort')

    # Docker run.
    with pytest.raises(subprocess.CalledProcessError) as exc:
        pytest.run(image_id=image_ids[0])
    stdout, stderr = exc.value.output, exc.value.stderr

    # Verify.
    for hook in hooks:
        assert b'\nFIRING HOOK: /hook-%s.sh' % hook.encode('utf8') in stderr
        assert b'\n_HOOK_SCRIPT=/hook-%s.sh' % hook.encode('utf8') in stdout
        assert b'\nEND OF HOOK: /hook-%s.sh' % hook.encode('utf8') in stderr
    assert stderr.count(b'\nEND OF HOOK: ') == len(hooks)  # Verify no other hooks fired.


@pytest.mark.usefixtures('cdemu')
def test_failed_after_makemkvcon(tmpdir):
    """Test errors that happen after makemkvcon background and foreground trick.

    :param py.path.local tmpdir: pytest fixture.
    """
    hooks = ('pre-on-err', 'post-on-err', 'pre-on-err-touch', 'post-on-err-touch')
    with build_image(tmpdir.join('root')) as (root, _, image_ids):
        for hook in hooks:
            root.ensure('hook-{}.sh'.format(hook)).write('env |sort')
        root.ensure('hook-post-rip.sh').write('false')

    # Docker run.
    with pytest.raises(subprocess.CalledProcessError) as exc:
        pytest.run(image_id=image_ids[0])
    stdout, stderr = exc.value.output, exc.value.stderr

    # Verify.
    for hook in hooks:
        assert b'\nFIRING HOOK: /hook-%s.sh' % hook.encode('utf8') in stderr
        assert b'\n_HOOK_SCRIPT=/hook-%s.sh' % hook.encode('utf8') in stdout
        assert b'\nEND OF HOOK: /hook-%s.sh' % hook.encode('utf8') in stderr
    assert stderr.count(b'\nEND OF HOOK: ') == len(hooks)  # Verify no other hooks fired.


@pytest.mark.parametrize('fail', [False, True])
@pytest.mark.parametrize('no_eject', [False, True])
@pytest.mark.usefixtures('cdemu')
def test_eject(tmpdir, fail, no_eject):
    """Test post and pre eject hooks.

    :param py.path.local tmpdir: pytest fixture.
    :param bool fail: Cause a failure during the run.
    :param bool no_eject: Set environment variable to 'true' or 'false'.
    """
    hooks = ('pre-success-eject', 'post-success-eject', 'pre-failed-eject', 'post-failed-eject')
    with build_image(tmpdir.join('root')) as (root, _, image_ids):
        for hook in hooks:
            root.ensure('hook-{}.sh'.format(hook)).write('echo eject hook fired!')
        if fail:
            root.ensure('hook-pre-rip.sh').write('false')

    # Docker run.
    args = ['-e', 'FAILED_EJECT=true'] + (['-e', 'NO_EJECT=true'] if no_eject else [])
    if fail:
        with pytest.raises(subprocess.CalledProcessError) as exc:
            pytest.run(args=args, image_id=image_ids[0])
        stdout, stderr = exc.value.output, exc.value.stderr
    else:
        stdout, stderr = pytest.run(args=args, image_id=image_ids[0])

    # Verify.
    if no_eject:
        assert stdout.count(b'eject hook fired!') == 0
    else:
        assert stdout.count(b'eject hook fired!') == 2
        if fail:
            assert b'\nFIRING HOOK: /hook-pre-failed-eject.sh' in stderr
            assert b'\nFIRING HOOK: /hook-post-failed-eject.sh' in stderr
        else:
            assert b'\nFIRING HOOK: /hook-pre-success-eject.sh' in stderr
            assert b'\nFIRING HOOK: /hook-post-success-eject.sh' in stderr


@pytest.mark.parametrize('fail', [False, True])
@pytest.mark.usefixtures('cdemu')
def test_wait(tmpdir, fail):
    """Test waiting for background jobs.

    :param py.path.local tmpdir: pytest fixture.
    :param bool fail: Cause a failure during the run.
    """
    with build_image(tmpdir.join('root')) as (root, _, image_ids):
        pre_rip = root.ensure('hook-pre-rip.sh')
        pre_rip.write(
            'do_wait () {\n'
            '    sleep 2\n'
            '    echo do_wait done!\n'
            '}\n'
            'do_wait &\n'
        )
        if fail:
            pre_rip.write('false\n', 'a')

    # Docker run.
    if fail:
        with pytest.raises(subprocess.CalledProcessError) as exc:
            pytest.run(image_id=image_ids[0])
        stdout, stderr = exc.value.output, exc.value.stderr
    else:
        stdout, stderr = pytest.run(image_id=image_ids[0])

    # Verify.
    assert b'do_wait done!' in stdout


@pytest.mark.parametrize('fail', [False, True])
@pytest.mark.usefixtures('cdemu')
def test_wait_nested(tmpdir, fail):
    """Test waiting for background jobs created by background jobs.

    :param py.path.local tmpdir: pytest fixture.
    :param bool fail: Cause a failure during the run.
    """
    with build_image(tmpdir.join('root')) as (root, _, image_ids):
        post_title = root.ensure('hook-post-title.sh')
        post_title.write(
            'do_wait () {\n'
            '    for _ in {1..5}; do\n'
            '        if readlink /proc/*/exe |grep -q makemkvcon &> /dev/null; then sleep 1; else break; fi\n'
            '    done\n'
            '    sleep 5\n'
            '    echo do_wait done!\n'
            '}\n'
            'do_wait &\n'
        )
        if fail:
            root.ensure('hook-post-rip.sh').write('false\n', 'a')

    # Docker run.
    if fail:
        with pytest.raises(subprocess.CalledProcessError) as exc:
            pytest.run(image_id=image_ids[0])
        stdout, stderr = exc.value.output, exc.value.stderr
    else:
        stdout, stderr = pytest.run(image_id=image_ids[0])

    # Verify.
    assert b'do_wait done!' in stdout
