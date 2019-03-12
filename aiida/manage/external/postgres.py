# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Provides an API for postgres database maintenance tasks.

This API creates and drops postgres users and databases used by the
``verdi quicksetup`` commandline tool. It allows convenient access to this
functionality from within python without knowing details about how postgres is
installed by default on various systems. If the postgres setup is not the
default installation, additional information needs to be provided.
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

try:
    import subprocess32 as subprocess
except ImportError:
    import subprocess

import click

from aiida.cmdline.utils import echo

_CREATE_USER_COMMAND = 'CREATE USER "{}" WITH PASSWORD \'{}\''
_DROP_USER_COMMAND = 'DROP USER "{}"'
_CREATE_DB_COMMAND = ('CREATE DATABASE "{}" OWNER "{}" ENCODING \'UTF8\' '
                      'LC_COLLATE=\'en_US.UTF-8\' LC_CTYPE=\'en_US.UTF-8\' '
                      'TEMPLATE=template0')
_DROP_DB_COMMAND = 'DROP DATABASE "{}"'
_GRANT_PRIV_COMMAND = 'GRANT ALL PRIVILEGES ON DATABASE "{}" TO "{}"'
_GET_USERS_COMMAND = "SELECT usename FROM pg_user WHERE usename='{}'"
_CHECK_DB_EXISTS_COMMAND = "SELECT datname FROM pg_database WHERE datname='{}'"
_COPY_DB_COMMAND = 'CREATE DATABASE "{}" WITH TEMPLATE "{}" OWNER "{}"'


class Postgres(object):  # pylint: disable=useless-object-inheritance
    """
    Provides postgres database manipulation assuming no prior setup

    * Can be used to create the initial aiida database and database user.
    * Works in every reasonable environment, provided the user can sudo

    Tries to use psycopg2 with a fallback to psql subcommands (using ``sudo su`` to run as postgres user).

    :param port: (str) Assume the database server runs on this port
    :param interactive: (bool) Allow prompting the user for information
        Will also be passed to ``sudo`` (if using ``psycopg2`` fails) and to
        the callback that can be set to be called when automatic setup detection fails
    :param quiet: (bool) Suppress messages

    Simple Example::

        postgres = Postgres()
        postgres.determine_setup()
        postgres.create_dbuser('username', 'password')
        if not postgres.db_exists('dbname'):
            postgres.create_db('username', 'dbname')

    Complex Example::

        postgres = Postgres(interactive=True, dbinfo={'port': 5433})
        postgres.setup_fail_callback = prompt_db_info
        postgres.determine_setup()
        if postgres.pg_execute:
            print('setup sucessful!')

    Note: In postgresql
     * you cannot drop databases you are currently connected to
     * 'template0' is the unmodifiable template database (which you cannot connect to)
     * 'template1' is the modifiable template database (which you can connect to)
    """

    def __init__(self, interactive=False, quiet=True, dbinfo=None):
        """Store postgres connection info.

        :param interactive: use True for verdi commands
        :param quiet: use False to show warnings/exceptions
        :param dbinfo: psycopg dictionary containing keys like 'host', 'user', 'port', 'database'
        """
        self.interactive = interactive
        self.quiet = quiet
        self.pg_execute = _pg_execute_not_connected
        self.setup_fail_callback = None
        self.setup_fail_counter = 0
        self.setup_max_tries = 1

        if dbinfo is None:
            dbinfo = {
                'host': 'localhost',
                'port': 5432,
                'user': None,
            }

        self._dbinfo = dbinfo

    @classmethod
    def from_profile(cls, profile, **kwargs):
        """Create Postgres instance with dbinfo from profile data."""
        get = profile.dictionary.get
        dbinfo = dict(
            host=get('AIIDADB_HOST', 'localhost'),
            port=get('AIIDADB_PORT', 5432),
            user=get('AIIDADB_USER', None),
            database=get('AIIDADB_NAME', None),
            password=get('AIIDADB_PASS', None),
        )
        return Postgres(dbinfo=dbinfo, **kwargs)

    def set_setup_fail_callback(self, callback):
        """
        Set a callback to be called when setup cannot be determined automatically

        :param callback: a callable with signature ``callback(interactive, dbinfo)``
        """
        self.setup_fail_callback = callback

    def set_dbinfo(self, dbinfo):
        """Set the dbinfo manually"""
        self._dbinfo = dbinfo

    def get_dbinfo(self):
        return self._dbinfo.copy()

    def determine_setup(self):
        """ Find out how postgres can be accessed.

        Depending on how postgres is set up, psycopg2 can be used to create dbs and db users,
        otherwise a subprocess has to be used that executes psql as an os user with the right permissions.

        Note: We aim for a setup that is can manipulate (create/drop) databases and database users.
         We therefore do *not* want to connect to databases of AiiDA profiles and will connect to 'template1'.

        """
        # find out if we run as a postgres superuser or can connect as postgres
        # This will work on OSX in some setups but not in the default Debian one
        dbinfo = self.get_dbinfo()
        dbinfo['database'] = 'template1'
        dbinfo['password'] = None
        for pg_user in (None, 'postgres'):
            local_dbinfo = dbinfo.copy()
            local_dbinfo['user'] = pg_user
            if _try_connect_psycopg(**local_dbinfo):
                self.pg_execute = _pg_execute_psyco
                self._dbinfo = local_dbinfo
                break

        # This will work for the default Debian postgres setup, assuming that sudo is available to the user
        if self.pg_execute == _pg_execute_not_connected:  # pylint: disable=comparison-with-callable
            # Check if the user can find the sudo command
            if _sudo_exists():
                dbinfo['user'] = 'postgres'
                if _try_subcmd(non_interactive=bool(not self.interactive), **dbinfo):
                    self.pg_execute = _pg_execute_sh
                    self._dbinfo = dbinfo
            else:
                echo.echo_warning('Could not find `sudo`. No way of connecting to the database could be found.')

        # This is to allow for any other setup
        if self.pg_execute == _pg_execute_not_connected:  # pylint: disable=comparison-with-callable
            self.setup_fail_counter += 1
            self._no_setup_detected()
        elif not self.interactive and not self.quiet:
            echo.echo_warning(('Database setup not confirmed, (non-interactive). '
                               'This may cause problems if the current user is not '
                               'allowed to create databases.'))

        return bool(self.pg_execute != _pg_execute_not_connected)  # pylint: disable=comparison-with-callable

    def create_dbuser(self, dbuser, dbpass):
        """
        Create a database user in postgres

        :param dbuser: (str), Name of the user to be created.
        :param dbpass: (str), Password the user should be given.
        """
        self.pg_execute(_CREATE_USER_COMMAND.format(dbuser, dbpass), **self._dbinfo)

    def drop_dbuser(self, dbuser):
        """
        Drop a database user in postgres

        :param dbuser: (str), Name of the user to be dropped.
        """
        self.pg_execute(_DROP_USER_COMMAND.format(dbuser), **self._dbinfo)

    def dbuser_exists(self, dbuser):
        """
        Find out if postgres user with name dbuser exists

        :param dbuser: (str) database user to check for
        :return: (bool) True if user exists, False otherwise
        """
        return bool(self.pg_execute(_GET_USERS_COMMAND.format(dbuser), **self._dbinfo))

    def create_db(self, dbuser, dbname):
        """
        Create a database in postgres

        :param dbuser: (str), Name of the user which should own the db.
        :param dbname: (str), Name of the database.
        """
        self.pg_execute(_CREATE_DB_COMMAND.format(dbname, dbuser), **self._dbinfo)
        self.pg_execute(_GRANT_PRIV_COMMAND.format(dbname, dbuser), **self._dbinfo)

    def drop_db(self, dbname):
        """
        Drop a database in postgres

        :param dbname: (str), Name of the database.
        """
        self.pg_execute(_DROP_DB_COMMAND.format(dbname), **self._dbinfo)

    def copy_db(self, src_db, dest_db, dbuser):
        self.pg_execute(_COPY_DB_COMMAND.format(dest_db, src_db, dbuser), **self._dbinfo)

    def db_exists(self, dbname):
        """
        Check wether a postgres database with dbname exists

        :param dbname: Name of the database to check for
        :return: (bool), True if database exists, False otherwise
        """
        return bool(self.pg_execute(_CHECK_DB_EXISTS_COMMAND.format(dbname), **self._dbinfo))

    def _no_setup_detected(self):
        """Print a warning message and calls the failed setup callback"""
        message = '\n'.join([
            'Detected no known postgres setup, some information is needed to create the aiida database and grant ',
            'aiida access to it. If you feel unsure about the following parameters, first check if postgresql is ',
            'installed. If postgresql is not installed please exit and install it, then run verdi quicksetup again.',
            'If postgresql is installed, please ask your system manager to provide you with the following parameters:'
        ])
        if not self.quiet:
            echo.echo_warning(message)
        if self.setup_fail_callback and self.setup_fail_counter <= self.setup_max_tries:
            self._dbinfo = self.setup_fail_callback(self.interactive, self._dbinfo)
            self.determine_setup()

    def try_connect(self):
        """Try connecting using stored dbinfo."""
        return _try_connect_psycopg(**self._dbinfo)


def manual_setup_instructions(dbuser, dbname):
    """Create a message with instructions for manually creating a database"""
    dbpass = '<password>'
    instructions = '\n'.join([
        'Please run the following commands as the user for PostgreSQL (Ubuntu: $sudo su postgres):',
        '',
        '\t$ psql template1',
        '\t==> ' + _CREATE_USER_COMMAND.format(dbuser, dbpass),
        '\t==> ' + _CREATE_DB_COMMAND.format(dbname, dbuser),
        '\t==> ' + _GRANT_PRIV_COMMAND.format(dbname, dbuser),
    ])
    return instructions


def prompt_db_info(*args):  # pylint: disable=unused-argument
    """
    Prompt interactively for postgres database connecting details

    Can be used as a setup fail callback for :py:class:`aiida.manage.external.postgres.Postgres`

    :return: dictionary with the following keys: host, port, database, user
    """
    access = False
    while not access:
        dbinfo = {}
        dbinfo['host'] = click.prompt('postgres host', default='localhost', type=str)
        dbinfo['port'] = click.prompt('postgres port', default=5432, type=int)
        dbinfo['database'] = click.prompt('template', default='template1', type=str)
        dbinfo['user'] = click.prompt('postgres super user', default='postgres', type=str)
        echo.echo('')
        echo.echo('trying to access postgres..')
        if _try_connect_psycopg(**dbinfo):
            access = True
        else:
            dbinfo['password'] = click.prompt(
                'postgres password of {}'.format(dbinfo['user']), hide_input=True, type=str, default='')
            if not dbinfo.get('password'):
                dbinfo.pop('password')
    return dbinfo


def _try_connect_psycopg(**kwargs):
    """
    try to start a psycopg2 connection.

    :return: True if successful, False otherwise
    """
    from psycopg2 import connect
    success = False
    try:
        conn = connect(**kwargs)
        success = True
        conn.close()
    except Exception:  # pylint: disable=broad-except
        pass
    return success


def _sudo_exists():
    """
    Check that the sudo command can be found

    :return: True if successful, False otherwise
    """
    try:
        subprocess.check_output(['sudo', '-V'])
    except subprocess.CalledProcessError:
        return False
    except OSError:
        return False

    return True


def _try_subcmd(**kwargs):
    """
    try to run psql in a subprocess.

    :return: True if successful, False otherwise
    """
    success = False
    try:
        kwargs['stderr'] = subprocess.STDOUT
        _pg_execute_sh(r'\q', **kwargs)
        success = True
    except subprocess.CalledProcessError:
        pass
    return success


def _pg_execute_psyco(command, **kwargs):
    """
    executes a postgres commandline through psycopg2

    :param command: A psql command line as a str
    :param kwargs: will be forwarded to psycopg2.connect
    """
    from psycopg2 import connect, ProgrammingError
    conn = connect(**kwargs)
    conn.autocommit = True
    output = None
    with conn:
        with conn.cursor() as cur:
            cur.execute(command)
            try:
                output = cur.fetchall()
            except ProgrammingError:
                pass
    conn.close()
    return output


def _pg_execute_sh(command, user='postgres', **kwargs):
    """
    executes a postgres command line as another system user in a subprocess.

    :param command: A psql command line as a str
    :param user: Name of a system user with postgres permissions
    :param kwargs: connection details to forward to psql, signature as in psycopg2.connect

    To stop `sudo` from asking for a password and fail if one is required,
    pass `non_interactive=True` as a kwarg.
    """
    options = ''
    database = kwargs.pop('database', None)
    if database:
        options += '-d {}'.format(database)
    kwargs.pop('password', None)
    host = kwargs.pop('host', None)
    if host:
        options += '-h {}'.format(host)
    port = kwargs.pop('port', None)
    if port:
        options += '-p {}'.format(port)

    # Build command line
    sudo_cmd = ['sudo']
    non_interactive = kwargs.pop('non_interactive', None)
    if non_interactive:
        sudo_cmd += ['-n']
    su_cmd = ['su', user, '-c']
    from aiida.common.escaping import escape_for_bash
    psql_cmd = ['psql {options} -tc {}'.format(escape_for_bash(command), options=options)]
    sudo_su_psql = sudo_cmd + su_cmd + psql_cmd
    result = subprocess.check_output(sudo_su_psql, **kwargs)
    result = result.decode('utf-8').strip().split('\n')
    result = [i for i in result if i]

    return result


def _pg_execute_not_connected(command, **kwargs):  # pylint: disable=unused-argument
    """
    A dummy implementation of a postgres command execution function.

    Represents inability to execute postgres commands.
    """
    from aiida.common.exceptions import FailedError
    raise FailedError('could not connect to postgres')
