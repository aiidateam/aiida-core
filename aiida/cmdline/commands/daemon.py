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

import click
import tabulate
from circus import get_arbiter
from circus import logger as circus_logger
from circus.circusd import daemonize
from circus.exc import CallError
from circus.pidfile import Pidfile
from circus.util import check_future_exception_and_log, configure_logger
from click_spinner import spinner as cli_spinner

from aiida.cmdline.baseclass import VerdiCommandWithSubcommands
from aiida.cmdline.commands import verdi, daemon_cmd
from aiida.cmdline.utils import decorators
from aiida.cmdline.utils.common import format_local_time, get_env_with_venv_bin
from aiida.cmdline.utils.daemon import CircusClient
from aiida.daemon.client import ProfileDaemonClient


@decorators.only_if_daemon_pid
def try_calling_running_client(client, cmd):
    """
    Call a given circus client with a given command only if pid file exists, handle timeout
    """
    result = None

    try:
        with cli_spinner():
            result = client.call(cmd)
    except CallError as err:
        if str(err) == 'Timed out.':
            click.echo('Daemon was not running but a PID file was found. '
                       'This indicates the daemon was terminated unexpectedly; '
                       'no action is required but proceed with caution.')
            sys.exit(0)
        raise err

    return result


def try_calling_client(client, cmd):
    """
    Call a given circus client with a given command with optional timeout
    """
    result = None

    try:
        with cli_spinner():
            result = client.call(cmd)
    except CallError as err:
        if str(err) == 'Timed out.':
            click.echo('failed, timed out')
            sys.exit(0)
        raise err

    return result


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
    profile = ProfileDaemonClient()
    client = profile.get_client()

    click.echo('Starting the daemon... ', nl=False)

    if foreground:
        command = ['verdi', 'daemon', '_start_circus', '--foreground']
    else:
        command = ['verdi', 'daemon', '_start_circus']

    try:
        currenv = get_env_with_venv_bin()
        subprocess.check_output(command, env=currenv)
    except subprocess.CalledProcessError as exception:
        click.echo('failed: {}'.format(exception))
        sys.exit(1)

    status_cmd = {
        'command': 'status',
        'properties': {
            'name': profile.daemon_name,
            'waiting': True
        }
    }

    response = try_calling_client(client, status_cmd)
    click.echo(response['status'])


@daemon_cmd.command()
@decorators.only_if_daemon_pid
@click.option('-a', '--all', 'all_profiles', is_flag=True, help='Show status for all daemons')
def status(all_profiles):
    """
    Print the status of the current daemon or all daemons
    """
    from aiida.common.profile import get_current_profile_name
    from aiida.common.setup import get_profiles_list

    if all_profiles is True:
        profile_list = [p for p in get_profiles_list() if not p.startswith('test_')]
    else:
        profile_list = [get_current_profile_name()]

    for profile_name in profile_list:
        click.secho('Profile: ', fg='red', bold=True, nl=False)
        click.secho('{}'.format(profile_name), bold=True)
        print_daemon_status(profile_name)
        click.echo()


@daemon_cmd.command()
@click.argument('num', default=1, type=int)
@decorators.only_if_daemon_pid
def incr(num):
    """
    Add NUM [default=1] workers to the running daemon
    """
    profile = ProfileDaemonClient()
    client = profile.get_client()

    incr_cmd = {
        'command': 'incr',
        'properties': {
            'name': profile.daemon_name,
            'nb': num
        }
    }

    response = try_calling_running_client(client, incr_cmd)
    click.echo(response['status'])


@daemon_cmd.command()
@click.argument('num', default=1, type=int)
@decorators.only_if_daemon_pid
def decr(num):
    """
    Remove NUM [default=1] workers from the running daemon
    """
    profile = ProfileDaemonClient()
    client = profile.get_client()

    incr_cmd = {
        'command': 'decr',
        'properties': {
            'name': profile.daemon_name,
            'nb': num
        }
    }

    response = try_calling_running_client(client, incr_cmd)
    click.echo(response['status'])


@daemon_cmd.command()
@decorators.with_dbenv()
@decorators.only_if_daemon_pid
def logshow():
    """
    Show the log of the daemon, press CTRL+C to quit
    """
    profile = ProfileDaemonClient()
    try:
        currenv = get_env_with_venv_bin()
        process = subprocess.Popen(
            ['tail', '-f', profile.daemon_log_file], env=currenv)
        process.wait()
    except KeyboardInterrupt:
        process.kill()


@daemon_cmd.command()
@click.option('--no-wait', is_flag=True, help='Do not wait for confirmation')
@decorators.only_if_daemon_pid
def stop(no_wait):
    """
    Stop the daemon
    """
    profile = ProfileDaemonClient()
    client = profile.get_client()

    wait = not no_wait

    quit_cmd = {'command': 'quit', 'properties': {'waiting': wait}}

    if wait:
        click.echo('Waiting for the daemon to shut down... ', nl=False)
    else:
        click.echo('Shutting the daemon down')

    response = try_calling_running_client(client, quit_cmd)

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
    profile = ProfileDaemonClient()
    client = profile.get_client()

    wait = not no_wait

    if reset:
        ctx.invoke(stop)
        ctx.invoke(start)
    else:
        restart_cmd = {
            'command': 'restart',
            'properties': {
                'name': profile.daemon_name,
                'waiting': wait
            }
        }

        if wait:
            click.echo('Restarting the daemon... ', nl=False)
        else:
            click.echo('Restarting the daemon')

        response = try_calling_running_client(client, restart_cmd)

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

    ..: Note: this should not be called directly from the commandline!
    """
    client = ProfileDaemonClient()

    env = get_env_with_venv_bin()
    env['PYTHONUNBUFFERED'] = 'True'
    loglevel = 'INFO'
    logoutput = '-'

    if not foreground:
        logoutput = client.circus_log_file

    arbiter_config = {
        'controller': client.get_endpoint(0),
        'pubsub_endpoint': client.get_endpoint(1),
        'stats_endpoint': client.get_endpoint(2),
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
                'filename': client.daemon_log_file
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


def print_daemon_status(profile_name):
    """
    Print the status information of the daemon for a given profile

    :param profile_name: the name of the profile
    """
    client = CircusClient(profile_name)

    if not client.is_daemon_running:
        click.echo('The daemon is not running')
        return

    status_response = client.get_status()

    if status_response['status'] == 'stopped':
        click.echo('The daemon is paused')
        return
    elif status_response['status'] == 'error':
        click.echo('The daemon is in an unexpected state. Please try restarting or stopping and then starting')
        return

    worker_response = client.get_worker_info()
    daemon_response = client.get_daemon_info()

    workers = [['PID', 'MEM %', 'CPU %', 'started']]
    for worker_pid, worker_info in worker_response['info'].items():
        worker_row = [
            worker_pid, worker_info['mem'], worker_info['cpu'],
            format_local_time(worker_info['create_time'])
        ]
        workers.append(worker_row)

    if len(workers) > 1:
        workers_info = tabulate.tabulate(workers, headers='firstrow', tablefmt='simple')
    else:
        workers_info = '--> No workers are running. Use verdi daemon incr to start some!\n'

    info = {
        'pid': daemon_response['info']['pid'],
        'time': format_local_time(daemon_response['info']['create_time']),
        'nworkers': len(workers) - 1,
        'workers': workers_info
    }

    message_tpl = (
        'Daemon is running as PID {pid} since {time}\nActive workers [{nworkers}]:\n{workers}\n'
        'Use verdi daemon [incr | decr] [num] to increase / decrease the amount of workers'
    )

    click.echo(message_tpl.format(**info))
