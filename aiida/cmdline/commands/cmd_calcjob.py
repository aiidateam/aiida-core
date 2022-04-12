# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name,too-many-locals
"""`verdi calcjob` commands."""
import os

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import arguments, options
from aiida.cmdline.params.types import CalculationParamType
from aiida.cmdline.utils import decorators, echo


@verdi.group('calcjob')
def verdi_calcjob():
    """Inspect and manage calcjobs."""


@verdi_calcjob.command('gotocomputer')
@arguments.CALCULATION('calcjob', type=CalculationParamType(sub_classes=('aiida.node:process.calculation.calcjob',)))
def calcjob_gotocomputer(calcjob):
    """
    Open a shell in the remote folder on the calcjob.

    This command opens a ssh connection to the folder on the remote
    computer on which the calcjob is being/has been executed.
    """
    from aiida.common.exceptions import NotExistent

    try:
        transport = calcjob.get_transport()
    except NotExistent as exception:
        echo.echo_critical(repr(exception))

    remote_workdir = calcjob.get_remote_workdir()

    if not remote_workdir:
        echo.echo_critical('no remote work directory for this calcjob, maybe the daemon did not submit it yet')

    command = transport.gotocomputer_command(remote_workdir)
    echo.echo_report('going to the remote work directory...')
    os.system(command)


@verdi_calcjob.command('res')
@arguments.CALCULATION('calcjob', type=CalculationParamType(sub_classes=('aiida.node:process.calculation.calcjob',)))
@options.DICT_KEYS()
@options.DICT_FORMAT()
@decorators.with_dbenv()
def calcjob_res(calcjob, fmt, keys):
    """Print data from the result output Dict node of a calcjob."""
    from aiida.cmdline.utils.echo import echo_dictionary

    try:
        results = calcjob.res.get_results()
    except ValueError as exception:
        echo.echo_critical(str(exception))

    if keys is not None:
        try:
            result = {k: results[k] for k in keys}
        except KeyError as exc:
            echo.echo_critical(f"key '{exc.args[0]}' was not found in the results dictionary")
    else:
        result = results

    echo_dictionary(result, fmt=fmt)


@verdi_calcjob.command('inputcat')
@arguments.CALCULATION('calcjob', type=CalculationParamType(sub_classes=('aiida.node:process.calculation.calcjob',)))
@click.argument('path', type=click.STRING, required=False)
@decorators.with_dbenv()
def calcjob_inputcat(calcjob, path):
    """
    Show the contents of one of the calcjob input files.

    You can specify the relative PATH in the raw input folder of the CalcJob.

    If PATH is not specified, the default input file path will be used, if defined by the calcjob plugin class.
    """
    import errno
    from shutil import copyfileobj
    import sys

    # Get path from the given CalcJobNode if not defined by user
    if path is None:
        path = calcjob.get_option('input_filename')

    # Get path from current process class of CalcJobNode if still not defined
    if path is None:
        fname = calcjob.process_class.spec_options.get('input_filename')
        if fname and fname.has_default():
            path = fname.default

    if path is None:
        # Still no path available
        echo.echo_critical(
            '"{}" and its process class "{}" do not define a default input file '
            '(option "input_filename" not found).\n'
            'Please specify a path explicitly.'.format(calcjob.__class__.__name__, calcjob.process_class.__name__)
        )

    try:
        # When we `cat`, it makes sense to directly send the output to stdout as it is
        with calcjob.base.repository.open(path, mode='rb') as fhandle:
            copyfileobj(fhandle, sys.stdout.buffer)
    except OSError as exception:
        # The sepcial case is breakon pipe error, which is usually OK.
        # It can happen if the output is redirected, for example, to `head`.
        if exception.errno != errno.EPIPE:
            # Incorrect path or file not readable
            echo.echo_critical(f'Could not open output path "{path}". Exception: {exception}')


@verdi_calcjob.command('outputcat')
@arguments.CALCULATION('calcjob', type=CalculationParamType(sub_classes=('aiida.node:process.calculation.calcjob',)))
@click.argument('path', type=click.STRING, required=False)
@decorators.with_dbenv()
def calcjob_outputcat(calcjob, path):
    """
    Show the contents of one of the calcjob retrieved outputs.

    You can specify the relative PATH in the retrieved folder of the CalcJob.

    If PATH is not specified, the default output file path will be used, if defined by the calcjob plugin class.
    Content can only be shown after the daemon has retrieved the remote files.
    """
    import errno
    from shutil import copyfileobj
    import sys

    try:
        retrieved = calcjob.outputs.retrieved
    except AttributeError:
        echo.echo_critical("No 'retrieved' node found. Have the calcjob files already been retrieved?")

    # Get path from the given CalcJobNode if not defined by user
    if path is None:
        path = calcjob.get_option('output_filename')

    # Get path from current process class of CalcJobNode if still not defined
    if path is None:
        fname = calcjob.process_class.spec_options.get('output_filename')
        if fname and fname.has_default():
            path = fname.default

    if path is None:
        # Still no path available
        echo.echo_critical(
            '"{}" and its process class "{}" do not define a default output file '
            '(option "output_filename" not found).\n'
            'Please specify a path explicitly.'.format(calcjob.__class__.__name__, calcjob.process_class.__name__)
        )

    try:
        # When we `cat`, it makes sense to directly send the output to stdout as it is
        with retrieved.base.repository.open(path, mode='rb') as fhandle:
            copyfileobj(fhandle, sys.stdout.buffer)
    except OSError as exception:
        # The sepcial case is breakon pipe error, which is usually OK.
        # It can happen if the output is redirected, for example, to `head`.
        if exception.errno != errno.EPIPE:
            # Incorrect path or file not readable
            echo.echo_critical(f'Could not open output path "{path}". Exception: {exception}')


@verdi_calcjob.command('inputls')
@decorators.with_dbenv()
@arguments.CALCULATION('calcjob', type=CalculationParamType(sub_classes=('aiida.node:process.calculation.calcjob',)))
@click.argument('path', type=click.STRING, required=False)
@click.option('-c', '--color', 'color', is_flag=True, default=False, help='color folders with a different color')
def calcjob_inputls(calcjob, path, color):
    """
    Show the list of the generated calcjob input files.

    You can specify a relative PATH in the raw input folder of the CalcJob.

    If PATH is not specified, the base path of the input folder will be used.
    """
    from aiida.cmdline.utils.repository import list_repository_contents

    try:
        list_repository_contents(calcjob, path, color)
    except FileNotFoundError:
        echo.echo_critical(f'the path `{path}` does not exist for the given node')


@verdi_calcjob.command('outputls')
@decorators.with_dbenv()
@arguments.CALCULATION('calcjob', type=CalculationParamType(sub_classes=('aiida.node:process.calculation.calcjob',)))
@click.argument('path', type=click.STRING, required=False)
@click.option('-c', '--color', 'color', is_flag=True, default=False, help='color folders with a different color')
def calcjob_outputls(calcjob, path, color):
    """
    Show the list of the retrieved calcjob output files.

    You can specify a relative PATH in the retrieved folder of the CalcJob.

    If PATH is not specified, the base path of the retrieved folder will be used.
    Content can only be shown after the daemon has retrieved the remote files.
    """
    from aiida.cmdline.utils.repository import list_repository_contents

    try:
        retrieved = calcjob.outputs.retrieved
    except AttributeError:
        echo.echo_critical("No 'retrieved' node found. Have the calcjob files already been retrieved?")

    try:
        list_repository_contents(retrieved, path, color)
    except FileNotFoundError:
        echo.echo_critical(f'the path `{path}` does not exist for the given node')


@verdi_calcjob.command('cleanworkdir')
@decorators.with_dbenv()
@arguments.CALCULATIONS('calcjobs', type=CalculationParamType(sub_classes=('aiida.node:process.calculation.calcjob',)))
@options.PAST_DAYS(default=None)
@options.OLDER_THAN(default=None)
@options.COMPUTERS(help='include only calcjobs that were ran on these computers')
@options.FORCE()
@options.EXIT_STATUS()
def calcjob_cleanworkdir(calcjobs, past_days, older_than, computers, force, exit_status):
    """
    Clean all content of all output remote folders of calcjobs.

    If no explicit calcjobs are specified as arguments, one or both of the -p and -o options has to be specified.
    If both are specified, a logical AND is done between the two, i.e. the calcjobs that will be cleaned have been
    modified AFTER [-p option] days from now, but BEFORE [-o option] days from now.
    """
    from aiida import orm
    from aiida.orm.utils.remote import get_calcjob_remote_paths

    if calcjobs:
        if (past_days is not None and older_than is not None):
            echo.echo_critical('specify either explicit calcjobs or use the filtering options')
    else:
        if (past_days is None and older_than is None):
            echo.echo_critical('if no explicit calcjobs are specified, at least one filtering option is required')

    calcjobs_pks = [calcjob.pk for calcjob in calcjobs]
    path_mapping = get_calcjob_remote_paths(
        calcjobs_pks,
        past_days,
        older_than,
        computers,
        exit_status=exit_status,
        only_not_cleaned=True,
    )

    if path_mapping is None:
        echo.echo_critical('no calcjobs found with the given criteria')

    if not force:
        path_count = sum([len(paths) for computer, paths in path_mapping.items()])
        warning = f'Are you sure you want to clean the work directory of {path_count} calcjobs?'
        click.confirm(warning, abort=True)

    user = orm.User.collection.get_default()

    for computer_uuid, paths in path_mapping.items():

        counter = 0
        computer = orm.load_computer(uuid=computer_uuid)
        transport = orm.AuthInfo.collection.get(dbcomputer_id=computer.pk, aiidauser_id=user.pk).get_transport()

        with transport:
            for remote_folder in paths:
                remote_folder._clean(transport=transport)  # pylint:disable=protected-access
                counter += 1

        echo.echo_success(f'{counter} remote folders cleaned on {computer.label}')
