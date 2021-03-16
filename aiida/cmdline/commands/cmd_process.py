# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=too-many-arguments
"""`verdi process` command."""
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
    type=click.Choice(CalculationQueryBuilder.valid_projections), default=CalculationQueryBuilder.default_projections
)
@options.ORDER_BY()
@options.ORDER_DIRECTION()
@options.GROUP(help='Only include entries that are a member of this group.')
@options.ALL(help='Show all entries, regardless of their process state.')
@options.PROCESS_STATE()
@options.PROCESS_LABEL()
@options.PAUSED()
@options.EXIT_STATUS()
@options.FAILED()
@options.PAST_DAYS()
@options.LIMIT()
@options.RAW()
@decorators.with_dbenv()
def process_list(
    all_entries, group, process_state, process_label, paused, exit_status, failed, past_days, limit, project, raw,
    order_by, order_dir
):
    """Show a list of running or terminated processes.

    By default, only those that are still running are shown, but there are options
    to show also the finished ones."""
    # pylint: disable=too-many-locals
    from tabulate import tabulate
    from aiida.cmdline.utils.common import print_last_process_state_change, check_worker_load

    relationships = {}

    if group:
        relationships['with_node'] = group

    builder = CalculationQueryBuilder()
    filters = builder.get_filters(all_entries, process_state, process_label, paused, exit_status, failed)
    query_set = builder.get_query_set(
        relationships=relationships, filters=filters, order_by={order_by: order_dir}, past_days=past_days, limit=limit
    )
    projected = builder.get_projected(query_set, projections=project)

    headers = projected.pop(0)

    if raw:
        tabulated = tabulate(projected, tablefmt='plain')
        echo.echo(tabulated)
    else:
        tabulated = tabulate(projected, headers=headers)
        echo.echo(tabulated)
        echo.echo(f'\nTotal results: {len(projected)}\n')
        print_last_process_state_change()
        # Second query to get active process count
        # Currently this is slow but will be fixed wiith issue #2770
        # We place it at the end so that the user can Ctrl+C after getting the process table.
        builder = CalculationQueryBuilder()
        filters = builder.get_filters(process_state=('created', 'waiting', 'running'))
        query_set = builder.get_query_set(filters=filters)
        projected = builder.get_projected(query_set, projections=['pk'])
        worker_slot_use = len(projected) - 1
        check_worker_load(worker_slot_use)


@verdi_process.command('show')
@arguments.PROCESSES()
@decorators.with_dbenv()
def process_show(processes):
    """Show details for one or multiple processes."""
    from aiida.cmdline.utils.common import get_node_info

    for process in processes:
        echo.echo(get_node_info(process))


@verdi_process.command('call-root')
@arguments.PROCESSES()
@decorators.with_dbenv()
def process_call_root(processes):
    """Show root process of the call stack for the given processes."""
    for process in processes:

        caller = process.caller

        if caller is None:
            echo.echo(f'No callers found for Process<{process.pk}>')
            continue

        while True:
            next_caller = caller.caller

            if next_caller is None:
                break

            caller = next_caller

        echo.echo(f'{caller.pk}')


@verdi_process.command('report')
@arguments.PROCESSES()
@click.option('-i', '--indent-size', type=int, default=2, help='Set the number of spaces to indent each level by.')
@click.option(
    '-l',
    '--levelname',
    type=click.Choice(LOG_LEVELS.keys()),
    default='REPORT',
    help='Filter the results by name of the log level.'
)
@click.option(
    '-m', '--max-depth', 'max_depth', type=int, default=None, help='Limit the number of levels to be printed.'
)
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
            echo.echo(f'Nothing to show for node type {process.__class__}')


@verdi_process.command('status')
@arguments.PROCESSES()
def process_status(processes):
    """Print the status of one or multiple processes."""
    from aiida.cmdline.utils.ascii_vis import format_call_graph

    for process in processes:
        graph = format_call_graph(process)
        echo.echo(graph)


@verdi_process.command('kill')
@arguments.PROCESSES()
@options.TIMEOUT()
@options.WAIT()
@decorators.with_dbenv()
@decorators.only_if_daemon_running(echo.echo_warning, 'daemon is not running, so process may not be reachable')
def process_kill(processes, timeout, wait):
    """Kill running processes."""

    controller = get_manager().get_process_controller()

    futures = {}
    for process in processes:

        if process.is_terminated:
            echo.echo_error(f'Process<{process.pk}> is already terminated')
            continue

        try:
            future = controller.kill_process(process.pk, msg='Killed through `verdi process kill`')
        except communications.UnroutableError:
            echo.echo_error(f'Process<{process.pk}> is unreachable')
        else:
            futures[future] = process

    process_actions(futures, 'kill', 'killing', 'killed', wait, timeout)


@verdi_process.command('pause')
@arguments.PROCESSES()
@options.ALL(help='Pause all active processes if no specific processes are specified.')
@options.TIMEOUT()
@options.WAIT()
@decorators.with_dbenv()
@decorators.only_if_daemon_running(echo.echo_warning, 'daemon is not running, so process may not be reachable')
def process_pause(processes, all_entries, timeout, wait):
    """Pause running processes."""
    from aiida.orm import ProcessNode, QueryBuilder

    controller = get_manager().get_process_controller()

    if processes and all_entries:
        raise click.BadOptionUsage('all', 'cannot specify individual processes and the `--all` flag at the same time.')

    if not processes and all_entries:
        active_states = options.active_process_states()
        builder = QueryBuilder().append(ProcessNode, filters={'attributes.process_state': {'in': active_states}})
        processes = builder.all(flat=True)

    futures = {}
    for process in processes:

        if process.is_terminated:
            echo.echo_error(f'Process<{process.pk}> is already terminated')
            continue

        try:
            future = controller.pause_process(process.pk, msg='Paused through `verdi process pause`')
        except communications.UnroutableError:
            echo.echo_error(f'Process<{process.pk}> is unreachable')
        else:
            futures[future] = process

    process_actions(futures, 'pause', 'pausing', 'paused', wait, timeout)


@verdi_process.command('play')
@arguments.PROCESSES()
@options.ALL(help='Play all paused processes if no specific processes are specified.')
@options.TIMEOUT()
@options.WAIT()
@decorators.with_dbenv()
@decorators.only_if_daemon_running(echo.echo_warning, 'daemon is not running, so process may not be reachable')
def process_play(processes, all_entries, timeout, wait):
    """Play (unpause) paused processes."""
    from aiida.orm import ProcessNode, QueryBuilder

    controller = get_manager().get_process_controller()

    if processes and all_entries:
        raise click.BadOptionUsage('all', 'cannot specify individual processes and the `--all` flag at the same time.')

    if not processes and all_entries:
        filters = CalculationQueryBuilder().get_filters(process_state=('created', 'waiting', 'running'), paused=True)
        builder = QueryBuilder().append(ProcessNode, filters=filters)
        processes = builder.all(flat=True)

    futures = {}
    for process in processes:

        if process.is_terminated:
            echo.echo_error(f'Process<{process.pk}> is already terminated')
            continue

        try:
            future = controller.play_process(process.pk)
        except communications.UnroutableError:
            echo.echo_error(f'Process<{process.pk}> is unreachable')
        else:
            futures[future] = process

    process_actions(futures, 'play', 'playing', 'played', wait, timeout)


@verdi_process.command('watch')
@arguments.PROCESSES()
@decorators.with_dbenv()
@decorators.only_if_daemon_running(echo.echo_warning, 'daemon is not running, so process may not be reachable')
def process_watch(processes):
    """Watch the state transitions for a process."""
    from time import sleep
    from kiwipy import BroadcastFilter

    def _print(communicator, body, sender, subject, correlation_id):  # pylint: disable=unused-argument
        """Format the incoming broadcast data into a message and echo it to stdout."""
        if body is None:
            body = 'No message specified'

        if correlation_id is None:
            correlation_id = '--'

        echo.echo(f'Process<{sender}> [{subject}|{correlation_id}]: {body}')

    communicator = get_manager().get_communicator()
    echo.echo_info('watching for broadcasted messages, press CTRL+C to stop...')

    for process in processes:

        if process.is_terminated:
            echo.echo_error(f'Process<{process.pk}> is already terminated')
            continue

        communicator.add_broadcast_subscriber(BroadcastFilter(_print, sender=process.pk))

    try:
        # Block this thread indefinitely until interrupt
        while True:
            sleep(2)
    except (SystemExit, KeyboardInterrupt):
        echo.echo('')  # add a new line after the interrupt character
        echo.echo_info('received interrupt, exiting...')
        try:
            communicator.close()
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
    from plumpy.futures import unwrap_kiwi_future
    from concurrent import futures

    from aiida.manage.external.rmq import CommunicationTimeout

    scheduled = {}
    try:
        for future in futures.as_completed(futures_map.keys(), timeout=timeout):
            # Get the corresponding process
            process = futures_map[future]

            try:
                # unwrap is need here since LoopCommunicator will also wrap a future
                future = unwrap_kiwi_future(future)
                result = future.result()
            except CommunicationTimeout:
                echo.echo_error(f'call to {infinitive} Process<{process.pk}> timed out')
            except Exception as exception:  # pylint: disable=broad-except
                echo.echo_error(f'failed to {infinitive} Process<{process.pk}>: {exception}')
            else:
                if result is True:
                    echo.echo_success(f'{past} Process<{process.pk}>')
                elif result is False:
                    echo.echo_error(f'problem {present} Process<{process.pk}>')
                elif isinstance(result, kiwipy.Future):
                    echo.echo_success(f'scheduled {infinitive} Process<{process.pk}>')
                    scheduled[result] = process
                else:
                    echo.echo_error(f'got unexpected response when {present} Process<{process.pk}>: {result}')

        if wait and scheduled:
            echo.echo_info(f"waiting for process(es) {','.join([str(proc.pk) for proc in scheduled.values()])}")

            for future in futures.as_completed(scheduled.keys(), timeout=timeout):
                process = scheduled[future]

                try:
                    result = future.result()
                except Exception as exception:  # pylint: disable=broad-except
                    echo.echo_error(f'failed to {infinitive} Process<{process.pk}>: {exception}')
                else:
                    if result is True:
                        echo.echo_success(f'{past} Process<{process.pk}>')
                    elif result is False:
                        echo.echo_error(f'problem {present} Process<{process.pk}>')
                    else:
                        echo.echo_error(f'got unexpected response when {present} Process<{process.pk}>: {result}')

    except futures.TimeoutError:
        echo.echo_error(f'timed out trying to {infinitive} processes {futures_map.values()}')
