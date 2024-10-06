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
from pathlib import Path

import click
from click_spinner import spinner

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import options
from aiida.cmdline.utils import decorators, echo
from aiida.common import exceptions
from aiida.tools.dumping import CollectionDumper, DataDumper, ProcessDumper
from aiida.tools.dumping.utils import dumper_pretty_print


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
@decorators.with_dbenv()
@click.pass_context
def storage_maintain(ctx, full, no_repack, force, dry_run, compress):
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

    if STORAGE_LOGGER.level <= logging.REPORT:
        # Only keep the first tqdm bar if it is info. To keep the nested bar information one needs report level
        set_progress_bar_tqdm(leave=STORAGE_LOGGER.level <= logging.INFO)
    else:
        set_progress_reporter(None)

    try:
        if full and no_repack:
            storage.maintain(full=full, dry_run=dry_run, do_repack=False, compress=compress)
        else:
            storage.maintain(full=full, dry_run=dry_run, compress=compress)
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


# TODO: Follow API of `verdi archive create`
# ? Specify groups via giving the groups, or just enabling "groups" and then all are dumped?
# ? Provide some mechanism to allow for both, e.g. if no argument is provided, all groups are dumped
@verdi_storage.command('dump')
@options.PATH()
@options.ALL()
@options.NODES()
@options.CODES()
@options.COMPUTERS()
@options.GROUPS()
@options.OVERWRITE()
@options.ALSO_RAW()
@options.ALSO_RICH()
@options.INCLUDE_INPUTS()
@options.INCLUDE_OUTPUTS()
@options.INCLUDE_ATTRIBUTES()
@options.INCLUDE_EXTRAS()
@options.FLAT()
@options.DUMP_PROCESSES()
@options.DUMP_DATA()
@options.CALCULATIONS_HIDDEN()
@options.DATA_HIDDEN()
@options.ORGANIZE_BY_GROUPS()
@options.RICH_OPTIONS()
@options.RICH_CONFIG_FILE()
@options.RICH_DUMP_ALL()
@options.DRY_RUN()
def archive_dump(
    path,
    all_entries,
    overwrite,
    nodes,
    groups,
    codes,
    computers,
    also_raw,
    also_rich,
    include_inputs,
    include_outputs,
    include_attributes,
    include_extras,
    flat,
    dump_processes,
    dump_data,
    calculations_hidden,
    data_hidden,
    organize_by_groups,
    rich_options,
    rich_config_file,
    rich_dump_all,
    dry_run,
):
    """Dump all data in an AiiDA profile's storage to disk."""
    from aiida import orm
    from aiida.manage import get_manager
    from aiida.tools.dumping.collection import DEFAULT_ENTITIES_TO_DUMP
    from aiida.tools.dumping.rich import DEFAULT_CORE_EXPORT_MAPPING

    profile = get_manager().get_profile()
    SAFEGUARD_FILE = '.verdi_storage_dump'  # noqa: N806

    if not str(path).endswith(profile.name):
        path /= profile.name

    dry_run_message = f"Dry run for dumping of profile `{profile.name}`'s data at path: `{path}`.\n"
    dry_run_message += 'Only directories will be created.'

    if dry_run:
        dump_processes = False
        dump_data = False
        echo.echo_report(dry_run_message)

    elif not dump_processes and not dump_data:
        echo.echo_report(dry_run_message)

    else:
        echo.echo_report(f"Dumping of profile `{profile.name}`'s data at path: `{path}`.")

        from aiida.tools.dumping.utils import validate_make_dump_path

        try:
            validate_make_dump_path(
                overwrite=overwrite,
                path_to_validate=path,
                enforce_safeguard=True,
                safeguard_file=SAFEGUARD_FILE,
            )
        except FileExistsError as exc:
            echo.echo_critical(str(exc))

        (path / SAFEGUARD_FILE).touch()

    processdumper_kwargs = {
        'include_inputs': include_inputs,
        'include_outputs': include_outputs,
        'include_attributes': include_attributes,
        'include_extras': include_extras,
        'flat': flat,
    }

    datadumper_kwargs = {
        'also_raw': also_raw,
        'also_rich': also_rich,
    }

    collection_kwargs = {
        'should_dump_processes': dump_processes,
        'should_dump_data': dump_data,
        # 'calculations_hidden': calculations_hidden,
        # 'data_hidden': data_hidden,
        'organize_by_groups': organize_by_groups,
    }

    rich_kwargs = {
        'rich_options': rich_options,
        'rich_config_file': rich_config_file,
        'rich_dump_all': rich_dump_all,
    }

    # hiding_kwargs = {
    #     'calculations_hidden': calculations_hidden,
    #     'data_hidden': data_hidden
    # }

    data_dumper = DataDumper(
        dump_parent_path=path,
        overwrite=overwrite,
        data_hidden=data_hidden,
        rich_options_dict=DEFAULT_CORE_EXPORT_MAPPING,
        **datadumper_kwargs,
        **rich_kwargs,
    )

    process_dumper = ProcessDumper(
        dump_parent_path=path,
        overwrite=overwrite,
        data_dumper=data_dumper,
        calculations_hidden=calculations_hidden,
        **processdumper_kwargs,
        **datadumper_kwargs,
        **rich_kwargs,
    )

    if all_entries:
        entries_to_dump = None
        entities_to_dump = DEFAULT_ENTITIES_TO_DUMP

    else:
        entities_to_dump = set()
        if nodes:
            entries_to_dump['nodes'] = nodes
            entities_to_dump.extend({type(node) for node in nodes})

        if codes:
            entries_to_dump['codes'] = codes
            entities_to_dump.add(orm.Code)

        if computers:
            entries_to_dump['computers'] = computers
            entities_to_dump.add(orm.Computer)

        if groups:
            entries_to_dump['groups'] = groups
            entities_to_dump.add(orm.Group)

    collection_kwargs['entities_to_dump'] = entities_to_dump

    # === Dump the data that is not associated with any group ===

    collection_dumper = CollectionDumper(
        dump_parent_path=path,
        output_path=path / 'no_groups',
        calculations_hidden=calculations_hidden,
        data_hidden=data_hidden,
        **collection_kwargs,
        **rich_kwargs,
        data_dumper=data_dumper,
        process_dumper=process_dumper,
    )
    collection_dumper.create_entity_counter()
    # dumper_pretty_print(collection_dumper)

    
    
    if dump_processes:
        # if collection_dumper._should_dump_processes():
        if collection_dumper._should_dump_processes():
            echo.echo_report(f'Dumping processes not in any group for profile `{profile.name}`...')
            collection_dumper.dump_processes()
    if dump_data:
        if not also_rich and not also_raw:
            echo.echo_critical('`--dump-data was given, but neither --also-raw or --also-rich specified.')
        echo.echo_report(f'Dumping data not in any group for profile {profile.name}...')
        
        collection_dumper.dump_core_data_rich()
        # collection_dumper.dump_plugin_data()

    # === Dump data per-group if Groups exist in profile or are selected ===

    if groups is None:
        groups = orm.QueryBuilder().append(orm.Group).all(flat=True)

    if len(groups) > 0:
        for group in groups:
            # group_path = path / group.label
            group_subdir = Path(*group.type_string.split('.'))
            group_path = path / 'groups' / group_subdir / group.label

            collection_dumper = CollectionDumper(
                dump_parent_path=path,
                output_path=group_path,
                overwrite=overwrite,
                group=group,
                **processdumper_kwargs,
                **datadumper_kwargs,
                **collection_kwargs,
                **rich_kwargs,
                process_dumper=process_dumper,
                data_dumper=data_dumper,
            )
            collection_dumper.create_entity_counter()
            # group_dumper.pretty_print()

            if dump_processes:
                # The additional `_should_dump_processes` check here ensures that no reporting like
                # "Dumping processes for group `SSSP/1.3/PBE/efficiency`" is printed for groups that
                # don't contain processes
                if collection_dumper._should_dump_processes():
                    echo.echo_report(f'Dumping processes for group `{group.label}`...')
                    collection_dumper.dump_processes()
            if dump_data:
                echo.echo_report(f'Dumping data for group `{group.label}`...')
                collection_dumper.dump_core_data_rich()
                # collection_dumper.dump_plugin_data()
