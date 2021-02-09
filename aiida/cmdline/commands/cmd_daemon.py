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

import os
import subprocess
import time
import sys

import click
from click_spinner import spinner

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.utils import decorators, echo
from aiida.cmdline.utils.common import get_env_with_venv_bin
from aiida.cmdline.utils.daemon import get_daemon_status, \
    print_client_response_status, delete_stale_pid_file, _START_CIRCUS_COMMAND
from aiida.manage.configuration import get_config


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
    from aiida.engine.daemon.client import get_daemon_client

    client = get_daemon_client()

    echo.echo('Starting the daemon... ', nl=False)

    if foreground:
        command = ['verdi', '-p', client.profile.name, 'daemon', _START_CIRCUS_COMMAND, '--foreground', str(number)]
    else:
        command = ['verdi', '-p', client.profile.name, 'daemon', _START_CIRCUS_COMMAND, str(number)]

    try:
        currenv = get_env_with_venv_bin()
        subprocess.check_output(command, env=currenv, stderr=subprocess.STDOUT)  # pylint: disable=unexpected-keyword-arg
    except subprocess.CalledProcessError as exception:
        click.secho('FAILED', fg='red', bold=True)
        echo.echo_critical(str(exception))

    # We add a small timeout to give the pid-file a chance to be created
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

    config = get_config()

    if all_profiles is True:
        profiles = [profile for profile in config.profiles if not profile.is_test_profile]
    else:
        profiles = [config.current_profile]

    daemons_running = []
    for profile in profiles:
        client = get_daemon_client(profile.name)
        delete_stale_pid_file(client)
        click.secho('Profile: ', fg='red', bold=True, nl=False)
        click.secho(f'{profile.name}', bold=True)
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

    try:
        currenv = get_env_with_venv_bin()
        process = subprocess.Popen(['tail', '-f', client.daemon_log_file], env=currenv)
        process.wait()
    except KeyboardInterrupt:
        process.kill()


@verdi_daemon.command()
@click.option('--no-wait', is_flag=True, help='Do not wait for confirmation.')
@click.option('--all', 'all_profiles', is_flag=True, help='Stop all daemons.')
def stop(no_wait, all_profiles):
    """Stop the daemon.

    Returns exit code 0 if the daemon was shut down successfully (or was not running), non-zero if there was an error.
    """
    from aiida.engine.daemon.client import get_daemon_client

    config = get_config()

    if all_profiles is True:
        profiles = [profile for profile in config.profiles if not profile.is_test_profile]
    else:
        profiles = [config.current_profile]

    for profile in profiles:

        client = get_daemon_client(profile.name)

        click.secho('Profile: ', fg='red', bold=True, nl=False)
        click.secho(f'{profile.name}', bold=True)

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
                click.echo('The daemon was not running.')
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
    from circus import get_arbiter
    from circus import logger as circus_logger
    from circus.circusd import daemonize
    from circus.pidfile import Pidfile
    from circus.util import check_future_exception_and_log, configure_logger

    from aiida.engine.daemon.client import get_daemon_client

    if foreground and number > 1:
        raise click.ClickException('can only run a single worker when running in the foreground')

    client = get_daemon_client()

    loglevel = client.loglevel
    logoutput = '-'

    if not foreground:
        logoutput = client.circus_log_file

    arbiter_config = {
        'controller': client.get_controller_endpoint(),
        'pubsub_endpoint': client.get_pubsub_endpoint(),
        'stats_endpoint': client.get_stats_endpoint(),
        'logoutput': logoutput,
        'loglevel': loglevel,
        'debug': False,
        'statsd': True,
        'pidfile': client.circus_pid_file,
        'watchers': [{
            'cmd': client.cmd_string,
            'name': client.daemon_name,
            'numprocesses': number,
            'virtualenv': client.virtualenv,
            'copy_env': True,
            'stdout_stream': {
                'class': 'FileStream',
                'filename': client.daemon_log_file,
            },
            'stderr_stream': {
                'class': 'FileStream',
                'filename': client.daemon_log_file,
            },
            'env': get_env_with_venv_bin(),
        }]
    }  # yapf: disable

    if not foreground:
        daemonize()

    arbiter = get_arbiter(**arbiter_config)
    pidfile = Pidfile(arbiter.pidfile)

    try:
        pidfile.create(os.getpid())
    except RuntimeError as exception:
        echo.echo_critical(str(exception))

    # Configure the logger
    loggerconfig = None
    loggerconfig = loggerconfig or arbiter.loggerconfig or None
    configure_logger(circus_logger, loglevel, logoutput, loggerconfig)

    # Main loop
    should_restart = True

    while should_restart:
        try:
            future = arbiter.start()
            should_restart = False
            if check_future_exception_and_log(future) is None:
                should_restart = arbiter._restarting  # pylint: disable=protected-access
        except Exception as exception:
            # Emergency stop
            arbiter.loop.run_sync(arbiter._emergency_stop)  # pylint: disable=protected-access
            raise exception
        except KeyboardInterrupt:
            pass
        finally:
            arbiter = None
            if pidfile is not None:
                pidfile.unlink()
