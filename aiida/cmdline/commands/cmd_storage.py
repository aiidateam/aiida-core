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
from click_spinner import spinner

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import options
from aiida.cmdline.utils import decorators, echo
from aiida.common import exceptions


@verdi.group('storage')
def verdi_storage():
    """Inspect and manage stored data for a profile."""


@verdi_storage.command('version')
def storage_version():
    """Print the current version of the storage schema."""
    from aiida import get_profile
    profile = get_profile()
    head_version = profile.storage_cls.version_head()
    profile_version = profile.storage_cls.version_profile(profile)
    echo.echo(f'Latest storage schema version: {head_version!r}')
    echo.echo(f'Storage schema version of {profile.name!r}: {profile_version!r}')


@verdi_storage.command('migrate')
@options.FORCE()
def storage_migrate(force):
    """Migrate the storage to the latest schema version."""
    from aiida.engine.daemon.client import get_daemon_client
    from aiida.manage import get_manager

    client = get_daemon_client()
    if client.is_daemon_running:
        echo.echo_critical('Migration aborted, the daemon for the profile is still running.')

    manager = get_manager()
    profile = manager.get_profile()
    storage_cls = profile.storage_cls

    if not force:

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
            return

    try:
        storage_cls.migrate(profile)
    except (exceptions.ConfigurationError, exceptions.StorageMigrationError) as exception:
        echo.echo_critical(str(exception))
    else:
        echo.echo_success('migration completed')


@verdi_storage.group('integrity')
def storage_integrity():
    """Checks for the integrity of the data storage."""


@verdi_storage.command('info')
@click.option('--detailed', is_flag=True, help='Provides more detailed information.')
@decorators.with_dbenv()
def storage_info(detailed):
    """Summarise the contents of the storage."""
    from aiida.manage.manager import get_manager

    manager = get_manager()
    storage = manager.get_profile_storage()

    with spinner():
        data = storage.get_info(detailed=detailed)

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
    help=
    'Run the maintenance in dry-run mode which will print actions that would be taken without actually executing them.'
)
@decorators.with_dbenv()
@click.pass_context
def storage_maintain(ctx, full, dry_run):
    """Performs maintenance tasks on the repository."""
    from aiida.common.exceptions import LockingProfileError
    from aiida.manage.manager import get_manager

    manager = get_manager()
    profile = ctx.obj.profile
    storage = manager.get_profile_storage()

    if full:
        echo.echo_warning(
            '\nIn order to safely perform the full maintenance operations on the internal storage, the profile '
            f'{profile.name} needs to be locked. '
            'This means that no other process will be able to access it and will fail instead. '
            'Moreover, if any process is already using the profile, the locking attempt will fail and you will '
            'have to either look for these processes and kill them or wait for them to stop by themselves. '
            'Note that this includes verdi shells, daemon workers, scripts that manually load it, etc.\n'
            'For performing maintenance operations that are safe to run while actively using AiiDA, just run '
            '`verdi storage maintain` without the `--full` flag.\n'
        )

    else:
        echo.echo_report(
            '\nThis command will perform all maintenance operations on the internal storage that can be safely '
            'executed while still running AiiDA. '
            'However, not all operations that are required to fully optimize disk usage and future performance '
            'can be done in this way.\n'
            'Whenever you find the time or opportunity, please consider running `verdi storage maintain --full` '
            'for a more complete optimization.\n'
        )

    if not dry_run:
        if not click.confirm('Are you sure you want continue in this mode?'):
            return

    try:
        storage.maintain(full=full, dry_run=dry_run)
    except LockingProfileError as exception:
        echo.echo_critical(str(exception))
    echo.echo_success('Requested maintenance procedures finished.')
