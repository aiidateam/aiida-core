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

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.commands.cmd_calcjob import verdi_calcjob
from aiida.cmdline.commands.cmd_plugin import verdi_plugin
from aiida.cmdline.commands.cmd_process import verdi_process
from aiida.cmdline.params import arguments, options
from aiida.cmdline.utils import decorators

LIST_CMDLINE_PROJECT_DEFAULT = ('pk', 'ctime', 'process_state', 'type', 'job_state')
LIST_CMDLINE_PROJECT_CHOICES = ('pk', 'ctime', 'process_state', 'job_state', 'scheduler_state', 'computer', 'type',
                                'description', 'label', 'uuid', 'mtime', 'user', 'sealed')


@verdi.group('calculation')
def verdi_calculation():
    """Inspect and manage calculations."""


@verdi_calculation.command('gotocomputer')
@arguments.CALCULATION()
@click.pass_context
@decorators.deprecated_command("This command is deprecated. Use 'verdi calcjob gotocomputer' instead.")
def calculation_gotocomputer(ctx, calculation):
    """
    Open a shell and go to the calculation folder on the computer

    This command opens a ssh connection to the folder on the remote
    computer on which the calculation is being/has been executed.
    """
    ctx.invoke(verdi_calcjob.get_command(ctx, 'gotocomputer'), calcjob=calculation)


@verdi_calculation.command('list')
@arguments.CALCULATIONS()
@options.CALC_JOB_STATE()
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
@click.pass_context
@decorators.with_dbenv()
@decorators.deprecated_command("This command is deprecated. Use 'verdi process list' instead.")
def calculation_list(ctx, calculations, past_days, groups, all_entries, calc_job_state, process_state, exit_status,
                     failed, limit, order_by, project, all_users, raw, absolute_time):
    """Return a list of job calculations that are still running."""
    # pylint: disable=unused-argument
    ctx.invoke(
        verdi_process.get_command(ctx, 'list'),
        all_entries=all_entries,
        process_state=process_state,
        exit_status=exit_status,
        failed=failed,
        past_days=past_days,
        limit=limit,
        project=project,
        raw=raw)


@verdi_calculation.command('res')
@arguments.CALCULATION()
@click.option('-f', '--format', 'fmt', type=click.STRING, default='json+date', help='format for the output')
@click.option('-k', '--keys', 'keys', type=click.STRING, cls=options.MultipleValueOption, help='show only these keys')
@click.pass_context
@decorators.with_dbenv()
@decorators.deprecated_command("This command is deprecated. Use 'verdi calcjob res' instead.")
def calculation_res(ctx, calculation, fmt, keys):
    """Print data from the result output node of a calculation."""
    ctx.invoke(verdi_calcjob.get_command(ctx, 'res'), calcjob=calculation, fmt=fmt, keys=keys)


@verdi_calculation.command('show')
@arguments.CALCULATIONS()
@click.pass_context
@decorators.with_dbenv()
@decorators.deprecated_command("This command is deprecated. Use 'verdi process show' instead.")
def calculation_show(ctx, calculations):
    """Show a summary for one or multiple calculations."""
    ctx.invoke(verdi_process.get_command(ctx, 'show'), processes=calculations)


@verdi_calculation.command('logshow')
@arguments.CALCULATIONS()
@click.pass_context
@decorators.with_dbenv()
@decorators.deprecated_command("This command is deprecated. Use 'verdi process report' instead.")
def calculation_logshow(ctx, calculations):
    """Show the log for one or multiple calculations."""
    ctx.invoke(verdi_process.get_command(ctx, 'report'), processes=calculations)


@verdi_calculation.command('plugins')
@click.argument('entry_point', type=click.STRING, required=False)
@click.pass_context
@decorators.with_dbenv()
@decorators.deprecated_command("This command is deprecated. Use 'verdi plugin list' instead.")
def calculation_plugins(ctx, entry_point):
    """Print a list of registered calculations plugins or details of a specific calculations plugin."""
    ctx.invoke(verdi_plugin.get_command(ctx, 'list'), entry_point_group='aiida.calculations', entry_point=entry_point)


@verdi_calculation.command('inputcat')
@arguments.CALCULATION()
@click.argument('path', type=click.STRING, required=False)
@click.pass_context
@decorators.with_dbenv()
@decorators.deprecated_command("This command is deprecated. Use 'verdi calcjob inputcat' instead.")
def calculation_inputcat(ctx, calculation, path):
    """
    Show the contents of a file with relative PATH in the raw input folder of the CALCULATION.

    If PATH is not specified, the default input file path will be used, if defined by the calculation plugin class.
    """
    ctx.invoke(verdi_calcjob.get_command(ctx, 'inputcat'), calcjob=calculation, path=path)


@verdi_calculation.command('outputcat')
@arguments.CALCULATION()
@click.argument('path', type=click.STRING, required=False)
@click.pass_context
@decorators.with_dbenv()
@decorators.deprecated_command("This command is deprecated. Use 'verdi calcjob outputcat' instead.")
def calculation_outputcat(ctx, calculation, path):
    """
    Show the contents of a file with relative PATH in the retrieved folder of the CALCULATION.

    If PATH is not specified, the default output file path will be used, if defined by the calculation plugin class.
    Content can only be shown after the daemon has retrieved the remote files.
    """
    ctx.invoke(verdi_calcjob.get_command(ctx, 'outputcat'), calcjob=calculation, path=path)


@verdi_calculation.command('inputls')
@decorators.with_dbenv()
@arguments.CALCULATION()
@click.argument('path', type=click.STRING, required=False)
@click.option('-c', '--color', 'color', is_flag=True, default=False, help='color folders with a different color')
@click.pass_context
@decorators.deprecated_command("This command is deprecated. Use 'verdi calcjob inputls' instead.")
def calculation_inputls(ctx, calculation, path, color):
    """
    Show the list of files in the directory with relative PATH in the raw input folder of the CALCULATION.

    If PATH is not specified, the base path of the input folder will be used.
    """
    ctx.invoke(verdi_calcjob.get_command(ctx, 'inputls'), calcjob=calculation, path=path, color=color)


@verdi_calculation.command('outputls')
@decorators.with_dbenv()
@arguments.CALCULATION()
@click.argument('path', type=click.STRING, required=False)
@click.option('-c', '--color', 'color', is_flag=True, default=False, help='color folders with a different color')
@click.pass_context
@decorators.deprecated_command("This command is deprecated. Use 'verdi calcjob outputls' instead.")
def calculation_outputls(ctx, calculation, path, color):
    """
    Show the list of files in the directory with relative PATH in the raw input folder of the CALCULATION.

    If PATH is not specified, the base path of the retrieved folder will be used.
    Content can only be showm after the daemon has retrieved the remote files.
    """
    ctx.invoke(verdi_calcjob.get_command(ctx, 'outputls'), calcjob=calculation, path=path, color=color)


@verdi_calculation.command('kill')
@decorators.with_dbenv()
@arguments.CALCULATIONS()
@options.FORCE()
@click.pass_context
@decorators.deprecated_command("This command is deprecated. Use 'verdi process kill' instead.")
def calculation_kill(ctx, calculations, force):
    """Kill one or multiple running calculations."""
    ctx.invoke(verdi_process.process_kill, processes=calculations, force=force)


@verdi_calculation.command('cleanworkdir')
@decorators.with_dbenv()
@arguments.CALCULATIONS()
@options.PAST_DAYS(default=None)
@options.OLDER_THAN(default=None)
@options.COMPUTERS(help='include only calculations that were ran on these computers')
@options.FORCE()
@click.pass_context
@decorators.deprecated_command("This command is deprecated. Use 'verdi calcjob cleanworkdir' instead.")
def calculation_cleanworkdir(ctx, calculations, past_days, older_than, computers, force):
    """
    Clean all content of all output remote folders of calculations.

    If no explicit calculations are specified as arguments, one or both of the -p and -o options has to be specified.
    If both are specified, a logical AND is done between the two, i.e. the calculations that will be cleaned have been
    modified AFTER [-p option] days from now, but BEFORE [-o option] days from now.
    """
    ctx.invoke(
        verdi_calcjob.get_command(ctx, 'cleanworkdir'),
        calcjobs=calculations,
        past_days=past_days,
        older_than=older_than,
        computers=computers,
        force=force)
