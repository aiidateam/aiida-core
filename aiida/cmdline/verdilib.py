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
Command line commands for the main executable 'verdi' of aiida

If you want to define a new command line parameter, just define a new
class inheriting from VerdiCommand, and define a run(self,*args) method
accepting a variable-length number of parameters args
(the command-line parameters), which will be invoked when
this executable is called as
verdi NAME

Don't forget to add the docstring to the class: the first line will be the
short description, the following ones the long description.
"""
import sys
import os
import contextlib
import click

import aiida
from aiida.common.exceptions import (
    AiidaException, ConfigurationError, ProfileConfigurationError)
from aiida.cmdline.baseclass import VerdiCommand, VerdiCommandRouter
from aiida.cmdline import pass_to_django_manage
from aiida.backends import settings as settings_profile

# Import here from other files; once imported, it will be found and
# used as a command-line parameter
from aiida.cmdline.commands.user import User
import aiida.cmdline.commands.user as user
from aiida.cmdline.commands.calculation import Calculation
from aiida.cmdline.commands.code import Code
from aiida.cmdline.commands.computer import Computer
from aiida.cmdline.commands.daemon import Daemon
from aiida.cmdline.commands.data import Data
from aiida.cmdline.commands.devel import Devel
from aiida.cmdline.commands.exportfile import Export
from aiida.cmdline.commands.group import Group
from aiida.cmdline.commands.graph import Graph
from aiida.cmdline.commands.importfile import Import
from aiida.cmdline.commands.node import Node
from aiida.cmdline.commands.profile import Profile
from aiida.cmdline.commands.workflow import Workflow
from aiida.cmdline.commands.work import Work
from aiida.cmdline.commands.comment import Comment
from aiida.cmdline.commands.shell import Shell
from aiida.cmdline.commands.restapi import Restapi
from aiida.cmdline import execname


class ProfileParsingException(AiidaException):
    """
    Exception raised when parsing the profile command line option, if only
    -p is provided, and no profile is specified
    """

    def __init__(self, *args, **kwargs):
        self.minus_p_provided = kwargs.pop('minus_p_provided', False)

        super(ProfileParsingException, self).__init__(*args, **kwargs)


def parse_profile(argv, merge_equal=False):
    """
    Parse the argv to see if a profile has been specified, return it with the
    command position shift (index where the commands start)

    :param merge_equal: if True, merge things like
      ('verdi', '--profile', '=', 'x', 'y') to ('verdi', '--profile=x', 'y')
      but then return the correct index for the original array.

    :raise ProfileParsingException: if there is only 'verdi' specified, or
      if only 'verdi -p' (in these cases, one has respectively
      exception.minus_p_provided equal to False or True)
    """
    if merge_equal:
        if len(argv) >= 3:
            if argv[1] == '--profile' and argv[2] == '=':
                internal_argv = [argv[0], "".join(argv[1:4])] + list(argv[4:])
                shift = 2
            else:
                internal_argv = list(argv)
                shift = 0
        else:
            internal_argv = list(argv)
            shift = 0
    else:
        internal_argv = list(argv)
        shift = 0

    profile = None  # Use default profile if nothing is specified
    command_position = 1  # If there is no profile option
    try:
        profile_switch = internal_argv[1]
    except IndexError:
        raise ProfileParsingException(minus_p_provided=False)
    long_profile_prefix = '--profile='
    if profile_switch == '-p':
        try:
            profile = internal_argv[2]
        except IndexError:
            raise ProfileParsingException(minus_p_provided=True)
        command_position = 3
    elif profile_switch.startswith(long_profile_prefix):
        profile = profile_switch[len(long_profile_prefix):]
        command_position = 2
    else:
        # No profile switch, continue using argv[1] as the command name
        pass

    return profile, command_position + shift


@contextlib.contextmanager
def update_environment(new_argv):
    """
    Used as a context manager, changes sys.argv with the
    new_argv argument, and restores it upon exit.
    """
    import sys

    _argv = sys.argv[:]
    sys.argv = new_argv[:]
    yield

    # Restore old parameters when exiting from the context manager
    sys.argv = _argv


########################################################################
# HERE STARTS THE COMMAND FUNCTION LIST
########################################################################

class CompletionCommand(VerdiCommand):
    """
    Return the bash completion function to put in ~/.bashrc

    This command prints on screen the function to be inserted in
    your .bashrc command. You can copy and paste the output, or simply
    add
    eval "`verdi completioncommand`"
    to your .bashrc, *AFTER* having added the aiida/bin directory to the path.
    """

    def run(self, *args):
        """
        I put the documentation here, and I don't print it, so we
        don't clutter too much the .bashrc.

        * "${THE_WORDS[@]}" (with the @) puts each element as a different
          parameter; note that the variable expansion etc. is performed

        * I add a 'x' at the end and then remove it; in this way, $( ) will
          not remove trailing spaces

        * If the completion command did not print anything, we use
          the default bash completion for filenames

        * If instead the code prints something empty, thanks to the workaround
          above $OUTPUT is not empty, so we do go the the 'else' case
          and then, no substitution is suggested.
        """

        print r"""
function _aiida_verdi_completion
{
    OUTPUT=$( $1 completion "$COMP_CWORD" "${COMP_WORDS[@]}" ; echo 'x')
    OUTPUT=${OUTPUT%x}
    if [ -z "$OUTPUT" ]
    then
    # Only newline is a valid separator
        local IFS=$'\n'

        COMPREPLY=( $(compgen -o default -- "${COMP_WORDS[COMP_CWORD]}" ) )
    # Add either a slash or a space, depending on whether it is a folder
    # or a file. printf %q escapes the filename if there are spaces.
        for ((i=0; i < ${#COMPREPLY[@]}; i++)); do
            [ -d "${COMPREPLY[$i]}" ] && \
               COMPREPLY[$i]=$(printf %q%s "${COMPREPLY[$i]}" "/") || \
               COMPREPLY[$i]=$(printf %q%s "${COMPREPLY[$i]}" " ")
        done

    else
        COMPREPLY=( $(compgen -W "$OUTPUT" -- "${COMP_WORDS[COMP_CWORD]}" ) )
        # Always add a space after each command
        for ((i=0; i < ${#COMPREPLY[@]}; i++)); do
            COMPREPLY[$i]="${COMPREPLY[$i]} "
        done
    fi
}
complete -o nospace -F _aiida_verdi_completion verdi
"""

    def complete(self, subargs_idx, subargs):
        # disable further completion
        print ""


class Completion(VerdiCommand):
    """
    Manage bash completion

    Return a list of available commands, separated by spaces.
    Calls the correct function of the command if the TAB has been
    pressed after the first command.

    Returning without printing will use the default bash completion.
    """

    # TODO: manage completion at a deeper level

    def run(self, *args):
        try:
            cword = int(args[0])
            if cword <= 0:
                cword = 1
        except IndexError:
            cword = 1
        except ValueError:
            return

        try:
            profile, command_position = parse_profile(args[1:],
                                                      merge_equal=True)
        except ProfileParsingException as e:
            cword_offset = 0
        else:
            cword_offset = command_position - 1

        if cword == 1 + cword_offset:
            print " ".join(sorted(short_doc.keys()))
            return
        else:
            try:
                # args[0] is cword;
                # args[1] is the executable (verdi)
                # args[2] is the command for verdi
                # args[3:] are the following subargs
                command = args[2 + cword_offset]
            except IndexError:
                return
            try:
                CommandClass = list_commands[command]
            except KeyError:
                return
            CommandClass().complete(subargs_idx=cword - 2 - cword_offset,
                                    subargs=args[3 + cword_offset:])


class ListParams(VerdiCommand):
    """
    List available commands

    List available commands and their short description.
    For the long description, use the 'help' command.
    """

    def run(self, *args):
        print get_listparams()


class Help(VerdiCommand):
    """
    Describe a specific command

    Pass a further argument to get a description of a given command.
    """

    def run(self, *args):
        try:
            command = args[0]
        except IndexError:
            print get_listparams()
            print ""
            print (
                "Before each command you can specify the AiiDA profile to use,"
                " with 'verdi -p <profile> <command>' or "
                "'verdi --profile=<profile> <command>'")
            print ""
            print ("Use '{} help <command>' for more information "
                   "on a specific command.".format(execname))
            sys.exit(1)

        if command in short_doc:
            print "Description for '%s %s'" % (execname, command)
            print ""
            print "**", short_doc[command]
            if command in long_doc:
                print long_doc[command]
        else:
            print >> sys.stderr, (
                "{}: '{}' is not a valid command. "
                "See '{} help' for more help.".format(
                    execname, command, execname))
            get_command_suggestion(command)
            sys.exit(1)

    def complete(self, subargs_idx, subargs):
        if subargs_idx == 0:
            print " ".join(sorted(short_doc.keys()))
        else:
            print ""


class Install(VerdiCommand):
    """
    Install/setup aiida for the current user

    This command creates the ~/.aiida folder in the home directory
    of the user, interactively asks for the database settings and
    the repository location, does a setup of the daemon and runs
    a migrate command to create/setup the database.
    """

    def run(self, *args):
        click.echo('\nwarning: verdi install is deprecated, use verdi setup.\n')
        ctx = _setup_cmd.make_context('setup', list(args))
        with ctx:
            _setup_cmd.invoke(ctx)

    def complete(self, subargs_idx, subargs):
        """
        No completion after 'verdi install'.
        """
        print ""


class Setup(VerdiCommand):
    """
    Setup aiida for the current user

    This command creates the ~/.aiida folder in the home directory
    of the user, interactively asks for the database settings and
    the repository location, does a setup of the daemon and runs
    a migrate command to create/setup the database.
    """

    def run(self, *args):
        ctx = _setup_cmd.make_context('setup', list(args))
        with ctx:
            _setup_cmd.invoke(ctx)

    def complete(self, subargs_idx, subargs):
        """
        No completion after 'verdi install'.
        """
        print ""


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command('setup', context_settings=CONTEXT_SETTINGS)
@click.argument('profile', default='', type=str)
@click.option('--only-config', is_flag=True)
@click.option('--non-interactive', is_flag=True, help='never prompt the user for input, read values from options')
@click.option('--backend', type=click.Choice(['django', 'sqlalchemy']),
              help='ignored unless --non-interactive is given')
@click.option('--email', type=str, help='ignored unless --non-interactive is given')
@click.option('--db_host', type=str, help='ignored unless --non-interactive is given')
@click.option('--db_port', type=int, help='ignored unless --non-interactive is given')
@click.option('--db_name', type=str, help='ignored unless --non-interactive is given')
@click.option('--db_user', type=str, help='ignored unless --non-interactive is given')
@click.option('--db_pass', type=str, help='ignored unless --non-interactive is given')
@click.option('--first-name', type=str, help='ignored unless --non-interactive is given')
@click.option('--last-name', type=str, help='ignored unless --non-interactive is given')
@click.option('--institution', type=str, help='ignored unless --non-interactive is given')
@click.option('--no-password', is_flag=True, help='ignored unless --non-interactive is given')
@click.option('--repo', type=str, help='ignored unless --non-interactive is given')
def _setup_cmd(profile, only_config, non_interactive, backend, email, db_host, db_port, db_name, db_user, db_pass,
               first_name, last_name, institution, no_password, repo):
    '''verdi setup command, forward cmdline arguments to the setup function.'''
    setup(profile=profile,
          only_config=only_config,
          non_interactive=non_interactive,
          backend=backend,
          email=email,
          db_host=db_host,
          db_port=db_port,
          db_name=db_name,
          db_user=db_user,
          db_pass=db_pass,
          first_name=first_name,
          last_name=last_name,
          institution=institution,
          repo=repo)


def setup(profile, only_config, non_interactive=False, **kwargs):
    '''
    setup an aiida profile and aiida user (and the aiida default user).

    :param profile: Profile name
    :param only_config: do not create a new user
    :param non_interactive: do not prompt for configuration values, fail if not all values are given as kwargs.
    :param backend: one of 'django', 'sqlalchemy'
    :param email: valid email address for the user
    :param db_host: hostname for the database
    :param db_port: port to connect to the database
    :param db_user: name of the db user
    :param db_pass: password of the db user
    '''
    from aiida.common.setup import (create_base_dirs, create_configuration,
                                    set_default_profile, DEFAULT_UMASK,
                                    create_config_noninteractive)
    from aiida.backends.profile import BACKEND_SQLA, BACKEND_DJANGO
    from aiida.backends.utils import set_backend_type, get_backend_type
    from aiida.common.exceptions import InvalidOperation

    # ~ cmdline_args = list(args)

    # ~ only_user_config = False
    # ~ try:
    # ~ cmdline_args.remove('--only-config')
    # ~ only_user_config = True
    # ~ except ValueError:
    # ~ # Parameter not provided
    # ~ pass
    only_user_config = only_config

    # ~ if cmdline_args:
    # ~ print >> sys.stderr, "Unknown parameters on the command line: "
    # ~ print >> sys.stderr, ", ".join(cmdline_args)
    # ~ sys.exit(1)

    # create the directories to store the configuration files
    create_base_dirs()
    # gprofile = 'default' if profile is None else profile
    # ~ gprofile = profile if settings_profile.AIIDADB_PROFILE is None \
    # ~ else settings_profile.AIIDADB_PROFILE
    if settings_profile.AIIDADB_PROFILE and profile:
        sys.exit('the profile argument cannot be used if verdi is called with -p option: {} and {}'.format(
            settings_profile.AIIDADB_PROFILE, profile))
    gprofile = settings_profile.AIIDADB_PROFILE or profile
    if gprofile == profile:
        settings_profile.AIIDADB_PROFILE = profile
    if not settings_profile.AIIDADB_PROFILE:
        settings_profile.AIIDADB_PROFILE = 'default'

    # used internally later
    gprofile = settings_profile.AIIDADB_PROFILE

    created_conf = None
    # ask and store the configuration of the DB
    if non_interactive:
        try:
            created_conf = create_config_noninteractive(
                profile=gprofile,
                backend=kwargs['backend'],
                email=kwargs['email'],
                db_host=kwargs['db_host'],
                db_port=kwargs['db_port'],
                db_name=kwargs['db_name'],
                db_user=kwargs['db_user'],
                db_pass=kwargs.get('db_pass', ''),
                repo=kwargs['repo'],
                force_overwrite=kwargs.get('force_overwrite', False)
            )
        except ValueError as e:
            click.echo("Error during configuation: {}".format(e.message), err=True)
            sys.exit(1)
        except KeyError as e:
            sys.exit("--non-interactive requires all values to be given on the commandline! {}".format(e.message),
                     err=True)
    else:
        try:
            created_conf = create_configuration(profile=gprofile)
        except ValueError as e:
            print >> sys.stderr, "Error during configuration: {}".format(
                e.message)
            sys.exit(1)

        # set default DB profiles
        set_default_profile('verdi', gprofile, force_rewrite=False)
        set_default_profile('daemon', gprofile, force_rewrite=False)

    if only_user_config:
        print ("Only user configuration requested, "
               "skipping the migrate command")
    else:
        print "Executing now a migrate command..."

        backend_choice = created_conf['AIIDADB_BACKEND']
        if backend_choice == BACKEND_DJANGO:
            print("...for Django backend")
            # The correct profile is selected within load_dbenv.
            # Setting os.umask here since sqlite database gets created in
            # this step.
            old_umask = os.umask(DEFAULT_UMASK)

            # This check should be done more properly
            # try:
            #     backend_type = get_backend_type()
            # except KeyError:
            #     backend_type = None
            #
            # if backend_type is not None and backend_type != BACKEND_DJANGO:
            #     raise InvalidOperation("An already existing database found"
            #                            "and a different than the selected"
            #                            "backend was used for its "
            #                            "management.")

            try:
                pass_to_django_manage([execname, 'migrate'],
                                      profile=gprofile)
            finally:
                os.umask(old_umask)

            set_backend_type(BACKEND_DJANGO)

        elif backend_choice == BACKEND_SQLA:
            print("...for SQLAlchemy backend")
            from aiida import is_dbenv_loaded, load_dbenv
            if not is_dbenv_loaded():
                load_dbenv()

            from aiida.backends.sqlalchemy.models.base import Base
            from aiida.backends.sqlalchemy.utils import install_tc, reset_session
            from aiida.common.setup import get_profile_config

            # This check should be done more properly
            # try:
            #     backend_type = get_backend_type()
            # except KeyError:
            #     backend_type = None
            #
            # if backend_type is not None and backend_type != BACKEND_SQLA:
            #     raise InvalidOperation("An already existing database found"
            #                            "and a different than the selected"
            #                            "backend was used for its "
            #                            "management.")

            # Those import are necessary for SQLAlchemy to correctly create
            # the needed database tables.
            from aiida.backends.sqlalchemy.models.authinfo import (
                DbAuthInfo)
            from aiida.backends.sqlalchemy.models.comment import DbComment
            from aiida.backends.sqlalchemy.models.computer import (
                DbComputer)
            from aiida.backends.sqlalchemy.models.group import (
                DbGroup, table_groups_nodes)
            from aiida.backends.sqlalchemy.models.lock import DbLock
            from aiida.backends.sqlalchemy.models.log import DbLog
            from aiida.backends.sqlalchemy.models.node import (
                DbLink, DbNode, DbPath, DbCalcState)
            from aiida.backends.sqlalchemy.models.user import DbUser
            from aiida.backends.sqlalchemy.models.workflow import (
                DbWorkflow, DbWorkflowData, DbWorkflowStep)
            from aiida.backends.sqlalchemy.models.settings import DbSetting

            reset_session(get_profile_config(gprofile))
            from aiida.backends.sqlalchemy import get_scoped_session
            connection = get_scoped_session().connection()
            Base.metadata.create_all(connection)
            install_tc(connection)

            set_backend_type(BACKEND_SQLA)

        else:
            raise InvalidOperation("Not supported backend selected.")

    print "Database was created successfully"

    # I create here the default user
    print "Loading new environment..."
    if only_user_config:
        from aiida.backends.utils import load_dbenv, is_dbenv_loaded
        # db environment has not been loaded in this case
        if not is_dbenv_loaded():
            load_dbenv()

    from aiida.common.setup import DEFAULT_AIIDA_USER
    from aiida.orm.user import User as AiiDAUser

    if not AiiDAUser.search_for_users(email=DEFAULT_AIIDA_USER):
        print "Installing default AiiDA user..."
        nuser = AiiDAUser(email=DEFAULT_AIIDA_USER)
        nuser.first_name = "AiiDA"
        nuser.last_name = "Daemon"
        nuser.is_staff = True
        nuser.is_active = True
        nuser.is_superuser = True
        nuser.force_save()

    from aiida.common.utils import get_configured_user_email
    email = get_configured_user_email()
    print "Starting user configuration for {}...".format(email)
    if email == DEFAULT_AIIDA_USER:
        print "You set up AiiDA using the default Daemon email ({}),".format(
            email)
        print "therefore no further user configuration will be asked."
    else:
        # Ask to configure the new user
        if not non_interactive:
            user.configure.main(args=[email])
        else:
            # or don't ask
            user.do_configure(kwargs['email'], kwargs.get('first_name'),
                              kwargs.get('last_name'), kwargs.get('institution'),
                              True)

    print "Setup finished."


class Quicksetup(VerdiCommand):
    '''
    Quick setup for the most common usecase (1 user, 1 machine).

    Uses click for options. Creates a database user 'aiida_qs_<username>' with random password if it doesn't exist.
    Creates a 'aiidadb_qs_<username>' database (prompts to use or change the name if already exists).
    Makes sure not to overwrite existing databases or profiles without prompting for confirmation.
    '''
    from  aiida.backends.profile import (BACKEND_DJANGO, BACKEND_SQLA)

    _create_user_command = 'CREATE USER "{}" WITH PASSWORD \'{}\''
    _create_db_command = 'CREATE DATABASE "{}" OWNER "{}"'
    _grant_priv_command = 'GRANT ALL PRIVILEGES ON DATABASE "{}" TO "{}"'
    _get_users_command = "SELECT usename FROM pg_user WHERE usename='{}'"

    def run(self, *args):
        ctx = self._quicksetup_cmd.make_context('quicksetup', list(args))
        with ctx:
            ctx.obj = self
            self._quicksetup_cmd.invoke(ctx)

    def _get_pg_access(self):
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
            if self._try_connect(**dbinfo):
                can_connect = True
                dbinfo['user'] = pg_user
                break

        # This will work for the default Debian postgres setup
        if not can_connect:
            if self._try_subcmd(user='postgres'):
                can_subcmd = True
                dbinfo['user'] = 'postgres'
            else:
                can_subcmd = False

        # This is to allow for any other setup
        if not can_connect and not can_subcmd:
            click.echo(
                'Detected no known postgres setup, some information is needed to create the aiida database and grant aiida access to it.')
            click.echo('If you feel unsure about the following parameters, first check if postgresql is installed.')
            click.echo('If postgresql is not installed please exit and install it, then run verdi quicksetup again.')
            click.echo(
                'If postgresql is installed, please ask your system manager to provide you with the following parameters:')
            dbinfo = self._prompt_db_info()

        pg_method = None
        if can_connect:
            pg_method = self._pg_execute_psyco
        elif can_subcmd:
            pg_method = self._pg_execute_sh

        result = {
            'method': pg_method,
            'dbinfo': dbinfo,
        }
        return result

    def _prompt_db_info(self):
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
            if self._try_connect(**dbinfo):
                access = True
            else:
                dbinfo['password'] = click.prompt('postgres password of {}'.format(dbinfo['user']), hide_input=True,
                                                  type=str)
                if self._try_connect(**dbinfo):
                    access = True
                else:
                    click.echo(
                        'you may get prompted for a super user password and again for your postgres super user password')
                    if self._try_subcmd(**dbinfo):
                        access = True
                    else:
                        click.echo('Unable to connect to postgres, please try again')
        return dbinfo

    @click.command('quicksetup', context_settings=CONTEXT_SETTINGS)
    @click.option('--email', prompt='Email Address (will be used to identify your data when sharing)', type=str,
                  help='This email address will be associated with your data and will be exported along with it, should you choose to share any of your work')
    @click.option('--first-name', prompt='First Name', type=str)
    @click.option('--last-name', prompt='Last Name', type=str)
    @click.option('--institution', prompt='Institution', type=str)
    @click.option('--backend', type=click.Choice([BACKEND_DJANGO, BACKEND_SQLA]), default=BACKEND_DJANGO)
    @click.option('--db-port', type=str)
    @click.option('--db-user', type=str)
    @click.option('--db-user-pw', type=str)
    @click.option('--db-name', type=str)
    @click.option('--profile', type=str)
    @click.option('--repo', type=str)
    @click.pass_obj
    def _quicksetup_cmd(self, email, first_name, last_name, institution, backend, db_port, db_user, db_user_pw, db_name,
                        profile, repo):
        '''setup a sane aiida configuration with as little interaction as possible.'''
        from aiida.common.setup import create_base_dirs, AIIDA_CONFIG_FOLDER
        create_base_dirs()

        aiida_dir = os.path.expanduser(AIIDA_CONFIG_FOLDER)

        # access postgres
        pg_info = self._get_pg_access()
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
            if not self._dbuser_exists(dbuser, pg_execute, **dbinfo):
                self._create_dbuser(dbuser, dbpass, pg_execute, **dbinfo)
            else:
                dbname, create = self._check_db_name(dbname, pg_execute, **dbinfo)
            if create:
                self._create_db(dbuser, dbname, pg_execute, **dbinfo)
        except Exception as e:
            click.echo('\n'.join([
                'Oops! Something went wrong while creating the database for you.',
                'You may continue with the quicksetup, however:',
                'For aiida to work correctly you will have to do that yourself as follows.',
                'Please run the following commands as the user for PostgreSQL (Ubuntu: $sudo su postgres):',
                '',
                '\t$ psql template1',
                '\t==> ' + self._create_user_command.format(dbuser, dbpass),
                '\t==> ' + self._create_db_command.format(dbname, dbuser),
                '\t==> ' + self._grant_priv_command.format(dbname, dbuser),
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

        dbhost = dbinfo.get('host', 'localhost')
        dbport = dbinfo.get('port', '5432')

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
        setup(profile_name, only_config=False, non_interactive=True, **setup_args)

        # Loop over all valid processes and check if a default profile is set for them
        # If not set the newly created profile as default, otherwise prompt whether to override
        from aiida.cmdline.commands.profile import valid_processes

        default_profiles = confs.get('default_profiles', {})

        for process in valid_processes:

            default_profile = default_profiles.get(process, '')
            default_override = False

            if default_profile:
                default_override = click.confirm("The default profile for the '{}' process is set to '{}': "
                                                 "do you want to set the newly created '{}' as the new default? (can be reverted later)"
                                                 .format(process, default_profile, profile_name))

            if not default_profile or default_override:
                set_default_profile(process, profile_name, force_rewrite=True)

    def _try_connect(self, **kwargs):
        '''
        try to start a psycopg2 connection.

        :return: True if successful, False otherwise
        '''
        from psycopg2 import connect
        success = False
        try:
            connect(**kwargs)
            success = True
        except:
            pass
        return success

    def _try_subcmd(self, **kwargs):
        '''
        try to run psql in a subprocess.

        :return: True if successful, False otherwise
        '''
        success = False
        try:
            self._pg_execute_sh('\q', **kwargs)
            success = True
        except:
            pass
        return success

    def _create_dbuser(self, dbuser, dbpass, method=None, **kwargs):
        '''
        create a database user in postgres

        :param dbuser: Name of the user to be created.
        :param dbpass: Password the user should be given.
        :param method: callable with signature method(psql_command, **connection_info)
            where connection_info contains keys for psycopg2.connect.
        :param kwargs: connection info as for psycopg2.connect.
        '''
        method(self._create_user_command.format(dbuser, dbpass), **kwargs)

    def _create_db(self, dbuser, dbname, method=None, **kwargs):
        '''create a database in postgres

        :param dbuser: Name of the user which should own the db.
        :param dbname: Name of the database.
        :param method: callable with signature method(psql_command, **connection_info)
            where connection_info contains keys for psycopg2.connect.
        :param kwargs: connection info as for psycopg2.connect.
        '''
        method(self._create_db_command.format(dbname, dbuser), **kwargs)
        method(self._grant_priv_command.format(dbname, dbuser), **kwargs)

    def _pg_execute_psyco(self, command, **kwargs):
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

    def _pg_execute_sh(self, command, user='postgres', **kwargs):
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
        result = sp.check_output(
            ['sudo', 'su', user, '-c', 'psql {options} -tc {}'.format(escape_for_bash(command), options=options)],
            **kwargs)
        if isinstance(result, str):
            result = result.strip().split('\n')
            result = [i for i in result if i]
        return result

    def _dbuser_exists(self, dbuser, method, **kwargs):
        '''return True if postgres user with name dbuser exists, False otherwise.'''
        return bool(method(self._get_users_command.format(dbuser), **kwargs))

    def _check_db_name(self, dbname, method=None, **kwargs):
        '''looks up if a database with the name exists, prompts for using or creating a differently named one'''
        create = True
        while create and method("SELECT datname FROM pg_database WHERE datname='{}'".format(dbname), **kwargs):
            click.echo('database {} already exists!'.format(dbname))
            if not click.confirm('Use it (make sure it is not used by another profile)?'):
                dbname = click.prompt('new name', type=str, default=dbname)
            else:
                create = False
        return dbname, create


class Run(VerdiCommand):
    """
    Execute an AiiDA script
    """

    def run(self, *args):
        from aiida.backends.utils import load_dbenv, is_dbenv_loaded

        if not is_dbenv_loaded():
            load_dbenv()
        import argparse
        from aiida.cmdline.commands.shell import default_modules_list
        import aiida.orm.autogroup
        from aiida.orm.autogroup import Autogroup

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='Execute an AiiDA script.')
        parser.add_argument('-g', '--group', type=bool, default=True,
                            help='Enables the autogrouping, default = True')
        parser.add_argument('-n', '--groupname', type=str, default=None,
                            help='Specify the name of the auto group')
        # parser.add_argument('-o','--grouponly', type=str, nargs='+', default=['all'],
        #                            help='Limit the grouping to specific classes (by default, all classes are grouped')
        parser.add_argument('-e', '--exclude', type=str, nargs='+', default=[],
                            help=('Autogroup only specific calculation classes.'
                                  " Select them by their module name.")
                            )
        parser.add_argument('-E', '--excludesubclasses', type=str, nargs='+',
                            default=[],
                            help=('Autogroup only specific calculation classes.'
                                  " Select them by their module name.")
                            )
        parser.add_argument('-i', '--include', type=str, nargs='+',
                            default=['all'],
                            help=('Autogroup only specific data classes.'
                                  " Select them by their module name.")
                            )
        parser.add_argument('-I', '--includesubclasses', type=str, nargs='+',
                            default=[],
                            help=('Autogroup only specific code classes.'
                                  " Select them by their module name.")
                            )
        parser.add_argument('scriptname', metavar='ScriptName', type=str,
                            help='The name of the script you want to execute')
        parser.add_argument('new_args', metavar='ARGS',
                            nargs=argparse.REMAINDER, type=str,
                            help='Further parameters to pass to the script')
        parsed_args = parser.parse_args(args)

        # Prepare the environment for the script to be run
        globals_dict = {
            '__builtins__': globals()['__builtins__'],
            '__name__': '__main__',
            '__file__': parsed_args.scriptname,
            '__doc__': None,
            '__package__': None}

        ## dynamically load modules (the same of verdi shell) - but in
        ## globals_dict, not in the current environment
        for app_mod, model_name, alias in default_modules_list:
            globals_dict["{}".format(alias)] = getattr(
                __import__(app_mod, {}, {}, model_name), model_name)

        if parsed_args.group:
            automatic_group_name = parsed_args.groupname
            if automatic_group_name is None:
                import datetime

                now = datetime.datetime.now()
                automatic_group_name = "Verdi autogroup on " + now.strftime(
                    "%Y-%m-%d %H:%M:%S")

            aiida_verdilib_autogroup = Autogroup()
            aiida_verdilib_autogroup.set_exclude(parsed_args.exclude)
            aiida_verdilib_autogroup.set_include(parsed_args.include)
            aiida_verdilib_autogroup.set_exclude_with_subclasses(
                parsed_args.excludesubclasses)
            aiida_verdilib_autogroup.set_include_with_subclasses(
                parsed_args.includesubclasses)
            aiida_verdilib_autogroup.set_group_name(automatic_group_name)
            ## Note: this is also set in the exec environment!
            ## This is the intended behavior
            aiida.orm.autogroup.current_autogroup = aiida_verdilib_autogroup

        try:
            f = open(parsed_args.scriptname)
        except IOError:
            print >> sys.stderr, "{}: Unable to load file '{}'".format(
                self.get_full_command_name(), parsed_args.scriptname)
            sys.exit(1)
        else:
            try:
                # Must add also argv[0]
                new_argv = [parsed_args.scriptname] + parsed_args.new_args
                with update_environment(new_argv=new_argv):
                    # Add local folder to sys.path
                    sys.path.insert(0, os.path.abspath(os.curdir))
                    # Pass only globals_dict
                    exec (f, globals_dict)
                    # print sys.argv
            except SystemExit as e:
                ## Script called sys.exit()
                # print sys.argv, "(sys.exit {})".format(e.message)

                ## Note: remember to re-raise, the exception to have
                ## the error code properly returned at the end!
                raise
            finally:
                f.close()


########################################################################
# HERE ENDS THE COMMAND FUNCTION LIST
########################################################################
# From here on: utility functions

def get_listparams():
    """
    Return a string with the list of parameters, to be printed

    The advantage of this function is that the calling routine can
    choose to print it on stdout or stderr, depending on the needs.
    """
    max_length = max(len(i) for i in short_doc.keys())

    name_desc = [(cmd.ljust(max_length + 2), desc.strip())
                 for cmd, desc in short_doc.iteritems()]

    name_desc = sorted(name_desc)

    return ("List of the most relevant available commands:" + os.linesep +
            os.linesep.join(["  * {} {}".format(name, desc)
                             for name, desc in name_desc]))


def get_command_suggestion(command):
    """
    A function that prints on stderr a list of similar commands
    """
    import difflib

    similar_cmds = difflib.get_close_matches(command, short_doc.keys())
    if similar_cmds:
        print >> sys.stderr, ""
        print >> sys.stderr, "Did you mean this?"
        print >> sys.stderr, "\n".join(["     {}".format(i)
                                        for i in similar_cmds])


def print_usage(execname):
    print >> sys.stderr, ("Usage: {} [--profile=PROFILENAME|-p PROFILENAME] "
                          "COMMAND [<args>]".format(execname))
    print >> sys.stderr, ""
    print >> sys.stderr, get_listparams()
    print >> sys.stderr, "See '{} help' for more help.".format(execname)


def exec_from_cmdline(argv):
    """
    The main function to be called. Pass as parameter the sys.argv.
    """
    ### This piece of code takes care of creating a list of valid
    ### commands and of their docstrings for dynamic management of
    ### the code.
    ### It defines a few global variables

    global execname
    global list_commands
    global short_doc
    global long_doc

    # import itself
    from aiida.cmdline import verdilib
    import inspect

    # List of command names that should be hidden or not completed.
    hidden_commands = ['completion', 'completioncommand', 'listparams']

    # Retrieve the list of commands
    verdilib_namespace = verdilib.__dict__

    list_commands = {v.get_command_name(): v for v in
                     verdilib_namespace.itervalues()
                     if inspect.isclass(v) and not v == VerdiCommand and
                     issubclass(v, VerdiCommand)
                     and not v.__name__.startswith('_')
                     and not v._abstract}

    # Retrieve the list of docstrings, managing correctly the
    # case of empty docstrings. Each value is a list of lines
    raw_docstrings = {k: (v.__doc__ if v.__doc__ else "").splitlines()
                      for k, v in list_commands.iteritems()}

    short_doc = {}
    long_doc = {}
    for k, v in raw_docstrings.iteritems():
        if k in hidden_commands:
            continue
        lines = [l.strip() for l in v]
        empty_lines = [bool(l) for l in lines]
        try:
            first_idx = empty_lines.index(True)  # The first non-empty line
        except ValueError:
            # All False
            short_doc[k] = "No description available"
            long_doc[k] = ""
            continue
        short_doc[k] = lines[first_idx]
        long_doc[k] = os.linesep.join(lines[first_idx + 1:])

    execname = os.path.basename(argv[0])

    try:
        profile, command_position = parse_profile(argv)
    except ProfileParsingException as e:
        print_usage(execname)
        sys.exit(1)

    # We now set the internal variable, if needed
    if profile is not None:
        settings_profile.AIIDADB_PROFILE = profile
    # I set the process to verdi
    settings_profile.CURRENT_AIIDADB_PROCESS = "verdi"

    # Finally, we parse the commands and their options
    try:
        command = argv[command_position]
    except IndexError:
        print_usage(execname)
        sys.exit(1)

    try:
        if command in list_commands:
            CommandClass = list_commands[command]()
            CommandClass.run(*argv[command_position + 1:])
        else:
            print >> sys.stderr, ("{}: '{}' is not a valid command. "
                                  "See '{} help' for more help.".format(
                execname, command, execname))
            get_command_suggestion(command)
            sys.exit(1)
    except ProfileConfigurationError as e:
        print >> sys.stderr, "The profile specified is not valid!"
        print >> sys.stderr, e.message
        sys.exit(1)


def run():
    try:
        aiida.cmdline.verdilib.exec_from_cmdline(sys.argv)
    except KeyboardInterrupt:
        pass  # print "CTRL+C caught, exiting from verdi..."
    except EOFError:
        pass  # print "CTRL+D caught, exiting from verdi..."
