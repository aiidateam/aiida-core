###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi broker` commands for managing the message broker service."""

from __future__ import annotations

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.utils import echo
from aiida.cmdline.utils.decorators import with_broker


@verdi.group('broker')
def verdi_broker():
    """Manage the message broker service.

    The message broker is required for daemon operation and process control.
    RabbitMQ is an external service managed by your system's service manager.
    ZMQ is a built-in broker service that is managed by these commands.
    """


def _check_broker_controllable(broker):
    """Check if the broker supports service control commands.

    :param broker: The broker instance
    :raises click.ClickException: If the broker does not support service control
    """
    if not hasattr(broker, 'controller'):
        broker_name = type(broker).__name__
        raise click.ClickException(
            f'Broker `{broker_name}` does not support this command.\n'
            'RabbitMQ is an external service - manage it using your system service manager '
            '(e.g., `systemctl start rabbitmq-server` or `brew services start rabbitmq`).'
        )


@verdi_broker.command('start')
@with_broker
def broker_start(broker):
    """Start the broker service.

    This command is only available for broker backends that run as a managed service
    (e.g., ZMQ). For RabbitMQ, use your system's service manager.
    """
    _check_broker_controllable(broker)

    if broker.controller.is_running():
        echo.echo_report('Broker service is already running.')
        return

    try:
        broker.controller.start()
        echo.echo_success('Broker service started.')
    except Exception as exc:
        raise click.ClickException(f'Failed to start broker service: {exc}') from exc


@verdi_broker.command('stop')
@with_broker
def broker_stop(broker):
    """Stop the broker service.

    This command is only available for broker backends that run as a managed service
    (e.g., ZMQ). For RabbitMQ, use your system's service manager.
    """
    _check_broker_controllable(broker)

    if not broker.controller.is_running():
        echo.echo_report('Broker service is not running.')
        return

    try:
        broker.controller.stop()
        echo.echo_success('Broker service stopped.')
    except Exception as exc:
        raise click.ClickException(f'Failed to stop broker service: {exc}') from exc


@verdi_broker.command('restart')
@with_broker
def broker_restart(broker):
    """Restart the broker service.

    This command is only available for broker backends that run as a managed service
    (e.g., ZMQ). For RabbitMQ, use your system's service manager.
    """
    _check_broker_controllable(broker)

    try:
        if broker.controller.is_running():
            broker.controller.stop()
        broker.controller.start()
        echo.echo_success('Broker service restarted.')
    except Exception as exc:
        raise click.ClickException(f'Failed to restart broker service: {exc}') from exc


@verdi_broker.command('status')
@with_broker
def broker_status(broker):
    """Show the broker service status."""
    echo.echo_report(f'Broker: {broker}')

    if hasattr(broker, 'controller'):
        if broker.controller.is_running():
            status = broker.controller.get_status()
            echo.echo_success('Broker service is running.')
            if status:
                echo.echo(f'  PID: {status.get("pid", "unknown")}')
                echo.echo(f'  Pending tasks: {status.get("pending_tasks", 0)}')
                echo.echo(f'  Processing tasks: {status.get("processing_tasks", 0)}')
        else:
            echo.echo_warning('Broker service is not running.')
            echo.echo_report('Start it with `verdi broker start`.')
    else:
        # RabbitMQ or other external broker
        echo.echo_report('This broker is an external service.')
        echo.echo_report('Check its status using your system service manager.')

        # Try to verify connectivity
        try:
            broker.get_communicator()
            echo.echo_success('Connection to broker successful.')
        except Exception as exc:
            echo.echo_warning(f'Cannot connect to broker: {exc}')
