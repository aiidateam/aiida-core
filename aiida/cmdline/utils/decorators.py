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
Various decorators useful for creating verdi commands, for example loading the dbenv lazily.

Always avoids trying to load the dbenv twice. When it has to be loaded,
a spinner ASCII widget is displayed.

Provides:
 * with_dbenv, a decorator to frontload the dbenv for functions
 * dbenv, a contextmanager to load the dbenv only if a specific
    code branch gets visited and possibly avoiding the overhead if not

"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from contextlib import contextmanager
from functools import wraps

from click_spinner import spinner

from . import echo

DAEMON_NOT_RUNNING_DEFAULT_MESSAGE = 'daemon is not running'

__all__ = ('with_dbenv', 'dbenv', 'only_if_daemon_running')


def load_dbenv_if_not_loaded(**kwargs):
    """
    load dbenv if necessary, run spinner meanwhile to show command hasn't crashed
    """
    from aiida.backends.utils import load_dbenv, is_dbenv_loaded
    from aiida.backends.settings import AIIDADB_PROFILE
    kwargs['profile'] = kwargs.get('profile', AIIDADB_PROFILE)
    if not is_dbenv_loaded():
        with spinner():
            load_dbenv(**kwargs)


def with_dbenv(*load_dbenv_args, **load_dbenv_kwargs):
    """Function decorator that will load the database environment only when the function is called."""

    def decorator(function):
        """
        Function decorator that loads the dbenv if necessary before running the function

        Example::

            @with_dbenv()
            def create_node():
                from aiida.orm import Int  # note the local import
                node = Int(5)
        """

        @wraps(function)
        def decorated_function(*args, **kwargs):
            """Load dbenv if not yet loaded, then run the original function."""
            from aiida.common.exceptions import ConfigurationError, IntegrityError

            try:
                load_dbenv_if_not_loaded(*load_dbenv_args, **load_dbenv_kwargs)
            except (IntegrityError, ConfigurationError) as exception:
                echo.echo_critical(str(exception))

            return function(*args, **kwargs)

        return decorated_function

    return decorator


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
    load_dbenv_if_not_loaded()
    yield


def only_if_daemon_running(echo_function=echo.echo_critical, message=None):
    """
    Function decorator for CLI command to print critical error and exit automatically when daemon is not running.

    The error printing and exit behavior can be controlled with the decorator keyword arguments. The default message
    that is printed can be overridden as well as the echo function that is to be used. By default it uses the
    `aiida.cmdline.utils.echo.echo_critical` function which automatically aborts the command. The function can be
    substituted by for example `aiida.cmdline.utils.echo.echo_warning` to instead print just a warning and continue.

    Example::

        @only_if_daemon_running(echo_function=echo.echo_warning, message='beware that the daemon is not running')
        def create_my_calculation():
            pass

    :param echo_function: echo function to issue the message, should be from `aiida.cmdline.utils.echo`
    :param message: optional message to override the default message
    """
    if message is None:
        message = DAEMON_NOT_RUNNING_DEFAULT_MESSAGE

    def decorator(function):
        """Function decorator that checks if daemon is running and echo's message if not."""

        @wraps(function)
        def decorated_function(*args, **kwargs):
            """If daemon pid file is not found / empty, echo message and call decorated function."""
            from aiida.engine.daemon.client import get_daemon_client

            daemon_client = get_daemon_client()

            if not daemon_client.get_daemon_pid():
                echo_function(message)

            return function(*args, **kwargs)

        return decorated_function

    return decorator


def check_circus_zmq_version(function):
    """
    Function decorator to check for the right ZMQ version before trying to run circus.

    Example::

        @click.command()
        @check_circus_zmq_version
        def do_circus_stuff():
            pass
    """

    @wraps(function)
    def decorated_function(*args, **kwargs):
        """
        Verify the PyZQM is the correct version or exit without doing anything
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

        return function(*args, **kwargs)

    return decorated_function


def deprecated_command(message):
    """Function decorator that will mark a click command as deprecated when invoked."""

    def decorator(function):
        """
        Function decorator that echoes a deprecation warning before doing anything else in a click commad.

        Example::

            @click.command()
            @deprecated_command('This command has been deprecated in AiiDA v1.0, please use 'foo' instead.)
            def mycommand():
                pass
        """

        @wraps(function)
        def decorated_function(*args, **kwargs):
            """Echo a deprecation warning before doing anything else."""
            from aiida.cmdline.utils import templates
            from aiida.manage.configuration import get_config
            from textwrap import wrap

            profile = get_config().current_profile

            if not profile.is_test_profile:
                template = templates.env.get_template('deprecated.tpl')
                width = 80
                echo.echo(template.render(msg=wrap(message, width), width=width))

            return function(*args, **kwargs)

        return decorated_function

    return decorator
