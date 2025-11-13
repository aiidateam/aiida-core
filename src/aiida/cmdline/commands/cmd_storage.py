###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi storage` commands."""

import logging
import sys

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
    """Print the current version of the storage schema.

    The command returns the following exit codes:

    * 0: If the storage schema is equal and compatible to the schema version of the code
    * 3: If the storage cannot be reached or is corrupt
    * 4: If the storage schema is compatible with the code schema version and probably needs to be migrated.
    """
    from aiida import get_profile
    from aiida.common.exceptions import CorruptStorage, IncompatibleStorageSchema, UnreachableStorage

    try:
        profile = get_profile()
        if profile is None:
            echo.echo_critical('Could not load default profile')
        head_version = profile.storage_cls.version_head()
        profile_version = profile.storage_cls.version_profile(profile)
        echo.echo(f'Latest storage schema version: {head_version!r}')
        echo.echo(f'Storage schema version of {profile.name!r}: {profile_version!r}')
    except Exception as exception:
        echo.echo_critical(f'Failed to determine the storage version: {exception}')

    try:
        profile.storage_cls(profile)
    except (CorruptStorage, UnreachableStorage) as exception:
        echo.echo_error(f'The storage cannot be reached or is corrupt: {exception}')
        sys.exit(3)
    except IncompatibleStorageSchema:
        echo.echo_error(
            f'The storage schema version {profile_version} is incompatible with the code version {head_version}.'
            'Run `verdi storage migrate` to migrate the storage.'
        )
        sys.exit(4)


@verdi_storage.command('migrate')
@options.FORCE()
def storage_migrate(force):
    """Migrate the storage to the latest schema version."""
    from aiida.engine.daemon.client import get_daemon_client
    from aiida.manage import get_manager

    manager = get_manager()
    profile = manager.get_profile()
    if profile is None:
        echo.echo_critical('Could not load default profile')

    if profile.process_control_backend:
        client = get_daemon_client()
        if client.is_daemon_running:
            echo.echo_critical('Migration aborted, the daemon for the profile is still running.')

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
    help='Perform all maintenance tasks, including the ones that should not be executed while the profile is in use.',
)
@click.option(
    '--no-repack', is_flag=True, help='Disable the repacking of the storage when running a `full maintenance`.'
)
@options.FORCE()
@click.option(
    '--dry-run',
    is_flag=True,
    help='Run the maintenance in dry-run mode to print actions that would be taken without actually executing them.',
)
@click.option(
    '--compress', is_flag=True, default=False, help='Use compression if possible when carrying out maintenance tasks.'
)
@click.option(
    '--clean-loose-per-pack/--no-clean-loose-per-pack',
    is_flag=True,
    default=True,
    help='Delete corresponding loose files immediately after each pack creation when running a `full maintenance`.',
)
@decorators.with_dbenv()
@click.pass_context
def storage_maintain(ctx, full, no_repack, force, dry_run, compress, clean_loose_per_pack):
    """Performs maintenance tasks on the repository."""
    from aiida.common.exceptions import LockingProfileError
    from aiida.common.progress_reporter import set_progress_bar_tqdm, set_progress_reporter
    from aiida.manage.manager import get_manager
    from aiida.storage.log import STORAGE_LOGGER

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

    if not dry_run and not force and not click.confirm('Are you sure you want continue in this mode?'):
        return

    if STORAGE_LOGGER.level <= logging.REPORT:  # type: ignore[attr-defined]
        # Only keep the first tqdm bar if it is info. To keep the nested bar information one needs report level
        set_progress_bar_tqdm(leave=STORAGE_LOGGER.level <= logging.INFO)
    else:
        set_progress_reporter(None)

    try:
        if full and no_repack:
            storage.maintain(
                full=full,
                dry_run=dry_run,
                do_repack=False,
                compress=compress,
                clean_loose_per_pack=clean_loose_per_pack,
            )
        else:
            storage.maintain(full=full, dry_run=dry_run, compress=compress, clean_loose_per_pack=clean_loose_per_pack)
    except LockingProfileError as exception:
        echo.echo_critical(str(exception))
    echo.echo_success('Requested maintenance procedures finished.')


@verdi_storage.command('backup')
@click.argument('dest', type=click.Path(file_okay=False), nargs=1)
@click.option(
    '--keep',
    type=int,
    required=False,
    help=(
        'Number of previous backups to keep in the destination, '
        'if the storage backend supports it. If not set, keeps all previous backups.'
    ),
)
@decorators.with_manager
@click.pass_context
def storage_backup(ctx, manager, dest: str, keep: int):
    """Backup the data storage of a profile.

    The backup is created in the destination `DEST`, in a subfolder that follows the naming convention
    backup_<timestamp>_<randstr> and a symlink called `last-backup` is pointed to it.

    Destination (DEST) can either be a local path, or a remote destination (reachable via ssh).
    In the latter case, remote destination needs to have the following syntax:

        [<remote_user>@]<remote_host>:<path>

    i.e., contain the remote host name and the remote path, separated by a colon (and optionally the
    remote user separated by an @ symbol). You can tune SSH parameters using the standard options given
    by OpenSSH, such as adding configuration options to ~/.ssh/config (e.g. to allow for passwordless
    login - recommended, since this script might ask multiple times for the password).

    NOTE: 'rsync' and other UNIX-specific commands are called, thus the command will not work on
    non-UNIX environments. What other executables are called, depend on the storage backend.
    """

    storage = manager.get_profile_storage()
    profile = ctx.obj.profile
    try:
        storage.backup(dest, keep)
    except NotImplementedError:
        echo.echo_critical(
            f'Profile {profile.name} uses the storage plugin `{profile.storage_backend}` which does not implement a '
            'backup mechanism.'
        )
    except (ValueError, exceptions.StorageBackupError) as exception:
        echo.echo_critical(str(exception))
    echo.echo_success(f'Data storage of profile `{profile.name}` backed up to `{dest}`.')
