"""Test error handling of scripts."""

import subprocess
from textwrap import dedent

import py
import pytest


@pytest.mark.usefixtures('cdemu')
def test_low_space(request, tmpdir):
    """Test low free space handling.

    :param request: pytest fixture.
    :param py.path.local tmpdir: pytest fixture.
    """
    # Create a 5 MiB filesystem container.
    fs_bin = tmpdir.join('fs.bin')
    with fs_bin.open('wb') as handle:
        for _ in range(524288):
            handle.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
    pytest.run(['mkfs.ext4', '-F', fs_bin], pty_stdin=False)

    # Mount the filesystem.
    output = tmpdir.ensure_dir('output')
    pytest.run(['sudo', 'mount', '-t', 'ext4', '-o', 'loop', fs_bin, output], pty_stdin=False)
    request.addfinalizer(lambda: pytest.run(['sudo', 'umount', output], pty_stdin=False))

    # Docker run.
    with pytest.raises(subprocess.CalledProcessError) as exc:
        pytest.run(['docker', 'run', '-it', '--device=/dev/cdrom',
                    '-v', '{}:/output'.format(output), 'robpol86/makemkv'])
    assert b'Terminating MakeMKV due to low disk space.' in exc.value.output


def test_read_error(request, tmpdir):
    """Test disc opening error handling.

    :param request: pytest fixture.
    :param py.path.local tmpdir: pytest fixture.
    """
    # Create corrupt ISO.
    iso = tmpdir.join('corrupt.iso')
    py.path.local(__file__).dirpath().join('sample.iso').copy(iso)
    with iso.open('rb+') as handle:
        handle.seek(102400)
        for _ in range(100000):
            handle.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')

    # Load the ISO.
    pytest.cdload(iso)
    request.addfinalizer(pytest.cdunload)

    # Docker run.
    output = tmpdir.ensure_dir('output')
    with pytest.raises(subprocess.CalledProcessError) as exc:
        pytest.run(['docker', 'run', '-it', '--device=/dev/cdrom',
                    '-v', '{}:/output'.format(output), 'robpol86/makemkv'])
    assert b'Failed to open disc' in exc.value.output


def test_rip_error(request, tmpdir):
    """Test failed rips error handling.

    :param request: pytest fixture.
    :param py.path.local tmpdir: pytest fixture.
    """
    # Duplicate ISO.
    iso = tmpdir.join('duplicate.iso')
    py.path.local(__file__).dirpath().join('sample.iso').copy(iso)

    # Load the ISO.
    pytest.cdload(iso)
    request.addfinalizer(pytest.cdunload)

    # Create abrupt zeroing script.
    script = tmpdir.join('script.sh')
    script.write(dedent("""\
        #!/bin/bash
        ISO="$2"
        abrupt_zero () {
            local ret=0
            sed -u "/Analyzing seamless segments/q5" || ret=$?
            [ ${ret} -ne 5 ] && return
            echo "ZEROING OUT ISO FILE"
            dd bs=4096 seek=177 count=1 if=/dev/zero of="$ISO"
            sync
            cat
        }
        docker run -it --device=/dev/cdrom -v $1:/output robpol86/makemkv |abrupt_zero
        exit ${PIPESTATUS[0]}
        """))

    # Run.
    output = tmpdir.ensure_dir('output')
    with pytest.raises(subprocess.CalledProcessError) as exc:
        pytest.run(['bash', script, output, iso])
    assert b'ERROR: One or more titles failed.' in exc.value.output
