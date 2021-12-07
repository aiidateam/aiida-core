# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi storage` commands."""

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import options
from aiida.cmdline.utils import echo
from aiida.common import exceptions


@verdi.group('storage')
def verdi_storage():
    """Inspect and manage stored data for a profile."""


@verdi_storage.command('migrate')
@options.FORCE()
def storage_migrate(force):
    """Migrate the storage to the latest schema version."""
    from aiida.engine.daemon.client import get_daemon_client
    from aiida.manage.manager import get_manager

    client = get_daemon_client()
    if client.is_daemon_running:
        echo.echo_critical('Migration aborted, the daemon for the profile is still running.')

    manager = get_manager()
    profile = manager.get_profile()
    backend = manager._load_backend(schema_check=False)  # pylint: disable=protected-access

    if force:
        try:
            backend.migrate()
        except (exceptions.ConfigurationError, exceptions.DatabaseMigrationError) as exception:
            echo.echo_critical(str(exception))
        return

    echo.echo_warning('Migrating your storage might take a while and is not reversible.')
    echo.echo_warning('Before continuing, make sure you have completed the following steps:')
    echo.echo_warning('')
    echo.echo_warning(' 1. Make sure you have no active calculations and workflows.')
    echo.echo_warning(' 2. If you do, revert the code to the previous version and finish running them first.')
    echo.echo_warning(' 3. Stop the daemon using `verdi daemon stop`')
    echo.echo_warning(' 4. Make a backup of your database and repository')
    echo.echo_warning('')
    echo.echo_warning('', nl=False)

    expected_answer = 'MIGRATE NOW'
    confirm_message = 'If you have completed the steps above and want to migrate profile "{}", type {}'.format(
        profile.name, expected_answer
    )

    try:
        response = click.prompt(confirm_message)
        while response != expected_answer:
            response = click.prompt(confirm_message)
    except click.Abort:
        echo.echo('\n')
        echo.echo_critical('Migration aborted, the data has not been affected.')
    else:
        try:
            backend.migrate()
        except (exceptions.ConfigurationError, exceptions.DatabaseMigrationError) as exception:
            echo.echo_critical(str(exception))
        else:
            echo.echo_success('migration completed')


@verdi_storage.group('integrity')
def storage_integrity():
    """Checks for the integrity of the data storage."""


@verdi_storage.command('info')
@click.option('--statistics', is_flag=True, help='Provides more in-detail statistically relevant data.')
def storage_info(statistics):
    """Summarise the contents of the storage."""
    from aiida.backends.control import get_repository_info
    from aiida.cmdline.utils.common import get_database_summary
    from aiida.orm import QueryBuilder

    data = {}
    data['database'] = get_database_summary(QueryBuilder, statistics)
    data['repository'] = get_repository_info(statistics=statistics)

    echo.echo_dictionary(data, sort_keys=False, fmt='yaml')


@verdi_storage.command('maintain')
@click.option(
    '--full',
    is_flag=True,
    help='Perform all maintenance tasks, including the ones that should not be executed while the profile is in use.'
)
@click.option(
    '--dry-run',
    is_flag=True,
    help='Returns information that allows to estimate the impact of the maintenance operations.'
)
def storage_maintain(full, dry_run):
    """Performs maintenance tasks on the repository."""
    from aiida.backends.control import get_repository_report, repository_maintain

    if dry_run and full:
        echo.echo_critical('You cannot request both `--dry-run` and `--full` at the same time.')

    if dry_run:
        maintainance_report = {'repository': get_repository_report()}
        echo.echo('\nReport on storage maintainance status:\n')
        echo.echo_dictionary(maintainance_report, sort_keys=False, fmt='yaml')
        return

    if full:

        echo.echo_warning(
            '\nIn order to safely perform the full maintenance operations on the internal storage, no other '
            'process should be using the AiiDA profile being maintained. '
            'This includes daemon workers, verdi shells, scripts with the profile loaded, etc). '
            'Please make sure there is nothing like this currently running and that none is started until '
            'these procedures conclude. '
            'For performing maintanance operations that are safe to run while actively using AiiDA, just run '
            '`verdi storage maintain`, without the `--full` flag.\n'
        )

    else:

        echo.echo(
            '\nThis command will perform all maintenance operations on the internal storage that can be safely '
            'executed while still running AiiDA. '
            'However, not all operations that are required to fully optimize disk usage and future performance '
            'can be done in this way. '
            'Whenever you find the time or opportunity, please consider running `verdi repository maintenance '
            '--full` for a more complete optimization.\n'
        )

    if not click.confirm('Are you sure you want continue in this mode?'):
        return

    maintainance_report = repository_maintain(full=full)
    echo.echo('\nMaintainance procedures finished.')
    if len(maintainance_report) > 0:
        echo.echo('\nMaintainance report:\n')
        echo.echo_dictionary(maintainance_report, sort_keys=False, fmt='yaml')
