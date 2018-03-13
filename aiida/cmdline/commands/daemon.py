# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Verdi daemon commands
"""
import os
import sys
import subprocess
import time

import click
from click_spinner import spinner

from aiida.cmdline.baseclass import VerdiCommandWithSubcommands
from aiida.cmdline.commands import verdi, daemon_cmd
from aiida.cmdline.utils import decorators
from aiida.cmdline.utils.common import format_local_time, get_env_with_venv_bin
from aiida.cmdline.utils.daemon import CircusClient
from aiida.common.profile import get_current_profile_name
from aiida.common.setup import get_profiles_list


class Daemon(VerdiCommandWithSubcommands):
    """
    Manage the AiiDA daemon

    This command allows to interact with the AiiDA daemon.
    Valid subcommands are:

    * start: start the daemon

    * stop: restart the daemon

    * restart: restart the aiida daemon, waiting for it to cleanly exit\
        before restarting it.

    * status: inquire the status of the Daemon.

    * logshow: show the log in a continuous fashion, similar to the 'tail -f' \
        command. Press CTRL+C to exit.
    """

    def __init__(self):
        """
        A dictionary with valid commands and functions to be called:
        start, stop, status and restart.
        """
        self.valid_subcommands = {
            'start': (self.cli, self.complete_none),
            'status': (self.cli, self.complete_none),
            'restart': (self.cli, self.complete_none),
            'stop': (self.cli, self.complete_none),
            'incr': (self.cli, self.complete_none),
            'decr': (self.cli, self.complete_none),
            'logshow': (self.cli, self.complete_none),
            '_start_circus': (self.cli, self.complete_none),
        }

    def cli(self, *args):  # pylint: disable=unused-argument,no-self-use
        verdi.main()


@daemon_cmd.command()
@click.option('--foreground', is_flag=True, help='Run in foreground')
@decorators.with_dbenv()
@decorators.check_circus_zmq_version
def start(foreground):
    """
    Start the daemon
    """
    client = CircusClient()
    profile = client.daemon_client.profile_name

    click.echo('Starting the daemon... ', nl=False)

    if foreground:
        command = ['verdi', '-p', profile, 'daemon', '_start_circus', '--foreground']
    else:
        command = ['verdi', '-p', profile, 'daemon', '_start_circus']

    try:
        currenv = get_env_with_venv_bin()
        subprocess.check_output(command, env=currenv)
    except subprocess.CalledProcessError as exception:
        click.echo('failed: {}'.format(exception))
        sys.exit(1)

    # We add a small timeout to give the pid-file a chance to be created
    with spinner():
        time.sleep(1)
        response = client.get_status()

    click.echo(response['status'])


@daemon_cmd.command()
@click.option('--all', 'all_profiles', is_flag=True, help='Show all daemons')
def status(all_profiles):
    """
    Print the status of the current daemon or all daemons
    """
    if all_profiles is True:
        profiles = [p for p in get_profiles_list() if not p.startswith('test_')]
    else:
        profiles = [get_current_profile_name()]

    for profile_name in profiles:
        click.secho('Profile: ', fg='red', bold=True, nl=False)
        click.secho('{}'.format(profile_name), bold=True)
        result = get_daemon_status(profile_name)
        click.echo(result)


@daemon_cmd.command()
@click.argument('number', default=1, type=int)
@decorators.only_if_daemon_pid
def incr(number):
    """
    Add NUMBER [default=1] workers to the running daemon
    """
    client = CircusClient()
    response = client.increase_workers(number)
    click.echo(response['status'])


@daemon_cmd.command()
@click.argument('number', default=1, type=int)
@decorators.only_if_daemon_pid
def decr(number):
    """
    Remove NUMBER [default=1] workers from the running daemon
    """
    client = CircusClient()
    response = client.decrease_workers(number)
    click.echo(response['status'])


@daemon_cmd.command()
def logshow():
    """
    Show the log of the daemon, press CTRL+C to quit
    """
    client = CircusClient()
    logfile = client.daemon_client.daemon_log_file

    try:
        currenv = get_env_with_venv_bin()
        process = subprocess.Popen(['tail', '-f', logfile], env=currenv)
        process.wait()
    except KeyboardInterrupt:
        process.kill()


@daemon_cmd.command()
@click.option('--no-wait', is_flag=True, help='Do not wait for confirmation')
@click.option('--all', 'all_profiles', is_flag=True, help='Stop all daemons')
def stop(no_wait, all_profiles):
    """
    Stop the daemon
    """
    if all_profiles is True:
        profiles = [p for p in get_profiles_list() if not p.startswith('test_')]
    else:
        profiles = [get_current_profile_name()]

    for profile_name in profiles:

        client = CircusClient(profile_name)

        click.secho('Profile: ', fg='red', bold=True, nl=False)
        click.secho('{}'.format(profile_name), bold=True)

        if not client.is_daemon_running:
            click.echo('Daemon was not running')
            continue

        wait = not no_wait

        if wait:
            click.echo('Waiting for the daemon to shut down... ', nl=False)
        else:
            click.echo('Shutting the daemon down')

        response = client.stop_daemon(wait)

        if wait:
            click.echo(response['status'])


@daemon_cmd.command()
@click.option('--reset', is_flag=True, help='Completely reset the daemon')
@click.option('--no-wait', is_flag=True, help='Do not wait for confirmation')
@click.pass_context
@decorators.with_dbenv()
@decorators.only_if_daemon_pid
def restart(ctx, reset, no_wait):
    """
    Restart the daemon. By default will only reset the workers of the running daemon.
    After the restart the same amount of workers will be running. If the --reset flag
    is passed, however, the full circus daemon will be stopped and restarted with just
    a single worker
    """
    client = CircusClient()

    wait = not no_wait

    if reset:
        ctx.invoke(stop)
        ctx.invoke(start)
    else:

        if wait:
            click.echo('Restarting the daemon... ', nl=False)
        else:
            click.echo('Restarting the daemon')

        response = client.restart_daemon(wait)

        if wait:
            click.echo(response['status'])


@daemon_cmd.command()
@click.option('--foreground', is_flag=True, help='Run in foreground')
@decorators.with_dbenv()
@decorators.check_circus_zmq_version
def _start_circus(foreground):
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

    circus_client = CircusClient()
    daemon_client = circus_client.daemon_client

    env = get_env_with_venv_bin()
    env['PYTHONUNBUFFERED'] = 'True'
    loglevel = 'INFO'
    logoutput = '-'

    if not foreground:
        logoutput = daemon_client.circus_log_file

    arbiter_config = {
        'controller': circus_client.get_endpoint(0),
        'pubsub_endpoint': circus_client.get_endpoint(1),
        'stats_endpoint': circus_client.get_endpoint(2),
        'logoutput': logoutput,
        'loglevel': loglevel,
        'debug': False,
        'statsd': True,
        'pidfile': daemon_client.circus_pid_file,
        'watchers': [{
            'name': daemon_client.name,
            'cmd': daemon_client.cmd_string,
            'virtualenv': daemon_client.virtualenv,
            'copy_env': True,
            'stdout_stream': {
                'class': 'FileStream',
                'filename': daemon_client.daemon_log_file
            },
            'env': env,
        }]
    } # yapf: disable

    if not foreground:
        daemonize()

    arbiter = get_arbiter(**arbiter_config)
    pidfile = Pidfile(arbiter.pidfile)

    try:
        pidfile.create(os.getpid())
    except RuntimeError as err:
        click.echo(str(err))
        sys.exit(1)

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
        except Exception as err:
            # emergency stop
            arbiter.loop.run_sync(arbiter._emergency_stop)  # pylint: disable=protected-access
            raise err
        except KeyboardInterrupt:
            pass
        finally:
            arbiter = None
            if pidfile is not None:
                pidfile.unlink()

    sys.exit(0)


def get_daemon_status(profile_name):
    """
    Print the status information of the daemon for a given profile

    :param profile_name: the name of the profile
    """
    from tabulate import tabulate

    client = CircusClient(profile_name)

    if not client.is_daemon_running:
        return 'The daemon is not running'

    status_response = client.get_status()

    if status_response['status'] == 'stopped':
        return 'The daemon is paused'
    elif status_response['status'] == 'error':
        return 'The daemon is in an unexpected state, try verdi daemon restart --reset'

    worker_response = client.get_worker_info()
    daemon_response = client.get_daemon_info()

    workers = [['PID', 'MEM %', 'CPU %', 'started']]
    for worker_pid, worker_info in worker_response['info'].items():
        worker_row = [worker_pid, worker_info['mem'], worker_info['cpu'], format_local_time(worker_info['create_time'])]
        workers.append(worker_row)

    if len(workers) > 1:
        workers_info = tabulate(workers, headers='firstrow', tablefmt='simple')
    else:
        workers_info = '--> No workers are running. Use verdi daemon incr to start some!\n'

    info = {
        'pid': daemon_response['info']['pid'],
        'time': format_local_time(daemon_response['info']['create_time']),
        'nworkers': len(workers) - 1,
        'workers': workers_info
    }

    template = ('Daemon is running as PID {pid} since {time}\nActive workers [{nworkers}]:\n{workers}\n'
                'Use verdi daemon [incr | decr] [num] to increase / decrease the amount of workers')

    return template.format(**info)
