"""Test options exposed to users."""

import pytest


@pytest.mark.parametrize('debug', [None, False, True])
@pytest.mark.usefixtures('cdemu')
def test_debug(tmpdir, debug):
    """Test DEBUG environment variable.

    :param py.path.local tmpdir: pytest fixture.
    :param bool debug: Set environment variable to 'true', 'false', or don't set.
    """
    output = tmpdir.ensure_dir('output')
    if debug is True:
        args = ['-e', 'DEBUG=true']
    elif debug is False:
        args = ['-e', 'DEBUG=false']
    else:
        args = []

    # Docker run.
    stdout, stderr = pytest.run(args=args, output=output)

    # Verify.
    if debug is True:
        # Assert env is called.
        assert b'\n+ env' in stderr
        assert b'\nPATH=/' in stdout
        # Assert set +x is called.
        assert b'makemkvcon mkv' in stderr
        # Assert eject is verbose.
        assert b'\neject: device name is' in stdout
    else:
        assert b'\n+ env' not in stderr
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
        args = []

    # Docker run.
    stdout, stderr = pytest.run(args=args, output=output)

    # Verify.
    if no_eject is True:
        assert b'\nEjecting...' not in stdout
    else:
        assert b'\nEjecting...' in stdout
    assert b'\nCurrent operation: Scanning CD-ROM devices' in stdout
    assert b'\nDone after 00:00:' in stdout
