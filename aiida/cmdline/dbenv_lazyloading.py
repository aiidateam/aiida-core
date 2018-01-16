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
Load the dbenv lazily, especially useful in commandline commands

Always avoids trying to load the dbenv twice. When it has to be loaded,
a spinner ASCII widget is displayed.

Provides:
 * with_dbenv, a decorator to frontload the dbenv for functions
 * dbenv, a contextmanager to load the dbenv only if a specific
    code branch gets visited and possibly avoiding the overhead if not

"""
from contextlib import contextmanager
from functools import wraps

from click_spinner import spinner as cli_spinner


def load_dbenv_if_not_loaded(**kwargs):
    """
    load dbenv if necessary, run spinner meanwhile to show command hasn't crashed
    """
    from aiida.backends.utils import load_dbenv, is_dbenv_loaded
    if not is_dbenv_loaded():
        with cli_spinner():
            load_dbenv(**kwargs)


def with_dbenv(function):
    """
    Function decorator that loads the dbenv if necessary before running the function

    Example::

        @with_dbenv
        def create_my_calculation():
            from aiida.orm import CalculationFactory  # note the local import
            my_calc = CalculationFactory('mycalc.mycalc')
    """

    @wraps(function)
    def decorated_function(*args, **kwargs):
        """load dbenv if not yet loaded, then run the original function"""
        load_dbenv_if_not_loaded()
        return function(*args, **kwargs)

    return decorated_function


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
