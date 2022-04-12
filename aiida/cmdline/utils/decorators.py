# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Various decorators useful for creating verdi commands, for example loading the dbenv lazily.

Always avoids trying to load the dbenv twice. When it has to be loaded,
a spinner ASCII widget is displayed.

Provides:
 * with_dbenv, a decorator to frontload the dbenv for functions
 * dbenv, a contextmanager to load the dbenv only if a specific
    code branch gets visited and possibly avoiding the overhead if not

"""
from contextlib import contextmanager

from click_spinner import spinner
from wrapt import decorator

from . import echo

DAEMON_NOT_RUNNING_DEFAULT_MESSAGE = 'daemon is not running'

__all__ = ('with_dbenv', 'dbenv', 'only_if_daemon_running')


def load_backend_if_not_loaded():
    """Load the database backend environment for the currently loaded profile.

    If no profile has been loaded yet, the default profile will be loaded first. A spinner will be shown during both
    actions to indicate that the function is working and has not crashed, since loading can take a second.
    """
    from aiida.manage import get_manager

    manager = get_manager()

    if manager.get_profile() is None or not manager.profile_storage_loaded:
        with spinner():
            manager.load_profile()  # This will load the default profile if no profile has already been loaded
            manager.get_profile_storage()  # This will load the backend of the loaded profile, if not already loaded


def with_dbenv():
    """Function decorator that will load the database environment for the currently loaded profile.

    .. note:: if no profile has been loaded yet, the default profile will be loaded first.

    Example::

        @with_dbenv()
        def create_node():
            from aiida.orm import Int  # note the local import
            node = Int(1).store()
    """

    @decorator
    def wrapper(wrapped, _, args, kwargs):
        """The wrapped function that should be called after having loaded the backend."""
        from aiida.common.exceptions import ConfigurationError, IntegrityError, LockedProfileError

        try:
            load_backend_if_not_loaded()
        except (IntegrityError, ConfigurationError, LockedProfileError) as exception:
            echo.echo_critical(str(exception))

        return wrapped(*args, **kwargs)

    return wrapper


@contextmanager
def dbenv():
    """
    Loads the dbenv for a specific region of code, does not unload afterwards

    Only use when it makes it possible to avoid loading the dbenv for certain
    code paths

    Good Example::

        # do this
        @click.command()
        @click.option('--with-db', is_flag=True)
        def profile_info(with_db):
            # read the config file
            click.echo(profile_config)

            # load the db only if necessary
            if with_db:
                with dbenv():
                    # gather db statistics for the profile
                    click.echo(db_statistics)

    This will run very fast without the --with-db flag and slow only if database info is requested

    Do not use if you will end up loading the dbenv anyway

    Bad Example::

        # don't do this
        def my_function():
            with dbenv():
                # read from db

            # do db unrelated stuff
    """
    load_backend_if_not_loaded()
    yield


def only_if_daemon_running(echo_function=echo.echo_critical, message=None):
    """Function decorator for CLI command to print critical error and exit automatically when daemon is not running.

    The error printing and exit behavior can be controlled with the decorator keyword arguments. The default message
    that is printed can be overridden as well as the echo function that is to be used. By default it uses the
    `aiida.cmdline.utils.echo.echo_critical` function which automatically aborts the command. The function can be
    substituted by for example `aiida.cmdline.utils.echo.echo_warning` to instead print just a warning and continue.

    Example::

        @only_if_daemon_running(echo_function=echo.echo_warning, message='beware that the daemon is not running')
        def create_node():
            pass

    :param echo_function: echo function to issue the message, should be from `aiida.cmdline.utils.echo`
    :param message: optional message to override the default message
    """
    if message is None:
        message = DAEMON_NOT_RUNNING_DEFAULT_MESSAGE

    @decorator
    def wrapper(wrapped, _, args, kwargs):
        """If daemon pid file is not found / empty, echo message and call decorated function."""
        from aiida.engine.daemon.client import get_daemon_client

        daemon_client = get_daemon_client()

        if not daemon_client.get_daemon_pid():
            echo_function(message)

        return wrapped(*args, **kwargs)

    return wrapper


@decorator
def check_circus_zmq_version(wrapped, _, args, kwargs):
    """
    Function decorator to check for the right ZMQ version before trying to run circus.

    Example::

        @click.command()
        @check_circus_zmq_version
        def do_circus_stuff():
            pass
    """
    import zmq
    try:
        zmq_version = [int(part) for part in zmq.__version__.split('.')[:2]]
        if len(zmq_version) < 2:
            raise ValueError()
    except (AttributeError, ValueError):
        echo.echo_critical('Unknown PyZQM version - aborting...')

    if zmq_version[0] < 13 or (zmq_version[0] == 13 and zmq_version[1] < 1):
        echo.echo_critical('AiiDA daemon needs PyZMQ >= 13.1.0 to run - aborting...')

    return wrapped(*args, **kwargs)


def deprecated_command(message):
    """Function decorator that will mark a click command as deprecated when invoked.

        Example::

            @click.command()
            @deprecated_command('This command has been deprecated in AiiDA v1.0, please use 'foo' instead.)
            def mycommand():
                pass
    """

    @decorator
    def wrapper(wrapped, _, args, kwargs):
        """Echo a deprecation warning before doing anything else."""
        from textwrap import wrap

        from aiida.cmdline.utils import templates

        template = templates.env.get_template('deprecated.tpl')
        width = 80
        echo.echo(template.render(msg=wrap(message, width - 4), width=width))

        return wrapped(*args, **kwargs)

    return wrapper
