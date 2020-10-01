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

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import options
from aiida.cmdline.params.types import TestModuleParamType
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
        * the `aiida.orm` module is imported when it doesn't need to be

    If either of these conditions are true, the command will raise a critical error
    """
    from aiida.manage.manager import get_manager

    manager = get_manager()

    if manager.backend_loaded:
        echo.echo_critical('potential `verdi` speed problem: database backend is loaded.')

    if 'aiida.orm' in sys.modules:
        echo.echo_critical('potential `verdi` speed problem: `aiida.orm` module is imported.')

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


@verdi_devel.command('tests')
@click.argument('paths', nargs=-1, type=TestModuleParamType(), required=False)
@options.VERBOSE(help='Print the class and function name for each test.')
@decorators.deprecated_command("This command has been removed in aiida-core v1.1.0. Please run 'pytest' instead.")
@decorators.with_dbenv()
def devel_tests(paths, verbose):  # pylint: disable=unused-argument
    """Run the unittest suite or parts of it.

    .. deprecated:: 1.1.0
        Entry point will be completely removed in `v2.0.0`.
    """


@verdi_devel.command('play', hidden=True)
def devel_play():
    """Play the Aida triumphal march by Giuseppe Verdi."""
    import webbrowser

    webbrowser.open_new('http://upload.wikimedia.org/wikipedia/commons/3/32/Triumphal_March_from_Aida.ogg')


@verdi_devel.command()
def configure_backup():
    """Configure backup of the repository folder."""
    from aiida.manage.backup.backup_setup import BackupSetup
    BackupSetup().run()
