# -*- coding: utf-8 -*-
"""
Various decorators useful for creating verdi commands, for example loading the dbenv lazily.

Always avoids trying to load the dbenv twice. When it has to be loaded,
a spinner ASCII widget is displayed.

Provides:
 * with_dbenv, a decorator to frontload the dbenv for functions
 * dbenv, a contextmanager to load the dbenv only if a specific
    code branch gets visited and possibly avoiding the overhead if not

"""
import sys
import click

from contextlib import contextmanager
from functools import wraps

from click_spinner import spinner


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
    def decorator(function):
        """
        Function decorator that loads the dbenv if necessary before running the function

        Example::

            @with_dbenv()
            def create_my_calculation():
                from aiida.orm import CalculationFactory  # note the local import
                my_calc = CalculationFactory('mycalc.mycalc')
        """

        @wraps(function)
        def decorated_function(*args, **kwargs):
            """load dbenv if not yet loaded, then run the original function"""
            load_dbenv_if_not_loaded(*load_dbenv_args, **load_dbenv_kwargs)
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


def only_if_daemon_pid(function):
    """
    Function decorator to exit with a message if the daemon is not found running (by checking pid file)

    Example::

        @only_if_daemon_pid
        def create_my_calculation():
            pass
    """

    @wraps(function)
    def decorated_function(*args, **kwargs):
        """
        If daemon pid file is not found / empty, exit without doing anything
        """
        from aiida.daemon.client import DaemonClient

        daemon_client = DaemonClient()

        if not daemon_client.get_daemon_pid():
            click.echo('The daemon is not running')
            sys.exit(0)

        return function(*args, **kwargs)

    return decorated_function


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
            click.echo('Unknown PyZQM version - aborting...')
            sys.exit(0)

        if zmq_version[0] < 13 or (zmq_version[0] == 13 and zmq_version[1] < 1):
            click.echo('AiiDA daemon needs PyZMQ >= 13.1.0 to run - aborting...')
            sys.exit(0)

        return function(*args, **kwargs)

    return decorated_function