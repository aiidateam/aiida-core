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

__all__ = ('Postgres', 'PostgresConnectionMode', 'DEFAULT_DBINFO')

import click

from aiida.cmdline.utils import echo
from .pgsu import PGSU, PostgresConnectionMode, DEFAULT_DBINFO

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


class Postgres(PGSU):
    """
    Adds convenience functions to pgsu.Postgres.

    Provides conenience functions for
      * creating/dropping users
      * creating/dropping databases

    etc. See pgsu.Postgres for implementation details.

    Example::

        postgres = Postgres()
        postgres.create_dbuser('username', 'password')
        if not postgres.db_exists('dbname'):
            postgres.create_db('username', 'dbname')
    """

    @classmethod
    def from_profile(cls, profile, **kwargs):
        """Create Postgres instance with dbinfo from AiiDA profile data.

        Note: This only uses host and port from the profile, since the others are not going to be relevant for the
          database superuser.

        :param profile: AiiDA profile instance
        :param kwargs: keyword arguments forwarded to Postgres constructor

        :returns: Postgres instance pre-populated with data from AiiDA profile
        """
        dbinfo = DEFAULT_DBINFO.copy()

        get = profile.dictionary.get
        dbinfo.update(
            dict(
                host=get('AIIDADB_HOST', DEFAULT_DBINFO['host']),
                port=get('AIIDADB_PORT', DEFAULT_DBINFO['port']),
            ))
        return Postgres(dbinfo=dbinfo, **kwargs)

    def check_db_name(self, dbname):
        """Looks up if a database with the name exists, prompts for using or creating a differently named one."""
        create = True
        while create and self.db_exists(dbname):
            echo.echo_info('database {} already exists!'.format(dbname))
            if not click.confirm('Use it (make sure it is not used by another profile)?'):
                dbname = click.prompt('new name', type=str, default=dbname)
            else:
                create = False
        return dbname, create

    def create_dbuser(self, dbuser, dbpass):
        """
        Create a database user in postgres

        :param dbuser: (str), Name of the user to be created.
        :param dbpass: (str), Password the user should be given.
        """
        self.execute(_CREATE_USER_COMMAND.format(dbuser, dbpass))

    def drop_dbuser(self, dbuser):
        """
        Drop a database user in postgres

        :param dbuser: (str), Name of the user to be dropped.
        """
        self.execute(_DROP_USER_COMMAND.format(dbuser))

    def dbuser_exists(self, dbuser):
        """
        Find out if postgres user with name dbuser exists

        :param dbuser: (str) database user to check for
        :return: (bool) True if user exists, False otherwise
        """
        return bool(self.execute(_GET_USERS_COMMAND.format(dbuser)))

    def create_db(self, dbuser, dbname):
        """
        Create a database in postgres

        :param dbuser: (str), Name of the user which should own the db.
        :param dbname: (str), Name of the database.
        """
        self.execute(_CREATE_DB_COMMAND.format(dbname, dbuser))
        self.execute(_GRANT_PRIV_COMMAND.format(dbname, dbuser))

    def drop_db(self, dbname):
        """
        Drop a database in postgres

        :param dbname: (str), Name of the database.
        """
        self.execute(_DROP_DB_COMMAND.format(dbname))

    def copy_db(self, src_db, dest_db, dbuser):
        self.execute(_COPY_DB_COMMAND.format(dest_db, src_db, dbuser))

    def db_exists(self, dbname):
        """
        Check wether a postgres database with dbname exists

        :param dbname: Name of the database to check for
        :return: (bool), True if database exists, False otherwise
        """
        return bool(self.execute(_CHECK_DB_EXISTS_COMMAND.format(dbname)))


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
