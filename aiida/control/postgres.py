"""Provides an API for postgres database maintenance tasks"""
import click


_create_user_command = 'CREATE USER "{}" WITH PASSWORD \'{}\''
_drop_user_command = 'DROP USER "{}"'
_create_db_command = 'CREATE DATABASE "{}" OWNER "{}"'
_drop_db_command = 'DROP DATABASE "{}"'
_grant_priv_command = 'GRANT ALL PRIVILEGES ON DATABASE "{}" TO "{}"'
_get_users_command = "SELECT usename FROM pg_user WHERE usename='{}'"
_check_db_exists_command = "SELECT datname FROM pg_database WHERE datname='{}'"


class Postgres(object):
    """
    Object that provides postgres database manipulation assuming no prior setup

    * Can be used to create the initial aiida db user and database.
    * Works in every reasonable environment, provided the user can sudo

    Tries to use psychopg2 with a fallback to psql subcommands.
    """

    def __init__(self, interactive=False, quiet=True):
        self.interactive = interactive
        self.quiet = quiet
        self.pg_execute = None
        self.dbinfo = {}
        self.setup_fail_callback = setup_fail_callback

    def set_setup_fail_callback(self, callback):
        self.setup_fail_callback = callback

    def determine_setup(self):
        """
        find out how postgres can be accessed.

        Depending on how postgres is set up, psycopg2 can be used to create dbs and db users, otherwise a subprocess has to be used that executes psql as an os user with the right permissions.
        :return: (method, info) where method is a method that executes psql commandlines and info is a dict with keyword arguments to be used with method.
        """
        # find out if we run as a postgres superuser or can connect as postgres
        # This will work on OSX in some setups but not in the default Debian one
        can_connect = False
        can_subcmd = None
        dbinfo = {'user': None, 'database': 'template1'}
        for pg_user in [None, 'postgres']:
            if _try_connect(**dbinfo):
                self.pg_execute = _pg_execute_psyco
                self.dbinfo['user'] = pg_user
                break

        # This will work for the default Debian postgres setup
        if not self.cmd_type:
            if not self.interactive:
                self.pg_execute = _pg_execute_sh
                self.dbinfo['user'] = 'postgres'
            elif _try_subcmd(user='postgres'):
                self.pg_execute = _pg_execute_sh
                self.dbinfo['user'] = 'postgres'

        # This is to allow for any other setup
        if not self.cmd_type:
            self._no_setup_detected()
        elif not self.interactive and not self.quiet:
            click.echo('Database setup not confirmed, (non-interactive). This may cause problems if the current user is not allowed to create databases.')

    def create_dbuser(self, dbuser, dbpass):
        """
        create a database user in postgres

        :param dbuser: Name of the user to be created.
        :param dbpass: Password the user should be given.
        """
        self.pg_execute(_create_user_command.format(dbuser, dbpass), **self.dbinfo)

    def drop_dbuser(self, dbuser):
        """
        drop a database user in postgres

        :param dbuser: Name of the user to be dropped.
        :param method: callable with signature method(psql_command, **connection_info)
            where connection_info contains keys for psycopg2.connect.
        :param kwargs: connection info as for psycopg2.connect.
        """
        self.pg_execute(self._drop_user_command.format(dbuser), **self.dbinfo)

    def dbuser_exists(self, dbuser):
        """return True if postgres user with name dbuser exists, False otherwise."""
        return bool(self.pg_execute(_get_users_command.format(dbuser), **self.dbinfo))

    def create_db(self, dbuser, dbname):
        """create a database in postgres

        :param dbuser: Name of the user which should own the db.
        :param dbname: Name of the database.
        :param method: callable with signature method(psql_command, **connection_info)
            where connection_info contains keys for psycopg2.connect.
        :param kwargs: connection info as for psycopg2.connect.
        """
        self.pg_execute(_create_db_command.format(dbname, dbuser), **self.dbinfo)
        self.pg_execute(_grant_priv_command.format(dbname, dbuser), **self.dbinfo)

    def _drop_db(self, dbname):
        """drop a database in postgres

        :param dbname: Name of the database.
        :param method: callable with signature method(psql_command, **connection_info)
            where connection_info contains keys for psycopg2.connect.
        :param kwargs: connection info as for psycopg2.connect.
        """
        self.pg_execute(self._drop_db_command.format(dbname), **self.dbinfo)

    def db_exists(self, dbname):
        """return True if database with dbname exists."""
        return bool(self.pg_execute(_check_db_exists_command.format(dbname), **self.dbinfo))

    def manual_instructions(self, dbuser, dbname):
        dbpass = '<password>'
        instructions = '\n'.join([
            'Please run the following commands as the user for PostgreSQL (Ubuntu: $sudo su postgres):',
            '',
            '\t$ psql template1',
            '\t==> ' + _create_user_command.format(dbuser, dbpass),
            '\t==> ' + _create_db_command.format(dbname, dbuser),
            '\t==> ' + _grant_priv_command.format(dbname, dbuser),
        ])
        return instructions

    def _no_setup_detected(self):
        click.echo('Detected no known postgres setup, some information is needed to create the aiida database and grant aiida access to it.')
        click.echo('If you feel unsure about the following parameters, first check if postgresql is installed.')
        click.echo('If postgresql is not installed please exit and install it, then run verdi quicksetup again.')
        click.echo('If postgresql is installed, please ask your system manager to provide you with the following parameters:')
        self.dbinfo = self.setup_fail_callback(self.interactive, self.dbinfo)


def _prompt_db_info():
    """
    Prompt interactively for postgres database connecting details.

    :return: dictionary with the following keys: host, port, database, user
    """
    access = False
    while not access:
        dbinfo = {}
        dbinfo['host'] = click.prompt('postgres host', default='localhost', type=str)
        dbinfo['port'] = click.prompt('postgres port', default=5432, type=int)
        dbinfo['database'] = click.prompt('template', default='template1', type=str)
        dbinfo['user'] = click.prompt('postgres super user', default='postgres', type=str)
        click.echo('')
        click.echo('trying to access postgres..')
        if _try_connect(**dbinfo):
            access = True
        else:
            dbinfo['password'] = click.prompt('postgres password of {}'.format(dbinfo['user']), hide_input=True, type=str)
            if _try_connect(**dbinfo):
                access = True
            else:
                click.echo('you may get prompted for a super user password and again for your postgres super user password')
                if _try_subcmd(**dbinfo):
                    access = True
                else:
                    click.echo('Unable to connect to postgres, please try again')
    return dbinfo


def _try_connect(**kwargs):
    """
    try to start a psycopg2 connection.

    :return: True if successful, False otherwise
    """
    from psycopg2 import connect
    success = False
    try:
        connect(**kwargs)
        success = True
    except Exception:  # pylint: disable=broad-except
        pass
    return success


def _try_subcmd(**kwargs):
    """
    try to run psql in a subprocess.

    :return: True if successful, False otherwise
    """
    success = False
    try:
        _pg_execute_sh(r'\q', **kwargs)
        success = True
    except Exception:
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
    return output


def _pg_execute_sh(command, user='postgres', **kwargs):
    """
    executes a postgres command line as another system user in a subprocess.

    :param command: A psql command line as a str
    :param user: Name of a system user with postgres permissions
    :param kwargs: connection details to forward to psql, signature as in psycopg2.connect
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
    try:
        import subprocess32 as sp
    except ImportError:
        import subprocess as sp
    from aiida.common.utils import escape_for_bash
    result = sp.check_output(['sudo', 'su', user, '-c', 'psql {options} -tc {}'.format(escape_for_bash(command), options=options)], **kwargs)
    if isinstance(result, str):
        result = result.strip().split('\n')
        result = [i for i in result if i]
    return result
