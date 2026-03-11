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


@verdi_daemon.command()
@click.option('--foreground', is_flag=True, help='Run in foreground.')
@click.argument('number', required=False, type=int, callback=validate_daemon_workers)
@options.TIMEOUT(default=None, required=False, type=int)
@decorators.with_dbenv()
@decorators.requires_broker
def start(foreground, number, timeout):
    """Start the daemon with NUMBER workers.

    If the NUMBER of desired workers is not specified, the default is used, which is determined by the configuration
    option `daemon.default_workers`, which if not explicitly changed defaults to 1.

    Returns exit code 0 if the daemon is OK, non-zero if there was an error.
    """
    from aiida.engine.daemon.client import DaemonException
    from aiida.engine.daemon.daemon import AiidaDaemonController

    echo.echo(f'Starting the daemon with {number} workers... ', nl=False)
    try:
        AiidaDaemonController().start(number, foreground)
    except DaemonException as exception:
        echo.echo('FAILED', fg=echo.COLORS['error'], bold=True)
        echo.echo_critical(str(exception))
    else:
        echo.echo('OK', fg=echo.COLORS['success'], bold=True)


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
    from tabulate import tabulate

    from aiida.cmdline.utils.common import format_local_time
    from aiida.engine.daemon.daemon import AiidaDaemonController

    if all_profiles is True:
        profiles = [profile for profile in ctx.obj.config.profiles if not profile.is_test_profile]
    else:
        profiles = [ctx.obj.profile]

    daemons_running = []

    for profile in profiles:
        daemon = AiidaDaemonController(profile)
        echo.echo('Profile: ', fg=echo.COLORS['report'], bold=True, nl=False)
        echo.echo(f'{profile.name}', bold=True)

        daemon_status = daemon.get_status()

        if daemon_status['status'] != 'running':
            echo.echo_error('The daemon is not running.')
            daemons_running.append(False)
            continue

        daemons_running.append(True)

        workers = []
        for worker_info in daemon_status['workers']:
            workers.append([
                worker_info['pid'],
                worker_info['state'],
                format_local_time(worker_info['started']),
                worker_info['failures'],
            ])

        if workers:
            workers_info = tabulate(workers, headers=['PID', 'State', 'Started', 'Failures'], tablefmt='simple')
        else:
            workers_info = '--> No workers are running. Use `verdi daemon incr` to start some!\n'

        start_time = format_local_time(daemon_status['started'])
        echo.echo(
            f'Daemon is running as PID {daemon_status["pid"]} since {start_time}\n'
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
    from aiida.engine.daemon.client import DaemonException
    from aiida.engine.daemon.daemon import AiidaDaemonController

    echo.echo(f'Starting {number} daemon workers... ', nl=False)
    try:
        AiidaDaemonController().increase_workers(number)
    except DaemonException as exception:
        echo.echo('FAILED', fg=echo.COLORS['error'], bold=True)
        echo.echo_critical(str(exception))
    else:
        echo.echo('OK', fg=echo.COLORS['success'], bold=True)


@verdi_daemon.command()
@click.argument('number', default=1, type=int)
@options.TIMEOUT(default=None, required=False, type=int)
@decorators.requires_broker
@decorators.only_if_daemon_running()
def decr(number, timeout):
    """Remove NUMBER [default=1] workers from the running daemon.

    Returns exit code 0 if the daemon is OK, non-zero if there was an error.
    """
    from aiida.engine.daemon.client import DaemonException
    from aiida.engine.daemon.daemon import AiidaDaemonController

    echo.echo(f'Stopping {number} daemon workers... ', nl=False)
    try:
        AiidaDaemonController().decrease_workers(number)
    except DaemonException as exception:
        echo.echo('FAILED', fg=echo.COLORS['error'], bold=True)
        echo.echo_critical(str(exception))
    else:
        echo.echo('OK', fg=echo.COLORS['success'], bold=True)


@verdi_daemon.command()
def logshow():
    """Show the log of the daemon, press CTRL+C to quit."""
    from aiida.engine.daemon.daemon import AiidaDaemonController

    daemon = AiidaDaemonController()
    log_file = daemon.daemon_log_file

    if log_file is None:
        echo.echo_critical('No daemon log file found. Has the daemon been started?')

    with subprocess.Popen(['tail', '-f', log_file]) as process:
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
    from aiida.engine.daemon.client import DaemonException, DaemonNotRunningException
    from aiida.engine.daemon.daemon import AiidaDaemonController

    if all_profiles is True:
        profiles = [profile for profile in ctx.obj.config.profiles if not profile.is_test_profile]
    else:
        profiles = [ctx.obj.profile]

    for profile in profiles:
        echo.echo('Profile: ', fg=echo.COLORS['report'], bold=True, nl=False)
        echo.echo(f'{profile.name}', bold=True)
        echo.echo('Stopping the daemon... ', nl=False)
        try:
            AiidaDaemonController(profile).stop()
        except DaemonNotRunningException:
            echo.echo('OK', fg=echo.COLORS['success'], bold=True)
        except DaemonException as exception:
            echo.echo('FAILED', fg=echo.COLORS['error'], bold=True)
            echo.echo_critical(str(exception))
        else:
            echo.echo('OK', fg=echo.COLORS['success'], bold=True)


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

    number = ctx.obj.config.get_option('daemon.default_workers', ctx.obj.profile.name)
    ctx.invoke(stop)
    ctx.invoke(start, number=number)


@verdi_daemon.command('_supervisor', hidden=True)
@click.argument('number', required=True, type=int)
@decorators.with_dbenv()
@decorators.requires_broker
def run_supervisor(number):
    """Start the daemon supervisor process (internal, called by AiidaDaemonController.start).

    This is the subprocess entry point that performs the double-fork daemonization.
    It should not be called directly by users.
    """
    from aiida.engine.daemon.daemon import AiidaDaemonController, AiidaWorkerConfig, ServiceConfigMap, DaemonController

    daemon = AiidaDaemonController()
    service_configs = ServiceConfigMap([AiidaWorkerConfig(num_workers=number)])
    DaemonController.start(daemon._daemon_dir, service_configs, foreground=False)


@verdi_daemon.command('worker')
@decorators.with_dbenv()
@decorators.requires_broker
def worker():
    """Run a single daemon worker in the current interpreter."""
    from aiida.engine.daemon.worker import start_daemon_worker

    start_daemon_worker(foreground=True)
