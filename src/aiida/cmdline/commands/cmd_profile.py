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
    broker: str = 'zmq',
    use_rabbitmq: bool | None = None,
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
    :param broker: Message broker backend ('rabbitmq', 'zmq', or 'none').
    :param use_rabbitmq: Deprecated. Use ``broker`` instead. ``--use-rabbitmq`` is equivalent to ``broker='rabbitmq'``
        and ``--no-use-rabbitmq`` to ``broker='none'``.
    :param kwargs: Arguments to initialise instance of the selected storage implementation.
    """
    # Handle deprecated --use-rabbitmq/--no-use-rabbitmq option
    if use_rabbitmq is not None:
        from aiida.common.warnings import warn_deprecation

        warn_deprecation('The `--use-rabbitmq` option is deprecated. Use `--broker` instead.', version=3)
        broker = 'rabbitmq' if use_rabbitmq else 'none'
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

    if broker == 'rabbitmq':
        from aiida.brokers.rabbitmq.defaults import detect_rabbitmq_config

        try:
            broker_config = detect_rabbitmq_config()
        except ConnectionError as exception:
            echo.echo_warning(f'RabbitMQ server not reachable: {exception}.')
        else:
            echo.echo_success(f'RabbitMQ server detected with connection parameters: {broker_config}')
            broker_backend = 'core.rabbitmq'

        echo.echo_report('The broker can be reconfigured later with `verdi profile set-broker`.')

    elif broker == 'zmq':
        broker_backend = 'core.zmq'
        broker_config = {}
        echo.echo_success('ZMQ broker configured (no external service required).')
        echo.echo_report('The ZMQ broker service will be started automatically with the daemon.')

    else:  # broker == 'none'
        echo.echo_report('Creating profile without a message broker.')
        echo.echo_report('A broker can be configured at a later point in time with `verdi profile set-broker`.')
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
        setup.SETUP_BROKER_BACKEND(),
        setup.SETUP_USE_RABBITMQ(),  # Deprecated, for backward compatibility
    ],
)
def profile_setup():
    """Set up a new profile."""


def _apply_broker_change(
    ctx: click.Context,
    profile: Profile,
    broker_backend: str | None,
    broker_config: dict | None,
    force: bool,
) -> None:
    """Apply a broker backend change to an existing profile.

    Refuses the change while the target profile still has active processes, as their tasks live in the current broker
    and would be stranded by the switch. If the daemon is running it is stopped before the change is applied, and
    restarted afterwards (unless the new backend is ``None``, in which case the daemon cannot run).

    :param ctx: The context of the CLI command.
    :param profile: The profile whose broker is being changed.
    :param broker_backend: Entry point name of the new broker (e.g. ``core.rabbitmq``), or ``None`` to remove it.
    :param broker_config: Connection configuration for the new broker, or ``None`` when there is none.
    :param force: If True, do not prompt before stopping and restarting a running daemon.
    """
    from aiida.engine.processes.control import get_active_processes
    from aiida.manage.configuration import profile_context

    # Inspect the target profile's own storage so the active-process check is correct even when it is not the
    # currently loaded profile.
    with profile_context(profile, allow_switch=True):
        active_processes = get_active_processes(project='id')

    if active_processes:
        echo.echo_critical(
            f'Cannot change the broker of profile `{profile.name}` while {len(active_processes)} process(es) are still '
            'active. Wait for them to finish or kill them with `verdi process kill`, then try again.'
        )

    daemon_client = None
    daemon_running = False

    # A daemon can only be running when the profile already has a broker configured.
    if profile.process_control_backend is not None:
        from aiida.engine.daemon.client import DaemonClient

        daemon_client = DaemonClient(profile)
        daemon_running = daemon_client.is_daemon_running

    if daemon_running and daemon_client is not None:
        echo.echo_warning('The daemon is running. It will be stopped to apply the broker change.')
        if not force:
            click.confirm('Do you want to stop the daemon and apply the change?', abort=True)
        daemon_client.stop_daemon(wait=True)

    profile.set_process_controller(name=broker_backend, config=broker_config or {})
    ctx.obj.config.update_profile(profile)
    ctx.obj.config.store()

    if daemon_running and daemon_client is not None:
        if broker_backend is None:
            echo.echo_report('The daemon was stopped; a profile without a broker cannot run a daemon.')
        else:
            echo.echo_report('Restarting the daemon...')
            daemon_client.start_daemon()
            echo.echo_success('Daemon restarted successfully.')


@verdi_profile.command('set-broker')
@click.argument('backend', type=click.Choice(['rabbitmq', 'zmq', 'none']))
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
def profile_set_broker(ctx, /, profile, backend, non_interactive, force, **kwargs):
    """Set the message broker for a profile.

    BACKEND selects which message broker the profile uses:

    \b
    * `rabbitmq`: use a RabbitMQ server (external service; connection details via the `--broker-*` options)
    * `zmq`: use the built-in ZMQ broker (no external service required)
    * `none`: remove the broker (the daemon cannot run and processes cannot be submitted)

    The broker cannot be changed while there are active processes. If the daemon is running, it is stopped while the
    change is applied and restarted afterwards.
    """
    if backend == 'rabbitmq':
        from aiida.brokers.rabbitmq.defaults import detect_rabbitmq_config

        connection_params = {
            key.removeprefix('broker_'): value for key, value in kwargs.items() if key.startswith('broker_')
        }
        try:
            broker_config = detect_rabbitmq_config(**connection_params)
        except ConnectionError as exception:
            echo.echo_warning(f'Unable to connect to RabbitMQ server: {exception}')
            if not force:
                click.confirm('Do you want to continue with the provided configuration?', abort=True)
            broker_config = {key: value for key, value in kwargs.items() if key.startswith('broker_')}
        else:
            echo.echo_success('Connected to RabbitMQ with the provided connection parameters')
        broker_backend = 'core.rabbitmq'
    elif backend == 'zmq':
        broker_backend = 'core.zmq'
        broker_config = {}
    else:  # backend == 'none'
        from aiida.common import docs

        broker_backend = None
        broker_config = None
        echo.echo_report(f'See {docs.URL_NO_BROKER} for details on the limitations of running without a broker.')

    _apply_broker_change(ctx, profile, broker_backend, broker_config, force)

    if broker_backend is None:
        echo.echo_success(f'Removed the broker for profile `{profile.name}`.')
    else:
        echo.echo_success(f'Broker for profile `{profile.name}` set to `{broker_backend}`.')


@verdi_profile.command('configure-rabbitmq', deprecated='Please use `verdi profile set-broker rabbitmq` instead.')
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
def profile_configure_rabbitmq(ctx, /, profile, non_interactive, force, **kwargs):
    """Configure RabbitMQ for a profile.

    Enable RabbitMQ for a profile that was created without a broker, or reconfigure existing connection details.
    """
    ctx.invoke(
        profile_set_broker,
        profile=profile,
        backend='rabbitmq',
        non_interactive=non_interactive,
        force=force,
        **kwargs,
    )


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
        'This is a new feature which is still in its testing phase.\n'
        'If you encounter unexpected behavior or bugs, please report them via:\n'
        '   Discourse: https://aiida.discourse.group\n'
        '   GitHub: https://github.com/aiidateam/aiida-core/issues'
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
