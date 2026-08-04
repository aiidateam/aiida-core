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

Every tutorial module runs this in a visible setup cell, so that data created in
earlier modules is available in later ones (when the modules run in the same
working directory).

The whole tutorial is confined to its own configuration directory,
``.aiida-tutorial/`` in the current working directory, set via ``AIIDA_PATH``.
It therefore never interferes with an AiiDA setup you may already have: nothing
is written into your real ``~/.aiida``, your default profile is left alone, and
your running daemons are untouched. This works the same whether the cell runs in
the docs build (CI), in a downloaded notebook, or pasted into your own notebook.
Delete ``.aiida-tutorial/`` to remove every trace of the tutorial.

If you would rather use your own existing profile (e.g. from ``verdi presto``),
skip this setup cell entirely and load your profile instead::

    from aiida import load_profile
    load_profile()
"""

import hashlib
import json
import os
import pathlib
import shutil
import sys
import time
import urllib.request
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
    """Fetch any missing tutorial helper files into ``include/``.

    Lets a notebook running outside the tutorial repository (for example, cells
    pasted into your own notebook) import the shared helpers. No-op when they
    are already present, as in a repo clone or the docs build.
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


# Derive a short suffix from the mtimes of all setup scripts: stable across
# all modules in one build, but bumped whenever any setup logic changes,
# so stale profiles from older builds don't get reused.
# ``include/`` relative to the working directory (not ``__file__``), so this still
# works when the cell is inlined into a downloaded notebook, where ``__file__`` is
# undefined. Matches the path used by ``_ensure_tutorial_helpers`` above.
_include_dir = pathlib.Path('include')
_mtimes = sorted(int(p.stat().st_mtime) for p in _include_dir.glob('setup_*.py'))
_session_hash = hashlib.sha1(str(_mtimes).encode()).hexdigest()[:8]
profile_name = f'tutorial-{_session_hash}'

# Isolate the whole tutorial in its own configuration directory (``.aiida-tutorial/``
# in the current working directory), so it never touches an AiiDA setup you may
# already have: no profiles written into your real ``~/.aiida``, no change to your
# default profile, no interaction with your running daemons. ``AIIDA_PATH`` also
# propagates to ``!verdi`` shell calls in the notebook, so they see this same
# sandbox. Delete ``.aiida-tutorial/`` to remove every trace of the tutorial.
os.environ['AIIDA_PATH'] = str(pathlib.Path('.aiida-tutorial').resolve())
AiiDAConfigDir.set()  # re-read AIIDA_PATH (set above) and create the sandbox config dir
reset_config()  # drop any config already loaded for a different directory

# ``create=True`` so the sandbox config file is created on first run instead of
# raising. On later runs the existing sandbox config is loaded untouched.
config = get_config(create=True)

# Remove stale tutorial profiles left over from previous runs in this sandbox: any
# ``tutorial-*`` profile whose hash differs from the current one. Safe to run from
# every module's setup cell, since it never touches the current profile (so data
# created in earlier modules survives), and the sandbox never contains any of your
# own profiles. Best-effort: a leftover we cannot fully remove must never block the
# tutorial from starting.
for _stale_name in [n for n in config.profile_names if n.startswith('tutorial-') and n != profile_name]:
    try:
        _stale_client = get_daemon_client(_stale_name)
        if _stale_client.is_daemon_running:
            # ``is_daemon_running`` only checks the PID file; the underlying circus
            # process may already be gone (``stop_daemon`` then cleans the PID file
            # and raises), or unreachable (a timeout). Tolerate either.
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

# Start the daemon (idempotent) so verdi status mirrors `verdi presto`'s.
_daemon_client = get_daemon_client(profile_name)
# ``is_daemon_running`` only checks that the PID file exists. That file can be left
# behind stale when the daemon is killed without cleanup (a kernel restart between
# runs, a reboot), which then makes ``verdi status`` report the daemon unreachable.
# Remove a stale PID file first (a healthy daemon's file is left untouched) so the
# check below reflects reality, then (re)start when needed.
_daemon_client._clean_potentially_stale_pid_file()
if not _daemon_client.is_daemon_running:
    _daemon_client.start_daemon()

# Wait for the ZMQ broker watcher to actually be up before continuing.
# `start_daemon` only waits for circusd itself, not for its child watchers,
# so a verdi status call right after can still see "Broker is NOT running".
_broker = get_manager().get_broker()
if isinstance(_broker, ZeromqBroker):
    _deadline = time.monotonic() + 10.0
    while not _broker.check_service_reachable() and time.monotonic() < _deadline:
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
    # Some environments (e.g. the ReadTheDocs build) install the ``gsrd`` console
    # script next to the interpreter without adding that directory to PATH, so
    # ``shutil.which`` misses it; look there before giving up.
    _candidate = pathlib.Path(sys.executable).parent / 'gsrd'
    if _candidate.is_file():
        _gsrd_executable = str(_candidate)
if _gsrd_executable is None:
    msg = (
        "Could not find the 'gsrd' executable. "
        'Install it with '
        '`uv pip install "gsrd @ git+https://github.com/GeigerJ2/gsrd.git@fix/dont-raise-on-trivial-state"` '
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
