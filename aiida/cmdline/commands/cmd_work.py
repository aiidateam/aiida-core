# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=too-many-arguments
"""`verdi work` command."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.commands.cmd_plugin import verdi_plugin
from aiida.cmdline.commands.cmd_process import verdi_process
from aiida.cmdline.params import arguments, options, types
from aiida.cmdline.utils import decorators
from aiida.cmdline.utils.query.calculation import CalculationQueryBuilder
from aiida.common.log import LOG_LEVELS


@verdi.group('work')
def verdi_work():
    """Inspect and manage work calculations."""
    pass


@verdi_work.command('list')
@options.PROJECT(
    type=click.Choice(CalculationQueryBuilder.valid_projections), default=CalculationQueryBuilder.default_projections)
@options.ALL(help='Show all entries, regardless of their process state.')
@options.PROCESS_STATE()
@options.EXIT_STATUS()
@options.FAILED()
@options.PAST_DAYS()
@options.LIMIT()
@options.RAW()
@click.pass_context
@decorators.with_dbenv()
def work_list(ctx, all_entries, process_state, exit_status, failed, past_days, limit, project, raw):
    """Show a list of work calculations that are still running."""
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


@verdi_work.command('report')
@arguments.WORKFLOWS(type=types.WorkflowParamType(sub_classes=('aiida.node:process.workflow.workchain',)))
@click.option('-i', '--indent-size', type=int, default=2, help='set the number of spaces to indent each level by')
@click.option(
    '-l',
    '--levelname',
    type=click.Choice(LOG_LEVELS.keys()),
    default='REPORT',
    help='filter the results by name of the log level')
@click.option('-m', '--max-depth', 'max_depth', type=int, default=None, help='limit the number of levels to be printed')
@click.pass_context
def work_report(ctx, workflows, levelname, indent_size, max_depth):
    # pylint: disable=too-many-locals
    """
    Return a list of recorded log messages for the WorkChain with pk=PK
    """
    ctx.invoke(
        verdi_process.get_command(ctx, 'report'),
        processes=workflows,
        levelname=levelname,
        indent_size=indent_size,
        max_depth=max_depth)


@verdi_work.command('show')
@arguments.WORKFLOWS()
@click.pass_context
@decorators.with_dbenv()
@decorators.deprecated_command("This command is deprecated. Use 'verdi process status' instead.")
def work_show(ctx, workflows):
    """Show a summary for one or multiple workflows."""
    ctx.invoke(verdi_process.get_command(ctx, 'show'), processes=workflows)


@verdi_work.command('status')
@arguments.WORKFLOWS()
@click.pass_context
def work_status(ctx, workflows):
    """Print the status of work workflows."""
    ctx.invoke(verdi_process.get_command(ctx, 'status'), processes=workflows)


@verdi_work.command('plugins')
@click.argument('entry_point', type=click.STRING, required=False)
@click.pass_context
@decorators.with_dbenv()
@decorators.deprecated_command("This command is deprecated. Use 'verdi plugin list' instead.")
def work_plugins(ctx, entry_point):
    """Print a list of registered workflow plugins or details of a specific workflow plugin."""
    ctx.invoke(verdi_plugin.get_command(ctx, 'list'), entry_point_group='aiida.workflows', entry_point=entry_point)


@verdi_work.command('kill')
@arguments.WORKFLOWS()
@click.pass_context
@decorators.deprecated_command("This command is deprecated. Use 'verdi process kill' instead.")
def work_kill(ctx, workflows):
    """Kill work workflows."""
    ctx.invoke(verdi_process.process_kill, processes=workflows)


@verdi_work.command('pause')
@arguments.WORKFLOWS()
@click.pass_context
@decorators.deprecated_command("This command is deprecated. Use 'verdi process pause' instead.")
def work_pause(ctx, workflows):
    """Pause running work workflows."""
    ctx.invoke(verdi_process.process_kill, processes=workflows)


@verdi_work.command('play')
@arguments.WORKFLOWS()
@click.pass_context
@decorators.deprecated_command("This command is deprecated. Use 'verdi process play' instead.")
def work_play(ctx, workflows):
    """Play paused work workflows."""
    ctx.invoke(verdi_process.process_kill, processes=workflows)


@verdi_work.command('watch')
@arguments.WORKFLOWS()
@click.pass_context
@decorators.deprecated_command("This command is deprecated. Use 'verdi process watch' instead.")
def work_watch(ctx, workflows):
    """Watch the state transitions for work workflows."""
    ctx.invoke(verdi_process.process_kill, processes=workflows)
