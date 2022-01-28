# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
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
from typing import TYPE_CHECKING

import click
from pgsu import DEFAULT_DSN as DEFAULT_DBINFO  # pylint: disable=no-name-in-module
from pgsu import PGSU, PostgresConnectionMode

from aiida.cmdline.utils import echo

if TYPE_CHECKING:
    from aiida.manage.configuration import Profile

__all__ = ('Postgres', 'PostgresConnectionMode', 'DEFAULT_DBINFO')

# The last placeholder is for adding privileges of the user
_CREATE_USER_COMMAND = 'CREATE USER "{}" WITH PASSWORD \'{}\' {}'
_DROP_USER_COMMAND = 'DROP USER "{}"'
_CREATE_DB_COMMAND = (
    'CREATE DATABASE "{}" OWNER "{}" ENCODING \'UTF8\' '
    'LC_COLLATE=\'en_US.UTF-8\' LC_CTYPE=\'en_US.UTF-8\' '
    'TEMPLATE=template0'
)
_DROP_DB_COMMAND = 'DROP DATABASE "{}"'
_GRANT_PRIV_COMMAND = 'GRANT ALL PRIVILEGES ON DATABASE "{}" TO "{}"'
_USER_EXISTS_COMMAND = "SELECT usename FROM pg_user WHERE usename='{}'"
_CHECK_DB_EXISTS_COMMAND = "SELECT datname FROM pg_database WHERE datname='{}'"
_COPY_DB_COMMAND = 'CREATE DATABASE "{}" WITH TEMPLATE "{}" OWNER "{}"'


class Postgres(PGSU):
    """
    Adds convenience functions to :py:class:`pgsu.PGSU`.

    Provides convenience functions for
      * creating/dropping users
      * creating/dropping databases

    etc.

    Example::

        postgres = Postgres()
        postgres.create_dbuser('username', 'password')
        if not postgres.db_exists('dbname'):
            postgres.create_db('username', 'dbname')
    """

    def __init__(self, dbinfo=None, **kwargs):
        """See documentation of :py:meth:`pgsu.PGSU.__init__`."""
        super().__init__(dsn=dbinfo, **kwargs)

    @classmethod
    def from_profile(cls, profile: 'Profile', **kwargs):
        """Create Postgres instance with dbinfo from AiiDA profile data.

        Note: This only uses host and port from the profile, since the others are not going to be relevant for the
          database superuser.

        :param profile: AiiDA profile instance
        :param kwargs: keyword arguments forwarded to PGSU constructor

        :returns: Postgres instance pre-populated with data from AiiDA profile
        """
        dbinfo = DEFAULT_DBINFO.copy()
        dbinfo.update(
            dict(
                host=profile.storage_config['database_hostname'] or DEFAULT_DBINFO['host'],
                port=profile.storage_config['database_port'] or DEFAULT_DBINFO['port']
            )
        )

        return Postgres(dbinfo=dbinfo, **kwargs)

    ### DB user functions ###

    def dbuser_exists(self, dbuser):
        """
        Find out if postgres user with name dbuser exists

        :param str dbuser: database user to check for
        :return: (bool) True if user exists, False otherwise
        """
        return bool(self.execute(_USER_EXISTS_COMMAND.format(dbuser)))

    def create_dbuser(self, dbuser, dbpass, privileges=''):
        """
        Create a database user in postgres

        :param str dbuser: Name of the user to be created.
        :param str dbpass: Password the user should be given.
        :raises: psycopg2.errors.DuplicateObject if user already exists and
            self.connection_mode == PostgresConnectionMode.PSYCOPG
        """
        self.execute(_CREATE_USER_COMMAND.format(dbuser, dbpass, privileges))

    def drop_dbuser(self, dbuser):
        """
        Drop a database user in postgres

        :param str dbuser: Name of the user to be dropped.
        """
        self.execute(_DROP_USER_COMMAND.format(dbuser))

    def check_dbuser(self, dbuser):
        """Looks up if a given user already exists, prompts for using or creating a differently named one.

        :param str dbuser: Name of the user to be created or reused.
        :returns: tuple (dbuser, created)
        """
        if not self.interactive:
            return dbuser, not self.dbuser_exists(dbuser)
        create = True
        while create and self.dbuser_exists(dbuser):
            echo.echo_warning(f'Database user "{dbuser}" already exists!')
            if not click.confirm('Use it? '):
                dbuser = click.prompt('New database user name: ', type=str, default=dbuser)
            else:
                create = False
        return dbuser, create

    ### DB functions ###

    def db_exists(self, dbname):
        """
        Check wether a postgres database with dbname exists

        :param str dbname: Name of the database to check for
        :return: (bool), True if database exists, False otherwise
        """
        return bool(self.execute(_CHECK_DB_EXISTS_COMMAND.format(dbname)))

    def create_db(self, dbuser, dbname):
        """
        Create a database in postgres

        :param str dbuser: Name of the user which should own the db.
        :param str dbname: Name of the database.
        """
        self.execute(_CREATE_DB_COMMAND.format(dbname, dbuser))
        self.execute(_GRANT_PRIV_COMMAND.format(dbname, dbuser))

    def drop_db(self, dbname):
        """
        Drop a database in postgres

        :param str dbname: Name of the database.
        """
        self.execute(_DROP_DB_COMMAND.format(dbname))

    def copy_db(self, src_db, dest_db, dbuser):
        self.execute(_COPY_DB_COMMAND.format(dest_db, src_db, dbuser))

    def check_db(self, dbname):
        """Looks up if a database with the name exists, prompts for using or creating a differently named one.

        :param str dbname: Name of the database to be created or reused.
        :returns: tuple (dbname, created)
        """
        if not self.interactive:
            return dbname, not self.db_exists(dbname)
        create = True
        while create and self.db_exists(dbname):
            echo.echo_warning(f'database {dbname} already exists!')
            if not click.confirm('Use it (make sure it is not used by another profile)?'):
                dbname = click.prompt('new name', type=str, default=dbname)
            else:
                create = False
        return dbname, create

    def create_dbuser_db_safe(self, dbname, dbuser, dbpass):
        """Create DB and user + grant privileges.

        Prompts when reusing existing users / databases.
        """
        dbuser, create = self.check_dbuser(dbuser=dbuser)
        if create:
            self.create_dbuser(dbuser=dbuser, dbpass=dbpass)

        dbname, create = self.check_db(dbname=dbname)
        if create:
            self.create_db(dbuser, dbname)

        return dbuser, dbname

    @property
    def host_for_psycopg2(self):
        """Return correct host for psycopg2 connection (as required by regular AiiDA operation)."""
        host = self.dsn.get('host')
        if self.connection_mode == PostgresConnectionMode.PSQL:
            # If "sudo su postgres" was needed to create the DB, we are likely on Ubuntu, where
            # the same will *not* work for arbitrary database users => enforce TCP/IP connection
            host = host or 'localhost'

        return host

    @property
    def port_for_psycopg2(self):
        """Return port for psycopg2 connection (as required by regular AiiDA operation)."""
        return self.dsn.get('port')

    @property
    def dbinfo(self):
        """Alias for Postgres.dsn."""
        return self.dsn.copy()


def manual_setup_instructions(dbuser, dbname):
    """Create a message with instructions for manually creating a database"""
    dbpass = '<password>'
    instructions = '\n'.join([
        'Run the following commands as a UNIX user with access to PostgreSQL (Ubuntu: $ sudo su postgres):',
        '',
        '\t$ psql template1',
        f'	==> {_CREATE_USER_COMMAND.format(dbuser, dbpass, "")}',
        f'	==> {_CREATE_DB_COMMAND.format(dbname, dbuser)}',
        f'	==> {_GRANT_PRIV_COMMAND.format(dbname, dbuser)}',
    ])
    return instructions
