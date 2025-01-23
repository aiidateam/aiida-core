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
from aiida.tools.dumping import CollectionDumper, DataDumper, ProcessDumper


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


# ? Specify groups via giving the groups, or just enabling "groups" and then all are dumped?
# ? Provide some mechanism to allow for both, e.g. if no argument is provided, all groups are dumped
@verdi_profile.command('mirror')
@options.PATH()
@options.OVERWRITE()
# @options.INCREMENTAL()
@options.DUMP_PROCESSES()
@options.DUMP_DATA()
@options.DEDUPLICATE()
@options.INCLUDE_INPUTS()
@options.INCLUDE_OUTPUTS()
@options.INCLUDE_ATTRIBUTES()
@options.INCLUDE_EXTRAS()
@options.FLAT()
@options.ALSO_RAW()
@options.ALSO_RICH()
@options.RICH_SPEC()
@options.RICH_DUMP_ALL()
@options.DUMP_CONFIG_FILE()
@options.NODES()
@options.GROUPS()
@options.ORGANIZE_BY_GROUPS()
@options.ONLY_TOP_LEVEL_WORKFLOWS()
@options.DRY_RUN()
@click.pass_context
def profile_mirror(
    ctx,
    path,
    overwrite,
    organize_by_groups,
    dry_run,
    dump_processes,
    only_top_level_workflows,
    dump_data,
    deduplicate,
    also_raw,
    also_rich,
    include_inputs,
    include_outputs,
    include_attributes,
    include_extras,
    flat,
    rich_spec,
    rich_dump_all,
    dump_config_file,
    nodes,
    groups,
):
    """Dump all data in an AiiDA profile's storage to disk."""

    from pathlib import Path

    from aiida import orm
    from aiida.tools.dumping.parser import DumpConfigParser
    from aiida.tools.dumping.rich import (
        DEFAULT_CORE_EXPORT_MAPPING,
        rich_from_cli,
        rich_from_config,
    )
    from aiida.tools.dumping.utils import prepare_dump_path

    profile = ctx.obj['profile']

    if nodes and groups:
        echo.echo_critical('`nodes` and `groups` specified. Set only one.')

    if dump_config_file is None:
        general_kwargs = {
            'path': path,
            'overwrite': overwrite,
            # 'incremental': incremental,
            'dry_run': dry_run,
        }

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
            'only_top_level_workflows': only_top_level_workflows,
            'organize_by_groups': organize_by_groups,
        }

        rich_kwargs = {
            'rich_dump_all': rich_dump_all,
        }

        if rich_spec is not None:
            rich_spec_dict = rich_from_cli(rich_spec=rich_spec, **rich_kwargs)
        else:
            rich_spec_dict = DEFAULT_CORE_EXPORT_MAPPING

    # TODO: Also allow for mixing. Currently one can _only_ specify either the config file, or the arguments on the
    # TODO: command line
    else:
        kwarg_dicts_from_config = DumpConfigParser.parse_config_file(dump_config_file)

        general_kwargs = kwarg_dicts_from_config['general_kwargs']
        processdumper_kwargs = kwarg_dicts_from_config['processdumper_kwargs']
        datadumper_kwargs = kwarg_dicts_from_config['datadumper_kwargs']
        collection_kwargs = kwarg_dicts_from_config['collection_kwargs']
        rich_kwargs = kwarg_dicts_from_config['rich_kwargs']

        rich_spec_dict = rich_from_config(kwarg_dicts_from_config['rich_spec'], **rich_kwargs)

    # Obtain these specifically for easy access and modifications
    path = general_kwargs['path']
    overwrite = general_kwargs['overwrite']
    dry_run = general_kwargs['dry_run']
    incremental = not overwrite

    if path is None:
        path = Path.cwd() / f'{profile.name}-mirror'

    # TODO: Implement proper dry-run feature
    dry_run_message = f"Dry run for dumping of profile `{profile.name}`'s data at path: `{path}`.\n"
    dry_run_message += 'Only directories will be created.'

    if dry_run or (not collection_kwargs['should_dump_processes'] and not collection_kwargs['should_dump_data']):
        echo.echo_report(dry_run_message)
        return

    else:
        echo.echo_report(f"Dumping of profile `{profile.name}`'s data at path: `{path}`.")

    SAFEGUARD_FILE = '.verdi_profile_mirror'  # noqa: N806

    try:
        prepare_dump_path(
            path_to_validate=path,
            overwrite=overwrite,
            incremental=incremental,
            safeguard_file=SAFEGUARD_FILE,
        )
    except FileExistsError as exc:
        echo.echo_critical(str(exc))

    (path / SAFEGUARD_FILE).touch()

    data_dumper = DataDumper(
        dump_parent_path=path,
        overwrite=overwrite,
        incremental=incremental,
        rich_spec_dict=rich_spec_dict,
        **datadumper_kwargs,
    )
    # dumper_pretty_print(data_dumper)

    process_dumper = ProcessDumper(
        dump_parent_path=path,
        overwrite=overwrite,
        incremental=incremental,
        data_dumper=data_dumper,
        **processdumper_kwargs,
    )
    # dumper_pretty_print(process_dumper)

    # TODO: Possibly implement specifying specific computers
    # TODO: Although, users could just specify the relevant nodes
    # TODO: Also add option to specify node types via entry points
    # TODO: Use `batch_iter` from aiida.tools.archive.common

    # === Dump the data that is not associated with any group ===
    if not groups:
        collection_dumper = CollectionDumper(
            dump_parent_path=path,
            overwrite=overwrite,
            incremental=incremental,
            nodes=nodes,
            **collection_kwargs,
            **rich_kwargs,
            data_dumper=data_dumper,
            process_dumper=process_dumper,
            deduplicate=deduplicate,
        )
        collection_dumper.create_entity_counter()
        # dumper_pretty_print(collection_dumper, include_private_and_dunder=False)

        if dump_processes and collection_dumper._should_dump_processes():
            echo.echo_report(f'Dumping processes not in any group for profile `{profile.name}`...')
            collection_dumper.dump_processes()

        if dump_data:
            if not also_rich and not also_raw:
                echo.echo_critical('`--dump-data was given, but neither --also-raw or --also-rich specified.')
            echo.echo_report(f'Dumping data not in any group for profile {profile.name}...')

            # collection_dumper.dump_data_rich()

    # === Dump data per-group if Groups exist in profile or are selected ===
    # TODO: Invert default behavior here, as I typically want to dump all entries
    # TODO: Possibly define a new click option instead
    # all_entries = not all_entries
    if not groups:  # and all_entries:
        groups = orm.QueryBuilder().append(orm.Group).all(flat=True)

    if groups:
        if not nodes:
            for group in groups:
                collection_dumper = CollectionDumper(
                    dump_parent_path=path,
                    overwrite=overwrite,
                    incremental=incremental,
                    group=group,
                    **collection_kwargs,
                    **rich_kwargs,
                    process_dumper=process_dumper,
                    data_dumper=data_dumper,
                    deduplicate=deduplicate,
                )

                collection_dumper.create_entity_counter()
                if dump_processes:
                    # The additional `_should_dump_processes` check here ensures that no reporting like
                    # "Dumping processes for group `SSSP/1.3/PBE/efficiency`" is printed for groups that
                    # don't contain processes
                    if collection_dumper._should_dump_processes():
                        echo.echo_report(f'Dumping processes for group `{group.label}`...')
                        collection_dumper.dump_processes()
                if dump_data:
                    echo.echo_report(f'Dumping data for group `{group.label}`...')
                    collection_dumper.dump_data_rich()
