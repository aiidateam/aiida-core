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
from aiida.cmdline.params import arguments, options
from aiida.cmdline.utils import defaults, echo
from aiida.common import exceptions
from aiida.manage.configuration import get_config


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

    if not config.profiles:
        echo.echo_info('no profiles configured')
    else:

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
    if not profile:
        echo.echo_critical('no profile to show')

    echo.echo_info('Configuration for: {}'.format(profile.name))
    data = sorted([(k.lower(), v) for k, v in profile.dictionary.items()])
    echo.echo(tabulate.tabulate(data))


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
@options.FORCE(help='to skip questions and warnings about loss of data')
@click.option(
    '--include-config/--skip-config',
    default=True,
    show_default=True,
    help='Include deletion of entry in configuration file.')
@click.option(
    '--include-db/--skip-db', default=True, show_default=True, help='Include deletion of associated database.')
@click.option(
    '--include-repository/--skip-repository',
    default=True,
    show_default=True,
    help='Include deletion of associated file repository.')
@arguments.PROFILES(required=True)
def profile_delete(force, include_config, include_db, include_repository, profiles):
    """
    Delete PROFILES (names, separated by spaces) from the aiida config file,
    including the associated databases and file repositories.
    """
    from aiida.manage.configuration.setup import delete_profile

    for profile in profiles:
        echo.echo_info("Deleting profile '{}'".format(profile.name))
        delete_profile(
            profile,
            non_interactive=force,
            include_db=include_db,
            include_repository=include_repository,
            include_config=include_config)
