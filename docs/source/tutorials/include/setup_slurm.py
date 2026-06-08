"""SSH plumbing for the SLURM container used by Module 4.

The docs build starts a ``xenonmiddleware/slurm:17`` Docker container that
exposes SSH on port 5001. This script:

1. Copies the pre-generated SSH key into a tempdir (NOT ``~/.ssh/``).
2. Runs ``ssh-keyscan`` against the container into a dedicated known_hosts
   file in the same tempdir.
3. Appends a small marker-gated ``Host slurm-ssh`` block to ``~/.ssh/config``
   that points at the tempdir files. ``~/.ssh/known_hosts`` is never touched.

The actual computer/code registration happens in live ``verdi`` cells inside
the tutorial notebook. This script only handles the SSH plumbing that would
be distracting to show in the tutorial.

If the SLURM container is not reachable (e.g. when running locally without
Docker), the script prints a warning and skips the setup.

Why ssh-keyscan and not ``UserKnownHostsFile /dev/null``: a previous version
disabled host-key verification with ``/dev/null`` + ``StrictHostKeyChecking
no``. That worked for OpenSSH but not for asyncssh (the aiida-core transport
backend), which resolves ``/dev/null`` into ``known_hosts=[]`` and refuses
the connection. The ssh-keyscan approach keeps host-key verification on,
works for both backends, and is MITM-safe over the localhost loopback.

Why ``~/.ssh/config`` still gets touched: aiida-core's asyncssh transport
calls ``asyncssh.connect(machine)`` with no way to inject a custom config
file, so the ``Host slurm-ssh`` alias has to live somewhere asyncssh reads
by default. The block here is marker-delimited and idempotently rewritten,
so removing it (or this file) leaves no trace beyond a single section in
``~/.ssh/config``.
"""

import pathlib
import re
import shutil
import socket
import subprocess
import tempfile

SLURM_SSH_HOST = 'localhost'
SLURM_SSH_PORT = 5001
SLURM_SSH_USER = 'xenon'
COMPUTER_LABEL = 'slurm-ssh'

repo_root = pathlib.Path(__file__).resolve().parents[5]
slurm_key_src = repo_root / '.github' / 'config' / 'slurm_rsa'

# Sensitive state lives in a tempdir, not ``~/.ssh/``. ``/tmp`` survives a
# sphinx build but not a reboot, which is fine: every M4 build self-heals.
state_dir = pathlib.Path(tempfile.gettempdir()) / 'aiida-tutorial-slurm'
state_dir.mkdir(mode=0o700, exist_ok=True)
slurm_key = state_dir / 'slurm_rsa'
slurm_known_hosts = state_dir / 'known_hosts'

ssh_dir = pathlib.Path.home() / '.ssh'
ssh_dir.mkdir(mode=0o700, exist_ok=True)
ssh_config = ssh_dir / 'config'

MARKER_START = f'# --- AiiDA tutorial ({COMPUTER_LABEL}) START ---'
MARKER_END = f'# --- AiiDA tutorial ({COMPUTER_LABEL}) END ---'
LEGACY_MARKER = f'# --- AiiDA tutorial ({COMPUTER_LABEL}) ---'


def _container_reachable() -> bool:
    """Check whether the SLURM container's SSH port is open."""
    try:
        with socket.create_connection((SLURM_SSH_HOST, SLURM_SSH_PORT), timeout=2):
            return True
    except OSError:
        return False


def _strip_legacy_block(text: str) -> str:
    """Remove a pre-MARKER_START/END tutorial block from ``~/.ssh/config``.

    Older versions of this script wrote a single-marker block ending at the
    next blank line. Detect that shape and remove it so the new block does
    not conflict (SSH config rules: first matching ``Host`` directive wins).
    """
    pattern = re.compile(
        rf'(?:^|\n){re.escape(LEGACY_MARKER)}\n(?:[^\n]*\n)*?(?=\n|\Z)',
    )
    return pattern.sub('', text)


def _strip_current_block(text: str) -> str:
    """Remove any existing MARKER_START/END block from ``~/.ssh/config``."""
    pattern = re.compile(
        rf'(?:^|\n){re.escape(MARKER_START)}\n.*?{re.escape(MARKER_END)}\n?',
        re.DOTALL,
    )
    return pattern.sub('', text)


if not _container_reachable():
    print(
        f'WARNING: SLURM container not reachable at {SLURM_SSH_HOST}:{SLURM_SSH_PORT}. '
        'Module 4 remote-execution cells will not work. '
        'Start the container with: docker run -d -p 5001:22 xenonmiddleware/slurm:17'
    )
else:
    if not slurm_key_src.exists():
        msg = f'expected SSH key for the SLURM container at {slurm_key_src}, but the file is missing'
        raise FileNotFoundError(msg)

    # 1. Private key in the tempdir (overwrite if stale).
    if not slurm_key.exists() or slurm_key.read_bytes() != slurm_key_src.read_bytes():
        shutil.copy(slurm_key_src, slurm_key)
    slurm_key.chmod(0o600)

    # 2. Host-key trust: scan the container fresh on every build. Localhost
    # loopback, so no network MITM surface. Rescanning self-heals when the
    # container restarts with a new key.
    scan = subprocess.run(
        ['ssh-keyscan', '-p', str(SLURM_SSH_PORT), SLURM_SSH_HOST],
        capture_output=True,
        text=True,
        check=True,
    )
    slurm_known_hosts.write_text(scan.stdout)
    slurm_known_hosts.chmod(0o600)

    # 3. ``~/.ssh/config`` block: marker-delimited, idempotently rewritten.
    # Only references files in ``state_dir``; ``~/.ssh/known_hosts`` is
    # never touched.
    new_block = (
        f'{MARKER_START}\n'
        f'Host {COMPUTER_LABEL}\n'
        f'    HostName {SLURM_SSH_HOST}\n'
        f'    User {SLURM_SSH_USER}\n'
        f'    Port {SLURM_SSH_PORT}\n'
        f'    IdentityFile {slurm_key}\n'
        f'    UserKnownHostsFile {slurm_known_hosts}\n'
        f'    LogLevel ERROR\n'
        f'{MARKER_END}\n'
    )
    existing = ssh_config.read_text() if ssh_config.exists() else ''
    cleaned = _strip_current_block(_strip_legacy_block(existing)).rstrip('\n')
    separator = '\n\n' if cleaned else ''
    ssh_config.write_text(f'{cleaned}{separator}{new_block}')
    ssh_config.chmod(0o600)
