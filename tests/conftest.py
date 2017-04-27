"""pytest fixtures."""

import os
import pty
import subprocess
import time

import py
import pytest

HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, '..'))


def run(command=None, args=None, output=None, environ=None, cwd=None, pty_stdin=True):
    """Run a command and return the output. Supports string and py.path paths.

    :raise CalledProcessError: Command exits non-zero.

    :param iter command: Command to run.
    :param iter args: List of command line arguments to insert to command.
    :param str output: Path to bind mount to /output when `command` is None.
    :param dict environ: Environment variables to set/override in the command.
    :param str cwd: Current working directory. Default is tests directory.
    :param bool pty_stdin: Spawn a fake pty in memory to please Docker.

    :return: Command stdout and stderr output.
    :rtype: tuple
    """
    if command is None:
        assert output is not None
        command = ['docker', 'run', '--device=/dev/cdrom', '-v', '{}:/output'.format(output), 'robpol86/makemkv']
    if args:
        command = command[:-1] + list(args) + command[-1:]

    env = os.environ.copy()
    if environ:
        env.update(environ)

    # Simulate stdin pty so 'docker run -it' doesn't complain.
    master, slave = pty.openpty() if pty_stdin else (0, 0)

    # Run command.
    try:
        result = subprocess.run(
            [str(i) for i in command], check=True, cwd=cwd or HERE, env=env,
            stderr=subprocess.PIPE, stdin=slave or None, stdout=subprocess.PIPE,
            timeout=30
        )
    finally:
        if pty_stdin:
            os.close(slave)
            os.close(master)

    return result.stdout, result.stderr


def cdload(path=None):
    """Load the ISO into the virtual CD-ROM device.

    :param path: File path of ISO file to load if not sample.iso.
    """
    try:
        run(['cdemu', 'load', '0', path or 'sample.iso'])
    except subprocess.CalledProcessError as exc:
        if b'AlreadyLoaded' not in exc.stderr:
            raise

    for _ in range(50):
        if os.path.exists('/dev/cdrom'):
            return
        time.sleep(0.1)
    if not os.path.exists('/dev/cdrom'):
        raise IOError('Failed to load cdemu device!')


def cdunload():
    """Eject the ISO from the virtual CD-ROM device."""
    for _ in range(3):
        run(['cdemu', 'unload', '0'])
        for _ in range(50):
            if not os.path.exists('/dev/cdrom'):
                return
            time.sleep(0.1)
    if os.path.exists('/dev/cdrom'):
        raise IOError('Failed to unload cdemu device!')


def pytest_namespace():
    """Add objects to the pytest namespace. Can be retrieved by importing pytest and accessing pytest.<name>.

    :return: Namespace dict.
    :rtype: dict
    """
    return dict(
        cdload=cdload,
        cdunload=cdunload,
        ROOT=py.path.local(ROOT),
        run=run,
    )


@pytest.fixture
def cdemu():
    """Load sample.iso before running test function, then unload."""
    cdload()
    yield
    cdunload()
