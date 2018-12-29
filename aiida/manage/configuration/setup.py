# -*- coding: utf-8 -*-
"""Module that defines methods required to setup a new AiiDA instance."""
from __future__ import absolute_import

import os

from aiida.cmdline.utils import echo


def create_instance_directories():
    """Create the base directories required for a new AiiDA instance.

    This will create the base AiiDA directory defined by the AIIDA_CONFIG_FOLDER variable, unless it already exists.
    Subsequently, it will create the daemon directory within it and the daemon log directory.
    """
    from .settings import AIIDA_CONFIG_FOLDER, DAEMON_DIR, DAEMON_LOG_DIR, DEFAULT_UMASK

    directory_base = os.path.expanduser(AIIDA_CONFIG_FOLDER)
    directory_daemon = os.path.join(directory_base, DAEMON_DIR)
    directory_daemon_log = os.path.join(directory_base, DAEMON_LOG_DIR)

    umask = os.umask(DEFAULT_UMASK)

    try:
        if not os.path.isdir(directory_base):
            os.makedirs(directory_base)

        if not os.path.isdir(directory_daemon):
            os.makedirs(directory_daemon)

        if not os.path.isdir(directory_daemon_log):
            os.makedirs(directory_daemon_log)
    finally:
        os.umask(umask)


def setup_profile(profile_name, only_config, set_default=False, non_interactive=False, **kwargs):
    """
    Setup an AiiDA profile and AiiDA user (and the AiiDA default user).

    :param profile_name: Profile name
    :param only_config: do not create a new user
    :param set_default: set the new profile as the default
    :param non_interactive: do not prompt for configuration values, fail if not all values are given as kwargs.
    :param backend: one of 'django', 'sqlalchemy'
    :param email: valid email address for the user
    :param db_host: hostname for the database
    :param db_port: port to connect to the database
    :param db_user: name of the db user
    :param db_pass: password of the db user
    """
    # pylint: disable=superfluous-parens,too-many-locals,too-many-statements,too-many-branches
    from aiida.backends import settings
    from aiida.backends.profile import BACKEND_SQLA, BACKEND_DJANGO
    from aiida.backends.utils import set_backend_type
    from aiida.cmdline.commands import cmd_user
    from aiida.common.exceptions import InvalidOperation
    from aiida.common.setup import create_profile, create_profile_noninteractive
    from aiida.manage import get_config, get_manager
    from .settings import DEFAULT_AIIDA_USER

    config = get_config()
    manager = get_manager()

    only_user_config = only_config

    # Create the directories to store the configuration files
    create_instance_directories()

    # we need to overwrite this variable for the following to work
    settings.AIIDADB_PROFILE = profile_name

    profile = None
    # ask and store the configuration of the DB
    if non_interactive:
        try:
            profile = create_profile_noninteractive(
                config=config,
                profile_name=profile_name,
                backend=kwargs['backend'],
                email=kwargs['email'],
                db_host=kwargs['db_host'],
                db_port=kwargs['db_port'],
                db_name=kwargs['db_name'],
                db_user=kwargs['db_user'],
                db_pass=kwargs.get('db_pass', ''),
                repo=kwargs['repo'],
                force_overwrite=kwargs.get('force_overwrite', False))
        except ValueError as exception:
            echo.echo_critical("Error during configuation: {}".format(exception))
        except KeyError as exception:
            import traceback
            echo.echo(traceback.format_exc())
            echo.echo_critical(
                "--non-interactive requires all values to be given on the commandline! Missing argument: {}".format(
                    exception.args[0]))
    else:
        try:
            profile = create_profile(config=config, profile_name=profile_name)
        except ValueError as exception:
            echo.echo_critical("Error during configuration: {}".format(exception))

    # Add the created profile and set it as the new default profile
    config.add_profile(profile_name, profile)
    config.set_default_profile(profile_name, overwrite=set_default)
    config.store()

    if only_user_config:
        echo.echo("Only user configuration requested, skipping the migrate command")
    else:
        echo.echo("Executing now a migrate command...")

        backend_choice = profile['AIIDADB_BACKEND']
        if backend_choice == BACKEND_DJANGO:
            echo.echo("...for Django backend")
            backend = manager._load_backend(schema_check=False)  # pylint: disable=protected-access
            backend.migrate()
            set_backend_type(BACKEND_DJANGO)

        elif backend_choice == BACKEND_SQLA:
            echo.echo("...for SQLAlchemy backend")
            backend = manager._load_backend(schema_check=False)  # pylint: disable=protected-access
            backend.migrate()
            set_backend_type(BACKEND_SQLA)

        else:
            raise InvalidOperation("Not supported backend selected.")

    echo.echo("Database was created successfully")
    from aiida import orm

    if not orm.User.objects.find({'email': DEFAULT_AIIDA_USER}):
        echo.echo("Installing default AiiDA user...")
        nuser = orm.User(email=DEFAULT_AIIDA_USER, first_name="AiiDA", last_name="Daemon")
        nuser.is_active = True
        nuser.store()

    email = manager.get_profile().default_user_email
    echo.echo("Starting user configuration for {}...".format(email))
    if email == DEFAULT_AIIDA_USER:
        echo.echo("You set up AiiDA using the default Daemon email ({}),".format(email))
        echo.echo("therefore no further user configuration will be asked.")
    else:
        if non_interactive:
            # Here we map the keyword arguments onto the command line arguments
            # for verdi user configure.  We have to be careful that there the
            # argument names are the same as those int he kwargs dict
            commands = [kwargs['email'], '--non-interactive']

            for arg in ('first_name', 'last_name', 'institution'):
                value = kwargs.get(arg, None)
                if value is not None:
                    commands.extend(('--{}'.format(arg.replace('_', '-')), str(value)))
        else:
            commands = [email]

        # Ask to configure the user
        try:
            # pylint: disable=no-value-for-parameter
            cmd_user.configure(commands)
        except SystemExit:
            # Have to catch this as the configure command will do a sys.exit()
            pass

    echo.echo("Setup finished.")
