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

import re
import sys
import typing as t

import click
import wrapt

from aiida.cmdline.commands.cmd_devel import verdi_devel
from aiida.cmdline.params import arguments, options
from aiida.cmdline.utils import decorators, echo, echo_tabulate

if t.TYPE_CHECKING:
    import requests


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


def echo_response(response: 'requests.Response', exit_on_error: bool = True) -> None:
    """Echo the response of a request.

    :param response: The response to the request.
    :param exit_on_error: Boolean, if ``True``, call ``sys.exit`` with the status code of the response.
    """
    import requests

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
    """Decorate a function injecting a :class:`aiida.brokers.rabbitmq.client.RabbitmqManagementClient`."""
    from aiida.brokers.rabbitmq.client import RabbitmqManagementClient

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


@cmd_rabbitmq.command('server-properties')
@decorators.with_manager
def cmd_server_properties(manager):
    """List the server properties."""
    import yaml

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
    default=('name', 'messages', 'state'),
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
    echo_tabulate(output, headers=headers, tablefmt=tablefmt)


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
@decorators.with_broker
@decorators.only_if_daemon_not_running()
def cmd_tasks_list(broker):
    """List all active process tasks.

    This command prints a list of process pk's for which there is an active process task with RabbitMQ. Since tasks can
    only be seen when they are not currently with a daemon worker, this command can only be run when the daemon is not
    running.
    """
    from aiida.engine.processes.control import get_process_tasks

    for pk in get_process_tasks(broker):
        echo.echo(pk)


@cmd_tasks.command('analyze', deprecated='Use `verdi process repair` instead.')
@click.option('--fix', is_flag=True, help='Attempt to fix the inconsistencies if any are detected.')
@decorators.only_if_daemon_not_running()
@click.pass_context
def cmd_tasks_analyze(ctx, fix):
    """Perform analysis of process tasks.

    This command will perform a query of the database to find all "active" processes, meaning those that haven't yet
    reached a terminal state, and cross-references this with the active process tasks that are in the process queue of
    RabbitMQ. Any active process that does not have a corresponding process task can be considered a zombie, as it will
    never be picked up by a daemon worker to complete it and will effectively be "stuck". Any process task that does not
    correspond to an active process is useless and should be discarded. Finally, duplicate process tasks are also
    problematic and duplicates should be discarded.

    Use ``-v INFO`` to be more verbose and print more information.
    """
    from .cmd_process import process_repair

    ctx.invoke(process_repair, dry_run=not fix)


@cmd_tasks.command('revive')
@arguments.PROCESSES()
@options.FORCE()
@decorators.only_if_daemon_running(message='The daemon has to be running for this command to work.')
def cmd_tasks_revive(processes, force):
    """Revive processes that seem stuck and are no longer reachable.

    Warning: Use only as a last resort after you've gone through the checklist below.

    \b
        1. Does ``verdi status`` indicate that both daemon and RabbitMQ are running properly?
           If not, restart the daemon with ``verdi daemon restart`` and restart RabbitMQ.
        2. Try ``verdi process play <PID>``.
           If you receive a message that the process is no longer reachable,
           use ``verdi devel rabbitmq tasks revive <PID>``.

    Details: When RabbitMQ loses the process task before the process has completed, the process is never picked up by
    the daemon and will remain "stuck". ``verdi devel rabbitmq tasks revive`` recreates the task, which can lead to
    multiple instances of the task being executed and should thus be used with caution.
    """
    from aiida.engine.processes.control import revive_processes

    if not force:
        echo.echo_warning('This command should only be used if you are absolutely sure the process task was lost.')
        click.confirm(text='Do you want to continue?', abort=True)

    revive_processes(processes)
