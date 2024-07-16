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

from pgsu import DEFAULT_DSN as DEFAULT_DBINFO
from pgsu import PGSU, PostgresConnectionMode

if TYPE_CHECKING:
    from aiida.manage.configuration import Profile

# The last placeholder is for adding privileges of the user
_CREATE_USER_COMMAND = 'CREATE USER "{}" WITH PASSWORD \'{}\' {}'
_DROP_USER_COMMAND = 'DROP USER "{}"'
_CREATE_DB_COMMAND = (
    'CREATE DATABASE "{}" OWNER "{}" ENCODING \'UTF8\' '
    "LC_COLLATE='en_US.UTF-8' LC_CTYPE='en_US.UTF-8' "
    'TEMPLATE=template0'
)
_DROP_DB_COMMAND = 'DROP DATABASE "{}"'
_GRANT_ROLE_COMMAND = 'GRANT "{}" TO current_user'
_USER_EXISTS_COMMAND = "SELECT usename FROM pg_user WHERE usename='{}'"
_CHECK_DB_EXISTS_COMMAND = "SELECT datname FROM pg_database WHERE datname='{}'"
_COPY_DB_COMMAND = 'CREATE DATABASE "{}" WITH TEMPLATE "{}" OWNER "{}"'


class Postgres(PGSU):
    """Adds convenience functions to :py:class:`pgsu.PGSU`.

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
                port=profile.storage_config['database_port'] or DEFAULT_DBINFO['port'],
            )
        )

        return Postgres(dbinfo=dbinfo, **kwargs)

    ### DB user functions ###

    def dbuser_exists(self, dbuser):
        """Find out if postgres user with name dbuser exists

        :param str dbuser: database user to check for
        :return: (bool) True if user exists, False otherwise
        """
        return bool(self.execute(_USER_EXISTS_COMMAND.format(dbuser)))

    def create_dbuser(self, dbuser, dbpass, privileges=''):
        """Create a database user in postgres

        :param str dbuser: Name of the user to be created.
        :param str dbpass: Password the user should be given.
        :raises: psycopg.errors.DuplicateObject if user already exists and
            self.connection_mode == PostgresConnectionMode.PSYCOPG
        """
        self.execute(_CREATE_USER_COMMAND.format(dbuser, dbpass, privileges))
        # Ensure the database superuser (current_user) has the right to make `dbuser` the owner of new databases.
        # Required for some postgresql installations.
        self.execute(_GRANT_ROLE_COMMAND.format(dbuser))

    def drop_dbuser(self, dbuser):
        """Drop a database user in postgres

        :param str dbuser: Name of the user to be dropped.
        """
        self.execute(_DROP_USER_COMMAND.format(dbuser))

    def find_new_dbuser(self, start_from='aiida'):
        """Find database user that does not yet exist.

        Generates names of the form "aiida_1", "aiida_2", etc. until it finds a name that does not yet exist.

        :param str start_from: start from this name
        :returns: dbuser
        """
        dbuser = start_from
        i = 0
        while self.dbuser_exists(dbuser):
            i = i + 1
            dbuser = f'{start_from}_{i}'

        return dbuser

    def can_user_authenticate(self, dbuser, dbpass):
        """Check whether the database user credentials are valid.

        Checks whether dbuser has access to the `template1` postgres database via psycopg.

        :param dbuser: the database user
        :param dbpass: the database password
        :return: True if the credentials are valid, False otherwise
        """
        import psycopg
        from pgsu import _execute_psyco

        dsn = self.dsn.copy()
        dsn['user'] = dbuser
        dsn['password'] = dbpass

        try:
            _execute_psyco('SELECT 1', dsn)
        except psycopg.OperationalError:
            return False

        return True

    ### DB functions ###

    def db_exists(self, dbname):
        """Check wether a postgres database with dbname exists

        :param str dbname: Name of the database to check for
        :return: (bool), True if database exists, False otherwise
        """
        return bool(self.execute(_CHECK_DB_EXISTS_COMMAND.format(dbname)))

    def create_db(self, dbuser, dbname):
        """Create a database in postgres

        :param str dbuser: Name of the user which should own the db.
        :param str dbname: Name of the database.
        """
        self.execute(_CREATE_DB_COMMAND.format(dbname, dbuser))

    def drop_db(self, dbname):
        """Drop a database in postgres

        :param str dbname: Name of the database.
        """
        self.execute(_DROP_DB_COMMAND.format(dbname))

    def copy_db(self, src_db, dest_db, dbuser):
        self.execute(_COPY_DB_COMMAND.format(dest_db, src_db, dbuser))

    def find_new_db(self, start_from='aiida'):
        """Find database name that does not yet exist.

        Generates names of the form "aiida_1", "aiida_2", etc. until it finds a name that does not yet exist.

        :param str start_from: start from this name
        :returns: dbname
        """
        dbname = start_from
        i = 0
        while self.db_exists(dbname):
            i = i + 1
            dbname = f'{start_from}_{i}'

        return dbname

    def create_dbuser_db_safe(self, dbname, dbuser, dbpass):
        """Create DB and user + grant privileges.

        An existing database user is reused, if it is able to authenticate.
        If not, a new username is generated on the fly.

        An existing database is not reused (unsafe), a new database name is generated on the fly.

        :param str dbname: Name of the database.
        :param str dbuser: Name of the user which should own the db.
        :param str dbpass: Password the user should be given.
        :returns: (dbuser, dbname)
        """
        from aiida.cmdline.utils import echo

        if not self.dbuser_exists(dbuser):
            self.create_dbuser(dbuser=dbuser, dbpass=dbpass)
        elif not self.can_user_authenticate(dbuser, dbpass):
            echo.echo_warning(f'Database user "{dbuser}" already exists but is unable to authenticate.')
            dbuser = self.find_new_dbuser(dbuser)
            self.create_dbuser(dbuser=dbuser, dbpass=dbpass)
        echo.echo_info(f'Using database user "{dbuser}".')

        if self.db_exists(dbname):
            echo.echo_warning(f'Database "{dbname}" already exists.')
            dbname = self.find_new_db(dbname)
        self.create_db(dbuser=dbuser, dbname=dbname)
        echo.echo_info(f'Using database "{dbname}".')

        return dbuser, dbname

    @property
    def host_for_psycopg(self):
        """Return correct host for psycopg connection (as required by regular AiiDA operation)."""
        host = self.dsn.get('host')
        if self.connection_mode == PostgresConnectionMode.PSQL:
            # If "sudo su postgres" was needed to create the DB, we are likely on Ubuntu, where
            # the same will *not* work for arbitrary database users => enforce TCP/IP connection
            host = host or 'localhost'

        return host

    @property
    def port_for_psycopg(self):
        """Return port for psycopg connection (as required by regular AiiDA operation)."""
        return self.dsn.get('port')

    @property
    def dbinfo(self):
        """Alias for Postgres.dsn."""
        return self.dsn.copy()


def manual_setup_instructions(db_username, db_name):
    """Create a message with instructions for manually creating a database"""
    db_pass = '<password>'
    instructions = '\n'.join(
        [
            'Run the following commands as a UNIX user with access to PostgreSQL (Ubuntu: $ sudo su postgres):',
            '',
            '\t$ psql template1',
            f'	==> {_CREATE_USER_COMMAND.format(db_username, db_pass, "")}',
            f'	==> {_GRANT_ROLE_COMMAND.format(db_username)}',
            f'	==> {_CREATE_DB_COMMAND.format(db_name, db_username)}',
        ]
    )
    return instructions
