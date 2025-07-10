###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi profile` command."""

from __future__ import annotations

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.groups import DynamicEntryPointCommandGroup
from aiida.cmdline.params import arguments, options
from aiida.cmdline.params.options.commands import setup
from aiida.cmdline.utils import defaults, echo
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.common import exceptions
from aiida.manage.configuration import Profile, create_profile, get_config


@verdi.group('profile')
def verdi_profile():
    """Inspect and manage the configured profiles."""


def command_create_profile(
    ctx: click.Context,
    storage_cls,
    profile: Profile,
    set_as_default: bool = True,
    email: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    institution: str | None = None,
    use_rabbitmq: bool = True,
    **kwargs,
):
    """Create a new profile, initialise its storage and create a default user.

    :param ctx: The context of the CLI command.
    :param storage_cls: The storage class obtained through loading the entry point from ``aiida.storage`` group.
    :param non_interactive: Whether the command was invoked interactively or not.
    :param profile: The profile instance. This is an empty ``Profile`` instance created by the command line argument
        which currently only contains the selected profile name for the profile that is to be created.
    :param set_as_default: Whether to set the created profile as the new default.
    :param email: Email for the default user.
    :param first_name: First name for the default user.
    :param last_name: Last name for the default user.
    :param institution: Institution for the default user.
    :param use_rabbitmq: Whether to configure RabbitMQ as the broker.
    :param kwargs: Arguments to initialise instance of the selected storage implementation.
    """
    from aiida.brokers.rabbitmq.defaults import detect_rabbitmq_config
    from aiida.common import docs
    from aiida.plugins.entry_point import get_entry_point_from_class

    if not storage_cls.read_only and email is None:
        raise click.BadParameter(
            'The option is required for storages that are not read-only.',
            param_hint='--email',
        )

    _, storage_entry_point = get_entry_point_from_class(storage_cls.__module__, storage_cls.__name__)
    assert storage_entry_point is not None

    broker_backend = None
    broker_config = None

    if use_rabbitmq:
        try:
            broker_config = detect_rabbitmq_config()
        except ConnectionError as exception:
            echo.echo_warning(f'RabbitMQ server not reachable: {exception}.')
        else:
            echo.echo_success(f'RabbitMQ server detected with connection parameters: {broker_config}')
            broker_backend = 'core.rabbitmq'

        echo.echo_report('RabbitMQ can be reconfigured with `verdi profile configure-rabbitmq`.')
    else:
        echo.echo_report('Creating profile without RabbitMQ.')
        echo.echo_report('It can be configured at a later point in time with `verdi profile configure-rabbitmq`.')
        echo.echo_report(f'See {docs.URL_NO_BROKER} for details on the limitations of running without a broker.')

    try:
        profile = create_profile(
            ctx.obj.config,
            name=profile.name,
            email=email,  # type: ignore[arg-type]
            first_name=first_name,
            last_name=last_name,
            institution=institution,
            storage_backend=storage_entry_point.name,
            storage_config=kwargs,
            broker_backend=broker_backend,
            broker_config=broker_config,
        )
    except (
        ValueError,
        TypeError,
        exceptions.EntryPointError,
        exceptions.StorageMigrationError,
    ) as exception:
        echo.echo_critical(str(exception))

    echo.echo_success(f'Created new profile `{profile.name}`.')

    if set_as_default:
        ctx.invoke(profile_set_default, profile=profile)


@verdi_profile.group(
    'setup',
    cls=DynamicEntryPointCommandGroup,
    command=command_create_profile,
    entry_point_group='aiida.storage',
    shared_options=[
        setup.SETUP_PROFILE_NAME(),
        setup.SETUP_PROFILE_SET_AS_DEFAULT(),
        setup.SETUP_USER_EMAIL(required=False),
        setup.SETUP_USER_FIRST_NAME(),
        setup.SETUP_USER_LAST_NAME(),
        setup.SETUP_USER_INSTITUTION(),
        setup.SETUP_USE_RABBITMQ(),
    ],
)
def profile_setup():
    """Set up a new profile."""


@verdi_profile.command('configure-rabbitmq')  # type: ignore[arg-type]
@arguments.PROFILE(default=defaults.get_default_profile)
@options.FORCE()
@setup.SETUP_BROKER_PROTOCOL()
@setup.SETUP_BROKER_USERNAME()
@setup.SETUP_BROKER_PASSWORD()
@setup.SETUP_BROKER_HOST()
@setup.SETUP_BROKER_PORT()
@setup.SETUP_BROKER_VIRTUAL_HOST()
@options.NON_INTERACTIVE(default=True, show_default='--non-interactive')
@click.pass_context
def profile_configure_rabbitmq(ctx, profile, non_interactive, force, **kwargs):
    """Configure RabbitMQ for a profile.

    Enable RabbitMQ for a profile that was created without a broker, or reconfigure existing connection details.
    """
    from aiida.brokers.rabbitmq.defaults import detect_rabbitmq_config

    broker_config = {key: value for key, value in kwargs.items() if key.startswith('broker_')}
    connection_params = {key.lstrip('broker_'): value for key, value in broker_config.items()}

    try:
        broker_config = detect_rabbitmq_config(**connection_params)
    except ConnectionError as exception:
        echo.echo_warning(f'Unable to connect to RabbitMQ server: {exception}')
        if not force:
            click.confirm('Do you want to continue with the provided configuration?', abort=True)
    else:
        echo.echo_success('Connected to RabbitMQ with the provided connection parameters')

    profile.set_process_controller(name='core.rabbitmq', config=broker_config)
    ctx.obj.config.update_profile(profile)
    ctx.obj.config.store()

    echo.echo_success(f'RabbitMQ configuration for `{profile.name}` updated to: {broker_config}')


@verdi_profile.command('list')
def profile_list():
    """Display a list of all available profiles."""
    try:
        config = get_config()
    except (
        exceptions.MissingConfigurationError,
        exceptions.ConfigurationError,
    ) as exception:
        # This can happen for a fresh install and the `verdi setup` has not yet been run. In this case it is still nice
        # to be able to see the configuration directory, for instance for those who have set `AIIDA_PATH`. This way
        # they can at least verify that it is correctly set.
        from aiida.manage.configuration.settings import AiiDAConfigDir

        echo.echo_report(f'configuration folder: {AiiDAConfigDir.get()}')
        echo.echo_critical(str(exception))
    else:
        echo.echo_report(f'configuration folder: {config.dirpath}')

    if not config.profiles:
        echo.echo_warning(
            'no profiles configured: Run `verdi presto` to automatically setup a profile using all defaults or use '
            '`verdi profile setup` for more control.'
        )
    else:
        sort = lambda profile: profile.name  # noqa: E731
        highlight = lambda profile: profile.name == config.default_profile_name  # noqa: E731
        echo.echo_formatted_list(config.profiles, ['name'], sort=sort, highlight=highlight)


def _strip_private_keys(dct: dict):
    """Remove private keys (starting `_`) from the dictionary."""
    return {
        key: _strip_private_keys(value) if isinstance(value, dict) else value
        for key, value in dct.items()
        if not key.startswith('_')
    }


@verdi_profile.command('show')
@arguments.PROFILE(default=defaults.get_default_profile)
def profile_show(profile):
    """Show details for a profile."""
    if profile is None:
        echo.echo_critical('no profile to show')

    echo.echo_report(f'Profile: {profile.name}')
    config = _strip_private_keys(profile.dictionary)
    echo.echo_dictionary(config, fmt='yaml')


@verdi_profile.command('setdefault', deprecated='Please use `verdi profile set-default` instead.')
@arguments.PROFILE(required=True, default=None)
def profile_setdefault(profile):
    """Set a profile as the default profile."""
    _profile_set_default(profile)


@verdi_profile.command('set-default')
@arguments.PROFILE(required=True, default=None)
def profile_set_default(profile):
    """Set a profile as the default profile."""
    _profile_set_default(profile)


def _profile_set_default(profile):
    try:
        config = get_config()
    except (
        exceptions.MissingConfigurationError,
        exceptions.ConfigurationError,
    ) as exception:
        echo.echo_critical(str(exception))

    config.set_default_profile(profile.name, overwrite=True).store()
    echo.echo_success(f'{profile.name} set as default profile')


@verdi_profile.command('delete')
@options.FORCE(help='Skip any prompts for confirmation.')
@click.option(
    '--delete-data/--keep-data',
    default=None,
    help='Whether to delete the storage with all its data or not. This flag has to be explicitly specified',
)
@arguments.PROFILES(required=True)
def profile_delete(force, delete_data, profiles):
    """Delete one or more profiles.

    The PROFILES argument takes one or multiple profile names that will be deleted. Deletion here means that the profile
    will be removed from the config file. If ``--delete-storage`` is specified, the storage containing all data is also
    deleted.
    """
    if force and delete_data is None:
        raise click.BadParameter(
            'When the `-f/--force` flag is used either `--delete-data` or `--keep-data` has to be explicitly specified.'
        )

    if not force and delete_data is None:
        echo.echo_warning('Do you also want to permanently delete all data?', nl=False)
        delete_data = click.confirm('', default=False)

    for profile in profiles:
        suffix = click.style('including' if delete_data else 'without', fg='red', bold=True)
        echo.echo_warning(f'Deleting profile `{profile.name}`, {suffix} all data.')

        if not force:
            echo.echo_warning(
                'This operation cannot be undone, are you sure you want to continue?',
                nl=False,
            )

        if not force and not click.confirm(''):
            echo.echo_report(f'Deleting of `{profile.name}` cancelled.')
            continue

        get_config().delete_profile(profile.name, delete_storage=delete_data)
        echo.echo_success(f'Profile `{profile.name}` was deleted.')


@verdi_profile.command('dump')
@options.PATH()
@options.DRY_RUN()
@options.OVERWRITE()
@options.ALL()
@options.CODES()
@options.COMPUTERS()
@options.GROUPS()
@options.USER()
@options.PAST_DAYS()
@options.START_DATE()
@options.END_DATE()
@options.FILTER_BY_LAST_DUMP_TIME()
@options.ONLY_TOP_LEVEL_CALCS()
@options.ONLY_TOP_LEVEL_WORKFLOWS()
@options.DELETE_MISSING()
@options.SYMLINK_CALCS()
@options.ORGANIZE_BY_GROUPS()
@options.ALSO_UNGROUPED()
@options.RELABEL_GROUPS()
@options.INCLUDE_INPUTS()
@options.INCLUDE_OUTPUTS()
@options.INCLUDE_ATTRIBUTES()
@options.INCLUDE_EXTRAS()
@options.FLAT()
@options.DUMP_UNSEALED()
@click.pass_context
@with_dbenv()
def profile_dump(
    ctx,
    path,
    dry_run,
    overwrite,
    all_entries,
    codes,
    computers,
    groups,
    user,
    past_days,
    start_date,
    end_date,
    filter_by_last_dump_time,
    only_top_level_calcs,
    only_top_level_workflows,
    delete_missing,
    symlink_calcs,
    organize_by_groups,
    also_ungrouped,
    relabel_groups,
    include_inputs,
    include_outputs,
    include_attributes,
    include_extras,
    flat,
    dump_unsealed,
):
    """Dump all data in an AiiDA profile's storage to disk."""

    import traceback
    from pathlib import Path

    from aiida.cmdline.utils import echo
    from aiida.tools._dumping.utils import DumpPaths

    warning_msg = (
        'This is a new feature which is still in its testing phase. '
        'If you encounter unexpected behavior or bugs, please report them via Discourse or GitHub.'
    )
    echo.echo_warning(warning_msg)

    # --- Initial Setup ---
    profile = ctx.obj['profile']
    try:
        if path is None:
            profile_path = DumpPaths.get_default_dump_path(entity=profile)
            dump_base_output_path = Path.cwd() / profile_path
            echo.echo_report(f"No output path specified. Using default: '{dump_base_output_path}'")
        else:
            dump_base_output_path = Path(path).resolve()
            echo.echo_report(f'Using specified output path: `{dump_base_output_path}`')

        # Logical checks
        if not organize_by_groups and relabel_groups:
            echo.echo_warning('`relabel_groups` is True, but `organize_by_groups` is False.')
            return
        if dry_run and overwrite:
            msg = (
                '`--dry-run` and `--overwrite` selected (or set in config). Overwrite operation will NOT be performed.'
            )
            echo.echo_warning(msg)
            return

        # Run the dumping
        _ = profile.dump(
            output_path=dump_base_output_path,
            dry_run=dry_run,
            overwrite=overwrite,
            all_entries=all_entries,
            groups=list(groups) if groups else None,
            user=user,
            computers=computers,
            codes=codes,
            past_days=past_days,
            start_date=start_date,
            end_date=end_date,
            filter_by_last_dump_time=filter_by_last_dump_time,
            only_top_level_calcs=only_top_level_calcs,
            only_top_level_workflows=only_top_level_workflows,
            delete_missing=delete_missing,
            symlink_calcs=symlink_calcs,
            organize_by_groups=organize_by_groups,
            also_ungrouped=also_ungrouped,
            relabel_groups=relabel_groups,
            include_inputs=include_inputs,
            include_outputs=include_outputs,
            include_attributes=include_attributes,
            include_extras=include_extras,
            flat=flat,
            dump_unsealed=dump_unsealed,
        )

        if not dry_run and (
            all_entries or bool(codes or computers or groups or past_days or start_date or end_date or user)
        ):
            msg = f'Raw files for profile `{profile.name}` dumped into folder `{dump_base_output_path.name}`.'
            echo.echo_success(msg)
        elif dry_run:
            echo.echo_success('Dry run completed.')

    except Exception as e:
        msg = f'Unexpected error during dump of {profile.name}:\n ({e!s}).\n'
        echo.echo_critical(msg + traceback.format_exc())


@verdi_profile.command('from-backup')
@click.argument('path', type=click.Path(), nargs=1)
def profile_from_backup(path):
    import shutil
    import sqlite3
    import subprocess
    from pathlib import Path

    from aiida.manage.configuration import create_profile
    from aiida.manage.configuration.config import Config

    def import_sqlite_database(backup_db_path, target_db_path):
        """Import data from backup SQLite database to target database using SQLite's backup API."""
        print('Importing database content...')

        # First, let's check if the target database is properly initialized
        target_conn = sqlite3.connect(str(target_db_path))

        # Check if the database has the alembic_version table (indicates proper initialization)
        cursor = target_conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'")
        has_alembic = cursor.fetchone() is not None
        target_conn.close()

        if not has_alembic:
            print('Warning: Target database appears uninitialized. Using direct backup method.')
            # If target is not initialized, just do a direct backup
            backup_conn = sqlite3.connect(str(backup_db_path))
            target_conn = sqlite3.connect(str(target_db_path))

            try:
                with target_conn:
                    backup_conn.backup(target_conn)
                print('Database content imported successfully')
            finally:
                backup_conn.close()
                target_conn.close()
        else:
            print('Target database is initialized. Importing data while preserving schema...')
            # Target is initialized, so we need to import data more carefully
            backup_conn = sqlite3.connect(str(backup_db_path))
            target_conn = sqlite3.connect(str(target_db_path))

            try:
                # Attach the backup database
                target_conn.execute(f"ATTACH '{backup_db_path}' AS backup_db")

                # Get list of tables from backup (excluding schema management tables)
                tables = backup_conn.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type='table'
                    AND name NOT IN ('alembic_version', 'sqlite_sequence')
                """).fetchall()

                for (table_name,) in tables:
                    # Clear existing data
                    target_conn.execute(f'DELETE FROM {table_name}')

                    # Copy data from backup
                    target_conn.execute(f'INSERT INTO {table_name} SELECT * FROM backup_db.{table_name}')

                target_conn.commit()
                print('Database content imported successfully')

            finally:
                backup_conn.close()
                target_conn.close()

    def restore_repository(backup_container_path, target_container_path):
        """Restore the disk-objectstore container from backup."""
        print('Restoring repository...')

        if not backup_container_path.exists():
            print('Warning: No container directory found in backup')
            return

        if target_container_path.exists():
            shutil.rmtree(target_container_path)

        # Use rsync for efficient copying
        try:
            subprocess.run(
                ['rsync', '-arvz', str(backup_container_path) + '/', str(target_container_path) + '/'], check=True
            )
            print('Repository restored successfully')
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to shutil if rsync is not available
            shutil.copytree(backup_container_path, target_container_path)
            print('Repository restored using fallback method')

        # Fix UUID mismatch between database and container
        print('Synchronizing container UUID with database...')
        try:
            from disk_objectstore import Container

            # Get the actual UUID from the restored container
            container = Container(target_container_path)
            actual_container_uuid = container.container_id

            # Update the database to match the container UUID
            target_db = target_container_path.parent / 'database.sqlite'
            conn = sqlite3.connect(str(target_db))
            try:
                # Update the repository UUID in the database
                conn.execute(
                    "UPDATE db_dbsetting SET val = ? WHERE key = 'repository|uuid'", (f'"{actual_container_uuid}"',)
                )
                conn.commit()
                print(f'Updated database repository UUID to: {actual_container_uuid}')
            finally:
                conn.close()

        except Exception as e:
            print(f'Warning: Could not sync container UUID: {e}')
            print("You may need to run 'verdi storage maintain' to fix UUID mismatch")

    # Load backup configuration
    backup_config = Config.from_file(Path(path) / 'config.json')
    current_config = get_config()
    backup_profile = backup_config.get_profile(name=next(iter(backup_config.dictionary['profiles'].keys())))

    print(f'Restoring backup from profile: {backup_profile.name}')

    # Create new profile with fresh storage
    new_profile_name = f'{backup_profile.name}-restored'

    restored_profile = create_profile(
        current_config,
        name=new_profile_name,
        email=backup_profile.default_user_email,
        storage_backend=backup_profile.storage_backend,
        storage_config={},  # Fresh, empty storage config
    )
    current_config.add_profile(restored_profile)
    current_config.store()

    print(f'Created new profile: {new_profile_name}')

    # Import database content
    backup_db = Path(path) / 'database.sqlite'
    target_db = Path(restored_profile.storage_config['filepath']) / 'database.sqlite'
    import_sqlite_database(backup_db, target_db)

    # Restore the repository
    backup_container_path = Path(path) / 'last-backup' / 'container'
    target_container_path = Path(restored_profile.storage_config['filepath']) / 'container'
    restore_repository(backup_container_path, target_container_path)

    print(f"Profile '{new_profile_name}' restored successfully!")
