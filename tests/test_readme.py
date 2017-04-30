"""Test commands in README.md."""

import os
import re
import time

import py
import pytest

OUTPUT = py.path.local('/tmp/MakeMKV')


def write_udev(contents=''):
    """Write data to 85-makemkv.rules file then reload udev rules.

    :param str contents: Contents of file to write.
    """
    script = py.path.local('/etc/udev/rules.d/85-makemkv.rules')
    script.write(contents)
    pytest.run(['sudo', 'udevadm', 'control', '--reload'])


@pytest.mark.usefixtures('cdemu')
def test_manual(tmpdir):
    """Test example commands in "Run Manually" README section.

    :param py.path.local tmpdir: pytest fixture.
    """
    # Grab commands from README.
    with pytest.ROOT.join('README.md').open() as handle:
        for line in handle:
            if line.strip() == 'Now go ahead and run the image:':
                break
        partial = handle.read(1024)
    contents = re.compile(r'\n```bash\n(.+?)\n```\n', re.DOTALL).findall(partial)[0]
    script = tmpdir.join('script.sh')
    script.write(contents)

    # Run.
    if OUTPUT.check():
        OUTPUT.remove()
    pytest.run(['bash', script])
    assert OUTPUT.check()

    # Verify.
    pytest.verify(OUTPUT, gid=os.getgid(), uid=os.getuid(), modes=('drwxr-xr-x', '-rw-r--r--'))


def test_udev(request):
    """Test example udev rule in "Automated Run" README section.

    :param request: pytest fixture.
    """
    request.addfinalizer(pytest.cdunload)

    # Grab udev rule from README.
    with pytest.ROOT.join('README.md').open() as handle:
        for line in handle:
            if line.strip() == '## Automated Run':
                break
        partial = handle.read(1024)
    contents = re.compile(r'\n```\n(.+?)\n```\n', re.DOTALL).findall(partial)[0]
    write_udev(contents)
    request.addfinalizer(write_udev)  # Truncate.

    # Run.
    with pytest.container_ids_diff() as container_ids:
        if OUTPUT.check() and OUTPUT.listdir():
            OUTPUT.remove()
        OUTPUT.ensure_dir()
        pytest.cdload()
    assert len(container_ids) == 1
    cid = container_ids[0]

    # Wait up to 15 seconds for container to exit.
    for _ in range(30):
        if not pytest.run(['docker', 'ps', '-qf', 'id={}'.format(cid)])[0]:
            break
        time.sleep(0.5)

    # Verify.
    pytest.verify(OUTPUT, gid=os.getgid(), uid=os.getuid(), modes=('drwxr-xr-x', '-rw-r--r--'))
