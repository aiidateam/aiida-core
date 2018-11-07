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
from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import arguments, options
from aiida.cmdline.utils import decorators, echo
from aiida.cmdline.utils.query.calculation import CalculationQueryBuilder


@verdi.group('process')
def verdi_process():
    """Inspect and manage processes."""
    pass


@verdi_process.command('list')
@options.PROJECT(
    type=click.Choice(CalculationQueryBuilder.valid_projections), default=CalculationQueryBuilder.default_projections)
@options.ALL(help='Show all entries, regardless of their process state.')
@options.PROCESS_STATE()
@options.EXIT_STATUS()
@options.FAILED()
@options.PAST_DAYS()
@options.LIMIT()
@options.RAW()
@decorators.with_dbenv()
def process_list(all_entries, process_state, exit_status, failed, past_days, limit, project, raw):
    """Show a list of processes that are still running."""
    from tabulate import tabulate
    from aiida.cmdline.utils.common import print_last_process_state_change

    builder = CalculationQueryBuilder()
    filters = builder.get_filters(all_entries, process_state, exit_status, failed)
    query_set = builder.get_query_set(filters=filters, past_days=past_days, limit=limit)
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


@verdi_process.command('kill')
@arguments.PROCESSES()
@options.TIMEOUT()
@click.option(
    '--wait/--no-wait',
    default=False,
    help="wait for the action to be completed otherwise return as soon as it's scheduled")
@decorators.with_dbenv()
@decorators.only_if_daemon_running(echo.echo_warning, 'daemon is not running, so process may not be reachable')
def process_kill(processes, timeout, wait):
    """Kill running processes."""
    from aiida import work

    controller = work.AiiDAManager.get_process_controller()

    futures = {}
    for process in processes:

        if process.is_terminated:
            echo.echo_error('Process<{}> is already terminated'.format(process.pk))
            continue

        future = controller.kill_process(process.pk, msg='Killed through `verdi process kill`')
        futures[future] = process

    process_actions(futures, 'kill', 'killing', 'killed', wait, timeout)


@verdi_process.command('pause')
@arguments.PROCESSES()
@options.TIMEOUT()
@click.option(
    '--wait/--no-wait',
    default=False,
    help="wait for the action to be completed otherwise return as soon as it's scheduled")
@decorators.with_dbenv()
@decorators.only_if_daemon_running(echo.echo_warning, 'daemon is not running, so process may not be reachable')
def process_pause(processes, timeout, wait):
    """Pause running processes."""
    from aiida import work

    controller = work.AiiDAManager.get_process_controller()

    futures = {}
    for process in processes:

        if process.is_terminated:
            echo.echo_error('Process<{}> is already terminated'.format(process.pk))
            continue

        future = controller.pause_process(process.pk, msg='Paused through `verdi process pause`')
        futures[future] = process

    process_actions(futures, 'pause', 'pausing', 'paused', wait, timeout)


@verdi_process.command('play')
@arguments.PROCESSES()
@options.TIMEOUT()
@click.option(
    '--wait/--no-wait',
    default=False,
    help="wait for the action to be completed otherwise return as soon as it's scheduled")
@decorators.with_dbenv()
@decorators.only_if_daemon_running(echo.echo_warning, 'daemon is not running, so process may not be reachable')
def process_play(processes, timeout, wait):
    """Play paused processes."""
    from aiida import work

    controller = work.AiiDAManager.get_process_controller()

    futures = {}
    for process in processes:

        if process.is_terminated:
            echo.echo_error('Process<{}> is already terminated'.format(process.pk))
            continue

        future = controller.play_process(process.pk)
        futures[future] = process

    process_actions(futures, 'play', 'playing', 'played', wait, timeout)


@verdi_process.command('watch')
@arguments.PROCESSES()
@decorators.with_dbenv()
@decorators.only_if_daemon_running(echo.echo_warning, 'daemon is not running, so process may not be reachable')
def process_watch(processes):
    """Watch the state transitions for a process."""
    from kiwipy import BroadcastFilter
    from aiida import work
    import concurrent.futures

    def _print(body, sender, subject, correlation_id):
        echo.echo('pk={}, subject={}, body={}, correlation_id={}'.format(sender, subject, body, correlation_id))

    communicator = work.AiiDAManager.get_communicator()

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
    from aiida.work import CommunicationTimeout
    from concurrent import futures

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
