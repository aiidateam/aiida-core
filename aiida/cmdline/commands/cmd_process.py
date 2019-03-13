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
"""`verdi process` command."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import click

from kiwipy import communications

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import arguments, options
from aiida.cmdline.utils import decorators, echo
from aiida.cmdline.utils.query.calculation import CalculationQueryBuilder
from aiida.common.log import LOG_LEVELS
from aiida.manage.manager import get_manager


@verdi.group('process')
def verdi_process():
    """Inspect and manage processes."""


@verdi_process.command('list')
@options.PROJECT(
    type=click.Choice(CalculationQueryBuilder.valid_projections), default=CalculationQueryBuilder.default_projections)
@options.GROUP(help='Only include entries that are a member of this group.')
@options.ALL(help='Show all entries, regardless of their process state.')
@options.PROCESS_STATE()
@options.EXIT_STATUS()
@options.FAILED()
@options.PAST_DAYS()
@options.LIMIT()
@options.RAW()
@decorators.with_dbenv()
def process_list(all_entries, group, process_state, exit_status, failed, past_days, limit, project, raw):
    """Show a list of processes that are still running."""
    from tabulate import tabulate
    from aiida.cmdline.utils.common import print_last_process_state_change

    relationships = {}

    if group:
        relationships['with_node'] = group

    builder = CalculationQueryBuilder()
    filters = builder.get_filters(all_entries, process_state, exit_status, failed)
    query_set = builder.get_query_set(relationships=relationships, filters=filters, past_days=past_days, limit=limit)
    projected = builder.get_projected(query_set, projections=project)

    headers = projected.pop(0)

    if raw:
        tabulated = tabulate(projected, tablefmt='plain')
        echo.echo(tabulated)
    else:
        tabulated = tabulate(projected, headers=headers)
        echo.echo(tabulated)
        echo.echo('\nTotal results: {}\n'.format(len(projected)))
        print_last_process_state_change()


@verdi_process.command('show')
@arguments.PROCESSES()
@decorators.with_dbenv()
def process_show(processes):
    """Show a summary for one or multiple processes."""
    from aiida.cmdline.utils.common import get_node_info

    for process in processes:
        echo.echo(get_node_info(process))


@verdi_process.command('report')
@arguments.PROCESSES()
@click.option('-i', '--indent-size', type=int, default=2, help='Set the number of spaces to indent each level by.')
@click.option(
    '-l',
    '--levelname',
    type=click.Choice(LOG_LEVELS.keys()),
    default='REPORT',
    help='Filter the results by name of the log level.')
@click.option(
    '-m', '--max-depth', 'max_depth', type=int, default=None, help='Limit the number of levels to be printed.')
@decorators.with_dbenv()
def process_report(processes, levelname, indent_size, max_depth):
    """Show the log report for one or multiple processes."""
    from aiida.cmdline.utils.common import get_calcjob_report, get_workchain_report, get_process_function_report
    from aiida.orm import CalcJobNode, WorkChainNode, CalcFunctionNode, WorkFunctionNode

    for process in processes:
        if isinstance(process, CalcJobNode):
            echo.echo(get_calcjob_report(process))
        elif isinstance(process, WorkChainNode):
            echo.echo(get_workchain_report(process, levelname, indent_size, max_depth))
        elif isinstance(process, (CalcFunctionNode, WorkFunctionNode)):
            echo.echo(get_process_function_report(process))
        else:
            echo.echo('Nothing to show for node type {}'.format(process.__class__))


@verdi_process.command('status')
@arguments.PROCESSES()
def process_status(processes):
    """Print the status of the process."""
    from aiida.cmdline.utils.ascii_vis import format_call_graph

    for process in processes:
        graph = format_call_graph(process)
        echo.echo(graph)


@verdi_process.command('kill')
@arguments.PROCESSES()
@options.TIMEOUT()
@click.option(
    '--wait/--no-wait',
    default=False,
    help="Wait for the action to be completed otherwise return as soon as it's scheduled.")
@decorators.with_dbenv()
@decorators.only_if_daemon_running(echo.echo_warning, 'daemon is not running, so process may not be reachable')
def process_kill(processes, timeout, wait):
    """Kill running processes."""

    controller = get_manager().get_process_controller()

    futures = {}
    for process in processes:

        if process.is_terminated:
            echo.echo_error('Process<{}> is already terminated'.format(process.pk))
            continue

        try:
            future = controller.kill_process(process.pk, msg='Killed through `verdi process kill`')
        except communications.UnroutableError:
            echo.echo_error('Process<{}> is unreachable'.format(process.pk))
        else:
            futures[future] = process

    process_actions(futures, 'kill', 'killing', 'killed', wait, timeout)


@verdi_process.command('pause')
@arguments.PROCESSES()
@options.TIMEOUT()
@click.option(
    '--wait/--no-wait',
    default=False,
    help="Wait for the action to be completed otherwise return as soon as it's scheduled.")
@decorators.with_dbenv()
@decorators.only_if_daemon_running(echo.echo_warning, 'daemon is not running, so process may not be reachable')
def process_pause(processes, timeout, wait):
    """Pause running processes."""

    controller = get_manager().get_process_controller()

    futures = {}
    for process in processes:

        if process.is_terminated:
            echo.echo_error('Process<{}> is already terminated'.format(process.pk))
            continue

        try:
            future = controller.pause_process(process.pk, msg='Paused through `verdi process pause`')
        except communications.UnroutableError:
            echo.echo_error('Process<{}> is unreachable'.format(process.pk))
        else:
            futures[future] = process

    process_actions(futures, 'pause', 'pausing', 'paused', wait, timeout)


@verdi_process.command('play')
@arguments.PROCESSES()
@options.TIMEOUT()
@click.option(
    '--wait/--no-wait',
    default=False,
    help="Wait for the action to be completed otherwise return as soon as it's scheduled.")
@decorators.with_dbenv()
@decorators.only_if_daemon_running(echo.echo_warning, 'daemon is not running, so process may not be reachable')
def process_play(processes, timeout, wait):
    """Play paused processes."""

    controller = get_manager().get_process_controller()

    futures = {}
    for process in processes:

        if process.is_terminated:
            echo.echo_error('Process<{}> is already terminated'.format(process.pk))
            continue

        try:
            future = controller.play_process(process.pk)
        except communications.UnroutableError:
            echo.echo_error('Process<{}> is unreachable'.format(process.pk))
        else:
            futures[future] = process

    process_actions(futures, 'play', 'playing', 'played', wait, timeout)


@verdi_process.command('watch')
@arguments.PROCESSES()
@decorators.with_dbenv()
@decorators.only_if_daemon_running(echo.echo_warning, 'daemon is not running, so process may not be reachable')
def process_watch(processes):
    """Watch the state transitions for a process."""
    from kiwipy import BroadcastFilter
    import concurrent.futures

    def _print(body, sender, subject, correlation_id):
        echo.echo('pk={}, subject={}, body={}, correlation_id={}'.format(sender, subject, body, correlation_id))

    communicator = get_manager().get_communicator()

    for process in processes:

        if process.is_terminated:
            echo.echo_error('Process<{}> is already terminated'.format(process.pk))
            continue

        communicator.add_broadcast_subscriber(BroadcastFilter(_print, sender=process.pk))

    try:
        # Block this thread indefinitely
        concurrent.futures.Future().result()
    except (SystemExit, KeyboardInterrupt):
        try:
            communicator.stop()
        except RuntimeError:
            pass

        # Reraise to trigger clicks builtin abort sequence
        raise


def process_actions(futures_map, infinitive, present, past, wait=False, timeout=None):
    """
    Process the requested actions sent to a set of Processes given a map of the futures and the
    corresponding processes.  This function will echo the correct information strings based on
    the outcomes of the futures and the given verb conjugations.  You can optionally wait for
    any pending actions to be completed before the functions returns and use a timeout to put
    a maximum wait time on the actions.

    :param futures_map: the map of action futures and the corresponding processes
    :type futures_map: dict
    :param infinitive: the infinitive form of the action verb
    :type infinitive: str
    :param present: the present tense form
    :type present: str
    :param past: the past tense form
    :type past: str
    :param wait: if True, waits for pending actions to be competed, otherwise just returns
    :type wait: bool
    :param timeout: the timeout (in seconds) to wait for actions to be completed
    :type timeout: float
    """
    # pylint: disable=too-many-branches
    import kiwipy
    from concurrent import futures

    from aiida.manage.external.rmq import CommunicationTimeout

    scheduled = {}
    try:
        for future in futures.as_completed(futures_map.keys(), timeout=timeout):
            # Get the corresponding process
            process = futures_map[future]

            try:
                result = future.result()
            except CommunicationTimeout:
                echo.echo_error('call to {} Process<{}> timed out'.format(infinitive, process.pk))
            except Exception as exception:  # pylint: disable=broad-except
                echo.echo_error('failed to {} Process<{}>: {}'.format(infinitive, process.pk, exception))
            else:
                if result is True:
                    echo.echo_success('{} Process<{}>'.format(past, process.pk))
                elif result is False:
                    echo.echo_error('problem {} Process<{}>'.format(present, process.pk))
                elif isinstance(result, kiwipy.Future):
                    echo.echo_success('scheduled {} Process<{}>'.format(infinitive, process.pk))
                    scheduled[result] = process
                else:
                    echo.echo_error('got unexpected response when {} Process<{}>: {}'.format(
                        present, process.pk, result))

        if wait and scheduled:
            echo.echo_info('waiting for process(es) {}'.format(','.join([str(proc.pk) for proc in scheduled.values()])))

            for future in futures.as_completed(scheduled.keys(), timeout=timeout):
                process = scheduled[future]

                try:
                    result = future.result()
                except Exception as exception:  # pylint: disable=broad-except
                    echo.echo_error('failed to {} Process<{}>: {}'.format(infinitive, process.pk, exception))
                else:
                    if result is True:
                        echo.echo_success('{} Process<{}>'.format(past, process.pk))
                    elif result is False:
                        echo.echo_error('problem {} Process<{}>'.format(present, process.pk))
                    else:
                        echo.echo_error('got unexpected response when {} Process<{}>: {}'.format(
                            present, process.pk, result))

    except futures.TimeoutError:
        echo.echo_error('timed out trying to {} processes {}'.format(infinitive, futures_map.values()))
