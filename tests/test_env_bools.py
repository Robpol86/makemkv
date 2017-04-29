"""Test boolean environment variable options."""

import pytest


@pytest.mark.parametrize('debug', [None, False, True])
@pytest.mark.usefixtures('cdemu')
def test_debug(tmpdir, debug):
    """Test DEBUG environment variable.

    :param py.path.local tmpdir: pytest fixture.
    :param bool debug: Set environment variable to 'true', 'false', or don't set.
    """
    output = tmpdir.ensure_dir('output')
    command = ['docker', 'run', '--device=/dev/cdrom', '-v', '{}:/output'.format(output), 'robpol86/makemkv']
    if debug is True:
        command = command[:-1] + ['-e', 'DEBUG=true'] + command[-1:]
    elif debug is False:
        command = command[:-1] + ['-e', 'DEBUG=false'] + command[-1:]

    # Docker run.
    stdout, stderr = pytest.run(command)

    # Verify.
    if debug is True:
        # Assert env is called.
        assert b'+ env' in stderr
        assert b'\nPATH=/' in stdout
        # Assert set +x is called.
        assert b'makemkvcon mkv' in stderr
        # Assert eject is verbose.
        assert b'\neject: device name is' in stdout
    else:
        assert b'+ env' not in stderr
        assert b'\nID_FS_TYPE=udf' not in stdout
        assert b'makemkvcon mkv' not in stderr
        assert b'\neject: device name is' not in stdout
    assert b'\nCurrent operation: Scanning CD-ROM devices' in stdout
    assert b'\nDone after 00:00:' in stdout


@pytest.mark.parametrize('no_eject', [None, False, True])
@pytest.mark.usefixtures('cdemu')
def test_no_eject(tmpdir, no_eject):
    """Test NO_EJECT environment variable.

    :param py.path.local tmpdir: pytest fixture.
    :param bool no_eject: Set environment variable to 'true', 'false', or don't set.
    """
    output = tmpdir.ensure_dir('output')
    if no_eject is True:
        args = ['-e', 'NO_EJECT=true']
    elif no_eject is False:
        args = ['-e', 'NO_EJECT=false']
    else:
        args = list()

    # Docker run.
    stdout, stderr = pytest.run(args=args, output=output)

    # Verify.
    if no_eject is True:
        assert b'\nEjecting...' not in stdout
    else:
        assert b'\nEjecting...' in stdout
    assert b'\nCurrent operation: Scanning CD-ROM devices' in stdout
    assert b'\nDone after 00:00:' in stdout
