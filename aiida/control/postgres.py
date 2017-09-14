"""Provides an API for postgres database maintenance tasks"""
try:
    import subprocess32 as subprocess
except ImportError:
    import subprocess

import click

_CREATE_USER_COMMAND = 'CREATE USER "{}" WITH PASSWORD \'{}\''
_DROP_USER_COMMAND = 'DROP USER "{}"'
_CREATE_DB_COMMAND = 'CREATE DATABASE "{}" OWNER "{}"'
_DROP_DB_COMMAND = 'DROP DATABASE "{}"'
_GRANT_PRIV_COMMAND = 'GRANT ALL PRIVILEGES ON DATABASE "{}" TO "{}"'
_GET_USERS_COMMAND = "SELECT usename FROM pg_user WHERE usename='{}'"
_CHECK_DB_EXISTS_COMMAND = "SELECT datname FROM pg_database WHERE datname='{}'"


class Postgres(object):
    """
    Provides postgres database manipulation assuming no prior setup

    * Can be used to create the initial aiida db user and database.
    * Works in every reasonable environment, provided the user can sudo

    Tries to use psychopg2 with a fallback to psql subcommands.
    """

    def __init__(self, port=None, interactive=False, quiet=True):
        self.interactive = interactive
        self.quiet = quiet
        self.pg_execute = None
        self.dbinfo = {}
        if port:
            self.set_port(port)
        self.setup_fail_callback = None
        self.setup_fail_counter = 0
        self.setup_max_tries = 1

    def set_setup_fail_callback(self, callback):
        self.setup_fail_callback = callback

    def set_port(self, port):
        """Set the port manually"""
        self.dbinfo['port'] = port

    def determine_setup(self):
        """
        find out how postgres can be accessed.

        Depending on how postgres is set up, psycopg2 can be used to create dbs and db users,
        otherwise a subprocess has to be used that executes psql as an os user with the right permissions.

        :return: (method, info) where method is a method that executes psql commandlines and
            info is a dict with keyword arguments to be used with method.
        """
        # find out if we run as a postgres superuser or can connect as postgres
        # This will work on OSX in some setups but not in the default Debian one
        dbinfo = {'user': None, 'database': 'template1'}
        dbinfo.update(self.dbinfo)
        for pg_user in [None, 'postgres']:
            local_dbinfo = dbinfo.copy()
            local_dbinfo['user'] = pg_user
            if _try_connect(**local_dbinfo):
                self.pg_execute = _pg_execute_psyco
                self.dbinfo = local_dbinfo
                break

        # This will work for the default Debian postgres setup
        if not self.pg_execute:
            dbinfo['user'] = 'postgres'
            if _try_subcmd(
                    non_interactive=bool(not self.interactive), **dbinfo):
                self.pg_execute = _pg_execute_sh
                self.dbinfo = dbinfo

        # This is to allow for any other setup
        if not self.pg_execute:
            self.setup_fail_counter += 1
            self._no_setup_detected()
        elif not self.interactive and not self.quiet:
            click.echo((
                'Database setup not confirmed, (non-interactive). '
                'This may cause problems if the current user is not allowed to create databases.'
            ))

    def create_dbuser(self, dbuser, dbpass):
        """
        create a database user in postgres

        :param dbuser: Name of the user to be created.
        :param dbpass: Password the user should be given.
        """
        self.pg_execute(
            _CREATE_USER_COMMAND.format(dbuser, dbpass), **self.dbinfo)

    def drop_dbuser(self, dbuser):
        """
        drop a database user in postgres

        :param dbuser: Name of the user to be dropped.
        :param method: callable with signature method(psql_command, **connection_info)
            where connection_info contains keys for psycopg2.connect.
        :param kwargs: connection info as for psycopg2.connect.
        """
        self.pg_execute(_DROP_USER_COMMAND.format(dbuser), **self.dbinfo)

    def dbuser_exists(self, dbuser):
        """return True if postgres user with name dbuser exists, False otherwise."""
        return bool(
            self.pg_execute(_GET_USERS_COMMAND.format(dbuser), **self.dbinfo))

    def create_db(self, dbuser, dbname):
        """create a database in postgres

        :param dbuser: Name of the user which should own the db.
        :param dbname: Name of the database.
        :param method: callable with signature method(psql_command, **connection_info)
            where connection_info contains keys for psycopg2.connect.
        :param kwargs: connection info as for psycopg2.connect.
        """
        self.pg_execute(
            _CREATE_DB_COMMAND.format(dbname, dbuser), **self.dbinfo)
        self.pg_execute(
            _GRANT_PRIV_COMMAND.format(dbname, dbuser), **self.dbinfo)

    def drop_db(self, dbname):
        """drop a database in postgres

        :param dbname: Name of the database.
        :param method: callable with signature method(psql_command, **connection_info)
            where connection_info contains keys for psycopg2.connect.
        :param kwargs: connection info as for psycopg2.connect.
        """
        self.pg_execute(_DROP_DB_COMMAND.format(dbname), **self.dbinfo)

    def db_exists(self, dbname):
        """return True if database with dbname exists."""
        return bool(
            self.pg_execute(
                _CHECK_DB_EXISTS_COMMAND.format(dbname), **self.dbinfo))

    def _no_setup_detected(self):
        """Print a warning message and calls the failed setup callback"""
        message = '\n'.join([
            'Detected no known postgres setup, some information is needed to create the aiida database and grant aiida access to it.',
            'If you feel unsure about the following parameters, first check if postgresql is installed.',
            'If postgresql is not installed please exit and install it, then run verdi quicksetup again.',
            'If postgresql is installed, please ask your system manager to provide you with the following parameters:'
        ])
        if not self.quiet:
            click.echo(message)
        if self.setup_fail_callback and self.setup_fail_counter <= self.setup_max_tries:
            self.dbinfo = self.setup_fail_callback(self.interactive,
                                                   self.dbinfo)
            self.determine_setup()


def manual_setup_instructions(dbuser, dbname):
    """Create a message with instructions for manual setup"""
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


def prompt_db_info():
    """
    Prompt interactively for postgres database connecting details.

    :return: dictionary with the following keys: host, port, database, user
    """
    access = False
    while not access:
        dbinfo = {}
        dbinfo['host'] = click.prompt(
            'postgres host', default='localhost', type=str)
        dbinfo['port'] = click.prompt('postgres port', default=5432, type=int)
        dbinfo['database'] = click.prompt(
            'template', default='template1', type=str)
        dbinfo['user'] = click.prompt(
            'postgres super user', default='postgres', type=str)
        click.echo('')
        click.echo('trying to access postgres..')
        if _try_connect(**dbinfo):
            access = True
        else:
            dbinfo['password'] = click.prompt(
                'postgres password of {}'.format(dbinfo['user']),
                hide_input=True,
                type=str)
            if _try_connect(**dbinfo):
                access = True
            else:
                click.echo(
                    'you may get prompted for a super user password and again for your postgres super user password'
                )
                if _try_subcmd(**dbinfo):
                    access = True
                else:
                    click.echo(
                        'Unable to connect to postgres, please try again')
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
        kwargs['stderr'] = subprocess.STDOUT
        _pg_execute_sh(r'\q', **kwargs)
        success = True
    except subprocess.CalledProcessError:
        pass
    return success


def _pg_execute_psyco(command, **kwargs):
    '''
    executes a postgres commandline through psycopg2

    :param command: A psql command line as a str
    :param kwargs: will be forwarded to psycopg2.connect
    '''
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

    To stop `sudo` from asking for a password and fail if one is required,
    pass `noninteractive=True` as a kwarg.
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

    ## build command line
    sudo_cmd = ['sudo']
    non_interactive = kwargs.pop('non_interactive', None)
    if non_interactive:
        sudo_cmd += ['-n']
    su_cmd = ['su', user, '-c']
    from aiida.common.utils import escape_for_bash
    psql_cmd = [
        'psql {options} -tc {}'.format(
            escape_for_bash(command), options=options)
    ]
    sudo_su_psql = sudo_cmd + su_cmd + psql_cmd
    result = subprocess.check_output(sudo_su_psql, **kwargs)

    if isinstance(result, str):
        result = result.strip().split('\n')
        result = [i for i in result if i]
    return result
