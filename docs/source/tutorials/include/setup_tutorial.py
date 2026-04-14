"""Shared tutorial profile setup.

Creates (or loads) a lightweight ``tutorial`` profile with:

* SQLite storage (no PostgreSQL required)
* A ``localhost`` Computer with local transport and direct scheduler
* A ``python3@localhost`` Code pointing to the current Python interpreter

Every tutorial module runs this in a hidden cell so that data created in
earlier modules is available in later ones.

If you are running locally with your own profile (e.g. from ``verdi presto``),
replace the ``%run -i`` cell with::

    from aiida import load_profile
    load_profile()
"""

import os
import pathlib
import sys

from aiida import load_profile
from aiida.common.exceptions import NotExistent
from aiida.manage.configuration import create_profile, get_config
from aiida.orm import Computer, InstalledCode, load_code, load_computer

profile_name = 'tutorial'
config = get_config()

if profile_name not in config.profile_names:
    create_profile(
        config,
        name=profile_name,
        email='tutorial@aiida.net',
        storage_backend='core.sqlite_dos',
        storage_config={},
        broker_backend=None,
        broker_config=None,
    )
    config.set_option('runner.poll.interval', 1, scope=profile_name)
    config.set_option('warnings.development_version', False, scope=profile_name)
    config.set_default_profile(profile_name, overwrite=True)
    config.store()

load_profile(profile_name, allow_switch=True)
os.environ['AIIDA_PROFILE'] = profile_name

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

# Pre-register a Code with a short label so that ``verdi process list``
# shows "python3@localhost" instead of the full virtualenv path.
try:
    python_code = load_code('python3@localhost')
except NotExistent:
    python_code = InstalledCode(
        label='python3',
        computer=computer,
        filepath_executable=sys.executable,
        default_calc_job_plugin='core.shell',
    ).store()
