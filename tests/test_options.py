"""Test options exposed to users."""

import getpass

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
        args = list()

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


@pytest.mark.parametrize('gid', [-1, 0, 1000, 1234])
@pytest.mark.parametrize('uid', [-1, 0, 1000, 1234])
@pytest.mark.usefixtures('cdemu')
def test_ownership(tmpdir, gid, uid):
    """Test user and group IDs of directories and MKV files. 1000 is the default ID in the container.

    :param py.path.local tmpdir: pytest fixture.
    :param int gid: Set MKV_GID to this if not -1, otherwise don't set.
    :param int uid: Set MKV_UID to this if not -1, otherwise don't set.
    """
    output = tmpdir.ensure_dir('output')
    args = list()
    if gid >= 0:
        args += ['-e', 'MKV_GID={}'.format(gid)]
    if uid >= 0:
        args += ['-e', 'MKV_UID={}'.format(uid)]

    # Docker run.
    pytest.run(args=args, output=output)
    pytest.run(['sudo', 'setfacl', '-Rm', 'u:{}:rX'.format(getpass.getuser()), output])

    # Verify.
    pytest.verify(output, gid=1234 if gid == 1234 else 1000, uid=1234 if uid == 1234 else 1000)
