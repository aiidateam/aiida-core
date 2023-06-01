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
from sqlalchemy.util.compat import nullcontext

from aiida.cmdline import is_verbose
from aiida.cmdline.groups.verdi import VerdiCommandGroup
from aiida.cmdline.params import options
from aiida.storage.psql_dos.migrator import PsqlDosMigrator


class AlembicRunner:
    """Wrapper around the alembic command line tool that first loads an AiiDA profile."""

    def __init__(self) -> None:
        self.profile = None

    def execute_alembic_command(self, command_name, connect=True, **kwargs):
        """Execute an Alembic CLI command.

        :param command_name: the sub command name
        :param kwargs: parameters to pass to the command
        """
        if self.profile is None:
            raise click.ClickException('No profile specified')
        migrator = PsqlDosMigrator(self.profile)

        context = migrator._alembic_connect() if connect else nullcontext(migrator._alembic_config())  # pylint: disable=protected-access
        with context as config:
            command = getattr(alembic.command, command_name)
            config.stdout = click.get_text_stream('stdout')
            command(config, **kwargs)


pass_runner = click.make_pass_decorator(AlembicRunner, ensure=True)


@click.group(cls=VerdiCommandGroup)
@options.PROFILE(required=True)
@pass_runner
def alembic_cli(runner, profile):
    """Simple wrapper around the alembic command line tool that first loads an AiiDA profile."""
    runner.profile = profile


@alembic_cli.command('revision')
@click.argument('message')
@pass_runner
def alembic_revision(runner, message):
    """Create a new database revision."""
    # to-do this does not currently work, because `alembic.RevisionContext._run_environment` has issues with heads
    # (it works if we comment out the initial autogenerate check)
    runner.execute_alembic_command('revision', message=message, autogenerate=True, head='main@head')


@alembic_cli.command('current')
@options.VERBOSITY()
@pass_runner
def alembic_current(runner):
    """Show the current revision."""
    runner.execute_alembic_command('current', verbose=is_verbose())


@alembic_cli.command('history')
@click.option('-r', '--rev-range')
@options.VERBOSITY()
@pass_runner
def alembic_history(runner, rev_range):
    """Show the history for the given revision range."""
    runner.execute_alembic_command('history', connect=False, rev_range=rev_range, verbose=is_verbose())


@alembic_cli.command('show')
@click.argument('revision', type=click.STRING)
@pass_runner
def alembic_show(runner, revision):
    """Show details of the given REVISION."""
    runner.execute_alembic_command('show', rev=revision)


@alembic_cli.command('upgrade')
@click.argument('revision', type=click.STRING)
@pass_runner
def alembic_upgrade(runner, revision):
    """Upgrade the database to the given REVISION."""
    runner.execute_alembic_command('upgrade', revision=revision)


@alembic_cli.command('downgrade')
@click.argument('revision', type=click.STRING)
@pass_runner
def alembic_downgrade(runner, revision):
    """Downgrade the database to the given REVISION."""
    runner.execute_alembic_command('downgrade', revision=revision)


if __name__ == '__main__':
    alembic_cli()  # pylint: disable=no-value-for-parameter
