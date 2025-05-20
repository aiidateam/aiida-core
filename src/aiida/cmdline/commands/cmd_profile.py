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
@options.DUMP_PROCESSES()
@options.DUMP_DATA()
@options.ONLY_TOP_LEVEL_CALCS()
@options.ONLY_TOP_LEVEL_WORKFLOWS()
@options.DELETE_MISSING()
@options.SYMLINK_CALCS()
@options.ORGANIZE_BY_GROUPS()
@options.ALSO_UNGROUPED()
@options.UPDATE_GROUPS()
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
    dump_processes,
    dump_data,
    only_top_level_calcs,
    only_top_level_workflows,
    delete_missing,
    symlink_calcs,
    organize_by_groups,
    also_ungrouped,
    update_groups,
    include_inputs,
    include_outputs,
    include_attributes,
    include_extras,
    flat,
    dump_unsealed,
):
    """Dump all data in an AiiDA profile's storage to disk.

    If 'aiida_dump_config.yaml' exists in the target directory, it will be used
    as the sole source of configuration settings, ignoring other CLI flags.
    Otherwise, CLI flags will be used.
    """
    import traceback
    from pathlib import Path

    from pydantic import ValidationError

    from aiida.cmdline.utils import echo
    from aiida.tools.dumping import ProfileDumper
    from aiida.tools.dumping.config import DumpConfig, DumpMode, ProfileDumpSelection
    from aiida.tools.dumping.utils.paths import DumpPaths

    warning_msg = (
        'This is a new feature which is still in its testing phase. '
        'If you encounter unexpected behavior or bugs, please report them via Discourse or GitHub.'
    )
    echo.echo_warning(warning_msg)

    # --- Initial Setup ---
    profile = ctx.obj['profile']
    final_dump_config = None
    try:
        if path is None:
            profile_path = DumpPaths.get_default_dump_path(entity=profile)
            dump_base_output_path = Path.cwd() / profile_path
            echo.echo_report(f"No output path specified. Using default: '{dump_base_output_path}'")
        else:
            dump_base_output_path = Path(path).resolve()
            echo.echo_report(f"Using specified output path: '{dump_base_output_path}'")

        config_file_path = dump_base_output_path / DumpPaths.CONFIG_FILE_NAME

        if config_file_path.is_file():
            # --- Config File Exists: Load ONLY from file ---
            try:
                config_path_rel = config_file_path.relative_to(Path.cwd())
            except ValueError:
                config_path_rel = config_file_path
            echo.echo_report(f"Config file found at '{config_path_rel}'.")
            echo.echo_report('Using config file settings ONLY (ignoring other CLI flags).')
            try:
                # Validate and create config SOLELY from the file
                final_dump_config = DumpConfig.parse_yaml_file(config_file_path)
            except (ValidationError, FileNotFoundError, ValueError) as e:
                echo.echo_critical(f'Error loading or validating config file {config_file_path}: {e}')
                return
        else:
            # --- Config File Does NOT Exist: Use ONLY CLI args ---
            echo.echo_report('No config file found. Using command-line arguments.')
            try:
                # Gather all relevant CLI args here
                config_input_data = {
                    'dry_run': dry_run,
                    'overwrite': overwrite,
                    'all_entries': all_entries,
                    'groups': list(groups) if groups else [],
                    'past_days': past_days,
                    'start_date': start_date,
                    'end_date': end_date,
                    'user': user,
                    'codes': codes,
                    'computers': computers,
                    'filter_by_last_dump_time': filter_by_last_dump_time,
                    'dump_processes': dump_processes,
                    'dump_data': dump_data,
                    'only_top_level_calcs': only_top_level_calcs,
                    'only_top_level_workflows': only_top_level_workflows,
                    'delete_missing': delete_missing,
                    'symlink_calcs': symlink_calcs,
                    'organize_by_groups': organize_by_groups,
                    'also_ungrouped': also_ungrouped,
                    'update_groups': update_groups,
                    'include_inputs': include_inputs,
                    'include_outputs': include_outputs,
                    'include_attributes': include_attributes,
                    'include_extras': include_extras,
                    'flat': flat,
                    'dump_unsealed': dump_unsealed,
                }
                final_dump_config = DumpConfig.model_validate(config_input_data)
            except ValidationError as e:
                echo.echo_critical(f'Invalid command-line arguments provided:\n{e}')
                return

        # --- Check final determined scope ---
        if (
            final_dump_config.profile_dump_selection == ProfileDumpSelection.NONE
            and final_dump_config.dump_mode != DumpMode.DRY_RUN
        ):
            echo.echo_warning('No specific data selection determined from config file or CLI arguments.')
            msg = 'Please specify `--all` to dump all profile data or filters such as `groups`, `user` etc.'
            echo.echo_warning(msg)
            echo.echo_warning('Use `--help` for all options and `--dry-run` to preview.')

        # --- Other logical checks ---
        if not final_dump_config.organize_by_groups and final_dump_config.update_groups:
            echo.echo_warning('`update_groups` is True, but `organize_by_groups` is False.')
        if final_dump_config.dump_mode == DumpMode.DRY_RUN and overwrite:
            msg = (
                '`--dry-run` and `--overwrite` selected (or set in config). Overwrite operation will NOT be performed.'
            )
            echo.echo_warning(msg)

        # --- Instantiate and Run ProfileDumper ---
        profile_dumper = ProfileDumper(config=final_dump_config, output_path=dump_base_output_path)
        profile_dumper.dump()

        if (
            final_dump_config.dump_mode != DumpMode.DRY_RUN
            and final_dump_config.profile_dump_selection != ProfileDumpSelection.NONE
        ):
            msg = f'Raw files for profile `{profile.name}` dumped into folder `{dump_base_output_path.name}`.'
            echo.echo_success(msg)
        else:
            echo.echo_success('Dry run completed.')

    except Exception as e:
        msg = f'Unexpected error during dump of {profile.name}:\n ({e!s}).\n'
        echo.echo_critical(msg + traceback.format_exc())
