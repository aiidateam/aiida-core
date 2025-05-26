###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi process` command."""

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import arguments, options, types
from aiida.cmdline.params.options.overridable import OverridableOption
from aiida.cmdline.utils import decorators, echo
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.common.log import LOG_LEVELS, capture_logging

REPAIR_INSTRUCTIONS = """\
If one ore more processes are unreachable, you can run the following commands to try and repair them:

    verdi daemon stop
    verdi process repair
    verdi daemon start
"""


def valid_projections():
    """Return list of valid projections for the ``--project`` option of ``verdi process list``.

    This indirection is necessary to prevent loading the imported module which slows down tab-completion.
    """
    from aiida.tools.query.calculation import CalculationQueryBuilder

    return CalculationQueryBuilder.valid_projections


def default_projections():
    """Return list of default projections for the ``--project`` option of ``verdi process list``.

    This indirection is necessary to prevent loading the imported module which slows down tab-completion.
    """
    from aiida.tools.query.calculation import CalculationQueryBuilder

    return CalculationQueryBuilder.default_projections


def get_most_recent_node():
    """Return the most recent process node.

    :returns: The ``ProcessNode`` with the latest ``ctime``.
    """
    from aiida.orm import ProcessNode, QueryBuilder

    process = QueryBuilder().append(ProcessNode, tag='n').order_by({'n': {'ctime': 'desc'}}).first(flat=True)
    echo.echo_info(f'Most recent node matched: `{process}`.')
    return process


@verdi.group('process')
def verdi_process():
    """Inspect and manage processes."""


@verdi_process.command('list')
@options.PROJECT(type=types.LazyChoice(valid_projections), default=lambda: default_projections())
@options.ORDER_BY()
@options.ORDER_DIRECTION()
@options.GROUP(help='Only include entries that are a member of this group.')
@options.ALL(help='Show all entries, regardless of their process state.')
@options.PROCESS_STATE()
@options.PROCESS_LABEL()
@options.PAUSED()
@options.EXIT_STATUS()
@options.FAILED()
@options.PAST_DAYS()
@options.LIMIT()
@options.RAW()
@click.pass_context
@decorators.with_dbenv()
def process_list(
    ctx,
    all_entries,
    group,
    process_state,
    process_label,
    paused,
    exit_status,
    failed,
    past_days,
    limit,
    project,
    raw,
    order_by,
    order_dir,
):
    """Show a list of processes.

    By default, only processes that are still running are shown, but there are options to show also the finished ones.
    """
    from tabulate import tabulate

    from aiida.cmdline.commands.cmd_daemon import execute_client_command
    from aiida.cmdline.utils.common import print_last_process_state_change
    from aiida.common.docs import URL_NO_BROKER
    from aiida.common.exceptions import ConfigurationError
    from aiida.engine.daemon.client import get_daemon_client
    from aiida.orm import ProcessNode, QueryBuilder
    from aiida.tools.query.calculation import CalculationQueryBuilder

    relationships = {}

    if group:
        relationships['with_node'] = group

    builder = CalculationQueryBuilder()
    filters = builder.get_filters(all_entries, process_state, process_label, paused, exit_status, failed)
    query_set = builder.get_query_set(
        relationships=relationships, filters=filters, order_by={order_by: order_dir}, past_days=past_days, limit=limit
    )
    projected = builder.get_projected(query_set, projections=project)
    headers = projected.pop(0)

    if raw:
        tabulated = tabulate(projected, tablefmt='plain')
        echo.echo(tabulated)
        return

    tabulated = tabulate(projected, headers=headers)
    echo.echo(tabulated)
    echo.echo(f'\nTotal results: {len(projected)}\n')

    if 'cached' in project:
        echo.echo_report('\u267b Processes marked with check-mark were not run but taken from the cache.')
        echo.echo_report('Add the option `-P pk cached_from` to the command to display cache source.')

    print_last_process_state_change()

    try:
        client = get_daemon_client()
    except ConfigurationError:
        echo.echo_warning(f'This profile does not have a broker and so it has no daemon. See {URL_NO_BROKER}')
        return

    if not client.is_daemon_running:
        echo.echo_warning('The daemon is not running', bold=True)
        return

    echo.echo_report('Checking daemon load... ', nl=False)
    response = execute_client_command('get_numprocesses')

    if not response:
        # Daemon could not be reached
        return

    try:
        active_workers = response['numprocesses']
    except KeyError:
        echo.echo_report('No active daemon workers.')
    else:
        # Second query to get active process count. Currently this is slow but will be fixed with issue #2770. It is
        # placed at the end of the command so that the user can Ctrl+C after getting the process table.
        slots_per_worker = ctx.obj.config.get_option('daemon.worker_process_slots', scope=ctx.obj.profile.name)
        active_processes = (
            QueryBuilder()
            .append(ProcessNode, filters={'attributes.process_state': {'in': ('created', 'waiting', 'running')}})
            .count()
        )
        available_slots = active_workers * slots_per_worker

        if active_workers == 0:
            echo.echo_warning('The daemon has no active workers!')
            echo.echo_warning('Increase the number of workers with `verdi daemon incr`.')
            return

        percent_load = active_processes / available_slots

        if percent_load > 0.9:  # 90%
            echo.echo_warning(f'{percent_load * 100:.0f}% of the available daemon worker slots have been used!')
            echo.echo_warning('Increase the number of workers with `verdi daemon incr`.')
        else:
            echo.echo_report(f'Using {percent_load * 100:.0f}% of the available daemon worker slots.')


@verdi_process.command('show')
@arguments.PROCESSES()
@options.MOST_RECENT_NODE()
@decorators.with_dbenv()
def process_show(processes, most_recent_node):
    """Show details of processes.

    Show details for one or multiple processes."""
    from aiida.cmdline.utils.common import get_node_info

    if not processes and not most_recent_node:
        raise click.UsageError(
            'Please specify one or multiple processes by their identifier (PK, UUID or label) or use an option.'
        )

    if processes and most_recent_node:
        raise click.BadOptionUsage(
            'most_recent_node',
            'cannot specify individual processes and the `-M/--most-recent-node` flag at the same time.',
        )

    if most_recent_node:
        processes = [get_most_recent_node()]

    for process in processes:
        echo.echo(get_node_info(process))


@verdi_process.command('call-root')
@arguments.PROCESSES()
@decorators.with_dbenv()
def process_call_root(processes):
    """Show root process of processes.

    Show root process(es) of the call stack for one or multiple processes."""
    if not processes:
        raise click.UsageError('Please specify one or multiple processes by their identifier (PK, UUID or label).')
    for process in processes:
        caller = process.caller

        if caller is None:
            echo.echo(f'No callers found for Process<{process.pk}>')
            continue

        while True:
            next_caller = caller.caller

            if next_caller is None:
                break

            caller = next_caller

        echo.echo(f'{caller.pk}')


@verdi_process.command('report')
@arguments.PROCESSES()
@options.MOST_RECENT_NODE()
@click.option('-i', '--indent-size', type=int, default=2, help='Set the number of spaces to indent each level by.')
@click.option(
    '-l',
    '--levelname',
    type=click.Choice(list(LOG_LEVELS)),
    default='REPORT',
    help='Filter the results by name of the log level.',
)
@click.option(
    '-m', '--max-depth', 'max_depth', type=int, default=None, help='Limit the number of levels to be printed.'
)
@decorators.with_dbenv()
def process_report(processes, most_recent_node, levelname, indent_size, max_depth):
    """Show the log report of processes.

    Show the log report for one or multiple processes."""
    from aiida.cmdline.utils.common import get_calcjob_report, get_process_function_report, get_workchain_report
    from aiida.orm import CalcFunctionNode, CalcJobNode, WorkChainNode, WorkFunctionNode

    if not processes and not most_recent_node:
        raise click.UsageError(
            'Please specify one or multiple processes by their identifier (PK, UUID or label) or use an option.'
        )

    if processes and most_recent_node:
        raise click.BadOptionUsage(
            'most_recent_node',
            'cannot specify individual processes and the `-M/--most-recent-node` flag at the same time.',
        )

    if most_recent_node:
        processes = [get_most_recent_node()]

    for process in processes:
        if isinstance(process, CalcJobNode):
            echo.echo(get_calcjob_report(process))
        elif isinstance(process, WorkChainNode):
            echo.echo(get_workchain_report(process, levelname, indent_size, max_depth))
        elif isinstance(process, (CalcFunctionNode, WorkFunctionNode)):
            echo.echo(get_process_function_report(process))
        else:
            echo.echo(f'Nothing to show for node type {process.__class__}')


@verdi_process.command('status')
@options.MOST_RECENT_NODE()
@click.option('-c', '--call-link-label', 'call_link_label', is_flag=True, help='Include the call link label if set.')
@click.option(
    '-m', '--max-depth', 'max_depth', type=int, default=None, help='Limit the number of levels to be printed.'
)
@arguments.PROCESSES()
def process_status(call_link_label, most_recent_node, max_depth, processes):
    """Show the status of processes.

    Show the status of one or multiple processes."""
    from aiida.cmdline.utils.ascii_vis import format_call_graph

    if not processes and not most_recent_node:
        raise click.UsageError(
            'Please specify one or multiple processes by their identifier (PK, UUID or label) or use an option.'
        )

    if processes and most_recent_node:
        raise click.BadOptionUsage(
            'most_recent_node',
            'cannot specify individual processes and the `-M/--most-recent-node` flag at the same time.',
        )

    if most_recent_node:
        processes = [get_most_recent_node()]

    for process in processes:
        graph = format_call_graph(process, max_depth=max_depth, call_link_label=call_link_label)
        echo.echo(graph)


@verdi_process.command('kill')
@arguments.PROCESSES()
@options.ALL(help='Kill all processes if no specific processes are specified.')
@OverridableOption(
    '-t',
    '--timeout',
    type=click.FLOAT,
    default=5.0,
    show_default=True,
    help='Time in seconds to wait for a response of the kill task before timing out.',
)()
@options.WAIT()
@OverridableOption(
    '-F',
    '--force-kill',
    is_flag=True,
    default=False,
    help='Kills the process without waiting for a confirmation if the job has been killed.\n'
    'Note: This may lead to orphaned jobs on your HPC and should be used with caution.',
)()
@decorators.with_dbenv()
def process_kill(processes, all_entries, timeout, wait, force_kill):
    """Kill running processes.

    Kill one or multiple running processes."""
    from aiida.engine.processes import control

    if not processes and not all_entries:
        raise click.UsageError(
            'Please specify one or multiple processes by their identifier (PK, UUID or label) or use an option.'
        )

    if processes and all_entries:
        raise click.BadOptionUsage('all', 'cannot specify individual processes and the `--all` flag at the same time.')

    if all_entries:
        click.confirm('Are you sure you want to kill all processes?', abort=True)

    if force_kill:
        echo.echo_warning('Force kill is enabled. This may lead to orphaned jobs on your HPC.')
        msg_text = 'Force killed through `verdi process kill`'
    else:
        msg_text = 'Killed through `verdi process kill`'
    with capture_logging() as stream:
        try:
            control.kill_processes(
                processes,
                msg_text=msg_text,
                force_kill=force_kill,
                all_entries=all_entries,
                timeout=timeout,
                wait=wait,
            )
        except control.ProcessTimeoutException as exception:
            echo.echo_critical(f'{exception}\n{REPAIR_INSTRUCTIONS}')

        if 'unreachable' in stream.getvalue():
            echo.echo_report(REPAIR_INSTRUCTIONS)


@verdi_process.command('pause')
@arguments.PROCESSES()
@options.ALL(help='Pause all active processes if no specific processes are specified.')
@options.TIMEOUT()
@options.WAIT()
@decorators.with_dbenv()
def process_pause(processes, all_entries, timeout, wait):
    """Pause running processes.

    Pause one or multiple running processes."""
    from aiida.engine.processes import control

    if not processes and not all_entries:
        raise click.UsageError(
            'Please specify one or multiple processes by their identifier (PK, UUID or label) or use an option.'
        )

    if processes and all_entries:
        raise click.BadOptionUsage('all', 'cannot specify individual processes and the `--all` flag at the same time.')

    with capture_logging() as stream:
        try:
            control.pause_processes(
                processes,
                msg_text='Paused through `verdi process pause`',
                all_entries=all_entries,
                timeout=timeout,
                wait=wait,
            )
        except control.ProcessTimeoutException as exception:
            echo.echo_critical(f'{exception}\n{REPAIR_INSTRUCTIONS}')

        if 'unreachable' in stream.getvalue():
            echo.echo_report(REPAIR_INSTRUCTIONS)


@verdi_process.command('play')
@arguments.PROCESSES()
@options.ALL(help='Play all paused processes if no specific processes are specified.')
@options.TIMEOUT()
@options.WAIT()
@decorators.with_dbenv()
def process_play(processes, all_entries, timeout, wait):
    """Play (unpause) paused processes.

    Play (unpause) one or multiple paused processes."""
    from aiida.engine.processes import control

    if not processes and not all_entries:
        raise click.UsageError(
            'Please specify one or multiple processes by their identifier (PK, UUID or label) or use an option.'
        )

    if processes and all_entries:
        raise click.BadOptionUsage('all', 'cannot specify individual processes and the `--all` flag at the same time.')

    with capture_logging() as stream:
        try:
            control.play_processes(processes, all_entries=all_entries, timeout=timeout, wait=wait)
        except control.ProcessTimeoutException as exception:
            echo.echo_critical(f'{exception}\n{REPAIR_INSTRUCTIONS}')

        if 'unreachable' in stream.getvalue():
            echo.echo_report(REPAIR_INSTRUCTIONS)


@verdi_process.command('watch')
@arguments.PROCESSES()
@options.MOST_RECENT_NODE()
@decorators.with_dbenv()
@decorators.with_broker
@decorators.only_if_daemon_running(echo.echo_warning, 'daemon is not running, so process may not be reachable')
def process_watch(broker, processes, most_recent_node):
    """Watch the state transitions of processes.

    Watch the state transitions for one or multiple running processes."""

    if not processes and not most_recent_node:
        raise click.UsageError(
            'Please specify one or multiple processes by their identifier (PK, UUID or label) or use an option.'
        )

    if processes and most_recent_node:
        raise click.BadOptionUsage(
            'most_recent_node',
            'cannot specify individual processes and the `-M/--most-recent-node` flag at the same time.',
        )

    from time import sleep

    from kiwipy import BroadcastFilter

    def _print(communicator, body, sender, subject, correlation_id):
        """Format the incoming broadcast data into a message and echo it to stdout."""
        if body is None:
            body = 'No message specified'

        if correlation_id is None:
            correlation_id = '--'

        echo.echo(f'Process<{sender}> [{subject}|{correlation_id}]: {body}')

    communicator = broker.get_communicator()
    echo.echo_report('watching for broadcasted messages, press CTRL+C to stop...')

    if most_recent_node:
        processes = [get_most_recent_node()]

    for process in processes:
        if process.is_terminated:
            echo.echo_error(f'Process<{process.pk}> is already terminated')
            continue

        communicator.add_broadcast_subscriber(BroadcastFilter(_print, sender=process.pk))

    try:
        # Block this thread indefinitely until interrupt
        while True:
            sleep(2)
    except (SystemExit, KeyboardInterrupt):
        echo.echo('')  # add a new line after the interrupt character
        echo.echo_report('received interrupt, exiting...')
        try:
            communicator.close()
        except RuntimeError:
            pass

        # Reraise to trigger clicks builtin abort sequence
        raise


@verdi_process.command('repair')
@options.DRY_RUN()
@decorators.only_if_daemon_not_running()
@decorators.with_manager
@decorators.with_broker
def process_repair(manager, broker, dry_run):
    """Automatically repair all stuck processes.

    N.B.: This command requires the daemon to be stopped.

    This command queries the database to find all "active" processes, meaning those that haven't yet reached a terminal
    state, and cross-references them with the active process tasks in the process queue of RabbitMQ. Any active process
    that does not have a corresponding process task can be considered a zombie, as it will never be picked up by a
    daemon worker to complete it and will effectively be "stuck". Any process task that does not correspond to an active
    process is useless and should be discarded. Finally, duplicate process tasks are also problematic and are discarded.
    """
    from aiida.engine.processes.control import get_active_processes, get_process_tasks, iterate_process_tasks

    active_processes = get_active_processes(project='id')
    process_tasks = get_process_tasks(broker)

    set_active_processes = set(active_processes)
    set_process_tasks = set(process_tasks)

    echo.echo_info(f'Active processes: {active_processes}')
    echo.echo_info(f'Process tasks: {process_tasks}')

    state_inconsistent = False

    if len(process_tasks) != len(set_process_tasks):
        state_inconsistent = True
        echo.echo_warning('There are duplicates process tasks: ', nl=False)
        echo.echo(set(x for x in process_tasks if process_tasks.count(x) > 1))

    if set_process_tasks.difference(set_active_processes):
        state_inconsistent = True
        echo.echo_warning('There are process tasks for terminated processes: ', nl=False)
        echo.echo(set_process_tasks.difference(set_active_processes))

    if set_active_processes.difference(set_process_tasks):
        state_inconsistent = True
        echo.echo_warning('There are active processes without process task: ', nl=False)
        echo.echo(set_active_processes.difference(set_process_tasks))

    if not state_inconsistent:
        echo.echo_success('No inconsistencies detected between database and RabbitMQ.')
        return

    echo.echo_warning('Inconsistencies detected between database and RabbitMQ.')

    if dry_run:
        echo.echo_critical('This was a dry-run, no changes will be made.')

    # At this point we have either exited because of inconsistencies and ``--dry-run`` was passed, or we returned
    # because there were no inconsistencies, so all that is left is to address inconsistencies
    echo.echo_report('Attempting to fix inconsistencies')

    # Eliminate duplicate tasks and tasks that correspond to terminated process
    for task in iterate_process_tasks(broker):
        pid = task.body.get('args', {}).get('pid', None)
        if pid not in set_active_processes:
            with task.processing() as outcome:
                outcome.set_result(False)
            echo.echo_report(f'Acknowledged task `{pid}`')

    # Revive zombie processes that no longer have a process task
    process_controller = manager.get_process_controller()
    for pid in set_active_processes:
        if pid not in set_process_tasks:
            process_controller.continue_process(pid)
            echo.echo_report(f'Revived process `{pid}`')


@verdi_process.command('dump')
@arguments.PROCESS()
@options.PATH()
@options.DRY_RUN()
@options.OVERWRITE()
@options.INCLUDE_INPUTS()
@options.INCLUDE_OUTPUTS()
@options.INCLUDE_ATTRIBUTES()
@options.INCLUDE_EXTRAS()
@options.FLAT()
@options.DUMP_UNSEALED()
@click.pass_context
@with_dbenv()
def process_dump(
    ctx,
    process,
    path,
    dry_run,
    overwrite,
    include_inputs,
    include_outputs,
    include_attributes,
    include_extras,
    flat,
    dump_unsealed,
) -> None:
    """Dump process input and output files to disk.

    Child calculations/workflows (also called `CalcJob`s/`CalcFunction`s and `WorkChain`s/`WorkFunction`s in AiiDA
    jargon) run by the parent workflow are contained in the directory tree as sub-folders and are sorted by their
    creation time. The directory tree thus mirrors the logical execution of the workflow, which can also be queried by
    running `verdi process status <pk>` on the command line.

    By default, input and output files of each calculation can be found in the corresponding "inputs" and
    "outputs" directories (the former also contains the hidden ".aiida" folder with machine-readable job execution
    settings). Additional input and output files (depending on the type of calculation) are placed in the "node_inputs"
    and "node_outputs", respectively.

    Lastly, every folder also contains a hidden, human-readable `aiida_node_metadata.yaml` file with the relevant AiiDA
    node data for further inspection.
    """
    import traceback
    from pathlib import Path

    from pydantic import ValidationError

    from aiida.cmdline.utils import echo
    from aiida.tools.archive.exceptions import ExportValidationError
    from aiida.tools.dumping.config import DumpConfig, DumpMode
    from aiida.tools.dumping.utils import DumpPaths

    warning_msg = (
        'This is a new feature which is still in its testing phase. '
        'If you encounter unexpected behavior or bugs, please report them via Discourse or GitHub.'
    )
    echo.echo_warning(warning_msg)

    # --- Initial Setup ---
    final_dump_config = None

    try:
        if path is None:
            process_path = DumpPaths.get_default_dump_path(process)
            dump_base_output_path = Path.cwd() / process_path
            msg = f'No output path specified. Using default: `{dump_base_output_path}`'
            echo.echo_report(msg)
        else:
            echo.echo_report(f"Using specified output path: '{path}'")
            dump_base_output_path = Path(path).resolve()

        try:
            # Gather relevant CLI args for group dump
            config_input_data = {
                'dry_run': dry_run,
                'overwrite': overwrite,
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

        # --- Logical Checks ---
        # Check for dry_run + overwrite based on final config
        if overwrite and dry_run:
            msg = 'Config specifies both `dry_run` and `overwrite` as True. Overwrite will NOT be performed.'
            echo.echo_warning(msg)

        # Execute dumping
        process.dump(config=final_dump_config, output_path=dump_base_output_path)

        if final_dump_config.dump_mode != DumpMode.DRY_RUN:
            msg = f'Raw files for process `{process.pk}` dumped into folder `{dump_base_output_path.name}`.'
            echo.echo_success(msg)
        else:
            echo.echo_success('Dry run completed.')

    except ExportValidationError as e:
        echo.echo_critical(f'Data validation error during dump: {e!s}')
    except Exception as e:
        msg = f'Unexpected error during dump of process {process.pk}:\n ({e!s}).\n'
        echo.echo_critical(msg + traceback.format_exc())
