###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi daemon` commands."""

from __future__ import annotations

import subprocess
import sys
import typing as t

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import options
from aiida.cmdline.utils import decorators, echo


def validate_daemon_workers(ctx, param, value):
    """Validate the value for the number of daemon workers to start with default set by config."""
    if value is None:
        value = ctx.obj.config.get_option('daemon.default_workers', ctx.obj.profile.name)

    if not isinstance(value, int):
        raise click.BadParameter(f'{value} is not an integer')

    if value <= 0:
        raise click.BadParameter(f'{value} is not a positive non-zero integer')

    return value


@verdi.group('daemon')
def verdi_daemon():
    """Inspect and manage the daemon."""


def execute_client_command(command: str, daemon_not_running_ok: bool = False, **kwargs) -> dict[str, t.Any] | None:
    """Execute a command of the :class:`aiida.engine.daemon.client.DaemonClient` and echo whether it failed or not.

    :param command: The name of hte method.
    :param daemon_not_running_ok: If ``True``, the command raising an exception because the daemon was not running is
        not treated as a failure.
    :param kwargs: Keyword arguments that are passed to the client method.
    """
    from aiida.common.exceptions import ConfigurationError
    from aiida.engine.daemon.client import DaemonException, DaemonNotRunningException, get_daemon_client

    try:
        client = get_daemon_client()
    except ConfigurationError:
        echo.echo('WARNING', fg=echo.COLORS['warning'], bold=True)
        return None

    try:
        response = getattr(client, command)(**kwargs)
    except DaemonNotRunningException as exception:
        if daemon_not_running_ok:
            echo.echo('OK', fg=echo.COLORS['success'], bold=True)
        else:
            echo.echo('FAILED', fg=echo.COLORS['error'], bold=True)
            echo.echo_critical(str(exception))
    except DaemonException as exception:
        echo.echo('FAILED', fg=echo.COLORS['error'], bold=True)
        echo.echo_critical(str(exception))
    else:
        echo.echo('OK', fg=echo.COLORS['success'], bold=True)
        return response

    return None


@verdi_daemon.command()
@click.option('--foreground', is_flag=True, help='Run in foreground.')
@click.argument('number', required=False, type=int, callback=validate_daemon_workers)
@options.TIMEOUT(default=None, required=False, type=int)
@decorators.with_dbenv()
@decorators.requires_broker
@decorators.check_circus_zmq_version
def start(foreground, number, timeout):
    """Start the daemon with NUMBER workers.

    If the NUMBER of desired workers is not specified, the default is used, which is determined by the configuration
    option `daemon.default_workers`, which if not explicitly changed defaults to 1.

    Returns exit code 0 if the daemon is OK, non-zero if there was an error.
    """
    echo.echo(f'Starting the daemon with {number} workers... ', nl=False)
    from aiida.engine.daemon.daemon import AiidaDaemon
    # TODO foreground, timeout param
    AiidaDaemon().start(number, foreground)


@verdi_daemon.command()
@click.option('--all', 'all_profiles', is_flag=True, help='Show status of all daemons.')
@options.TIMEOUT(default=None, required=False, type=int)
@click.pass_context
@decorators.requires_loaded_profile()
@decorators.requires_broker
def status(ctx, all_profiles, timeout):
    """Print the status of the current daemon or all daemons.

    Returns exit code 0 if all requested daemons are running, else exit code 3.
    """
    from aiida.engine.daemon.daemon import AiidaDaemon
    # TODO foreground, timeout param
    AiidaDaemon().status()
    return
    from tabulate import tabulate

    from aiida.cmdline.utils.common import format_local_time
    from aiida.engine.daemon.client import DaemonException, get_daemon_client

    if all_profiles is True:
        profiles = [profile for profile in ctx.obj.config.profiles if not profile.is_test_profile]
    else:
        profiles = [ctx.obj.profile]

    daemons_running = []

    for profile in profiles:
        client = get_daemon_client(profile.name)
        echo.echo('Profile: ', fg=echo.COLORS['report'], bold=True, nl=False)
        echo.echo(f'{profile.name}', bold=True)

        try:
            client.get_status(timeout=timeout)
        except DaemonException as exception:
            echo.echo_error(str(exception))
            daemons_running.append(False)
            continue

        worker_response = client.get_worker_info()
        daemon_response = client.get_daemon_info()

        workers = []
        for pid, info in worker_response['info'].items():
            if isinstance(info, dict):
                row = [pid, info['mem'], info['cpu'], format_local_time(info['create_time'])]
            else:
                row = [pid, '-', '-', '-']
            workers.append(row)

        if workers:
            workers_info = tabulate(workers, headers=['PID', 'MEM %', 'CPU %', 'started'], tablefmt='simple')
        else:
            workers_info = '--> No workers are running. Use `verdi daemon incr` to start some!\n'

        start_time = format_local_time(daemon_response['info']['create_time'])
        echo.echo(
            f'Daemon is running as PID {daemon_response["info"]["pid"]} since {start_time}\n'
            f'Active workers [{len(workers)}]:\n{workers_info}\n'
            'Use `verdi daemon [incr | decr] [num]` to increase / decrease the number of workers'
        )

    if not all(daemons_running):
        sys.exit(3)


@verdi_daemon.command()
@click.argument('number', default=1, type=int)
@options.TIMEOUT(default=None, required=False, type=int)
@decorators.requires_broker
@decorators.only_if_daemon_running()
def incr(number, timeout):
    """Add NUMBER [default=1] workers to the running daemon.

    Returns exit code 0 if the daemon is OK, non-zero if there was an error.
    """
    echo.echo(f'Starting {number} daemon workers... ', nl=False)
    execute_client_command('increase_workers', number=number, timeout=timeout)


@verdi_daemon.command()
@click.argument('number', default=1, type=int)
@options.TIMEOUT(default=None, required=False, type=int)
@decorators.requires_broker
@decorators.only_if_daemon_running()
def decr(number, timeout):
    """Remove NUMBER [default=1] workers from the running daemon.

    Returns exit code 0 if the daemon is OK, non-zero if there was an error.
    """
    echo.echo(f'Stopping {number} daemon workers... ', nl=False)
    execute_client_command('decrease_workers', number=number, timeout=timeout)


@verdi_daemon.command()
def logshow():
    """Show the log of the daemon, press CTRL+C to quit."""
    from aiida.engine.daemon.client import get_daemon_client

    client = get_daemon_client()

    with subprocess.Popen(['tail', '-f', client.daemon_log_file], env=client.get_env()) as process:
        process.wait()


@verdi_daemon.command()
@click.option('--no-wait', is_flag=True, help='Do not wait for confirmation.')
@click.option('--all', 'all_profiles', is_flag=True, help='Stop all daemons.')
@options.TIMEOUT(default=None, required=False, type=int)
@decorators.requires_broker
@click.pass_context
def stop(ctx, no_wait, all_profiles, timeout):
    """Stop the daemon.

    Returns exit code 0 if the daemon was shut down successfully (or was not running), non-zero if there was an error.
    """
    from aiida.engine.daemon.daemon import AiidaDaemon
    # TODO no-wait, timeout

    if all_profiles is True:
        profiles = [profile for profile in ctx.obj.config.profiles if not profile.is_test_profile]
    else:
        profiles = [ctx.obj.profile]

    for profile in profiles:
        echo.echo('Profile: ', fg=echo.COLORS['report'], bold=True, nl=False)
        echo.echo(f'{profile.name}', bold=True)
        echo.echo('Stopping the daemon... ', nl=False)
        AiidaDaemon(profile).stop()
        execute_client_command('stop_daemon', daemon_not_running_ok=True, wait=not no_wait, timeout=timeout)


@verdi_daemon.command()
@click.option('--reset', is_flag=True, help='Completely reset the daemon.')
@click.option('--no-wait', is_flag=True, help='Do not wait for confirmation.')
@options.TIMEOUT(default=None, required=False, type=int)
@click.pass_context
@decorators.with_dbenv()
@decorators.requires_broker
@decorators.only_if_daemon_running()
def restart(ctx, reset, no_wait, timeout):
    """Restart the daemon.

    The daemon is stopped before being restarted with the default
    number of workers that is started when calling `verdi daemon start` manually.

    Returns exit code 0 if the result is OK, non-zero if there was an error.
    """
    if reset:
        echo.echo_deprecated(
            '`--reset` flag is deprecated. Now, `verdi daemon restart` by default restarts the full daemon.'
        )
    if no_wait:
        echo.echo_deprecated('The `--no-wait` flag is deprecated and no longer has any effect.')
    if timeout is not None:
        echo.echo_deprecated('The `--timeout` option is deprecated and no longer has any effect.')

    # These two lines can be simplified to `ctx.invoke(start)` once issue #950 in `click` is resolved.
    # Due to that bug, the `callback` of the `number` argument the `start` command is not being called, which is
    # responsible for settting the default value, which causes `None` to be passed and that triggers an exception.
    # As a temporary workaround, we fetch the default here manually and pass that in explicitly.
    number = ctx.obj.config.get_option('daemon.default_workers', ctx.obj.profile.name)
    ctx.invoke(stop)
    ctx.invoke(start, number=number)


@verdi_daemon.command(hidden=True)
@click.option('--foreground', is_flag=True, help='Run in foreground.')
@click.argument('number', required=False, type=int, callback=validate_daemon_workers)
@decorators.with_dbenv()
@decorators.requires_broker
@decorators.check_circus_zmq_version
def start_circus(foreground, number):
    """This will actually launch the circus daemon, either daemonized in the background or in the foreground.

    If run in the foreground all logs are redirected to stdout.

    .. note:: this should not be called directly from the commandline!
    """
    from aiida.engine.daemon.client import get_daemon_client

    get_daemon_client()._start_daemon(number_workers=number, foreground=foreground)


@verdi_daemon.command('worker')
@decorators.with_dbenv()
@decorators.requires_broker
def worker():
    """Run a single daemon worker in the current interpreter."""
    from aiida.engine.daemon.worker import start_daemon_worker

    start_daemon_worker(foreground=True)
