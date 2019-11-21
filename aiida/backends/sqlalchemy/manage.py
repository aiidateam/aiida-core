#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Simple wrapper around the alembic command line tool that first loads an AiiDA profile."""

import alembic
import click

from aiida.cmdline.params import options


def execute_alembic_command(command_name, **kwargs):
    """Execute an Alembic CLI command.

    :param command_name: the sub command name
    :param kwargs: parameters to pass to the command
    """
    from aiida.backends.sqlalchemy.manager import SqlaBackendManager

    manager = SqlaBackendManager()

    with manager.alembic_config() as config:
        command = getattr(alembic.command, command_name)
        command(config, **kwargs)


@click.group()
@options.PROFILE(required=True)
def alembic_cli(profile):
    """Simple wrapper around the alembic command line tool that first loads an AiiDA profile."""
    from aiida.manage.configuration import load_profile
    from aiida.manage.manager import get_manager

    load_profile(profile=profile.name)
    manager = get_manager()
    manager._load_backend(schema_check=False)  # pylint: disable=protected-access


@alembic_cli.command('revision')
@click.argument('message')
def alembic_revision(message):
    """Create a new database revision."""
    execute_alembic_command('revision', message=message, autogenerate=True)


@alembic_cli.command('current')
@options.VERBOSE()
def alembic_current(verbose):
    """Show the current revision."""
    execute_alembic_command('current', verbose=verbose)


@alembic_cli.command('history')
@click.option('-r', '--rev-range')
@options.VERBOSE()
def alembic_history(rev_range, verbose):
    """Show the history for the given revision range."""
    execute_alembic_command('history', rev_range=rev_range, verbose=verbose)


@alembic_cli.command('upgrade')
@click.argument('revision', type=click.STRING)
def alembic_upgrade(revision):
    """Upgrade the database to the given REVISION."""
    execute_alembic_command('upgrade', revision=revision)


@alembic_cli.command('downgrade')
@click.argument('revision', type=click.STRING)
def alembic_downgrade(revision):
    """Downgrade the database to the given REVISION."""
    execute_alembic_command('downgrade', revision=revision)


if __name__ == '__main__':
    alembic_cli()  # pylint: disable=no-value-for-parameter
