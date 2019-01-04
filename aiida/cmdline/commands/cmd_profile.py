# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi profile` command."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import click
import tabulate

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.utils import defaults, echo
from aiida.cmdline.params import arguments, options
from aiida.common import exceptions
from aiida.manage import get_config
from aiida.manage.external.postgres import Postgres


@verdi.group('profile')
def verdi_profile():
    """Inspect and manage the configured profiles."""


@verdi_profile.command('list')
def profile_list():
    """Displays list of all available profiles."""
    try:
        config = get_config()
    except (exceptions.MissingConfigurationError, exceptions.ConfigurationError) as exception:
        echo.echo_critical(str(exception))

    echo.echo_info('configuration folder: {}'.format(config.dirpath))

    default_profile = config.default_profile_name

    for profile in sorted(config.profiles, key=lambda p: p.name):
        if profile.name == default_profile:
            click.secho('{} {}'.format('*', profile.name), fg='green')
        else:
            click.secho('{} {}'.format(' ', profile.name))


@verdi_profile.command('show')
@arguments.PROFILE(required=False, callback=defaults.get_default_profile)
def profile_show(profile):
    """Show details for PROFILE or, when not specified, the default profile."""
    data = sorted([(k.lower(), v) for k, v in profile.dictionary.items()])
    echo.echo(tabulate.tabulate(data, headers=('Attribute', 'Value')))


@verdi_profile.command('setdefault')
@arguments.PROFILE()
def profile_setdefault(profile):
    """Set PROFILE as the default profile."""
    try:
        config = get_config()
    except (exceptions.MissingConfigurationError, exceptions.ConfigurationError) as exception:
        echo.echo_critical(str(exception))

    config.set_default_profile(profile.name, overwrite=True).store()
    echo.echo_success('{} set as default profile'.format(profile.name))


@verdi_profile.command('delete')
@options.FORCE(help='to skip any questions/warnings about loss of data')
@arguments.PROFILES()
def profile_delete(force, profiles):
    """
    Delete PROFILES separated by space from aiida config file
    along with its associated database and repository.
    """
    import os
    from six.moves.urllib.parse import urlparse  # pylint: disable=import-error
    import aiida.common.json as json

    try:
        config = get_config()
    except (exceptions.MissingConfigurationError, exceptions.ConfigurationError) as exception:
        echo.echo_critical(str(exception))

    profile_names = [profile.name for profile in profiles]
    users = [profile.dictionary.get('AIIDADB_USER', '') for profile in config.profiles]

    for profile_name in profile_names:
        try:
            profile = config.get_profile(profile_name)
        except exceptions.ProfileConfigurationError:
            echo.echo_error("profile '{}' does not exist".format(profile_name))
            continue

        profile_dictionary = profile.dictionary

        postgres = Postgres(port=profile_dictionary.get('AIIDADB_PORT'), interactive=True, quiet=False)
        postgres.dbinfo["user"] = profile_dictionary.get('AIIDADB_USER')
        postgres.dbinfo["host"] = profile_dictionary.get('AIIDADB_HOST')
        postgres.determine_setup()

        echo.echo(json.dumps(postgres.dbinfo, indent=4))

        db_name = profile_dictionary.get('AIIDADB_NAME', '')
        if not postgres.db_exists(db_name):
            echo.echo_info("Associated database '{}' does not exist.".format(db_name))
        elif force or click.confirm("Delete associated database '{}'?\n"
                                    "WARNING: All data will be lost.".format(db_name)):
            echo.echo_info("Deleting database '{}'.".format(db_name))
            postgres.drop_db(db_name)

        user = profile_dictionary.get('AIIDADB_USER', '')
        if not postgres.dbuser_exists(user):
            echo.echo_info("Associated database user '{}' does not exist.".format(user))
        elif users.count(user) > 1:
            echo.echo_info("Associated database user '{}' is used by other profiles "
                           "and will not be deleted.".format(user))
        elif force or click.confirm("Delete database user '{}'?".format(user)):
            echo.echo_info("Deleting user '{}'.".format(user))
            postgres.drop_dbuser(user)

        repo_uri = profile_dictionary.get('AIIDADB_REPOSITORY_URI', '')
        repo_path = urlparse(repo_uri).path
        repo_path = os.path.expanduser(repo_path)
        if not os.path.isabs(repo_path):
            echo.echo_info("Associated file repository '{}' does not exist.".format(repo_path))
        elif not os.path.isdir(repo_path):
            echo.echo_info("Associated file repository '{}' is not a directory.".format(repo_path))
        elif force or click.confirm("Delete associated file repository '{}'?\n"
                                    "WARNING: All data will be lost.".format(repo_path)):
            echo.echo_info("Deleting directory '{}'.".format(repo_path))
            import shutil
            shutil.rmtree(repo_path)

        if force or click.confirm(
                "Delete configuration for profile '{}'?\n"
                "WARNING: Permanently removes profile from the list of AiiDA profiles.".format(profile_name)):
            echo.echo_info("Deleting configuration for profile '{}'.".format(profile_name))
            config.remove_profile(profile_name).store()
