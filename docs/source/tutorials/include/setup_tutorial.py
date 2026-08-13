###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Shared tutorial profile setup, run as a visible cell at the top of every module.

Creates (or loads) an isolated ``tutorial-*`` profile in a sandbox config directory
(``.aiida-tutorial/`` in the working directory, via ``AIIDA_PATH``): SQLite storage, a
ZeroMQ broker, a running daemon, a ``localhost`` computer, and a ``gsrd@localhost`` code,
matching what ``verdi presto`` sets up. Nothing touches your real ``~/.aiida``; delete
``.aiida-tutorial/`` to remove every trace. The cell also fetches the shared ``include/``
helpers the modules import, so it is the intended entry point even if you already use AiiDA.
"""

import hashlib
import json
import os
import pathlib
import shutil
import sys
import time
import urllib.request
import warnings
from contextlib import suppress

from aiida import load_profile
from aiida.brokers import ZeromqBroker
from aiida.common.exceptions import NotExistent
from aiida.engine import get_daemon_client
from aiida.engine.daemon.client import DaemonException
from aiida.manage import get_manager
from aiida.manage.configuration import create_profile, get_config, reset_config
from aiida.manage.configuration.settings import AiiDAConfigDir
from aiida.orm import Computer, InstalledCode, load_code, load_computer


def _ensure_tutorial_helpers() -> None:
    """Fetch missing ``include/`` helpers so a notebook run outside the repo can import them.

    No-op when they are already present (repo clone, docs build).
    """
    include_dir = pathlib.Path('include')
    if all((include_dir / name).exists() for name in ('workflows.py', 'tasks.py', 'input.yaml')):
        return
    # TODO: switch to 'aiidateam/aiida-core' at the release tag once PR #7205 merges.
    repo, ref = 'GeigerJ2/aiida-core', 'docs/integrate-tutorials'
    api = f'https://api.github.com/repos/{repo}/contents/docs/source/tutorials/include?ref={ref}'
    include_dir.mkdir(exist_ok=True)
    for entry in json.loads(urllib.request.urlopen(api).read()):
        if entry['type'] == 'file' and not (include_dir / entry['name']).exists():
            urllib.request.urlretrieve(entry['download_url'], include_dir / entry['name'])


_ensure_tutorial_helpers()


# Suffix the profile name with a hash of the setup scripts' mtimes: stable within one build,
# bumped when setup logic changes so stale profiles are not reused. Use ``include/`` relative
# to the CWD (``__file__`` is undefined in a pasted cell).
_include_dir = pathlib.Path('include')
_mtimes = sorted(int(p.stat().st_mtime) for p in _include_dir.glob('setup_*.py'))
_session_hash = hashlib.sha1(str(_mtimes).encode()).hexdigest()[:8]
profile_name = f'tutorial-{_session_hash}'

# Isolate everything in its own config dir, so it never touches your real ``~/.aiida``.
# ``AIIDA_TUTORIAL_SANDBOX`` lets the docs build relocate it out of the sphinx-watched source
# tree (see ``conf.py``); pasted notebooks use ``.aiida-tutorial/`` in the CWD. Always overwrite
# ``AIIDA_PATH`` (never a user's exported value) to stay isolated.
_sandbox_dir = os.environ.get('AIIDA_TUTORIAL_SANDBOX', '.aiida-tutorial')
os.environ['AIIDA_PATH'] = str(pathlib.Path(_sandbox_dir).resolve())

# Silence the "Creating AiiDA configuration folder" warning (we create the sandbox on purpose);
# ``create=True`` creates its config on first run and loads it untouched afterwards.
with warnings.catch_warnings():
    warnings.filterwarnings('ignore', message='Creating AiiDA configuration folder')
    AiiDAConfigDir.set()  # re-read AIIDA_PATH and create the sandbox config dir
    reset_config()  # drop any config already loaded for a different directory
    config = get_config(create=True)

# Remove stale ``tutorial-*`` profiles from earlier runs (never the current one, so data from
# earlier modules survives). Best-effort: a leftover must never block startup.
for _stale_name in [n for n in config.profile_names if n.startswith('tutorial-') and n != profile_name]:
    try:
        _stale_client = get_daemon_client(_stale_name)
        if _stale_client.is_daemon_running:
            # is_daemon_running only checks the PID file; the circus process may be gone
            # (stop_daemon then cleans the file and raises) or unreachable. Tolerate both.
            with suppress(DaemonException):
                _stale_client.stop_daemon(wait=True)
        config.delete_profile(_stale_name, delete_storage=True)
    except Exception as _exc:  # best-effort cleanup, never fatal
        print(f'Note: could not remove stale tutorial profile {_stale_name!r}: {_exc}')

if profile_name not in config.profile_names:
    create_profile(
        config,
        name=profile_name,
        email='tutorial@aiida.net',
        storage_backend='core.sqlite_dos',
        storage_config={},
        broker_backend='core.zeromq',
        broker_config={},
    )
    config.set_option('runner.poll.interval', 1, scope=profile_name)
    config.set_option('warnings.development_version', False, scope=profile_name)
    config.set_default_profile(profile_name, overwrite=True)
    config.store()

load_profile(profile_name, allow_switch=True)
os.environ['AIIDA_PROFILE'] = profile_name

# Start the daemon (idempotent) so ``verdi status`` mirrors ``verdi presto``'s. is_daemon_running
# only checks the PID file, which a kernel restart or reboot can leave stale; clean a stale one
# first (a healthy daemon's file is untouched).
_daemon_client = get_daemon_client(profile_name)
_daemon_client._clean_potentially_stale_pid_file()
if not _daemon_client.is_daemon_running:
    _daemon_client.start_daemon()

# Wait for the ZMQ broker watcher: start_daemon only waits for circusd, not its child watchers,
# so a verdi status right after can still see "Broker is NOT running".
_broker = get_manager().get_broker()
if isinstance(_broker, ZeromqBroker):
    _deadline = time.monotonic() + 10.0
    while not _broker.check_service_reachable() and time.monotonic() < _deadline:
        time.sleep(0.2)

# create_profile does not create a localhost Computer (unlike ``verdi presto``).
try:
    computer = load_computer('localhost')
except NotExistent:
    computer = Computer(
        label='localhost',
        hostname='localhost',
        description='Localhost for tutorial',
        transport_type='core.local',
        scheduler_type='core.direct',
        workdir=str(pathlib.Path(config.dirpath) / 'scratch' / profile_name),
    ).store()
    computer.configure(safe_interval=0)
    computer.set_minimum_job_poll_interval(1)
    computer.set_default_mpiprocs_per_machine(1)

# Pre-register a Code for the ``gsrd`` CLI (https://github.com/aiidateam/gsrd).
_gsrd_executable = shutil.which('gsrd')
if _gsrd_executable is None:
    # Some environments (e.g. ReadTheDocs) install the console script next to the interpreter
    # without putting that directory on PATH, so ``shutil.which`` misses it.
    _candidate = pathlib.Path(sys.executable).parent / 'gsrd'
    if _candidate.is_file():
        _gsrd_executable = str(_candidate)
if _gsrd_executable is None:
    msg = (
        "Could not find the 'gsrd' executable. "
        'Install it with '
        '`uv pip install "gsrd @ git+https://github.com/aiidateam/gsrd.git"` '
        'before running the tutorial.'
    )
    raise RuntimeError(msg)

try:
    gsrd_code = load_code('gsrd@localhost')
except NotExistent:
    gsrd_code = InstalledCode(
        label='gsrd',
        computer=computer,
        filepath_executable=_gsrd_executable,
        default_calc_job_plugin='core.shell',
    ).store()
