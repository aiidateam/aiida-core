# -*- coding: utf-8 -*-
# pylint: disable=too-many-arguments
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi process` command."""
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
@decorators.with_dbenv()
@decorators.only_if_daemon_running(echo.echo_warning, 'daemon is not running, so process may not be reachable')
def process_kill(processes, timeout):
    """Kill running processes."""
    from aiida.work import RemoteException, DeliveryFailed, CommunicationTimeout, new_blocking_control_panel

    with new_blocking_control_panel(timeout=timeout) as control_panel:
        for process in processes:

            if process.is_terminated:
                echo.echo_error('Process<{}> is already terminated'.format(process.pk))
                continue

            try:
                if control_panel.kill_process(process.pk, msg='Killed through `verdi process kill`'):
                    echo.echo_success('killed Process<{}>'.format(process.pk))
                else:
                    echo.echo_error('problem killing Process<{}>'.format(process.pk))
            except CommunicationTimeout:
                echo.echo_error('call to kill Process<{}> timed out'.format(process.pk))
            except (RemoteException, DeliveryFailed) as exception:
                echo.echo_error('failed to kill Process<{}>: {}'.format(process.pk, exception))


@verdi_process.command('pause')
@arguments.PROCESSES()
@options.TIMEOUT()
@decorators.with_dbenv()
@decorators.only_if_daemon_running(echo.echo_warning, 'daemon is not running, so process may not be reachable')
def process_pause(processes, timeout):
    """Pause running processes."""
    from aiida.work import RemoteException, DeliveryFailed, CommunicationTimeout, new_blocking_control_panel

    with new_blocking_control_panel(timeout=timeout) as control_panel:
        for process in processes:

            if process.is_terminated:
                echo.echo_error('Process<{}> is already terminated'.format(process.pk))
                continue

            try:
                if control_panel.pause_process(process.pk, msg='Paused through `verdi process pause`'):
                    echo.echo_success('paused Process<{}>'.format(process.pk))
                else:
                    echo.echo_error('problem pausing Process<{}>'.format(process.pk))
            except CommunicationTimeout:
                echo.echo_error('call to pause Process<{}> timed out'.format(process.pk))
            except (RemoteException, DeliveryFailed) as exception:
                echo.echo_error('failed to pause Process<{}>: {}'.format(process.pk, exception))


@verdi_process.command('play')
@arguments.PROCESSES()
@options.TIMEOUT()
@decorators.with_dbenv()
@decorators.only_if_daemon_running(echo.echo_warning, 'daemon is not running, so process may not be reachable')
def process_play(processes, timeout):
    """Play paused processes."""
    from aiida.work import RemoteException, DeliveryFailed, CommunicationTimeout, new_blocking_control_panel

    with new_blocking_control_panel(timeout=timeout) as control_panel:
        for process in processes:

            if process.is_terminated:
                echo.echo_error('Process<{}> is already terminated'.format(process.pk))
                continue

            try:
                if control_panel.play_process(process.pk):
                    echo.echo_success('played Process<{}>'.format(process.pk))
                else:
                    echo.echo_critical('problem playing Process<{}>'.format(process.pk))
            except CommunicationTimeout:
                echo.echo_error('call to play Process<{}> timed out'.format(process.pk))
            except (RemoteException, DeliveryFailed) as exception:
                echo.echo_critical('failed to play Process<{}>: {}'.format(process.pk, exception))


@verdi_process.command('watch')
@arguments.PROCESSES()
@decorators.with_dbenv()
@decorators.only_if_daemon_running(echo.echo_warning, 'daemon is not running, so process may not be reachable')
def process_watch(processes):
    """Watch the state transitions for a process."""
    from kiwipy import BroadcastFilter
    from aiida.work.rmq import create_communicator

    def _print(body, sender, subject, correlation_id):
        echo.echo('pk={}, subject={}, body={}, correlation_id={}'.format(sender, subject, body, correlation_id))

    communicator = create_communicator()

    for process in processes:

        if process.is_terminated:
            echo.echo_error('Process<{}> is already terminated'.format(process.pk))
            continue

        communicator.add_broadcast_subscriber(BroadcastFilter(_print, sender=process.pk))

    try:
        communicator.await()
    except (SystemExit, KeyboardInterrupt):

        try:
            communicator.disconnect()
        except RuntimeError:
            pass

        # Reraise to trigger clicks builtin abort sequence
        raise
