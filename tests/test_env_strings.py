"""Test integer/numeric environment variable options."""

import pytest


@pytest.mark.parametrize('devname', ['', '/dev/cdrom', '/dev/sr0'])
@pytest.mark.usefixtures('cdemu')
def test_devname(tmpdir, devname):
    """Test DEVNAME environment variable.

    :param py.path.local tmpdir: pytest fixture.
    :param str devname: Set environment variable to this.
    """
    output = tmpdir.ensure_dir('output')
    command = ['docker', 'run', '-v', '{}:/output'.format(output), '-e', 'DEBUG=true', 'robpol86/makemkv']

    # Docker acts weird with /dev/cdrom and /dev/sr0 specified at the same time. Workaround:
    if devname == '/dev/sr0':
        command = command[:-1] + ['--device=/dev/sr0'] + command[-1:]
    else:
        command = command[:-1] + ['--device=/dev/cdrom', '--device=/dev/sr0'] + command[-1:]

    # Add env variable.
    if devname:
        command = command[:-1] + ['-e', 'DEVNAME={}'.format(devname)] + command[-1:]

    # Docker run.
    stdout, stderr = pytest.run(command)

    # Verify.
    assert b'--directio true dev:%s all' % (devname or '/dev/cdrom').encode('utf8') in stderr
    assert b'+ eject --verbose %s' % (devname or '/dev/cdrom').encode('utf8') in stderr
    assert b'\nDone after 00:00:' in stdout
    pytest.verify(output, gid=1000, uid=1000)
