"""Test error handling of scripts."""

import subprocess

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
