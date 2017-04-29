"""Test error handling of scripts."""

import os
import pty
import subprocess

import py
import pytest

HERE = os.path.dirname(__file__)


@pytest.mark.usefixtures('cdemu')
def test_low_space(request, tmpdir):
    """Test low free space handling.

    :param request: pytest fixture.
    :param py.path.local tmpdir: pytest fixture.
    """
    # Create a 5 MiB filesystem container.
    fs_bin = tmpdir.join('fs.bin')
    with fs_bin.open('w') as handle:
        handle.truncate(1024 * 1024 * 5)
    pytest.run(['mkfs.ext4', '-F', fs_bin])

    # Mount the filesystem.
    output = tmpdir.ensure_dir('output')
    pytest.run(['sudo', 'mount', '-t', 'ext4', '-o', 'loop', fs_bin, output])
    request.addfinalizer(lambda: pytest.run(['sudo', 'umount', output]))

    # Docker run.
    with pytest.raises(subprocess.CalledProcessError) as exc:
        pytest.run(output=output)
    assert b'Terminating MakeMKV due to low disk space.' in exc.value.stderr


def test_read_error(request, tmpdir):
    """Test disc opening error handling.

    :param request: pytest fixture.
    :param py.path.local tmpdir: pytest fixture.
    """
    # Create truncated ISO.
    iso = tmpdir.join('truncated.iso')
    py.path.local(__file__).dirpath().join('sample.iso').copy(iso)
    with iso.open('rb+') as handle:
        handle.truncate(1024000)

    # Load the ISO.
    pytest.cdload(iso)
    request.addfinalizer(pytest.cdunload)

    # Docker run.
    output = tmpdir.ensure_dir('output')
    with pytest.raises(subprocess.CalledProcessError) as exc:
        pytest.run(output=output)
    assert b'Failed to open disc' in exc.value.output


def test_rip_error(request, tmpdir):
    """Test failed rips error handling.

    :param request: pytest fixture.
    :param py.path.local tmpdir: pytest fixture.
    """
    # Duplicate ISO.
    iso = tmpdir.join('truncated.iso')
    py.path.local(__file__).dirpath().join('sample.iso').copy(iso)

    # Load the ISO.
    pytest.cdload(iso)
    request.addfinalizer(pytest.cdunload)

    # Execute.
    output = tmpdir.ensure_dir('output')
    command = ['docker', 'run', '--device=/dev/cdrom', '-v', '{}:/output'.format(output), '-e', 'DEBUG=true',
               'robpol86/makemkv']
    master, slave = pty.openpty()
    request.addfinalizer(lambda: [os.close(master), os.close(slave)])
    proc = subprocess.Popen(command, bufsize=1, cwd=HERE, stderr=subprocess.STDOUT, stdin=slave, stdout=subprocess.PIPE)

    # Read output.
    caught = False
    while proc.poll() is None or proc.stdout.peek(1):
        for line in proc.stdout:
            # Watch for specific line, then truncate ISO.
            if b'Analyzing seamless segments' in line:
                iso.open('w').close()
            elif b'ERROR: One or more titles failed.' in line:
                caught = True
            print(line)  # Write to stdout, pytest will print if test fails.

    # Verify.
    assert proc.poll() > 0
    assert caught is True


def test_no_disc(tmpdir):
    """Test no disc in device handling.

    :param py.path.local tmpdir: pytest fixture.
    """
    output = tmpdir.ensure_dir('output')
    command = ['docker', 'run', '--device=/dev/sr0', '-v', '{}:/output'.format(output), '-e', 'DEBUG=true',
               'robpol86/makemkv']
    pytest.cdunload()

    with pytest.raises(subprocess.CalledProcessError) as exc:
        pytest.run(command)
    assert b'Failed to open disc' in exc.value.output


@pytest.mark.parametrize('devname', ['', '/dev/dne', '/dev/does not exist'])
def test_no_device(tmpdir, devname):
    """Test no optical device handling.

    :param py.path.local tmpdir: pytest fixture.
    :param str devname: Set DEVNAME to this if truthy.
    """
    output = tmpdir.ensure_dir('output')
    command = ['docker', 'run', '-v', '{}:/output'.format(output), '-e', 'DEBUG=true', 'robpol86/makemkv']
    if devname:
        command = command[:-1] + ['-e', 'DEVNAME={}'.format(devname)] + command[-1:]

    with pytest.raises(subprocess.CalledProcessError) as exc:
        pytest.run(command)
    assert not list(output.visit())

    if devname:
        assert b'Device %s not a block-special file.' % devname.encode('utf8') in exc.value.stderr
    else:
        assert b'ERROR: Unable to find optical device.' in exc.value.stderr
