# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi daemon` commands."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import subprocess
import time

import click
from click_spinner import spinner

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.utils import decorators, echo
from aiida.cmdline.utils.common import get_env_with_venv_bin
from aiida.cmdline.utils.daemon import get_daemon_status, print_client_response_status
from aiida.manage.configuration import get_config


@verdi.group('daemon')
def verdi_daemon():
    """Inspect and manage the daemon."""


@verdi_daemon.command()
@click.option('--foreground', is_flag=True, help='Run in foreground.')
@decorators.with_dbenv()
@decorators.check_circus_zmq_version
def start(foreground):
    """
    Start the daemon
    """
    from aiida.engine.daemon.client import get_daemon_client

    client = get_daemon_client()

    echo.echo('Starting the daemon... ', nl=False)

    if foreground:
        command = ['verdi', '-p', client.profile.name, 'daemon', 'start-circus', '--foreground']
    else:
        command = ['verdi', '-p', client.profile.name, 'daemon', 'start-circus']

    try:
        currenv = get_env_with_venv_bin()
        subprocess.check_output(command, env=currenv)
    except subprocess.CalledProcessError as exception:
        echo.echo_critical('{}'.format(exception))

    # We add a small timeout to give the pid-file a chance to be created
    with spinner():
        time.sleep(1)
        response = client.get_status()

    print_client_response_status(response)


@verdi_daemon.command()
@click.option('--all', 'all_profiles', is_flag=True, help='Show all daemons.')
def status(all_profiles):
    """
    Print the status of the current daemon or all daemons
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
        click.secho('{}'.format(profile.name), bold=True)
        result = get_daemon_status(client)
        echo.echo(result)


@verdi_daemon.command()
@click.argument('number', default=1, type=int)
@decorators.only_if_daemon_running()
def incr(number):
    """
    Add NUMBER [default=1] workers to the running daemon
    """
    from aiida.engine.daemon.client import get_daemon_client

    client = get_daemon_client()
    response = client.increase_workers(number)
    print_client_response_status(response)


@verdi_daemon.command()
@click.argument('number', default=1, type=int)
@decorators.only_if_daemon_running()
def decr(number):
    """
    Remove NUMBER [default=1] workers from the running daemon
    """
    from aiida.engine.daemon.client import get_daemon_client

    client = get_daemon_client()
    response = client.decrease_workers(number)
    print_client_response_status(response)


@verdi_daemon.command()
def logshow():
    """
    Show the log of the daemon, press CTRL+C to quit
    """
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
    """
    Stop the daemon
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
        click.secho('{}'.format(profile.name), bold=True)

        if not client.is_daemon_running:
            echo.echo('Daemon was not running')
            continue

        wait = not no_wait

        if wait:
            echo.echo('Waiting for the daemon to shut down... ', nl=False)
        else:
            echo.echo('Shutting the daemon down')

        response = client.stop_daemon(wait)

        if wait:
            print_client_response_status(response)


@verdi_daemon.command()
@click.option('--reset', is_flag=True, help='Completely reset the daemon.')
@click.option('--no-wait', is_flag=True, help='Do not wait for confirmation.')
@click.pass_context
@decorators.with_dbenv()
@decorators.only_if_daemon_running()
def restart(ctx, reset, no_wait):
    """
    Restart the daemon. By default will only reset the workers of the running daemon.
    After the restart the same amount of workers will be running. If the --reset flag
    is passed, however, the full circus daemon will be stopped and restarted with just
    a single worker
    """
    from aiida.engine.daemon.client import get_daemon_client

    client = get_daemon_client()

    wait = not no_wait

    if reset:
        ctx.invoke(stop)
        ctx.invoke(start)
    else:

        if wait:
            echo.echo('Restarting the daemon... ', nl=False)
        else:
            echo.echo('Restarting the daemon')

        response = client.restart_daemon(wait)

        if wait:
            print_client_response_status(response)


@verdi_daemon.command()
@click.option('--foreground', is_flag=True, help='Run in foreground.')
@decorators.with_dbenv()
@decorators.check_circus_zmq_version
def start_circus(foreground):
    """
    This will actually launch the circus daemon, either daemonized in the background
    or in the foreground, printing all logs to stdout.

    .. note:: this should not be called directly from the commandline!
    """
    from circus import get_arbiter
    from circus import logger as circus_logger
    from circus.circusd import daemonize
    from circus.pidfile import Pidfile
    from circus.util import check_future_exception_and_log, configure_logger

    from aiida.engine.daemon.client import get_daemon_client

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
            'name': client.daemon_name,
            'cmd': client.cmd_string,
            'virtualenv': client.virtualenv,
            'copy_env': True,
            'stdout_stream': {
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
            arbiter = arbiter
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
