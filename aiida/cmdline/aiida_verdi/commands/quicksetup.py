#-*- coding: utf8 -*-
"""
verdi quicksetup command
"""
import click

from aiida.backends.profile import BACKEND_SQLA
from aiida.cmdline.aiida_verdi import options as cliopt

_create_user_command = 'CREATE USER "{}" WITH PASSWORD \'{}\''
_create_db_command = 'CREATE DATABASE "{}" OWNER "{}"'
_grant_priv_command = 'GRANT ALL PRIVILEGES ON DATABASE "{}" TO "{}"'
_get_users_command = "SELECT usename FROM pg_user WHERE usename='{}'"


def _get_pg_access():
    '''
    find out how postgres can be accessed.

    Depending on how postgres is set up, psycopg2 can be used to create dbs and db users, otherwise a subprocess has to be used that executes psql as an os user with the right permissions.
    :return: (method, info) where method is a method that executes psql commandlines and info is a dict with keyword arguments to be used with method.
    '''
    # find out if we run as a postgres superuser or can connect as postgres
    # This will work on OSX in some setups but not in the default Debian one
    can_connect = False
    can_subcmd = None
    dbinfo = {'user': None, 'database': 'template1'}
    for pg_user in [None, 'postgres']:
        if _try_connect(**dbinfo):
            can_connect = True
            dbinfo['user'] = pg_user
            break

    # This will work for the default Debian postgres setup
    if not can_connect:
        if _try_subcmd(user='postgres'):
            can_subcmd = True
            dbinfo['user'] = 'postgres'
        else:
            can_subcmd = False

    # This is to allow for any other setup
    if not can_connect and not can_subcmd:
        click.echo('Detected no known postgres setup, some information is needed to create the aiida database and grant aiida access to it.')
        click.echo('If you feel unsure about the following parameters, first check if postgresql is installed.')
        click.echo('If postgresql is not installed please exit and install it, then run verdi quicksetup again.')
        click.echo('If postgresql is installed, please ask your system manager to provide you with the following parameters:')
        dbinfo = _prompt_db_info()

    pg_method = None
    if can_connect:
        pg_method = _pg_execute_psyco
    elif can_subcmd:
        pg_method = _pg_execute_sh

    result = {
        'method': pg_method,
        'dbinfo': dbinfo,
    }
    return result


def _prompt_db_info():
    '''prompt interactively for postgres database connecting details.'''
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
    '''
    try to start a psycopg2 connection.

    :return: True if successful, False otherwise
    '''
    from psycopg2 import connect
    success = False
    try:
        connect(**kwargs)
        success = True
    except Exception:
        pass
    return success


def _try_subcmd(**kwargs):
    '''
    try to run psql in a subprocess.

    :return: True if successful, False otherwise
    '''
    success = False
    try:
        _pg_execute_sh(r'\q', **kwargs)
        success = True
    except Exception:
        pass
    return success


def _create_dbuser(dbuser, dbpass, method=None, **kwargs):
    '''
    create a database user in postgres

    :param dbuser: Name of the user to be created.
    :param dbpass: Password the user should be given.
    :param method: callable with signature method(psql_command, **connection_info)
        where connection_info contains keys for psycopg2.connect.
    :param kwargs: connection info as for psycopg2.connect.
    '''
    method(_create_user_command.format(dbuser, dbpass), **kwargs)


def _create_db(dbuser, dbname, method=None, **kwargs):
    '''create a database in postgres

    :param dbuser: Name of the user which should own the db.
    :param dbname: Name of the database.
    :param method: callable with signature method(psql_command, **connection_info)
        where connection_info contains keys for psycopg2.connect.
    :param kwargs: connection info as for psycopg2.connect.
    '''
    method(_create_db_command.format(dbname, dbuser), **kwargs)
    method(_grant_priv_command.format(dbname, dbuser), **kwargs)


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
    '''
    executes a postgres command line as another system user in a subprocess.

    :param command: A psql command line as a str
    :param user: Name of a system user with postgres permissions
    :param kwargs: connection details to forward to psql, signature as in psycopg2.connect
    '''
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


def _dbuser_exists(dbuser, method, **kwargs):
    '''return True if postgres user with name dbuser exists, False otherwise.'''
    return bool(method(_get_users_command.format(dbuser), **kwargs))


def _check_db_name(dbname, method=None, **kwargs):
    '''looks up if a database with the name exists, prompts for using or creating a differently named one'''
    create = True
    while create and method("SELECT datname FROM pg_database WHERE datname='{}'".format(dbname), **kwargs):
        click.echo('database {} already exists!'.format(dbname))
        if not click.confirm('Use it (make sure it is not used by another profile)?'):
            dbname = click.prompt('new name', type=str, default=dbname)
        else:
            create = False
    return dbname, create


@click.command(short_help='Quick setup for new users')
@cliopt.email(prompt='Email Address (for publishing experiments)', help='This email address will be associated with your data and will be exported along with it, should you choose to share any of your work')
@cliopt.first_name(prompt='First Name')
@cliopt.last_name(prompt='Last Name')
@cliopt.institution(prompt='Institution')
@cliopt.backend(default=BACKEND_SQLA)
@cliopt.db_user()
@cliopt.db_host()
@cliopt.db_pass()
@cliopt.db_name()
@cliopt.db_port()
@click.option('--profile', type=str, metavar='PROFILE_NAME', help='defaults to quicksetup')
@cliopt.repo()
@click.option('--make-deamonuser', is_flag=True, help='make the created profile the one that can run the daemon')
@click.option('--make-default', is_flag=True, help='make the created profile the default verdi profile')
@cliopt.non_interactive()
@click.pass_obj
def quicksetup(email, first_name, last_name, institution, backend, db_user, db_user_pw, db_name, db_host, db_port, profile, repo):
    '''
    Quick setup for the most common usecase (1 user, 1 machine).

    Uses click for options. Creates a database user 'aiida_qs_<username>' with random password if it doesn't exist.
    Creates a 'aiidadb_qs_<username>' database (prompts to use or change the name if already exists).
    Makes sure not to overwrite existing databases or profiles without prompting for confirmation.),
    '''
    import os
    from aiida.cmdline.commands2.setup import setup
    from aiida.common.setup import create_base_dirs, AIIDA_CONFIG_FOLDER
    create_base_dirs()

    aiida_dir = os.path.expanduser(AIIDA_CONFIG_FOLDER)

    # access postgres
    pg_info = _get_pg_access()
    pg_execute = pg_info['method']
    dbinfo = pg_info['dbinfo']

    # check if a database setup already exists
    # otherwise setup the database user aiida
    # setup the database aiida_qs_<username>
    from getpass import getuser
    from aiida.common.setup import generate_random_secret_key
    osuser = getuser()
    dbuser = db_user or 'aiida_qs_' + osuser
    dbpass = db_user_pw or generate_random_secret_key()
    dbname = db_name or 'aiidadb_qs_' + osuser

    # check if there is a profile that contains the db user already
    # and if yes, take the db user password from there
    # This is ok because a user can only see his own config files
    from aiida.common.setup import (set_default_profile, get_or_create_config)
    confs = get_or_create_config()
    profs = confs.get('profiles', {})
    for v in profs.itervalues():
        if v.get('AIIDADB_USER', '') == dbuser and not db_user_pw:
            dbpass = v.get('AIIDADB_PASS')
            print 'using found password for {}'.format(dbuser)
            break

    try:
        create = True
        if not _dbuser_exists(dbuser, pg_execute, **dbinfo):
            _create_dbuser(dbuser, dbpass, pg_execute, **dbinfo)
        else:
            dbname, create = _check_db_name(dbname, pg_execute, **dbinfo)
        if create:
            _create_db(dbuser, dbname, pg_execute, **dbinfo)
    except Exception as e:
        click.echo('\n'.join([
            'Oops! Something went wrong while creating the database for you.',
            'You may continue with the quicksetup, however:',
            'For aiida to work correctly you will have to do that yourself as follows.',
            'Please run the following commands as the user for PostgreSQL (Ubuntu: $sudo su postgres):',
            '',
            '\t$ psql template1',
            '\t==> ' + _create_user_command.format(dbuser, dbpass),
            '\t==> ' + _create_db_command.format(dbname, dbuser),
            '\t==> ' + _grant_priv_command.format(dbname, dbuser),
            '',
            'Or setup your (OS-level) user to have permissions to create databases and rerun quicksetup.',
            '']))
        raise e

    # create a profile, by default 'quicksetup' and prompt the user if
    # already exists
    profile_name = profile or 'quicksetup'
    write_profile = False
    confs = get_or_create_config()
    profile_name = profile or 'quicksetup'
    write_profile = False
    while not write_profile:
        if profile_name in confs.get('profiles', {}):
            if click.confirm('overwrite existing profile {}?'.format(profile_name)):
                write_profile = True
            else:
                profile_name = click.prompt('new profile name', type=str)
        else:
            write_profile = True

    dbhost = db_host or dbinfo.get('host', 'localhost')
    dbport = db_port or dbinfo.get('port', '5432')

    from os.path import isabs
    repo = repo or 'repository-{}/'.format(profile_name)
    if not isabs(repo):
        repo = os.path.join(aiida_dir, repo)

    setup_args = {
        'backend': backend,
        'email': email,
        'db_host': dbhost,
        'db_port': dbport,
        'db_name': dbname,
        'db_user': dbuser,
        'db_pass': dbpass,
        'repo': repo,
        'first_name': first_name,
        'last_name': last_name,
        'institution': institution,
        'force_overwrite': write_profile,
    }
    setup.invoke(profile_name, only_config=False, non_interactive=True, **setup_args)

    # set as new default profile
    # prompt if there is another non-quicksetup profile
    use_new = False
    defprof = confs.get('default_profiles', {})
    if defprof.get('daemon', '').startswith('quicksetup'):
        use_new = False
        if kwargs['make_deamonuser']:
            use_new = True
        elif not kwargs['non_interactive']:
            use_new = click.confirm('The daemon default profile is set to {}, do you want to set the newly created one ({}) as default? (can be changed back later)'.format(defprof['daemon'], profile_name))
        if use_new:
            set_default_profile('daemon', profile_name, force_rewrite=True)
    if defprof.get('verdi'):
        use_new = False
        if kwargs['make_default']:
            use_new = True
        elif not kwargs['non_interactive']:
            use_new = click.confirm('The verdi default profile is set to {}, do you want to set the newly created one ({}) as new default? (can be changed back later)'.format(defprof['verdi'], profile_name))
        if use_new:
            set_default_profile('verdi', profile_name, force_rewrite=True)

