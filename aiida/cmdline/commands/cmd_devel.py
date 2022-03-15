# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi devel` commands."""
import sys

import click

from aiida import get_profile
from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.utils import decorators, echo


@verdi.group('devel')
def verdi_devel():
    """Commands for developers."""


@verdi_devel.command('check-load-time')
def devel_check_load_time():
    """Check for common indicators that slowdown `verdi`.

    Check for environment properties that negatively affect the responsiveness of the `verdi` command line interface.
    Known pathways that increase load time:

        * the database environment is loaded when it doesn't need to be
        * Unexpected `aiida.*` modules are imported

    If either of these conditions are true, the command will raise a critical error
    """
    from aiida.manage import get_manager

    loaded_aiida_modules = [key for key in sys.modules if key.startswith('aiida.')]
    aiida_modules_str = '\n- '.join(sorted(loaded_aiida_modules))
    echo.echo_info(f'aiida modules loaded:\n- {aiida_modules_str}')

    manager = get_manager()

    if manager.profile_storage_loaded:
        echo.echo_critical('potential `verdi` speed problem: database backend is loaded.')

    allowed = ('aiida.cmdline', 'aiida.common', 'aiida.manage', 'aiida.plugins', 'aiida.restapi')
    for loaded in loaded_aiida_modules:
        if not any(loaded.startswith(mod) for mod in allowed):
            echo.echo_critical(
                f'potential `verdi` speed problem: `{loaded}` module is imported which is not in: {allowed}'
            )

    echo.echo_success('no issues detected')


@verdi_devel.command('check-undesired-imports')
def devel_check_undesired_imports():
    """Check that verdi does not import python modules it shouldn't.

    Note: The blacklist was taken from the list of packages in the 'atomic_tools' extra but can be extended.
    """
    loaded_modules = 0

    for modulename in ['seekpath', 'CifFile', 'ase', 'pymatgen', 'spglib', 'pymysql']:
        if modulename in sys.modules:
            echo.echo_warning(f'Detected loaded module "{modulename}"')
            loaded_modules += 1

    if loaded_modules > 0:
        echo.echo_critical(f'Detected {loaded_modules} unwanted modules')
    echo.echo_success('no issues detected')


@verdi_devel.command('run_daemon')
@decorators.with_dbenv()
def devel_run_daemon():
    """Run a daemon instance in the current interpreter."""
    from aiida.engine.daemon.runner import start_daemon
    start_daemon()


@verdi_devel.command('validate-plugins')
@decorators.with_dbenv()
def devel_validate_plugins():
    """Validate all plugins by checking they can be loaded."""
    from aiida.common.exceptions import EntryPointError
    from aiida.plugins.entry_point import validate_registered_entry_points

    try:
        validate_registered_entry_points()
    except EntryPointError as exception:
        echo.echo_critical(str(exception))

    echo.echo_success('all registered plugins could successfully loaded.')


@verdi_devel.command('run-sql')
@click.argument('sql', type=str)
def devel_run_sql(sql):
    """Run a raw SQL command on the profile database (only available for 'psql_dos' storage)."""
    from sqlalchemy import text

    from aiida.storage.psql_dos.utils import create_sqlalchemy_engine
    assert get_profile().storage_backend == 'psql_dos'
    with create_sqlalchemy_engine(get_profile().storage_config).connect() as connection:
        result = connection.execute(text(sql)).fetchall()

    if isinstance(result, (list, tuple)):
        for row in result:
            echo.echo(str(row))
    else:
        echo.echo(str(result))


@verdi_devel.command('play', hidden=True)
def devel_play():
    """Play the Aida triumphal march by Giuseppe Verdi."""
    import webbrowser
    webbrowser.open_new('http://upload.wikimedia.org/wikipedia/commons/3/32/Triumphal_March_from_Aida.ogg')
