# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module that defines methods required to setup a new AiiDA instance."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os

import click

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
    from aiida.manage.configuration import get_config
    from aiida.manage.manager import get_manager
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


def delete_repository(profile, non_interactive=True):
    """
    Delete an AiiDA file repository associated with an AiiDA profile.

    :param profile: AiiDA Profile
    :type profile: :class:`aiida.manage.configuration.profile.Profile`
    :param non_interactive: do not prompt for configuration values, fail if not all values are given as kwargs.
    :type non_interactive: bool
    """
    from six.moves.urllib.parse import urlparse  # pylint: disable=import-error

    pconfig = profile.dictionary
    repo_uri = pconfig.get('AIIDADB_REPOSITORY_URI', '')
    repo_path = urlparse(repo_uri).path
    repo_path = os.path.expanduser(repo_path)

    if not os.path.isabs(repo_path):
        echo.echo_info("Associated file repository '{}' does not exist.".format(repo_path))
        return

    if not os.path.isdir(repo_path):
        echo.echo_info("Associated file repository '{}' is not a directory.".format(repo_path))
        return

    if non_interactive or click.confirm("Delete associated file repository '{}'?\n"
                                        "WARNING: All data will be lost.".format(repo_path)):
        echo.echo_info("Deleting directory '{}'.".format(repo_path))
        import shutil
        shutil.rmtree(repo_path)


def delete_db(profile, non_interactive=True, verbose=False):
    """
    Delete an AiiDA database associated with an AiiDA profile.

    :param profile: AiiDA Profile
    :type profile: :class:`aiida.manage.configuration.profile.Profile`
    :param non_interactive: do not prompt for configuration values, fail if not all values are given as kwargs.
    :type non_interactive: bool
    :param verbose: if True, print parameters of DB connection
    :type verbose: bool
    """
    from aiida.manage.configuration import get_config
    from aiida.manage.external.postgres import Postgres
    from aiida.common import json

    pdict = profile.dictionary

    postgres = Postgres.from_profile(profile, interactive=not non_interactive, quiet=False)
    postgres.determine_setup()

    if verbose:
        echo.echo_info("Parameters used to connect to postgres:")
        echo.echo(json.dumps(postgres.get_dbinfo(), indent=4))

    db_name = pdict.get('AIIDADB_NAME', '')
    if not postgres.db_exists(db_name):
        echo.echo_info("Associated database '{}' does not exist.".format(db_name))
    elif non_interactive or click.confirm("Delete associated database '{}'?\n"
                                          "WARNING: All data will be lost.".format(db_name)):
        echo.echo_info("Deleting database '{}'.".format(db_name))
        postgres.drop_db(db_name)

    user = pdict.get('AIIDADB_USER', '')
    config = get_config()
    users = [profile.dictionary.get('AIIDADB_USER', '') for profile in config.profiles]

    if not postgres.dbuser_exists(user):
        echo.echo_info("Associated database user '{}' does not exist.".format(user))
    elif users.count(user) > 1:
        echo.echo_info("Associated database user '{}' is used by other profiles "
                       "and will not be deleted.".format(user))
    elif non_interactive or click.confirm("Delete database user '{}'?".format(user)):
        echo.echo_info("Deleting user '{}'.".format(user))
        postgres.drop_dbuser(user)


def delete_from_config(profile, non_interactive=True):
    """
    Delete an AiiDA profile from the config file.

    :param profile: AiiDA Profile
    :type profile: :class:`aiida.manage.configuration.profile.Profile`
    :param non_interactive: do not prompt for configuration values, fail if not all values are given as kwargs.
    :type non_interactive: bool
    """
    from aiida.manage.configuration import get_config

    if non_interactive or click.confirm("Delete configuration for profile '{}'?\n"
                                        "WARNING: Permanently removes profile from the list of AiiDA profiles.".format(
                                            profile.name)):
        echo.echo_info("Deleting configuration for profile '{}'.".format(profile.name))
        config = get_config()
        config.remove_profile(profile.name)
        config.store()


def delete_profile(profile, non_interactive=True, include_db=True, include_repository=True, include_config=True):
    """
    Delete an AiiDA profile and AiiDA user.

    :param profile: AiiDA profile
    :type profile: :class:`aiida.manage.configuration.profile.Profile`
    :param non_interactive: do not prompt for configuration values, fail if not all values are given as kwargs.
    :param include_db: Include deletion of associated database
    :type include_db: bool
    :param include_repository: Include deletion of associated file repository
    :type include_repository: bool
    :param include_config: Include deletion of entry from AiiDA configuration file
    :type include_config: bool
    """
    if include_db:
        delete_db(profile, non_interactive)

    if include_repository:
        delete_repository(profile, non_interactive)

    if include_config:
        delete_from_config(profile, non_interactive)
