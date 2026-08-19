###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Set up the tutorial's isolated AiiDA profile, run once at the top of each module.

Uses the same commands you would for your own work: ``verdi presto`` creates the profile (SQLite
storage, ZeroMQ broker, and a configured ``localhost`` computer), ``verdi code create`` registers
the ``gsrd`` CLI as a Code from ``gsrd_code.yaml``, and ``verdi daemon start`` brings the daemon up.
Everything lives in a ``.aiida-tutorial/`` sandbox (via ``AIIDA_PATH``) so nothing touches your real
``~/.aiida``; delete that folder to remove every trace. Module 1 creates the profile; the later
modules find it already there and just reconnect.
"""

import os
import shlex
import shutil
import subprocess
import sys
import time
import warnings
from pathlib import Path

from aiida import load_profile
from aiida.manage import get_manager
from aiida.manage.configuration import get_config, reset_config
from aiida.manage.configuration.settings import AiiDAConfigDir
from aiida.orm import load_code

PROFILE_NAME = 'tutorial'


def run_verdi(command: str) -> None:
    """Run a ``verdi`` CLI command, e.g. ``run_verdi('daemon start')``."""
    subprocess.run(['verdi', *shlex.split(command)], check=True)


def _ensure_helpers() -> None:
    """Download the ``include/`` helper files when running outside the repo (a no-op inside it)."""
    import json
    import urllib.request

    include = Path('include')
    if all((include / name).exists() for name in ('workflows.py', 'tasks.py', 'input.yaml', 'gsrd_code.yaml')):
        return
    # TODO: switch to 'aiidateam/aiida-core' at the release tag once PR #7205 merges.
    api = 'https://api.github.com/repos/GeigerJ2/aiida-core/contents/docs/source/tutorials/include?ref=docs/integrate-tutorials'
    include.mkdir(exist_ok=True)
    for entry in json.load(urllib.request.urlopen(api)):
        if entry['type'] == 'file' and not (include / entry['name']).exists():
            urllib.request.urlretrieve(entry['download_url'], include / entry['name'])


_ensure_helpers()

# Isolate AiiDA in a local sandbox so the tutorial never touches your real ``~/.aiida``; then
# re-read ``AIIDA_PATH`` so AiiDA uses it even if a profile was already loaded in this kernel.
os.environ['AIIDA_PATH'] = str(Path(os.environ.get('AIIDA_TUTORIAL_SANDBOX', '.aiida-tutorial')).resolve())
with warnings.catch_warnings():
    warnings.filterwarnings('ignore', message='Creating AiiDA configuration folder')
    AiiDAConfigDir.set()
    reset_config()
    config = get_config(create=True)

if PROFILE_NAME not in config.profile_names:
    gsrd = shutil.which('gsrd') or str(Path(sys.executable).parent / 'gsrd')
    run_verdi(f'presto --profile-name {PROFILE_NAME} --use-zeromq')
    run_verdi(f'-p {PROFILE_NAME} config set warnings.development_version False')
    run_verdi(
        f'-p {PROFILE_NAME} code create core.code.installed -n --config include/gsrd_code.yaml -X {shlex.quote(gsrd)}'
    )
    reset_config()  # re-read config from disk so this kernel sees the profile the subprocess created

load_profile(PROFILE_NAME, allow_switch=True)

# Bring up the daemon (needed to submit); a quiet no-op if it is already running, so the later
# modules do not each restart it.
if subprocess.run(['verdi', '-p', PROFILE_NAME, 'daemon', 'status'], capture_output=True, check=False).returncode:
    run_verdi(f'-p {PROFILE_NAME} daemon start')

# `daemon start` returns before the ZeroMQ broker watcher is reachable; wait for it so a
# `verdi status` right after does not report "Broker is NOT running".
_broker = get_manager().get_broker()
_deadline = time.monotonic() + 15.0
while _broker is not None and not _broker.check_service_reachable() and time.monotonic() < _deadline:
    time.sleep(0.2)

# Expose the gsrd Code to the notebook: the modules refer to it as ``gsrd_code``.
gsrd_code = load_code('gsrd@localhost')
