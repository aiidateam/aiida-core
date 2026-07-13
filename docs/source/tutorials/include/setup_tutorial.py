"""Shared tutorial profile setup.

Creates (or loads) a lightweight ``tutorial`` profile with:

* SQLite storage (no PostgreSQL required)
* ZMQ message broker (no external broker service required)
* A running daemon (so asynchronous submission works in later modules)
* A ``localhost`` Computer with local transport and direct scheduler
* A ``gsrd@localhost`` Code pointing to the ``gsrd`` CLI binary

The broker and daemon configuration matches what ``verdi presto`` sets up
on a fresh machine, so ``verdi status`` in the tutorial mirrors what users
will see locally.

Every tutorial module runs this in a visible setup cell, so that data created
in earlier modules is available in later ones. The profile is an isolated
sandbox: it never interferes with any AiiDA profile you already use, and stale
tutorial profiles from previous builds are cleaned up automatically.

If you would rather use your own existing profile (e.g. from ``verdi presto``),
replace the ``%run -i`` cell with::

    from aiida import load_profile
    load_profile()
"""

import hashlib
import os
import pathlib
import shutil
import time
from contextlib import suppress

from aiida import load_profile
from aiida.brokers import ZmqBroker
from aiida.common.exceptions import NotExistent
from aiida.engine import get_daemon_client
from aiida.engine.daemon.client import DaemonNotRunningException
from aiida.manage import get_manager
from aiida.manage.configuration import create_profile, get_config
from aiida.orm import Computer, InstalledCode, load_code, load_computer

# Derive a short suffix from the mtimes of all setup scripts: stable across
# all modules in one build, but bumped whenever any setup logic changes,
# so stale profiles from older builds don't get reused.
_include_dir = pathlib.Path(__file__).parent
_mtimes = sorted(int(p.stat().st_mtime) for p in _include_dir.glob('setup_*.py'))
_session_hash = hashlib.sha1(str(_mtimes).encode()).hexdigest()[:8]
profile_name = f'tutorial-{_session_hash}'
# ``create=True`` so a fresh machine (a new reader, or CI with no ~/.aiida yet)
# gets a config file created instead of raising. Existing configs are loaded
# untouched.
config = get_config(create=True)

# Remove stale tutorial profiles left over from previous builds: any
# ``tutorial-*`` profile whose hash differs from the current one. Safe to run
# from every module's setup cell, since it never touches the current profile
# (so data created in earlier modules survives) nor any of your own,
# non-tutorial profiles.
for _stale_name in [n for n in config.profile_names if n.startswith('tutorial-') and n != profile_name]:
    _stale_client = get_daemon_client(_stale_name)
    if _stale_client.is_daemon_running:
        # ``is_daemon_running`` only checks the PID file; the underlying circus
        # process may already be gone, in which case ``stop_daemon`` cleans the
        # PID file and then raises. Tolerate that.
        with suppress(DaemonNotRunningException):
            _stale_client.stop_daemon(wait=True)
    config.delete_profile(_stale_name, delete_storage=True)

if profile_name not in config.profile_names:
    create_profile(
        config,
        name=profile_name,
        email='tutorial@aiida.net',
        storage_backend='core.sqlite_dos',
        storage_config={},
        broker_backend='core.zmq',
        broker_config={},
    )
    config.set_option('runner.poll.interval', 1, scope=profile_name)
    config.set_option('warnings.development_version', False, scope=profile_name)
    config.set_default_profile(profile_name, overwrite=True)
    config.store()

load_profile(profile_name, allow_switch=True)
os.environ['AIIDA_PROFILE'] = profile_name

# Start the daemon (idempotent) so verdi status mirrors `verdi presto`'s.
_daemon_client = get_daemon_client(profile_name)
if not _daemon_client.is_daemon_running:
    _daemon_client.start_daemon()

# Wait for the ZMQ broker watcher to actually be up before continuing.
# `start_daemon` only waits for circusd itself, not for its child watchers,
# so a verdi status call right after can still see "Broker is NOT running".
_broker = get_manager().get_broker()
if isinstance(_broker, ZmqBroker):
    _deadline = time.monotonic() + 10.0
    while not _broker.is_running and time.monotonic() < _deadline:
        time.sleep(0.2)

# Ensure a localhost Computer exists (create_profile does not create one,
# unlike ``verdi presto``).
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

# Pre-register a Code pointing at the ``gsrd`` CLI binary installed in the
# active environment. ``gsrd`` is the small Gray-Scott reaction-diffusion
# simulator used throughout this tutorial; see https://github.com/aiidateam/gsrd.
_gsrd_executable = shutil.which('gsrd')
if _gsrd_executable is None:
    msg = (
        "Could not find the 'gsrd' executable in PATH. "
        'Install it with `pip install gsrd @ git+https://github.com/aiidateam/gsrd.git` '
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
