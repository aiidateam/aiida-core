#-*- coding: utf8 -*-
"""verdi setup command"""
import click
from aiida.cmdline.aiida_verdi import options, arguments


@click.command('setup', short_help='Setup an AiiDA profile')
@click.argument('profile', default='', metavar='PROFILE', type=str)  #, help='Profile Name to create/edit')
@click.option('--only-config', is_flag=True, help='Do not create a new user')
@options.non_interactive()
@options.backend()
@options.email()
@options.db_host()
@options.db_port()
@options.db_name()
@options.db_user()
@options.db_pass()
@options.first_name()
@options.last_name()
@options.institution()
@click.option('--no-password', is_flag=True, help='do not set a password (--non-interactive fails otherwise)')
@options.repo()
def setup(profile, only_config, non_interactive, backend, email, db_host, db_port, db_name, db_user, db_pass, first_name, last_name, institution, no_password, repo, **kwargs):
    '''
    Setup PROFILE for aiida for the current user

    This command creates the ~/.aiida folder in the home directory
    of the user, interactively asks for the database settings and
    the repository location, does a setup of the daemon and runs
    a migrate command to create/setup the database.

    In --non-interactive mode, the command will never prompt but
    instead expect all parameters to be given as commandline options.
    If values are missing or invalid, the command will fail.
    '''
    import os

    from aiida.common.setup import (create_base_dirs, create_configuration,
                                    set_default_profile, DEFAULT_UMASK,
                                    create_config_noninteractive)
    from aiida.backends import settings as settings_profile
    from aiida.backends.profile import BACKEND_SQLA, BACKEND_DJANGO
    from aiida.backends.utils import set_backend_type
    from aiida.cmdline import pass_to_django_manage, execname
    from aiida.common.exceptions import InvalidOperation

    only_user_config = only_config

    # create the directories to store the configuration files
    create_base_dirs()

    if settings_profile.AIIDADB_PROFILE and profile:
        click.Error('the profile argument cannot be used if verdi is called with -p option: {} and {}'.format(settings_profile.AIIDADB_PROFILE, profile))
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
                backend=backend,
                email=email,
                db_host=db_host,
                db_port=db_port,
                db_name=db_name,
                db_user=db_user,
                db_pass=db_pass,
                repo=repo,
                force_overwrite=kwargs.get('force_overwrite', False)
            )
        except ValueError as e:
            raise click.Error("Error during configuation: {}".format(e.message))
        except KeyError as e:
            raise click.Error("--non-interactive requires all values to be given on the commandline! {}".format(e.message))
    else:
        try:
            created_conf = create_configuration(profile=gprofile)
        except ValueError as e:
            raise click.Error("Error during configuration: {}".format(e.message))

        # set default DB profiles
        set_default_profile('verdi', gprofile, force_rewrite=False)
        set_default_profile('daemon', gprofile, force_rewrite=False)

    if only_user_config:
        click.echo("Only user configuration requested, "
                   "skipping the migrate command")
    else:
        click.echo("Executing now a migrate command...")

        backend_choice = created_conf['AIIDADB_BACKEND']
        if backend_choice == BACKEND_DJANGO:
            click.echo("...for Django backend")
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
            click.echo("...for SQLAlchemy backend")
            from aiida import is_dbenv_loaded, load_dbenv
            if not is_dbenv_loaded():
                load_dbenv()

            from aiida.backends.sqlalchemy.models.base import Base
            from aiida.backends.sqlalchemy.utils import (get_engine,
                                                         install_tc)
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

            connection = get_engine(get_profile_config(gprofile))
            Base.metadata.create_all(connection)
            install_tc(connection)

            set_backend_type(BACKEND_SQLA)

        else:
            raise InvalidOperation("Not supported backend selected.")

    click.echo("Database was created successfully")

    # I create here the default user
    click.echo("Loading new environment...")
    if only_user_config:
        from aiida.backends.utils import load_dbenv, is_dbenv_loaded
        # db environment has not been loaded in this case
        if not is_dbenv_loaded():
            load_dbenv()

    from aiida.common.setup import DEFAULT_AIIDA_USER
    from aiida.orm.user import User as AiiDAUser

    if not AiiDAUser.search_for_users(email=DEFAULT_AIIDA_USER):
        click.echo("Installing default AiiDA user...")
        nuser = AiiDAUser(email=DEFAULT_AIIDA_USER)
        nuser.first_name = "AiiDA"
        nuser.last_name = "Daemon"
        nuser.is_staff = True
        nuser.is_active = True
        nuser.is_superuser = True
        nuser.force_save()

    from aiida.common.utils import get_configured_user_email
    email = get_configured_user_email()
    click.echo("Starting user configuration for {}...".format(email))
    if email == DEFAULT_AIIDA_USER:
        click.echo("You set up AiiDA using the default Daemon email ({}),".format(
            email))
        click.echo("therefore no further user configuration will be asked.")
    else:
        # Ask to configure the new user
        from aiida.cmdline.commands.user import configure as user_configure
        if not non_interactive:
            user_configure.invoke()
        else:
            # or don't ask
            user_configure.invoke(
                email=kwargs['email'],
                first_name=kwargs.get('first_name'),
                last_name=kwargs.get('last_name'),
                institution=kwargs.get('institution'),
                no_password=True
            )

    click.echo("Setup finished.")
