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
from aiida.cmdline.params import options, types
from aiida.cmdline.utils import decorators, echo
from aiida.common import exceptions


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
    """Run a raw SQL command on the profile database (only available for 'core.psql_dos' storage)."""
    from sqlalchemy import text

    from aiida.storage.psql_dos.utils import create_sqlalchemy_engine
    assert get_profile().storage_backend == 'core.psql_dos'
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


@verdi_devel.command('launch-add')
@options.CODE(type=types.CodeParamType(entry_point='core.arithmetic.add'))
@click.option('-d', '--daemon', is_flag=True, help='Submit to the daemon instead of running blockingly.')
@click.option('-s', '--sleep', type=int, help='Set the `sleep` input in seconds.')
def devel_launch_arithmetic_add(code, daemon, sleep):
    """Launch an ``ArithmeticAddCalculation``.

    Unless specified with the option ``--code``, a suitable ``Code`` is automatically setup. By default the command
    configures ``bash`` on the ``localhost``. If the localhost is not yet configured as a ``Computer``, that is also
    done automatically.
    """
    from shutil import which

    from aiida.engine import run, submit
    from aiida.orm import InstalledCode, Int, load_code

    default_calc_job_plugin = 'core.arithmetic.add'

    if not code:
        try:
            code = load_code('bash@localhost')
        except exceptions.NotExistent:
            localhost = prepare_localhost()
            code = InstalledCode(
                label='bash',
                computer=localhost,
                filepath_executable=which('bash'),
                default_calc_job_plugin=default_calc_job_plugin
            ).store()
        else:
            assert code.default_calc_job_plugin == default_calc_job_plugin

    builder = code.get_builder()
    builder.x = Int(1)
    builder.y = Int(1)

    if sleep:
        builder.metadata.options.sleep = sleep

    if daemon:
        node = submit(builder)
        echo.echo_success(f'Submitted calculation `{node}`')
    else:
        _, node = run.get_node(builder)
        if node.is_finished_ok:
            echo.echo_success(f'ArithmeticAddCalculation<{node.pk}> finished successfully.')
        else:
            echo.echo_warning(f'ArithmeticAddCalculation<{node.pk}> did not finish successfully.')


def prepare_localhost():
    """Prepare and return the localhost as ``Computer``.

    If it doesn't already exist, the computer will be created, using ``core.local`` and ``core.direct`` as the entry
    points for the transport and scheduler type, respectively. In that case, the safe transport interval and the minimum
    job poll interval will both be set to 0 seconds in order to guarantee a throughput that is as fast as possible.

    :return: The localhost configured as a ``Computer``.
    """
    import tempfile

    from aiida.orm import Computer, load_computer

    try:
        computer = load_computer('localhost')
    except exceptions.NotExistent:
        echo.echo_warning('No `localhost` computer exists yet: creating and configuring the `localhost` computer.')
        computer = Computer(
            label='localhost',
            hostname='localhost',
            description='Localhost automatically created by `aiida.engine.launch_shell_job`',
            transport_type='core.local',
            scheduler_type='core.direct',
            workdir=tempfile.gettempdir(),
        ).store()
        computer.configure(safe_interval=0.)
        computer.set_minimum_job_poll_interval(0.)

    if not computer.is_configured:
        computer.configure()

    return computer
