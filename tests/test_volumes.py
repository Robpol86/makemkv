"""Test compatibility with different Docker volume types."""

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
