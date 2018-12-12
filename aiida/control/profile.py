# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=superfluous-parens,too-many-locals,too-many-statements,too-many-branches
"""Functions to create, inspect and manipulate profiles in the configuration file."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.cmdline.utils import echo


def setup_profile(profile, only_config, set_default=False, non_interactive=False, **kwargs):
    """
    Setup an AiiDA profile and AiiDA user (and the AiiDA default user).

    :param profile: Profile name
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
    from aiida.backends import settings
    from aiida.backends.profile import BACKEND_SQLA, BACKEND_DJANGO
    from aiida.backends.utils import set_backend_type
    from aiida.cmdline.commands import cmd_user
    from aiida.common.exceptions import InvalidOperation
    from aiida.manage.configuration.setup import create_instance_directories
    from aiida.common.setup import create_configuration, create_config_noninteractive
    from aiida.manage import get_manager, load_config
    from aiida.manage.configuration.settings import DEFAULT_AIIDA_USER

    manager = get_manager()

    only_user_config = only_config

    # Create the directories to store the configuration files
    create_instance_directories()

    # we need to overwrite this variable for the following to work
    settings.AIIDADB_PROFILE = profile

    created_conf = None
    # ask and store the configuration of the DB
    if non_interactive:
        try:
            created_conf = create_config_noninteractive(
                profile_name=profile,
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
            created_conf = create_configuration(profile_name=profile)
        except ValueError as exception:
            echo.echo_critical("Error during configuration: {}".format(exception))

    # Set default DB profile
    config = load_config()
    config.set_default_profile(profile, overwrite=set_default)

    if only_user_config:
        echo.echo("Only user configuration requested, skipping the migrate command")
    else:
        echo.echo("Executing now a migrate command...")

        backend_choice = created_conf['AIIDADB_BACKEND']
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
