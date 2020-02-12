# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi profile` command."""

import click
import tabulate

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import arguments, options
from aiida.cmdline.utils import defaults, echo
from aiida.common import exceptions
from aiida.manage.configuration import get_config


@verdi.group('profile')
def verdi_profile():
    """Inspect and manage the configured profiles."""


@verdi_profile.command('list')
def profile_list():
    """Display a list of all available profiles."""

    try:
        config = get_config()
    except (exceptions.MissingConfigurationError, exceptions.ConfigurationError) as exception:
        # This can happen for a fresh install and the `verdi setup` has not yet been run. In this case it is still nice
        # to be able to see the configuration directory, for instance for those who have set `AIIDA_PATH`. This way
        # they can at least verify that it is correctly set.
        from aiida.manage.configuration.settings import AIIDA_CONFIG_FOLDER
        echo.echo_info('configuration folder: {}'.format(AIIDA_CONFIG_FOLDER))
        echo.echo_critical(str(exception))
    else:
        echo.echo_info('configuration folder: {}'.format(config.dirpath))

    if not config.profiles:
        echo.echo_warning('no profiles configured: run `verdi setup` to create one')
    else:
        sort = lambda profile: profile.name
        highlight = lambda profile: profile.name == config.default_profile_name
        echo.echo_formatted_list(config.profiles, ['name'], sort=sort, highlight=highlight)


@verdi_profile.command('show')
@arguments.PROFILE(default=defaults.get_default_profile)
def profile_show(profile):
    """Show details for a profile."""
    if profile is None:
        echo.echo_critical('no profile to show')

    echo.echo_info('Configuration for: {}'.format(profile.name))
    data = sorted([(k.lower(), v) for k, v in profile.dictionary.items()])
    echo.echo(tabulate.tabulate(data))


@verdi_profile.command('setdefault')
@arguments.PROFILE(required=True, default=None)
def profile_setdefault(profile):
    """Set a profile as the default one."""
    try:
        config = get_config()
    except (exceptions.MissingConfigurationError, exceptions.ConfigurationError) as exception:
        echo.echo_critical(str(exception))

    config.set_default_profile(profile.name, overwrite=True).store()
    echo.echo_success('{} set as default profile'.format(profile.name))


@verdi_profile.command('delete')
@options.FORCE(help='to skip questions and warnings about loss of data')
@click.option(
    '--include-config/--skip-config',
    default=True,
    show_default=True,
    help='Include deletion of entry in configuration file.'
)
@click.option(
    '--include-db/--skip-db', default=True, show_default=True, help='Include deletion of associated database.'
)
@click.option(
    '--include-repository/--skip-repository',
    default=True,
    show_default=True,
    help='Include deletion of associated file repository.'
)
@arguments.PROFILES(required=True)
def profile_delete(force, include_config, include_db, include_repository, profiles):
    """
    Delete one or more profiles.

    You can specify more profile names (separated by spaces).
    These will be removed from the aiida config file,
    and the associated databases and file repositories will also be removed.
    """
    from aiida.manage.configuration.setup import delete_profile

    for profile in profiles:
        echo.echo_info("Deleting profile '{}'".format(profile.name))
        delete_profile(
            profile,
            non_interactive=force,
            include_db=include_db,
            include_repository=include_repository,
            include_config=include_config
        )
