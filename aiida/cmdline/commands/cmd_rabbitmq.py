# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi devel rabbitmq` commands."""
from __future__ import annotations

import collections
import re
import sys
import typing as t

import click
import requests
import tabulate
import wrapt
import yaml

from aiida.cmdline.commands.cmd_devel import verdi_devel
from aiida.cmdline.params import arguments, options
from aiida.cmdline.utils import decorators, echo

if t.TYPE_CHECKING:
    import kiwipy.rmq

    from aiida.manage.configuration.profile import Profile


@verdi_devel.group('rabbitmq')
def cmd_rabbitmq():
    """Commands to interact with RabbitMQ."""


@cmd_rabbitmq.group('queues')
def cmd_queues():
    """Commands to interact with RabbitMQ queues."""


@cmd_rabbitmq.group('tasks')
def cmd_tasks():
    """Commands related to process tasks."""


AVAILABLE_PROJECTORS = (
    'arguments',
    'auto_delete',
    'backing_queue_status',
    'consumer_utilisation',
    'consumers',
    'durable',
    'effective_policy_definition',
    'exclusive',
    'exclusive_consumer_tag',
    'garbage_collection',
    'head_message_timestamp',
    'idle_since',
    'memory',
    'message_bytes',
    'message_bytes_paged_out',
    'message_bytes_persistent',
    'message_bytes_ram',
    'message_bytes_ready',
    'message_bytes_unacknowledged',
    'messages',
    'messages_details',
    'messages_paged_out',
    'messages_persistent',
    'messages_ram',
    'messages_ready',
    'messages_ready_details',
    'messages_ready_ram',
    'messages_unacknowledged',
    'messages_unacknowledged_details',
    'messages_unacknowledged_ram',
    'name',
    'node',
    'operator_policy',
    'policy',
    'recoverable_slaves',
    'reductions',
    'reductions_details',
    'single_active_consumer_tag',
    'state',
    'type',
    'vhost',
)


def echo_response(response: requests.Response, exit_on_error: bool = True) -> None:
    """Echo the response of a request.

    :param response: The response to the request.
    :param exit_on_error: Boolean, if ``True``, call ``sys.exit`` with the status code of the response.
    """
    try:
        response.raise_for_status()
    except requests.HTTPError:
        click.secho(f'[{response.status_code}] ', fg='red', bold=True, nl=False)
        click.secho(f'{response.reason}: {response.url}')
        if exit_on_error:
            sys.exit(response.status_code)
    else:
        click.secho(f'[{response.status_code}] ', fg='green', bold=True)


@wrapt.decorator
@click.pass_context
def with_client(ctx, wrapped, _, args, kwargs):
    """Decorate a function injecting a :class:`aiida.manage.external.rmq.client.RabbitmqManagementClient`."""

    from aiida.manage.external.rmq.client import RabbitmqManagementClient
    config = ctx.obj.profile.process_control_config
    client = RabbitmqManagementClient(
        username=config['broker_username'],
        password=config['broker_password'],
        hostname=config['broker_host'],
        virtual_host=config['broker_virtual_host'],
    )

    if not client.is_connected:
        echo.echo_critical(
            'Could not connect to the management API. Make sure RabbitMQ is running and the management plugin is '
            'installed using `sudo rabbitmq-plugins enable rabbitmq_management`. The API is served on port 15672, so '
            'if you are connecting to RabbitMQ running in a Docker container, make sure that port is exposed.'
        )

    kwargs['client'] = client
    return wrapped(*args, **kwargs)


@wrapt.decorator
def with_manager(wrapped, _, args, kwargs):
    """Decorate a function injecting a :class:`kiwipy.rmq.communicator.RmqCommunicator`."""
    from aiida.manage import get_manager
    kwargs['manager'] = get_manager()
    return wrapped(*args, **kwargs)


@cmd_rabbitmq.command('server-properties')
@with_manager
def cmd_server_properties(manager):
    """List the server properties."""
    data = {}
    for key, value in manager.get_communicator().server_properties.items():
        data[key] = value.decode('utf-8') if isinstance(value, bytes) else value
    click.echo(yaml.dump(data, indent=4))


@cmd_queues.command('list')
@click.option(
    '-P',
    '--project',
    type=click.Choice(AVAILABLE_PROJECTORS),
    cls=options.MultipleValueOption,
    default=('name', 'messages', 'state')
)
@options.RAW()
@click.option('-f', '--filter-name', type=str, help='Provide a regex pattern to filter queues based on their name. ')
@with_client
def cmd_queues_list(client, project, raw, filter_name):
    """List all queues."""
    response = client.request('queues')

    if not response.ok:
        echo_response(response)

    if filter_name and 'name' not in project:
        raise click.BadParameter('cannot use `--filter-name` when not projecting `name`.')

    if filter_name:
        try:
            re.match(filter_name, '')
        except re.error as exception:
            raise click.BadParameter(f'invalid regex pattern: {exception}', param_hint='`--filter-name`')

    queues = [queue for queue in response.json() if re.match(filter_name or '', queue['name'])]
    output = [
        list(map(lambda key, values=queue: values.get(key, ''), project))  # type: ignore[misc]
        for queue in queues
    ]

    if not output:
        echo.echo_report('No queues matched.')
        return

    headers = [name.capitalize() for name in project] if not raw else []
    tablefmt = None if not raw else 'plain'
    echo.echo(tabulate.tabulate(output, headers=headers, tablefmt=tablefmt))


@cmd_queues.command('create')
@click.argument('queues', nargs=-1)
@with_client
def cmd_queues_create(client, queues):
    """Create new queues."""
    for queue in queues:
        response = client.request('queues/{virtual_host}/{queue}', {'queue': queue}, method='PUT')
        click.secho(f'Create `{queue}`... ', nl=False)
        echo_response(response)


@cmd_queues.command('delete')
@click.argument('queues', nargs=-1)
@with_client
def cmd_queues_delete(client, queues):
    """Delete existing queues."""
    for queue in queues:
        params = {'if-empty': True, 'if-unused': True}
        response = client.request('queues/{virtual_host}/{queue}', {'queue': queue}, method='DELETE', params=params)
        click.secho(f'Delete `{queue}`... ', nl=False)
        echo_response(response, exit_on_error=False)


@cmd_tasks.command('list')
@with_manager
@decorators.only_if_daemon_not_running()
@click.pass_context
def cmd_tasks_list(ctx, manager):
    """List all active process tasks.

    This command prints a list of process pk's for which there is an active process task with RabbitMQ. Since tasks can
    only be seen when they are not currently with a daemon worker, this command can only be run when the daemon is not
    running.
    """
    for pk in get_process_tasks(ctx.obj.profile, manager.get_communicator()):
        echo.echo(pk)


def get_active_processes() -> list[int]:
    """Return the list of pks of active processes.

    An active process is defined as a process that has a node with its attribute ``process_state`` set to one of:

        * ``created``
        * ``waiting``
        * ``running``

    :returns: A list of process pks that are marked as active in the database.
    """
    from aiida.engine import ProcessState
    from aiida.orm import ProcessNode, QueryBuilder

    return QueryBuilder().append(  # type: ignore[return-value]
        ProcessNode,
        filters={
            'attributes.process_state': {
                'in': [ProcessState.CREATED.value, ProcessState.WAITING.value, ProcessState.RUNNING.value]
            }
        },
        project='id'
    ).all(flat=True)


def iterate_process_tasks(
    profile: Profile, communicator: kiwipy.rmq.RmqCommunicator
) -> collections.abc.Iterator[kiwipy.rmq.RmqIncomingTask]:
    """Return the list of process pks that have a process task in the RabbitMQ process queue.

    :returns: A list of process pks that have a corresponding process task with RabbitMQ.
    """
    from aiida.manage.external.rmq import get_launch_queue_name

    launch_queue = get_launch_queue_name(profile.rmq_prefix)

    for task in communicator.task_queue(launch_queue):
        yield task


def get_process_tasks(profile: Profile, communicator: kiwipy.rmq.RmqCommunicator) -> list[int]:
    """Return the list of process pks that have a process task in the RabbitMQ process queue.

    :returns: A list of process pks that have a corresponding process task with RabbitMQ.
    """
    pks = []

    for task in iterate_process_tasks(profile, communicator):
        try:
            pks.append(task.body.get('args', {})['pid'])
        except KeyError:
            pass

    return pks


@cmd_tasks.command('analyze')
@click.option('--fix', is_flag=True, help='Attempt to fix the inconsistencies if any are detected.')
@with_manager
@decorators.only_if_daemon_not_running()
@click.pass_context
def cmd_tasks_analyze(ctx, manager, fix):
    """Perform analysis of process tasks.

    This command will perform a query of the database to find all "active" processes, meaning those that haven't yet
    reached a terminal state, and cross-references this with the active process tasks that are in the process queue of
    RabbitMQ. Any active process that does not have a corresponding process task can be considered a zombie, as it will
    never be picked up by a daemon worker to complete it and will effectively be "stuck". Any process task that does not
    correspond to an active process is useless and should be discarded. Finally, duplicate process tasks are also
    problematic and duplicates should be discarded.

    Use ``-v INFO`` to be more verbose and print more information.
    """
    active_processes = get_active_processes()
    process_tasks = get_process_tasks(ctx.obj.profile, manager.get_communicator())

    set_active_processes = set(active_processes)
    set_process_tasks = set(process_tasks)

    echo.echo_info(f'Active processes: {active_processes}')
    echo.echo_info(f'Process tasks: {process_tasks}')

    state_inconsistent = False

    if len(process_tasks) != len(set_process_tasks):
        state_inconsistent = True
        echo.echo_warning('There are duplicates process tasks: ', nl=False)
        echo.echo(set(x for x in process_tasks if process_tasks.count(x) > 1))

    if set_process_tasks.difference(set_active_processes):
        state_inconsistent = True
        echo.echo_warning('There are process tasks for terminated processes: ', nl=False)
        echo.echo(set_process_tasks.difference(set_active_processes))

    if set_active_processes.difference(set_process_tasks):
        state_inconsistent = True
        echo.echo_warning('There are active processes without process task: ', nl=False)
        echo.echo(set_active_processes.difference(set_process_tasks))

    if state_inconsistent and not fix:
        echo.echo_critical(
            'Inconsistencies detected between database and RabbitMQ. Run again with `--fix` to address problems.'
        )

    if not state_inconsistent:
        echo.echo_success('No inconsistencies detected between database and RabbitMQ.')
        return

    # At this point we have either exited because of inconsistencies and ``--fix`` was not passed, or we returned
    # because there were no inconsistencies, so all that is left is to address inconsistencies
    echo.echo_info('Attempting to fix inconsistencies')

    # Eliminate duplicate tasks and tasks that correspond to terminated process
    for task in iterate_process_tasks(ctx.obj.profile, manager.get_communicator()):
        pid = task.body.get('args', {}).get('pid', None)
        if pid not in set_active_processes:
            with task.processing() as outcome:
                outcome.set_result(False)
            echo.echo_report(f'Acknowledged task `{pid}`')

    # Revive zombie processes that no longer have a process task
    process_controller = manager.get_process_controller()
    for pid in set_active_processes:
        if pid not in set_process_tasks:
            process_controller.continue_process(pid)
            echo.echo_report(f'Revived process `{pid}`')


@cmd_tasks.command('revive')
@arguments.PROCESSES()
@options.FORCE()
@decorators.only_if_daemon_running(message='The daemon has to be running for this command to work.')
def cmd_tasks_revive(processes, force):
    """Revive processes that seem stuck and are no longer reachable.

    Warning: Use only as a last resort after you've gone through the checklist below.

    \b
        1. Does ``verdi status`` indicate that both daemon and RabbitMQ are running properly?
           If not, restart the daemon with ``verdi daemon restart --reset`` and restart RabbitMQ.
        2. Try ``verdi process play <PID>``.
           If you receive a message that the process is no longer reachable, use ``verdi devel revive <PID>``.

    Details: When RabbitMQ loses the process task before the process has completed, the process is never picked up by
    the daemon and will remain "stuck". ``verdi devel revive`` recreates the task, which can lead to multiple instances
    of the task being executed and should thus be used with caution.
    """
    from aiida.engine.processes.control import revive_processes

    if not force:
        echo.echo_warning('This command should only be used if you are absolutely sure the process task was lost.')
        click.confirm(text='Do you want to continue?', abort=True)

    revive_processes(processes)
