# -*- coding: utf-8 -*-
"""Daemon subcommand module."""
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import os
import sys
import subprocess
from functools import wraps

import click
import tabulate
from click_spinner import spinner as cli_spinner
from circus import logger, get_arbiter
from circus.circusd import daemonize
from circus.pidfile import Pidfile
from circus import __version__
from circus.util import configure_logger
from circus.util import check_future_exception_and_log
from circus.exc import CallError

from aiida.common.profile import ProfileConfig
from aiida.cmdline.commands import verdi, daemon_cmd
from aiida.cmdline.baseclass import VerdiCommandWithSubcommands
from aiida.cmdline.dbenv_lazyloading import with_dbenv
from aiida.backends.utils import is_dbenv_loaded


def is_daemon_user():
    """
    Return True if the user is the current daemon user, False otherwise.
    """
    from aiida.backends.utils import get_daemon_user
    from aiida.common.utils import get_configured_user_email

    daemon_user = get_daemon_user()
    this_user = get_configured_user_email()

    return daemon_user == this_user


def _get_env_with_venv_bin():
    """Get the environment for the daemon to run in."""
    from aiida.common import setup
    pybin = os.path.dirname(sys.executable)
    currenv = os.environ.copy()
    currenv['PATH'] = pybin + ':' + currenv['PATH']
    currenv['AIIDA_PATH'] = os.path.abspath(
        os.path.expanduser(setup.AIIDA_CONFIG_FOLDER))
    return currenv


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
        import aiida
        from aiida.common import setup

        self.valid_subcommands = {
            'start': (self.cli, self.complete_none),
            'stop': (self.cli, self.complete_none),
            'status': (self.cli, self.complete_none),
            'incr': (self.cli, self.complete_none),
            'decr': (self.cli, self.complete_none),
            'logshow': (self.cli, self.complete_none),
            'restart': (self.cli, self.complete_none),
            'configureuser': (self.configure_user, self.complete_none),
        }

        self.logfile = setup.DAEMON_LOG_FILE
        self.pidfile = setup.DAEMON_PID_FILE
        self.workdir = os.path.join(
            os.path.split(os.path.abspath(aiida.__file__))[0], "daemon")
        self.celerybeat_schedule = os.path.join(setup.AIIDA_CONFIG_FOLDER,
                                                setup.DAEMON_SUBDIR,
                                                "celerybeat-schedule")

    def cli(self, *args):  # pylint: disable=unused-argument,no-self-use
        verdi.main()

    def _get_pid_full_path(self):
        """
        Return the full path of the celery.pid file.
        """
        return os.path.normpath(os.path.expanduser(self.pidfile))

    def get_daemon_pid(self):
        """
        Return the daemon pid, as read from the celery.pid file.
        Return None if no pid is found (or the pid is not valid).
        """
        if os.path.isfile(self._get_pid_full_path()):
            try:
                return int(open(self._get_pid_full_path(), 'r').read().strip())
            except (ValueError, IOError):
                return None
        else:
            return None

    def kill_daemon(self):
        """
        This is the actual call that kills the daemon.

        There are some print statements inside, but no sys.exit, so it is
        safe to be called from other parts of the code.
        """
        from signal import SIGTERM
        import errno

        pid = self.get_daemon_pid()
        if pid is None:
            click.echo("Daemon not running (cannot find the PID for it)")
            return

        click.echo("Shutting down AiiDA Daemon ({})...".format(pid))
        try:
            os.kill(pid, SIGTERM)
        except OSError as err:
            if err.errno == errno.ESRCH:  # No such process
                click.echo("The process {} was not found! "
                           "Assuming it was already stopped.".format(pid))
                click.echo("Cleaning the .pid and .sock files...")
                self._clean_pid_files()
            else:
                raise

    def configure_user(self, *args):  # pylint: disable=too-many-locals
        """
        Configure the user that can run the daemon.
        """
        if not is_dbenv_loaded():
            from aiida.backends.utils import load_dbenv
            load_dbenv()

        if args:
            click.echo(
                "No arguments allowed for the '{}' command.".format(
                    self.get_full_command_name()),
                err=True)
            sys.exit(1)

        from aiida.utils import timezone
        from aiida.backends.utils import get_daemon_user, set_daemon_user
        from aiida.common.utils import (get_configured_user_email, query_yes_no,
                                        query_string)
        from aiida.daemon.timestamps import get_most_recent_daemon_timestamp
        from aiida.common.utils import str_timedelta
        from aiida.orm.user import User

        old_daemon_user = get_daemon_user()
        this_user = get_configured_user_email()

        click.echo("> Current default user: {}".format(this_user))
        click.echo(
            "> Currently configured user who can run the daemon: {}".format(
                old_daemon_user))
        if old_daemon_user == this_user:
            click.echo(
                "  (therefore, at the moment you are the user who can run "
                "the daemon)")
            pid = self.get_daemon_pid()
            if pid is not None:
                click.echo("The daemon is running! I will not proceed.")
                sys.exit(1)
        else:
            click.echo(
                "  (therefore, you cannot run the daemon, at the moment)")

        most_recent_timestamp = get_most_recent_daemon_timestamp()

        click.echo("*" * 76)
        click.echo("* {:72s} *".format(
            "WARNING! Change this setting only if you "
            "are sure of what you are doing."))
        click.echo("* {:72s} *".format("Moreover, make sure that the "
                                       "daemon is stopped."))

        if most_recent_timestamp is not None:
            timestamp_delta = timezone.now() - most_recent_timestamp
            last_check_string = (
                "[The most recent timestamp from the daemon was {}]".format(
                    str_timedelta(timestamp_delta)))
            click.echo("* {:72s} *".format(last_check_string))

        click.echo("*" * 76)

        answer = query_yes_no(
            "Are you really sure that you want to change "
            "the daemon user?",
            default="no")
        if not answer:
            sys.exit(0)

        click.echo("")
        click.echo(
            "Enter below the email of the new user who can run the daemon.")
        new_daemon_user_email = query_string("New daemon user: ", None)

        found_users = User.search_for_users(email=new_daemon_user_email)
        if not found_users:
            click.echo(
                "ERROR! The user you specified ({}) does "
                "not exist in the database!!".format(new_daemon_user_email))
            click.echo("The available users are {}".format(
                [_.email for _ in User.search_for_users()]))
            sys.exit(1)

        set_daemon_user(new_daemon_user_email)

        click.echo("The new user that can run the daemon is now {} {}.".format(
            found_users[0].first_name, found_users[0].last_name))

    def _clean_pid_files(self):
        """
        Tries to remove the celery.pid files from the .aiida/daemon
        subfolder. This is typically needed when the computer is restarted with
        the daemon still on.
        """
        import errno

        try:
            os.remove(self._get_pid_full_path())
        except OSError as err:
            # Ignore if errno = errno.ENOENT (2): no file found
            if err.errno != errno.ENOENT:  # No such file
                raise


def daemon_user_guard(function):
    """
    Function decorator that checks wether the user is the daemon user before running the function

    Example::

        @daemon_user_guard
        def create_my_calculation():
            ... do stuff ...
    """

    @wraps(function)
    @with_dbenv()
    def decorated_function(*args, **kwargs):
        """Check if the current user is allowed to run the daemon, only if yes, run the original function."""
        from aiida.backends.utils import get_daemon_user
        from aiida.common.utils import get_configured_user_email
        if not is_daemon_user():
            click.echo(
                "You are not the daemon user! I will not start the daemon.")
            click.echo("(The daemon user is '{}', you are '{}')".format(
                get_daemon_user(), get_configured_user_email()))
            click.echo("")
            click.echo("** FOR ADVANCED USERS ONLY: **")
            click.echo(
                "To change the current default user, use 'verdi install --only-config'"
            )
            click.echo(
                "To change the daemon user, use 'verdi daemon configureuser'")

            sys.exit(1)
        return function(*args, **kwargs)

    return decorated_function


def only_if_daemon_pid(function):
    """
    Function decorator to exit with a message if the daemon is not found running (by checking pid file).

    Example::

        @only_if_daemon_pid
        def create_my_calculation():
            ... do stuff ...
    """

    @wraps(function)
    def decorated_function(*args, **kwargs):
        """If daemon pid file is not found / empty, exit without doing anything."""
        profile_config = ProfileConfig()

        if not profile_config.get_daemon_pid:
            click.echo('The daemon is not running.')
            sys.exit(0)

        return function(*args, **kwargs)

    return decorated_function


@only_if_daemon_pid
def try_call_client(client, cmd):
    """Call a given circus client with a given command only if pid file exists, handle timeout."""
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


def check_circus_zmq_version(function):
    """
    Function decorator to check for the right ZMQ version before trying to run circus.

    Example::

        @click.command()
        @only_if_daemon_pid
        def do_circus_stuff():
            ... do stuff ...
    """

    @wraps(function)
    def decorated_function(*args, **kwargs):
        """If daemon pid file is not found / empty, exit without doing anything."""

        import zmq
        try:
            zmq_version = [int(part) for part in zmq.__version__.split('.')[:2]]
            if len(zmq_version) < 2:
                raise ValueError()
        except (AttributeError, ValueError):
            click.echo('Unknown PyZQM version - aborting...')
            sys.exit(0)

        if zmq_version[0] < 13 or (zmq_version[0] == 13 and zmq_version[1] < 1):
            click.echo(
                'aiida daemon needs PyZMQ >= 13.1.0 to run - aborting...')
            sys.exit(0)

        return function(*args, **kwargs)

    return decorated_function


@daemon_cmd.command()
@click.option(
    '--fg',
    '--foreground',
    is_flag=True,
    help="Start circusd in the background. Not supported on Windows")
@with_dbenv()
@daemon_user_guard
@check_circus_zmq_version
def start(foreground):
    """Start an aiida daemon."""

    # Create the arbiter
    profile_config = ProfileConfig()

    loglevel = 'INFO'
    logoutput = '-'

    if not foreground:
        logoutput = profile_config.circus_log_file
        daemonize()

    env = _get_env_with_venv_bin()
    env['PYTHONUNBUFFERED'] = 'True'

    arbiter = get_arbiter(
        controller=profile_config.get_endpoint(0),
        pubsub_endpoint=profile_config.get_endpoint(1),
        stats_endpoint=profile_config.get_endpoint(2),
        logoutput=logoutput,
        loglevel=loglevel,
        debug=False,
        statsd=True,
        pidfile=profile_config.circus_pid_file,
        watchers=[{
            'name': profile_config.daemon_name,
            'cmd': profile_config.cmd_string,
            'virtualenv': profile_config.virtualenv,
            'copy_env': True,
            'stdout_stream': {
                'class': 'FileStream',
                'filename': profile_config.daemon_log_file
            },
            'env': env,
        }])

    pidfile = Pidfile(arbiter.pidfile)

    try:
        pidfile.create(os.getpid())
    except RuntimeError as err:
        click.echo(str(err))
        sys.exit(1)

    # configure the logger
    loggerconfig = None
    loggerconfig = loggerconfig or arbiter.loggerconfig or None
    configure_logger(logger, loglevel, logoutput, loggerconfig)

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
@click.option('--wait', is_flag=True)
@only_if_daemon_pid
def stop(wait):
    """
    Stop the daemon.

    :param wait: If True, also verifies that the process was already
        killed. It attempts at most ``max_retries`` times, with ``sleep_between_retries``
        seconds between one attempt and the following one (both variables are
        for the time being hardcoded in the function).

    :return: None if ``wait_for_death`` is False. True/False if the process was
        actually dead or after all the retries it was still alive.
    """
    profile_config = ProfileConfig()
    client = profile_config.get_client()

    quit_cmd = {'command': 'quit', 'properties': {'waiting': wait}}

    if wait:
        click.echo("Waiting for the AiiDA Daemon to shut down...")

    try_call_client(client, quit_cmd)

    click.echo("AiiDA Daemon shut down correctly.")


def format_local_time(epoch_sec, format_str='%Y-%m-%d %H:%M:%S'):
    from aiida.utils import timezone
    return timezone.datetime.fromtimestamp(epoch_sec).strftime(format_str)


@daemon_cmd.command()
@only_if_daemon_pid
def status():
    """Print the status of the daemon."""
    profile_config = ProfileConfig()
    client = profile_config.get_client()

    status_cmd = {
        'command': 'status',
        'properties': {
            'name': profile_config.daemon_name
        }
    }
    status_response = try_call_client(client, status_cmd)

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
            'name': profile_config.daemon_name
        }
    }
    info_response = try_call_client(client, info_cmd)

    daemon_info_cmd = {'command': 'dstats', 'properties': {}}
    daemon_info_response = try_call_client(client, daemon_info_cmd)

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
@only_if_daemon_pid
def incr(num):
    """Add NUM [default=1] workers to a running daemon."""
    profile_config = ProfileConfig()
    client = profile_config.get_client()

    incr_cmd = {
        'command': 'incr',
        'properties': {
            'name': profile_config.daemon_name,
            'nb': num
        }
    }

    response = try_call_client(client, incr_cmd)
    click.echo(response['status'])


@daemon_cmd.command()
@click.argument('num', default=1, type=int)
@only_if_daemon_pid
def decr(num):
    """Add NUM [default=1] workers to a running daemon."""
    profile_config = ProfileConfig()
    client = profile_config.get_client()

    incr_cmd = {
        'command': 'decr',
        'properties': {
            'name': profile_config.daemon_name,
            'nb': num
        }
    }

    response = try_call_client(client, incr_cmd)
    click.echo(response['status'])


@daemon_cmd.command()
@with_dbenv()
@only_if_daemon_pid
def logshow():
    """Show the log of the daemon, press CTRL+C to quit."""
    profile_config = ProfileConfig()
    try:
        currenv = _get_env_with_venv_bin()
        process = subprocess.Popen(
            ['tail', '-f', profile_config.daemon_log_file], env=currenv)
        process.wait()
    except KeyboardInterrupt:
        # exit on CTRL+C
        process.kill()


@daemon_cmd.command()
@click.option('--wait', is_flag=True)
@with_dbenv()
@daemon_user_guard
def restart(wait):
    """
    Restart the daemon.

    Before restarting, wait for the daemon to really shut down.
    """
    profile_config = ProfileConfig()
    client = profile_config.get_client()

    restart_cmd = {
        'command': 'restart',
        'properties': {
            'name': profile_config.daemon_name,
            'waiting': wait
        }
    }

    result = try_call_client(client, restart_cmd)
    click.echo(result['status'])
