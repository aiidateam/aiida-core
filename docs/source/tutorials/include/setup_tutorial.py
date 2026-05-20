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

Every tutorial module runs this in a hidden cell so that data created in
earlier modules is available in later ones.

If you are running locally with your own profile (e.g. from ``verdi presto``),
replace the ``%run -i`` cell with::

    from aiida import load_profile
    load_profile()
"""

import hashlib
import os
import pathlib
import shutil
import time

from aiida import load_profile
from aiida.brokers.zmq.broker import ZmqBroker
from aiida.common.exceptions import NotExistent
from aiida.engine.daemon.client import get_daemon_client
from aiida.manage.configuration import create_profile, get_config
from aiida.manage.manager import get_manager
from aiida.orm import Computer, InstalledCode, load_code, load_computer

# Derive a short, time-based suffix from this script's mtime: stable across
# all modules in one build, but bumped whenever the setup logic changes,
# so stale profiles from older builds don't get reused.
_setup_mtime = int(pathlib.Path(__file__).stat().st_mtime)
_session_hash = hashlib.sha1(str(_setup_mtime).encode()).hexdigest()[:8]
profile_name = f'tutorial-{_session_hash}'
config = get_config()

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
