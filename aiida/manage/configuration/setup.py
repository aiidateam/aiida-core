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


def delete_repository(profile, non_interactive=True):
    """
    Delete an AiiDA file repository associated with an AiiDA profile.

    :param profile: AiiDA Profile
    :type profile: :class:`aiida.manage.configuration.profile.Profile`
    :param non_interactive: do not prompt for configuration values, fail if not all values are given as kwargs.
    :type non_interactive: bool
    """
    from six.moves.urllib.parse import urlparse  # pylint: disable=import-error

    repo_path = urlparse(profile.repository_uri).path
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

    postgres = Postgres.from_profile(profile, interactive=not non_interactive, quiet=False)

    if verbose:
        echo.echo_info("Parameters used to connect to postgres:")
        echo.echo(json.dumps(postgres.dbinfo, indent=4))

    database_name = profile.database_name
    if not postgres.db_exists(database_name):
        echo.echo_info("Associated database '{}' does not exist.".format(database_name))
    elif non_interactive or click.confirm("Delete associated database '{}'?\n"
                                          "WARNING: All data will be lost.".format(database_name)):
        echo.echo_info("Deleting database '{}'.".format(database_name))
        postgres.drop_db(database_name)

    user = profile.database_username
    config = get_config()
    users = [available_profile.database_username for available_profile in config.profiles]

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
