# -*- coding: utf-8 -*-
"""
verdi daemon cli utilities
"""
from aiida.common import aiidalogger


logger = aiidalogger.getChild('workflowmanager')


def is_daemon_user():
    """
    Return True if the user is the current daemon user, False otherwise.
    """
    from aiida.backends.utils import get_daemon_user
    from aiida.common.utils import get_configured_user_email

    daemon_user = get_daemon_user()
    this_user = get_configured_user_email()

    return daemon_user == this_user


def get_env_with_venv_bin():
    """get an environment to run the daemon in that respects the current virtualenvs"""
    import os
    import sys
    pybin = os.path.dirname(sys.executable)
    currenv = os.environ.copy()
    currenv['PATH'] = pybin + ':' + currenv['PATH']
    return currenv


def get_conffile_full_path():
    """Get the full path to the config file"""
    from os.path import expanduser, join
    from aiida.common import setup
    return expanduser(join(
        setup.AIIDA_CONFIG_FOLDER,
        setup.DAEMON_SUBDIR,
        setup.DAEMON_CONF_FILE))


def get_pid_full_path():
    """
    Return the full path of the supervisord.pid file.
    """
    from os.path import normpath, expanduser, join
    from aiida.common import setup

    return normpath(expanduser(
        join(setup.AIIDA_CONFIG_FOLDER,
             setup.DAEMON_SUBDIR, "supervisord.pid")))


def get_sock_full_path():
    """
    Return the full path of the supervisord.sock file.
    """
    from os.path import normpath, expanduser, join
    from aiida.common import setup

    return normpath(expanduser(
        join(setup.AIIDA_CONFIG_FOLDER,
             setup.DAEMON_SUBDIR, "supervisord.sock")))


def get_daemon_pid():
    """
    Return the daemon pid, as read from the supervisord.pid file.
    Return None if no pid is found (or the pid is not valid).
    """
    from os.path import isfile
    if isfile(get_pid_full_path()):
        try:
            return int(open(get_pid_full_path(), 'r').read().strip())
        except (ValueError, IOError):
            return None
    else:
        return None


def _clean_sock_files():
    """
    Tries to remove the supervisord.pid and .sock files from the .aiida/daemon
    subfolder. This is typically needed when the computer is restarted with
    the daemon still on.
    """
    import errno
    import os

    try:
        os.remove(get_sock_full_path())
    except OSError as e:
        # Ignore if errno = errno.ENOENT (2): no file found
        if e.errno != errno.ENOENT:  # No such file
            raise

    try:
        os.remove(get_pid_full_path())
    except OSError as e:
        # Ignore if errno = errno.ENOENT (2): no file found
        if e.errno != errno.ENOENT:  # No such file
            raise


def kill_daemon():
    """
    This is the actual call that kills the daemon.

    There are some print statements inside, but no sys.exit, so it is
    safe to be called from other parts of the code.
    """
    import click
    from signal import SIGTERM
    import errno
    import os

    pid = get_daemon_pid()
    if pid is None:
        click.echo("Daemon not running (cannot find the PID for it)")
        return

    click.echo("Shutting down AiiDA Daemon ({})...".format(pid))
    try:
        os.kill(pid, SIGTERM)
    except OSError as e:
        if e.errno == errno.ESRCH:  # No such process
            click.echo("The process {} was not found! Assuming it was already stopped.".format(pid))
            click.echo("Cleaning the .pid and .sock files...")
            _clean_sock_files()
        else:
            raise

