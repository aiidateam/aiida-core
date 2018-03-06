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
from aiida.daemon.client import ProfileDaemonClient


@decorators.only_if_daemon_pid
def try_calling_circus_client(client, cmd):
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
            'stop': (self.cli, self.complete_none),
            'status': (self.cli, self.complete_none),
            'incr': (self.cli, self.complete_none),
            'decr': (self.cli, self.complete_none),
            'logshow': (self.cli, self.complete_none),
            'restart': (self.cli, self.complete_none),
        }

    def cli(self, *args):  # pylint: disable=unused-argument,no-self-use
        verdi.main()


@daemon_cmd.command()
@click.option('-f', '--foreground', is_flag=True,
    help='Start circusd in the foreground, useful for debugging')
@decorators.with_dbenv()
@decorators.check_circus_zmq_version
def start(foreground):
    """
    Start the daemon
    """
    profile_daemon_client = ProfileDaemonClient()

    env = get_env_with_venv_bin()
    env['PYTHONUNBUFFERED'] = 'True'
    loglevel = 'INFO'
    logoutput = '-'

    if not foreground:
        logoutput = profile_daemon_client.circus_log_file

    arbiter_config = {
        'controller': profile_daemon_client.get_endpoint(0),
        'pubsub_endpoint': profile_daemon_client.get_endpoint(1),
        'stats_endpoint': profile_daemon_client.get_endpoint(2),
        'logoutput': logoutput,
        'loglevel': loglevel,
        'debug': False,
        'statsd': True,
        'pidfile': profile_daemon_client.circus_pid_file,
        'watchers': [
            {
                'name': profile_daemon_client.daemon_name,
                'cmd': profile_daemon_client.cmd_string,
                'virtualenv': profile_daemon_client.virtualenv,
                'copy_env': True,
                'stdout_stream': {
                    'class': 'FileStream',
                    'filename': profile_daemon_client.daemon_log_file
                },
                'env': env,
            }
        ]
    }

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


@daemon_cmd.command()
@click.option('--wait', is_flag=True, help='wait for confirmation')
@decorators.only_if_daemon_pid
def stop(wait):
    """
    Stop the daemon
    """
    profile_daemon_client = ProfileDaemonClient()
    client = profile_daemon_client.get_client()

    quit_cmd = {'command': 'quit', 'properties': {'waiting': wait}}

    if wait:
        click.echo("Waiting for the AiiDA Daemon to shut down...")

    try_calling_circus_client(client, quit_cmd)

    click.echo("AiiDA Daemon shut down correctly.")


@daemon_cmd.command()
@decorators.only_if_daemon_pid
def status():
    """
    Print the status of the daemon
    """
    profile_daemon_client = ProfileDaemonClient()
    client = profile_daemon_client.get_client()

    status_cmd = {
        'command': 'status',
        'properties': {
            'name': profile_daemon_client.daemon_name
        }
    }
    status_response = try_calling_circus_client(client, status_cmd)

    if status_response['status'] == 'stopped':
        click.echo('The daemon is paused')
        sys.exit(0)
    elif status_response['status'] == 'error':
        click.echo(
            'The daemon is in an unexpected state. Please try restarting or stopping and then starting.'
        )
        sys.exit(0)

    info_cmd = {
        'command': 'stats',
        'properties': {
            'name': profile_daemon_client.daemon_name
        }
    }
    info_response = try_calling_circus_client(client, info_cmd)

    daemon_info_cmd = {'command': 'dstats', 'properties': {}}
    daemon_info_response = try_calling_circus_client(client, daemon_info_cmd)

    workers = [['PID', 'MEM %', 'CPU %', 'started']]
    for worker_pid, worker_info in info_response['info'].items():
        worker_row = [
            worker_pid, worker_info['mem'], worker_info['cpu'],
            format_local_time(worker_info['create_time'])
        ]
        workers.append(worker_row)

    no_workers_msg = '--> No workers are running. Use verdi daemon incr to start some!\n'
    workers_table = tabulate.tabulate(
        workers, headers='firstrow',
        tablefmt='simple') if len(workers) > 1 else no_workers_msg

    info = {
        'pid': daemon_info_response['info']['pid'],
        'time': format_local_time(daemon_info_response['info']['create_time']),
        'nworkers': len(workers) - 1,
        'workers': workers_table
    }

    message_tpl = (
        'Daemon is running as PID {pid} since {time}\nActive workers [{nworkers}]:\n{workers}\nuse verdi daemon [incr | decr]'
        ' [num] to increase / decrease the amount of workers.')
    click.echo(message_tpl.format(**info))


@daemon_cmd.command()
@click.argument('num', default=1, type=int)
@decorators.only_if_daemon_pid
def incr(num):
    """
    Add NUM [default=1] workers to the running daemon
    """
    profile_daemon_client = ProfileDaemonClient()
    client = profile_daemon_client.get_client()

    incr_cmd = {
        'command': 'incr',
        'properties': {
            'name': profile_daemon_client.daemon_name,
            'nb': num
        }
    }

    response = try_calling_circus_client(client, incr_cmd)
    click.echo(response['status'])


@daemon_cmd.command()
@click.argument('num', default=1, type=int)
@decorators.only_if_daemon_pid
def decr(num):
    """
    Remove NUM [default=1] workers from the running daemon
    """
    profile_daemon_client = ProfileDaemonClient()
    client = profile_daemon_client.get_client()

    incr_cmd = {
        'command': 'decr',
        'properties': {
            'name': profile_daemon_client.daemon_name,
            'nb': num
        }
    }

    response = try_calling_circus_client(client, incr_cmd)
    click.echo(response['status'])


@daemon_cmd.command()
@decorators.with_dbenv()
@decorators.only_if_daemon_pid
def logshow():
    """
    Show the log of the daemon, press CTRL+C to quit
    """
    profile_daemon_client = ProfileDaemonClient()
    try:
        currenv = get_env_with_venv_bin()
        process = subprocess.Popen(
            ['tail', '-f', profile_daemon_client.daemon_log_file], env=currenv)
        process.wait()
    except KeyboardInterrupt:
        process.kill()


@daemon_cmd.command()
@click.option(
    '--wait',
    is_flag=True,
    help='wait for the daemon to stop before restarting')
@decorators.with_dbenv()
def restart(wait):
    """
    Restart the daemon
    """
    profile_daemon_client = ProfileDaemonClient()
    client = profile_daemon_client.get_client()

    restart_cmd = {
        'command': 'restart',
        'properties': {
            'name': profile_daemon_client.daemon_name,
            'waiting': wait
        }
    }

    result = try_calling_circus_client(client, restart_cmd)
    click.echo(result['status'])
