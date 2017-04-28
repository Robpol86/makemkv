"""Test options exposed to users."""

import json

import py
import pytest


@pytest.mark.parametrize('volume', ['bind', 'data', 'unspecified'])
@pytest.mark.usefixtures('cdemu')
def test_volume(tmpdir, volume):
    """Test Docker volume configurations.

    :param py.path.local tmpdir: pytest fixture.
    :param str volume: Configuration to test.
    """
    output = tmpdir.ensure_dir('output')
    command = ['docker', 'run', '--device=/dev/cdrom', '-e', 'DEBUG=true', 'robpol86/makemkv']
    if volume == 'bind':
        command = command[:-1] + ['-v', '{}:/output'.format(output)] + command[-1:]
    elif volume == 'data':
        command = command[:-1] + ['-v', '/output'] + command[-1:]

    # Docker run.
    with pytest.container_ids_diff() as container_ids:
        pytest.run(command)
    assert len(container_ids) == 1
    cid = container_ids[0]

    # Verify.
    if volume == 'bind':
        pytest.verify(output, gid=1000, uid=1000, modes=('drwx------', '-rw-r--r--'))
    elif volume == 'data':
        stdout = pytest.run(['docker', 'inspect', cid])[0]
        parsed = json.loads(stdout)
        mount = parsed[0]['Mounts'][0]
        assert mount['Destination'] == '/output'
        output = py.path.local(mount['Source'])
        pytest.verify(output, gid=1000, uid=1000, modes=('drwx------', '-rw-r--r--'))
    elif volume == 'unspecified':
        pass
    else:
        raise NotImplementedError


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

    # Verify.
    pytest.verify(output, gid=1234 if gid == 1234 else 1000, uid=1234 if uid == 1234 else 1000)


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
