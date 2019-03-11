# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name,too-many-locals
"""`verdi calcjob` commands."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
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
    Open a shell and go to the calcjob folder on the computer

    This command opens a ssh connection to the folder on the remote
    computer on which the calcjob is being/has been executed.
    """
    from aiida.common.exceptions import NotExistent

    try:
        transport = calcjob.get_transport()
    except NotExistent as exception:
        echo.echo_critical(exception)

    remote_workdir = calcjob.get_remote_workdir()

    if not remote_workdir:
        echo.echo_critical('no remote work directory for this calcjob, maybe the daemon did not submit it yet')

    command = transport.gotocomputer_command(remote_workdir)
    echo.echo_info('going to the remote work directory...')
    os.system(command)


@verdi_calcjob.command('res')
@arguments.CALCULATION('calcjob', type=CalculationParamType(sub_classes=('aiida.node:process.calculation.calcjob',)))
@click.option('-f', '--format', 'fmt', type=click.STRING, default='json+date', help='format for the output')
@click.option('-k', '--keys', 'keys', type=click.STRING, cls=options.MultipleValueOption, help='show only these keys')
@decorators.with_dbenv()
def calcjob_res(calcjob, fmt, keys):
    """Print data from the result output node of a calcjob."""
    from aiida.cmdline.utils.echo import echo_dictionary

    try:
        results = calcjob.res.get_results()
    except ValueError as exception:
        echo.echo_critical(str(exception))

    if keys is not None:
        try:
            result = {k: results[k] for k in keys}
        except KeyError as exc:
            echo.echo_critical("key '{}' was not found in the results dictionary".format(exc.args[0]))
    else:
        result = results

    echo_dictionary(result, fmt=fmt)


@verdi_calcjob.command('inputcat')
@arguments.CALCULATION('calcjob', type=CalculationParamType(sub_classes=('aiida.node:process.calculation.calcjob',)))
@click.argument('path', type=click.STRING, required=False)
@decorators.with_dbenv()
def calcjob_inputcat(calcjob, path):
    """
    Show the contents of a file with relative PATH in the raw input folder of the CALCULATION.

    If PATH is not specified, the default input file path will be used, if defined by the calcjob plugin class.
    """
    from aiida.plugins.entry_point import get_entry_point_from_class

    if path is None:

        path = calcjob.get_option('input_filename')

        if path is None:
            cls = calcjob.__class__
            _, entry_point = get_entry_point_from_class(cls.__module__, cls.__name__)
            echo.echo_critical('{} does not define a default input file. Please specify a path explicitly'.format(
                entry_point.name))

    try:
        content = calcjob.get_object_content(path)
    except Exception as exception:  # pylint: disable=broad-except
        echo.echo_critical('failed to get the content of file `{}`: {}'.format(path, exception))
    else:
        echo.echo(content)


@verdi_calcjob.command('outputcat')
@arguments.CALCULATION('calcjob', type=CalculationParamType(sub_classes=('aiida.node:process.calculation.calcjob',)))
@click.argument('path', type=click.STRING, required=False)
@decorators.with_dbenv()
def calcjob_outputcat(calcjob, path):
    """
    Show the contents of a file with relative PATH in the retrieved folder of the CALCULATION.

    If PATH is not specified, the default output file path will be used, if defined by the calcjob plugin class.
    Content can only be shown after the daemon has retrieved the remote files.
    """
    from aiida.plugins.entry_point import get_entry_point_from_class

    if path is None:

        path = calcjob.get_option('output_filename')

        if path is None:
            cls = calcjob.__class__
            _, entry_point = get_entry_point_from_class(cls.__module__, cls.__name__)
            echo.echo_critical('{} does not define a default output file. Please specify a path explicitly'.format(
                entry_point.name))

    try:
        retrieved = calcjob.outputs.retrieved
    except AttributeError:
        echo.echo_critical("No 'retrieved' node found. Have the calcjob files already been retrieved?")

    try:
        content = retrieved.get_object_content(path)
    except Exception as exception:  # pylint: disable=broad-except
        echo.echo_critical('failed to get the content of file `{}`: {}'.format(path, exception))
    else:
        echo.echo(content)


@verdi_calcjob.command('inputls')
@decorators.with_dbenv()
@arguments.CALCULATION('calcjob', type=CalculationParamType(sub_classes=('aiida.node:process.calculation.calcjob',)))
@click.argument('path', type=click.STRING, required=False)
@click.option('-c', '--color', 'color', is_flag=True, default=False, help='color folders with a different color')
def calcjob_inputls(calcjob, path, color):
    """
    Show the list of files in the directory with relative PATH in the raw input folder of the CALCULATION.

    If PATH is not specified, the base path of the input folder will be used.
    """
    from aiida.cmdline.utils.repository import list_repository_contents

    try:
        list_repository_contents(calcjob, path, color)
    except ValueError as exception:
        echo.echo_critical(exception)


@verdi_calcjob.command('outputls')
@decorators.with_dbenv()
@arguments.CALCULATION('calcjob', type=CalculationParamType(sub_classes=('aiida.node:process.calculation.calcjob',)))
@click.argument('path', type=click.STRING, required=False)
@click.option('-c', '--color', 'color', is_flag=True, default=False, help='color folders with a different color')
def calcjob_outputls(calcjob, path, color):
    """
    Show the list of files in the directory with relative PATH in the raw input folder of the CALCULATION.

    If PATH is not specified, the base path of the retrieved folder will be used.
    Content can only be showm after the daemon has retrieved the remote files.
    """
    from aiida.cmdline.utils.repository import list_repository_contents

    try:
        retrieved = calcjob.outputs.retrieved
    except AttributeError:
        echo.echo_critical("No 'retrieved' node found. Have the calcjob files already been retrieved?")

    try:
        list_repository_contents(retrieved, path, color)
    except ValueError as exception:
        echo.echo_critical(exception)


@verdi_calcjob.command('cleanworkdir')
@decorators.with_dbenv()
@arguments.CALCULATIONS('calcjobs', type=CalculationParamType(sub_classes=('aiida.node:process.calculation.calcjob',)))
@options.PAST_DAYS(default=None)
@options.OLDER_THAN(default=None)
@options.COMPUTERS(help='include only calcjobs that were ran on these computers')
@options.FORCE()
def calcjob_cleanworkdir(calcjobs, past_days, older_than, computers, force):
    """
    Clean all content of all output remote folders of calcjobs.

    If no explicit calcjobs are specified as arguments, one or both of the -p and -o options has to be specified.
    If both are specified, a logical AND is done between the two, i.e. the calcjobs that will be cleaned have been
    modified AFTER [-p option] days from now, but BEFORE [-o option] days from now.
    """
    from aiida.orm.utils.loaders import ComputerEntityLoader, IdentifierType
    from aiida.orm.utils.remote import clean_remote, get_calcjob_remote_paths
    from aiida import orm

    if calcjobs:
        if (past_days is not None and older_than is not None):
            echo.echo_critical('specify either explicit calcjobs or use the filtering options')
    else:
        if (past_days is None and older_than is None):
            echo.echo_critical('if no explicit calcjobs are specified, at least one filtering option is required')

    calcjobs_pks = [calcjob.pk for calcjob in calcjobs]
    path_mapping = get_calcjob_remote_paths(calcjobs_pks, past_days, older_than, computers)

    if path_mapping is None:
        echo.echo_critical('no calcjobs found with the given criteria')

    if not force:
        path_count = sum([len(paths) for computer, paths in path_mapping.items()])
        warning = 'Are you sure you want to clean the work directory of {} calcjobs?'.format(path_count)
        click.confirm(warning, abort=True)

    user = orm.User.objects.get_default()

    for computer_uuid, paths in path_mapping.items():

        counter = 0
        computer = ComputerEntityLoader.load_entity(computer_uuid, identifier_type=IdentifierType.UUID)
        transport = orm.AuthInfo.objects.get(dbcomputer_id=computer.id, aiidauser_id=user.id).get_transport()

        with transport:
            for path in paths:
                clean_remote(transport, path)
                counter += 1

        echo.echo_success('{} remote folders cleaned on {}'.format(counter, computer.name))
