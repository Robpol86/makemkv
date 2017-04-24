"""Test commands in README.md."""

import os
import re
import stat
import time

import py
import pytest

OUTPUT = py.path.local('/tmp/MakeMKV')


def verify():
    """Verify the output directory after test runs in this module."""
    # Verify tree.
    tree = sorted(OUTPUT.visit(), key=str)
    assert len(tree) == 2
    assert tree[0].fnmatch('/tmp/MakeMKV/Sample_2017-04-15-15-16-14-00_???')
    assert tree[1].fnmatch('/tmp/MakeMKV/Sample_2017-04-15-15-16-14-00_???/title00.mkv')

    # Verify file attributes.
    mkv_stat = tree[1].stat()
    assert mkv_stat.uid == os.getuid()
    assert mkv_stat.gid == os.getgid()
    assert 17345210 < mkv_stat.size < 17345220  # Target size is 17345216. May deviate a byte or two.
    assert stat.filemode(mkv_stat.mode) == '-rw-r--r--'


def write_udev(contents=''):
    """Write data to 85-makemkv.rules file then reload udev rules.

    :param str contents: Contents of file to write.
    """
    script = py.path.local('/etc/udev/rules.d/85-makemkv.rules')
    script.write(contents)
    pytest.run(['sudo', 'udevadm', 'control', '--reload'], pty_stdin=False)


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
    verify()


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
    if OUTPUT.check() and OUTPUT.listdir():
        OUTPUT.remove()
    OUTPUT.ensure_dir()
    pytest.cdload()
    for _ in range(30):
        if list(OUTPUT.visit(fil='Sample_2017-04-15-15-16-14-00_???/title00.mkv')):
            break
        time.sleep(0.5)

    # Verify.
    verify()
