# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi daemon` commands."""
import subprocess
import sys
import time

import click
from click_spinner import spinner

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.utils import decorators, echo
from aiida.cmdline.utils.daemon import delete_stale_pid_file, get_daemon_status, print_client_response_status
from aiida.manage import get_manager


def validate_daemon_workers(ctx, param, value):  # pylint: disable=unused-argument,invalid-name
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
@decorators.with_dbenv()
@decorators.check_circus_zmq_version
def start(foreground, number):
    """Start the daemon with NUMBER workers.

    If the NUMBER of desired workers is not specified, the default is used, which is determined by the configuration
    option `daemon.default_workers`, which if not explicitly changed defaults to 1.

    Returns exit code 0 if the daemon is OK, non-zero if there was an error.
    """
    from aiida.engine.daemon.client import DaemonException, get_daemon_client

    client = get_daemon_client()

    try:
        echo.echo(f'Starting the daemon with {number} workers... ', nl=False)
        client.start_daemon(number_workers=number, foreground=foreground)
    except DaemonException as exception:
        echo.echo('FAILED', fg=echo.COLORS['error'], bold=True)
        echo.echo_critical(str(exception))

    with spinner():
        time.sleep(1)
        response = client.get_status()

    retcode = print_client_response_status(response)
    if retcode:
        sys.exit(retcode)


@verdi_daemon.command()
@click.option('--all', 'all_profiles', is_flag=True, help='Show status of all daemons.')
def status(all_profiles):
    """Print the status of the current daemon or all daemons.

    Returns exit code 0 if all requested daemons are running, else exit code 3.
    """
    from aiida.engine.daemon.client import get_daemon_client

    manager = get_manager()
    config = manager.get_config()

    if all_profiles is True:
        profiles = [profile for profile in config.profiles if not profile.is_test_profile]
    else:
        profiles = [manager.get_profile()]

    daemons_running = []
    for profile in profiles:
        client = get_daemon_client(profile.name)
        delete_stale_pid_file(client)
        echo.echo('Profile: ', fg=echo.COLORS['report'], bold=True, nl=False)
        echo.echo(f'{profile.name}', bold=True)
        result = get_daemon_status(client)
        echo.echo(result)
        daemons_running.append(client.is_daemon_running)

    if not all(daemons_running):
        sys.exit(3)


@verdi_daemon.command()
@click.argument('number', default=1, type=int)
@decorators.only_if_daemon_running()
def incr(number):
    """Add NUMBER [default=1] workers to the running daemon.

    Returns exit code 0 if the daemon is OK, non-zero if there was an error.
    """
    from aiida.engine.daemon.client import get_daemon_client

    client = get_daemon_client()
    response = client.increase_workers(number)
    retcode = print_client_response_status(response)
    if retcode:
        sys.exit(retcode)


@verdi_daemon.command()
@click.argument('number', default=1, type=int)
@decorators.only_if_daemon_running()
def decr(number):
    """Remove NUMBER [default=1] workers from the running daemon.

    Returns exit code 0 if the daemon is OK, non-zero if there was an error.
    """
    from aiida.engine.daemon.client import get_daemon_client

    client = get_daemon_client()
    response = client.decrease_workers(number)
    retcode = print_client_response_status(response)
    if retcode:
        sys.exit(retcode)


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
def stop(no_wait, all_profiles):
    """Stop the daemon.

    Returns exit code 0 if the daemon was shut down successfully (or was not running), non-zero if there was an error.
    """
    from aiida.engine.daemon.client import get_daemon_client

    manager = get_manager()
    config = manager.get_config()

    if all_profiles is True:
        profiles = [profile for profile in config.profiles if not profile.is_test_profile]
    else:
        profiles = [manager.get_profile()]

    for profile in profiles:

        client = get_daemon_client(profile.name)

        echo.echo('Profile: ', fg=echo.COLORS['report'], bold=True, nl=False)
        echo.echo(f'{profile.name}', bold=True)

        if not client.is_daemon_running:
            echo.echo('Daemon was not running')
            continue

        delete_stale_pid_file(client)

        wait = not no_wait

        if wait:
            echo.echo('Waiting for the daemon to shut down... ', nl=False)
        else:
            echo.echo('Shutting the daemon down')

        response = client.stop_daemon(wait)

        if wait:
            if response['status'] == client.DAEMON_ERROR_NOT_RUNNING:
                echo.echo('The daemon was not running.')
            else:
                retcode = print_client_response_status(response)
                if retcode:
                    sys.exit(retcode)


@verdi_daemon.command()
@click.option('--reset', is_flag=True, help='Completely reset the daemon.')
@click.option('--no-wait', is_flag=True, help='Do not wait for confirmation.')
@click.pass_context
@decorators.with_dbenv()
@decorators.only_if_daemon_running()
def restart(ctx, reset, no_wait):
    """Restart the daemon.

    By default will only reset the workers of the running daemon. After the restart the same amount of workers will be
    running. If the `--reset` flag is passed, however, the full daemon will be stopped and restarted with the default
    number of workers that is started when calling `verdi daemon start` manually.

    Returns exit code 0 if the result is OK, non-zero if there was an error.
    """
    from aiida.engine.daemon.client import get_daemon_client

    client = get_daemon_client()
    wait = not no_wait

    if reset:
        ctx.invoke(stop)
        # These two lines can be simplified to `ctx.invoke(start)` once issue #950 in `click` is resolved.
        # Due to that bug, the `callback` of the `number` argument the `start` command is not being called, which is
        # responsible for settting the default value, which causes `None` to be passed and that triggers an exception.
        # As a temporary workaround, we fetch the default here manually and pass that in explicitly.
        number = ctx.obj.config.get_option('daemon.default_workers', ctx.obj.profile.name)
        ctx.invoke(start, number=number)
    else:

        if wait:
            echo.echo('Restarting the daemon... ', nl=False)
        else:
            echo.echo('Restarting the daemon')

        response = client.restart_daemon(wait)

        if wait:
            retcode = print_client_response_status(response)
            if retcode:
                sys.exit(retcode)


@verdi_daemon.command(hidden=True)
@click.option('--foreground', is_flag=True, help='Run in foreground.')
@click.argument('number', required=False, type=int, callback=validate_daemon_workers)
@decorators.with_dbenv()
@decorators.check_circus_zmq_version
def start_circus(foreground, number):
    """This will actually launch the circus daemon, either daemonized in the background or in the foreground.

    If run in the foreground all logs are redirected to stdout.

    .. note:: this should not be called directly from the commandline!
    """
    from aiida.engine.daemon.client import get_daemon_client
    get_daemon_client()._start_daemon(number_workers=number, foreground=foreground)  # pylint: disable=protected-access


@verdi_daemon.command('worker')
@decorators.with_dbenv()
def worker():
    """Run a single daemon worker in the current interpreter."""
    from aiida.engine.daemon.worker import start_daemon_worker
    start_daemon_worker()
