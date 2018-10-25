# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=protected-access,invalid-name,too-many-arguments,too-many-locals
"""`verdi calculation` commands."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import os

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import arguments, options, types
from aiida.cmdline.utils import decorators, echo
from aiida.common.setup import get_property

LIST_CMDLINE_PROJECT_DEFAULT = get_property('verdishell.calculation_list')
LIST_CMDLINE_PROJECT_CHOICES = ('pk', 'state', 'ctime', 'job_state', 'calculation_state', 'scheduler_state', 'computer',
                                'type', 'description', 'label', 'uuid', 'mtime', 'user', 'sealed')


@verdi.group('calculation')
def verdi_calculation():
    """Inspect and manage calculations."""
    pass


@verdi_calculation.command('gotocomputer')
@arguments.CALCULATION(
    type=types.CalculationParamType(sub_classes=('aiida.calculations:job', 'aiida.calculations:inline')))
def calculation_gotocomputer(calculation):
    """
    Open a shell and go to the calculation folder on the computer

    This command opens a ssh connection to the folder on the remote
    computer on which the calculation is being/has been executed.
    """
    from aiida.common.exceptions import NotExistent

    try:
        transport = calculation._get_transport()
    except NotExistent as exception:
        echo.echo_critical(exception)

    remote_workdir = calculation._get_remote_workdir()

    if not remote_workdir:
        echo.echo_critical('no remote work directory for this calculation, maybe the daemon did not submit it yet')

    command = transport.gotocomputer_command(remote_workdir)
    echo.echo_info('going to the remote work directory...')
    os.system(command)


@verdi_calculation.command('list')
@arguments.CALCULATIONS(
    type=types.CalculationParamType(sub_classes=('aiida.calculations:job', 'aiida.calculations:inline')))
@options.CALCULATION_STATE()
@options.PROCESS_STATE()
@options.EXIT_STATUS()
@options.FAILED()
@options.PAST_DAYS()
@options.LIMIT()
@options.ORDER_BY()
@options.PROJECT(type=click.Choice(LIST_CMDLINE_PROJECT_CHOICES), default=LIST_CMDLINE_PROJECT_DEFAULT)
@options.GROUPS(help='Show only calculations that are contained within one or more of these groups.')
@options.ALL(help='Show all entries, regardless of their process state.')
@options.ALL_USERS()
@options.RAW()
@click.option(
    '-t',
    '--absolute-time',
    'absolute_time',
    is_flag=True,
    default=False,
    help='print the absolute creation time, rather than the relative creation time')
@decorators.with_dbenv()
def calculation_list(calculations, past_days, groups, all_entries, calculation_state, process_state, exit_status,
                     failed, limit, order_by, project, all_users, raw, absolute_time):
    """Return a list of job calculations that are still running."""
    from aiida.cmdline.utils.common import print_last_process_state_change
    from aiida.orm.calculation.job import JobCalculation
    from aiida.work.processes import ProcessState

    if all_entries:
        process_state = None
        calculation_state = None

    PROCESS_STATE_KEY = 'attributes.{}'.format(JobCalculation.PROCESS_STATE_KEY)
    EXIT_STATUS_KEY = 'attributes.{}'.format(JobCalculation.EXIT_STATUS_KEY)

    filters = {}

    if calculation_state:
        process_state = None

    if process_state:
        calculation_state = None
        filters[PROCESS_STATE_KEY] = {'in': process_state}

    if failed:
        calculation_state = None
        filters[PROCESS_STATE_KEY] = {'==': ProcessState.FINISHED.value}
        filters[EXIT_STATUS_KEY] = {'>': 0}

    if exit_status is not None:
        calculation_state = None
        filters[PROCESS_STATE_KEY] = {'==': ProcessState.FINISHED.value}
        filters[EXIT_STATUS_KEY] = {'==': exit_status}

    JobCalculation._list_calculations(
        states=calculation_state,
        past_days=past_days,
        pks=[calculation.pk for calculation in calculations],
        all_users=all_users,
        groups=groups,
        relative_ctime=not absolute_time,
        order_by=order_by,
        limit=limit,
        filters=filters,
        projections=project,
        raw=raw,
    )

    if not raw:
        print_last_process_state_change(process_type='calculation')


@verdi_calculation.command('res')
@arguments.CALCULATION(
    type=types.CalculationParamType(sub_classes=('aiida.calculations:job', 'aiida.calculations:inline')))
@click.option('-f', '--format', 'fmt', type=click.STRING, default='json+date', help='format for the output')
@click.option('-k', '--keys', 'keys', type=click.STRING, cls=options.MultipleValueOption, help='show only these keys')
@decorators.with_dbenv()
def calculation_res(calculation, fmt, keys):
    """Print data from the result output node of a calculation."""
    from aiida.cmdline.utils.echo import echo_dictionary

    results = calculation.res._get_dict()

    if keys is not None:
        try:
            result = {k: results[k] for k in keys}
        except KeyError as exc:
            echo.echo_critical("key '{}' was not found in the .res dictionary".format(exc.args[0]))
    else:
        result = results

    echo_dictionary(result, fmt=fmt)


@verdi_calculation.command('show')
@arguments.CALCULATIONS(
    type=types.CalculationParamType(sub_classes=('aiida.calculations:job', 'aiida.calculations:inline')))
@decorators.with_dbenv()
def calculation_show(calculations):
    """Show a summary for one or multiple calculations."""
    from aiida.cmdline.utils.common import get_node_info

    for calculation in calculations:
        echo.echo(get_node_info(calculation))


@verdi_calculation.command('logshow')
@arguments.CALCULATIONS(
    type=types.CalculationParamType(sub_classes=('aiida.calculations:job', 'aiida.calculations:inline')))
@decorators.with_dbenv()
def calculation_logshow(calculations):
    """Show the log for one or multiple calculations."""
    from aiida.cmdline.utils.common import get_calculation_log_report

    for calculation in calculations:
        echo.echo(get_calculation_log_report(calculation))


@verdi_calculation.command('plugins')
@click.argument('entry_point', type=click.STRING, required=False)
@decorators.with_dbenv()
def calculation_plugins(entry_point):
    """Print a list of registered calculation plugins or details of a specific calculation plugin."""
    import json
    from aiida.common.exceptions import LoadingPluginFailed, MissingPluginError
    from aiida.plugins.entry_point import get_entry_point_names, load_entry_point

    if entry_point:
        try:
            plugin = load_entry_point('aiida.calculations', entry_point)
        except (LoadingPluginFailed, MissingPluginError) as exception:
            echo.echo_critical(str(exception))
        else:
            echo.echo_info(entry_point)
            echo.echo_info(plugin.__doc__ if plugin.__doc__ else 'no docstring available')
            echo.echo(json.dumps(plugin.process().get_description(), indent=4))

    else:
        entry_points = get_entry_point_names('aiida.calculations')
        if entry_points:
            echo.echo('Registered calculation entry points:')
            for ep in entry_points:
                echo.echo("* {}".format(ep))

            echo.echo('')
            echo.echo_info('Pass the entry point as an argument to display detailed information')
        else:
            echo.echo_error('No calculation plugins found')


@verdi_calculation.command('inputcat')
@arguments.CALCULATION(
    type=types.CalculationParamType(sub_classes=('aiida.calculations:job', 'aiida.calculations:inline')))
@click.argument('path', type=click.STRING, required=False)
@decorators.with_dbenv()
def calculation_inputcat(calculation, path):
    """
    Show the contents of a file with relative PATH in the raw input folder of the CALCULATION.

    If PATH is not specified, the default input file path will be used, if defined by the calculation plugin class.
    """
    from aiida.cmdline.utils.repository import cat_repo_files
    from aiida.plugins.entry_point import get_entry_point_from_class

    if path is None:

        path = calculation._DEFAULT_INPUT_FILE

        if path is None:
            cls = calculation.__class__
            _, entry_point = get_entry_point_from_class(cls.__module__, cls.__name__)
            echo.echo_critical('{} does not define a default input file. Please specify a path explicitly'.format(
                entry_point.name))

    try:
        cat_repo_files(calculation, os.path.join('raw_input', path))
    except ValueError as exc:
        echo.echo_critical(str(exc))
    except IOError as e:
        import errno
        # Ignore Broken pipe errors, re-raise everything else
        if e.errno == errno.EPIPE:
            pass
        else:
            raise


@verdi_calculation.command('outputcat')
@arguments.CALCULATION(
    type=types.CalculationParamType(sub_classes=('aiida.calculations:job', 'aiida.calculations:inline')))
@click.argument('path', type=click.STRING, required=False)
@decorators.with_dbenv()
def calculation_outputcat(calculation, path):
    """
    Show the contents of a file with relative PATH in the retrieved folder of the CALCULATION.

    If PATH is not specified, the default output file path will be used, if defined by the calculation plugin class.
    Content can only be shown after the daemon has retrieved the remote files.
    """
    from aiida.cmdline.utils.repository import cat_repo_files
    from aiida.plugins.entry_point import get_entry_point_from_class

    if path is None:

        path = calculation._DEFAULT_OUTPUT_FILE

        if path is None:
            cls = calculation.__class__
            _, entry_point = get_entry_point_from_class(cls.__module__, cls.__name__)
            echo.echo_critical('{} does not define a default output file. Please specify a path explicitly'.format(
                entry_point.name))

    try:
        retrieved = calculation.out.retrieved
    except AttributeError:
        echo.echo_critical("No 'retrieved' node found. Have the calculation files already been retrieved?")

    try:
        cat_repo_files(retrieved, os.path.join('path', path))
    except ValueError as exc:
        echo.echo_critical(str(exc))
    except IOError as e:
        import errno
        # Ignore Broken pipe errors, re-raise everything else
        if e.errno == errno.EPIPE:
            pass
        else:
            raise


@verdi_calculation.command('inputls')
@decorators.with_dbenv()
@arguments.CALCULATION(
    type=types.CalculationParamType(sub_classes=('aiida.calculations:job', 'aiida.calculations:inline')))
@click.argument('path', type=click.STRING, required=False)
@click.option('-c', '--color', 'color', is_flag=True, default=False, help='color folders with a different color')
def calculation_inputls(calculation, path, color):
    """
    Show the list of files in the directory with relative PATH in the raw input folder of the CALCULATION.

    If PATH is not specified, the base path of the input folder will be used.
    """
    from aiida.cmdline.utils.repository import list_repo_files
    from aiida.orm.implementation.general.calculation.job import _input_subfolder

    if path is not None:
        fullpath = os.path.join(_input_subfolder, path)
    else:
        fullpath = _input_subfolder

    try:
        list_repo_files(calculation, fullpath, color)
    except ValueError as exception:
        echo.echo_critical(exception)


@verdi_calculation.command('outputls')
@decorators.with_dbenv()
@arguments.CALCULATION(
    type=types.CalculationParamType(sub_classes=('aiida.calculations:job', 'aiida.calculations:inline')))
@click.argument('path', type=click.STRING, required=False)
@click.option('-c', '--color', 'color', is_flag=True, default=False, help='color folders with a different color')
def calculation_outputls(calculation, path, color):
    """
    Show the list of files in the directory with relative PATH in the raw input folder of the CALCULATION.

    If PATH is not specified, the base path of the retrieved folder will be used.
    Content can only be showm after the daemon has retrieved the remote files.
    """
    from aiida.cmdline.utils.repository import list_repo_files

    if path is not None:
        fullpath = os.path.join(calculation._path_subfolder_name, path)
    else:
        fullpath = calculation._path_subfolder_name

    try:
        retrieved = calculation.out.retrieved
    except AttributeError:
        echo.echo_critical("No 'retrieved' node found. Have the calculation files already been retrieved?")

    try:
        list_repo_files(retrieved, fullpath, color)
    except ValueError as exception:
        echo.echo_critical(exception)


@verdi_calculation.command('kill')
@decorators.with_dbenv()
@arguments.CALCULATIONS(
    type=types.CalculationParamType(sub_classes=('aiida.calculations:job', 'aiida.calculations:inline')))
@options.FORCE()
@decorators.deprecated_command("This command will be removed in a future release. Use 'verdi process kill' instead.")
def calculation_kill(calculations, force):
    """Kill one or multiple running calculations."""
    from aiida import work

    if not force:
        warning = 'Are you sure you want to kill {} calculations?'.format(len(calculations))
        click.confirm(warning, abort=True)

    with work.new_control_panel() as control_panel:
        futures = []
        for calculation in calculations:
            try:
                future = control_panel.kill_process(calculation)
                futures.append((calculation, future))
            except (work.RemoteException, work.DeliveryFailed) as exc:
                echo.echo_error('Calculation<{}> killing failed {}'.format(calculation, exc))

        for future in futures:
            result = control_panel._communicator.await(future[1])
            if result:
                echo.echo_success('Calculation<{}> successfully killed'.format(future[0]))
            else:
                echo.echo_error('Calculation<{}> killing failed {}'.format(future[0], result))


@verdi_calculation.command('cleanworkdir')
@decorators.with_dbenv()
@arguments.CALCULATIONS(
    type=types.CalculationParamType(sub_classes=('aiida.calculations:job', 'aiida.calculations:inline')))
@options.PAST_DAYS(default=None)
@options.OLDER_THAN(default=None)
@options.COMPUTERS(help='include only calculations that were ran on these computers')
@options.FORCE()
def calculation_cleanworkdir(calculations, past_days, older_than, computers, force):
    """
    Clean all content of all output remote folders of calculations.

    If no explicit calculations are specified as arguments, one or both of the -p and -o options has to be specified.
    If both are specified, a logical AND is done between the two, i.e. the calculations that will be cleaned have been
    modified AFTER [-p option] days from now, but BEFORE [-o option] days from now.
    """
    from aiida.orm.backends import construct_backend
    from aiida.orm.utils.loaders import ComputerEntityLoader, IdentifierType
    from aiida.orm.utils.remote import clean_remote, get_calculation_remote_paths

    if calculations:
        if (past_days is not None and older_than is not None):
            echo.echo_critical('specify either explicit calculations or use the filtering options')
    else:
        if (past_days is None and older_than is None):
            echo.echo_critical('if no explicit calculations are specified, at least one filtering option is required')

    calculations_pks = [calculation.pk for calculation in calculations]
    path_mapping = get_calculation_remote_paths(calculations_pks, past_days, older_than, computers)

    if path_mapping is None:
        echo.echo_critical('no calculations found with the given criteria')

    if not force:
        path_count = sum([len(paths) for computer, paths in path_mapping.items()])
        warning = 'Are you sure you want to clean the work directory of {} calculations?'.format(path_count)
        click.confirm(warning, abort=True)

    backend = construct_backend()
    user = backend.users.get_automatic_user()

    for computer_uuid, paths in path_mapping.items():

        counter = 0
        computer = ComputerEntityLoader.load_entity(computer_uuid, identifier_type=IdentifierType.UUID)
        transport = backend.authinfos.get(computer, user).get_transport()

        with transport:
            for path in paths:
                clean_remote(transport, path)
                counter += 1

        echo.echo_success('{} remote folders cleaned on {}'.format(counter, computer.name))
