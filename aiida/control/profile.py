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
import os
import sys

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
    from aiida.cmdline import EXECNAME
    from aiida.cmdline.commands import cmd_user
    from aiida.common.exceptions import InvalidOperation
    from aiida.common.setup import (create_base_dirs, create_configuration, set_default_profile, DEFAULT_UMASK,
                                    create_config_noninteractive)

    only_user_config = only_config

    # Create the directories to store the configuration files
    create_base_dirs()
    if settings.AIIDADB_PROFILE and profile:
        sys.exit('the profile argument cannot be used if verdi is called with -p option: {} and {}'.format(
            settings.AIIDADB_PROFILE, profile))
    gprofile = settings.AIIDADB_PROFILE or profile
    if gprofile == profile:
        settings.AIIDADB_PROFILE = profile
    if not settings.AIIDADB_PROFILE:
        settings.AIIDADB_PROFILE = 'default'

    # used internally later
    gprofile = settings.AIIDADB_PROFILE

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
            created_conf = create_configuration(profile=gprofile)
        except ValueError as exception:
            echo.echo_critical("Error during configuration: {}".format(exception))

        # Set default DB profile
        set_default_profile(gprofile, force_rewrite=False)

    if only_user_config:
        echo.echo("Only user configuration requested, skipping the migrate command")
    else:
        echo.echo("Executing now a migrate command...")

        backend_choice = created_conf['AIIDADB_BACKEND']
        if backend_choice == BACKEND_DJANGO:
            echo.echo("...for Django backend")
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
                from aiida.backends.djsite.utils import pass_to_django_manage
                pass_to_django_manage([EXECNAME, 'migrate'], profile=gprofile)
            finally:
                os.umask(old_umask)

            set_backend_type(BACKEND_DJANGO)

        elif backend_choice == BACKEND_SQLA:
            echo.echo("...for SQLAlchemy backend")
            from aiida import is_dbenv_loaded
            from aiida.backends.sqlalchemy.utils import _load_dbenv_noschemacheck, check_schema_version
            from aiida.backends.profile import load_profile

            # We avoid calling load_dbenv since we want to force the schema
            # migration
            if not is_dbenv_loaded():
                settings.LOAD_DBENV_CALLED = True
                # This is going to set global variables in settings, including settings.BACKEND
                load_profile()
                _load_dbenv_noschemacheck()

            # Perform the needed migration quietly
            check_schema_version(force_migration=True)
            set_backend_type(BACKEND_SQLA)

        else:
            raise InvalidOperation("Not supported backend selected.")

    echo.echo("Database was created successfully")

    # I create here the default user
    echo.echo("Loading new environment...")
    if only_user_config:
        from aiida.backends.utils import load_dbenv, is_dbenv_loaded
        # db environment has not been loaded in this case
        if not is_dbenv_loaded():
            load_dbenv()

    from aiida.common.setup import DEFAULT_AIIDA_USER
    from aiida.orm.backends import construct_backend

    backend = construct_backend()
    if not backend.users.find(email=DEFAULT_AIIDA_USER):
        echo.echo("Installing default AiiDA user...")
        nuser = backend.users.create(email=DEFAULT_AIIDA_USER, first_name="AiiDA", last_name="Daemon")
        nuser.is_active = True
        nuser.store()

    from aiida.common.utils import get_configured_user_email
    email = get_configured_user_email()
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

    if set_default:
        set_default_profile(profile, force_rewrite=True)

    echo.echo("Setup finished.")
