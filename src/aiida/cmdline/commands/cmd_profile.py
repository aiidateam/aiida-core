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
from aiida.common import exceptions
from aiida.manage.configuration import Profile, create_profile, get_config


@verdi.group('profile')
def verdi_profile():
    """Inspect and manage the configured profiles."""


def command_create_profile(
    ctx: click.Context,
    storage_cls,
    non_interactive: bool,
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
        raise click.BadParameter('The option is required for storages that are not read-only.', param_hint='--email')

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
    except (ValueError, TypeError, exceptions.EntryPointError, exceptions.StorageMigrationError) as exception:
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
    except (exceptions.MissingConfigurationError, exceptions.ConfigurationError) as exception:
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
    except (exceptions.MissingConfigurationError, exceptions.ConfigurationError) as exception:
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
            echo.echo_warning('This operation cannot be undone, are you sure you want to continue?', nl=False)

        if not force and not click.confirm(''):
            echo.echo_report(f'Deleting of `{profile.name}` cancelled.')
            continue

        get_config().delete_profile(profile.name, delete_storage=delete_data)
        echo.echo_success(f'Profile `{profile.name}` was deleted.')


@verdi_profile.command('mirror')
@options.PATH()
@options.OVERWRITE()
# @options.INCREMENTAL()
@options.DUMP_PROCESSES()
@options.DEDUPLICATE()
@options.INCLUDE_INPUTS()
@options.INCLUDE_OUTPUTS()
@options.INCLUDE_ATTRIBUTES()
@options.INCLUDE_EXTRAS()
@options.FLAT()
@options.DUMP_CONFIG_FILE()
@options.GROUPS()
@options.ORGANIZE_BY_GROUPS()
@options.DRY_RUN()
@click.pass_context
def profile_mirror(
    ctx,
    path,
    overwrite,
    organize_by_groups,
    dry_run,
    dump_processes,
    deduplicate,
    include_inputs,
    include_outputs,
    include_attributes,
    include_extras,
    flat,
    dump_config_file,
    groups,
):
    """Dump all data in an AiiDA profile's storage to disk."""

    import json
    from datetime import datetime
    from pathlib import Path

    from aiida.tools.dumping import ProcessDumper, ProfileDumper
    from aiida.tools.dumping.base import BaseDumper
    from aiida.tools.dumping.logger import DumpLogger
    from aiida.tools.dumping.utils import prepare_dump_path

    profile = ctx.obj['profile']

    incremental = not overwrite

    if path is None:
        path = Path.cwd() / f'{profile.name}-mirror'

    echo.echo_report(f'Mirroring data of profile `{profile.name}`at path: `{path}`.')

    SAFEGUARD_FILE: str = '.verdi_profile_mirror'  # noqa: N806
    safeguard_file_path: Path = path / SAFEGUARD_FILE

    try:
        prepare_dump_path(
            path_to_validate=path,
            overwrite=overwrite,
            incremental=incremental,
            safeguard_file=SAFEGUARD_FILE,
        )
    except FileExistsError as exc:
        echo.echo_critical(str(exc))

    breakpoint()

    try:
        with safeguard_file_path.open('r') as fhandle:
            last_dump_time = datetime.fromisoformat(fhandle.readlines()[-1].strip().split()[-1]).astimezone()
    except IndexError:
        last_dump_time = None

    if dry_run:
        node_counts = ProfileDumper._get_number_of_nodes_to_dump(last_dump_time)
        node_counts_str = ' & '.join(f'{count} {node_type}' for node_type, count in node_counts.items())
        dry_run_message = f'Dry run for mirroring of profile `{profile.name}`: {node_counts_str} to dump.\n'
        echo.echo_report(dry_run_message)
        return

    if incremental:
        msg = 'Incremental mirroring selected. Will update directory.'
        echo.echo_report(msg)

    try:
        dump_logger = DumpLogger.from_file(dump_parent_path=path)
    except (json.JSONDecodeError, OSError):
        dump_logger = DumpLogger(dump_parent_path=path)

    base_dumper = BaseDumper(
        dump_parent_path=path,
        overwrite=overwrite,
        incremental=incremental,
        last_dump_time=last_dump_time,
    )

    process_dumper = ProcessDumper(
        base_dumper=base_dumper,
        include_inputs=include_inputs,
        include_outputs=include_outputs,
        include_attributes=include_attributes,
        include_extras=include_extras,
        flat=flat,
    )

    profile_dumper = ProfileDumper(
        base_dumper=base_dumper,
        process_dumper=process_dumper,
        dump_logger=dump_logger,
        groups=groups,
        organize_by_groups=organize_by_groups,
        deduplicate=deduplicate,
        profile=profile,
        dump_processes=dump_processes,
    )

    profile_dumper.dump()

    # Append the current time to the file
    last_dump_time = datetime.now().astimezone()
    with safeguard_file_path.open('a') as fhandle:
        fhandle.write(f'Last profile mirror time: {last_dump_time.isoformat()}\n')

    # Write the logging json file to disk
    dump_logger.save_log()

    echo.echo_success(f'Dumped {dump_logger.counter} new nodes.')
