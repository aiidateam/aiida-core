# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Common utility functions for command line commands."""
import logging
import os
import sys
import textwrap
from typing import TYPE_CHECKING

from click import style
from tabulate import tabulate

from . import echo

if TYPE_CHECKING:
    from aiida.orm import WorkChainNode

__all__ = ('is_verbose',)


def is_verbose():
    """Return whether the configured logging verbosity is considered verbose, i.e., equal or lower to ``INFO`` level.

    .. note:: This checks the effective logging level that is set on the ``CMDLINE_LOGGER``. This means that it will
        consider the logging level set on the parent ``AIIDA_LOGGER`` if not explicitly set on itself. The level of the
        main logger can be manipulated from the command line through the ``VERBOSITY`` option that is available for all
        commands.

    """
    return echo.CMDLINE_LOGGER.getEffectiveLevel() <= logging.INFO


def get_env_with_venv_bin():
    """Create a clone of the current running environment with the AIIDA_PATH variable set directory of the config."""
    from aiida.common.warnings import warn_deprecation
    from aiida.manage.configuration import get_config

    warn_deprecation(
        '`get_env_with_venv_bin` function is deprecated use `aiida.engine.daemon.client.DaemonClient.get_env` instead.',
        version=3
    )

    config = get_config()

    currenv = os.environ.copy()
    currenv['PATH'] = f"{os.path.dirname(sys.executable)}:{currenv['PATH']}"
    currenv['AIIDA_PATH'] = config.dirpath
    currenv['PYTHONUNBUFFERED'] = 'True'

    return currenv


def format_local_time(timestamp, format_str='%Y-%m-%d %H:%M:%S'):
    """
    Format a datetime object or UNIX timestamp in a human readable format

    :param timestamp: a datetime object or a float representing a UNIX timestamp
    :param format_str: optional string format to pass to strftime
    """
    from aiida.common import timezone

    if isinstance(timestamp, float):
        return timezone.datetime.fromtimestamp(timestamp).strftime(format_str)

    return timestamp.strftime(format_str)


def print_last_process_state_change(process_type=None):
    """
    Print the last time that a process of the specified type has changed its state.

    :param process_type: optional process type for which to get the latest state change timestamp.
        Valid process types are either 'calculation' or 'work'.
    """
    from aiida.cmdline.utils.echo import echo_report
    from aiida.common import timezone
    from aiida.common.utils import str_timedelta
    from aiida.engine.utils import get_process_state_change_timestamp

    timestamp = get_process_state_change_timestamp(process_type)

    if timestamp is None:
        echo_report('last time an entry changed state: never')
    else:
        timedelta = timezone.delta(timestamp)
        formatted = format_local_time(timestamp, format_str='at %H:%M:%S on %Y-%m-%d')
        relative = str_timedelta(timedelta, negative_to_zero=True, max_num_fields=1)
        echo_report(f'last time an entry changed state: {relative} ({formatted})')


def get_node_summary(node):
    """Return a multi line string with a pretty formatted summary of a Node.

    :param node: a Node instance
    :return: a string summary of the node
    """
    from plumpy import ProcessState

    from aiida.orm import ProcessNode

    table_headers = ['Property', 'Value']
    table = []

    if isinstance(node, ProcessNode):
        table.append(['type', node.process_label])

        try:
            process_state = ProcessState(node.process_state)
        except (AttributeError, ValueError):
            pass
        else:
            process_state_string = process_state.value.capitalize()

            if process_state == ProcessState.FINISHED and node.exit_message:
                table.append(['state', f'{process_state_string} [{node.exit_status}] {node.exit_message}'])
            elif process_state == ProcessState.FINISHED:
                table.append(['state', f'{process_state_string} [{node.exit_status}]'])
            elif process_state == ProcessState.EXCEPTED:
                table.append(['state', f'{process_state_string} <{node.exception}>'])
            else:
                table.append(['state', process_state_string])

    else:
        table.append(['type', node.__class__.__name__])

    table.append(['pk', str(node.pk)])
    table.append(['uuid', str(node.uuid)])
    table.append(['label', node.label])
    table.append(['description', node.description])
    table.append(['ctime', node.ctime])
    table.append(['mtime', node.mtime])

    try:
        computer = node.computer
    except AttributeError:
        pass
    else:
        if computer is not None:
            table.append(['computer', f'[{node.computer.pk}] {node.computer.label}'])

    return tabulate(table, headers=table_headers)


def get_node_info(node, include_summary=True):
    """Return a multi line string of information about the given node, such as the incoming and outcoming links.

    :param include_summary: boolean, if True, also include a summary of node properties
    :return: a string summary of the node including a description of all its links and log messages
    """
    from aiida import orm
    from aiida.common.links import LinkType

    if include_summary:
        result = get_node_summary(node)
    else:
        result = ''

    nodes_caller = node.base.links.get_incoming(link_type=(LinkType.CALL_CALC, LinkType.CALL_WORK))
    nodes_called = node.base.links.get_outgoing(link_type=(LinkType.CALL_CALC, LinkType.CALL_WORK))
    nodes_input = node.base.links.get_incoming(link_type=(LinkType.INPUT_CALC, LinkType.INPUT_WORK))
    nodes_output = node.base.links.get_outgoing(link_type=(LinkType.CREATE, LinkType.RETURN))

    if nodes_input:
        result += f"\n{format_nested_links(nodes_input.nested(), headers=['Inputs', 'PK', 'Type'])}"

    if nodes_output:
        result += f"\n{format_nested_links(nodes_output.nested(), headers=['Outputs', 'PK', 'Type'])}"

    if nodes_caller:
        links = sorted(nodes_caller.all(), key=lambda x: x.node.ctime)
        result += f"\n{format_flat_links(links, headers=['Caller', 'PK', 'Type'])}"

    if nodes_called:
        links = sorted(nodes_called.all(), key=lambda x: x.node.ctime)
        result += f"\n{format_flat_links(links, headers=['Called', 'PK', 'Type'])}"

    log_messages = orm.Log.collection.get_logs_for(node)

    if log_messages:
        table = []
        table_headers = ['Log messages']
        table.append([f'There are {len(log_messages)} log messages for this calculation'])
        table.append([f"Run 'verdi process report {node.pk}' to see them"])
        result += f'\n\n{tabulate(table, headers=table_headers)}'

    return result


def format_flat_links(links, headers):
    """Given a flat list of LinkTriples, return a flat string representation.

    :param links: a list of LinkTriples
    :param headers: headers to use
    :return: formatted string
    """
    table = []

    for link_triple in links:
        table.append([
            link_triple.link_label, link_triple.node.pk,
            link_triple.node.base.attributes.get('process_label', '')
        ])

    result = f'\n{tabulate(table, headers=headers)}'

    return result


def format_nested_links(links, headers):
    """Given a nested dictionary of nodes, return a nested string representation.

    :param links: a nested dictionary of nodes
    :param headers: headers to use
    :return: nested formatted string
    """
    from collections.abc import Mapping

    import tabulate as tb

    tb.PRESERVE_WHITESPACE = True

    indent_size = 4

    def format_recursive(links, depth=0):
        """Recursively format a dictionary of nodes into indented strings."""
        rows = []
        for label, value in links.items():
            if isinstance(value, Mapping):
                rows.append([depth, label, '', ''])
                rows.extend(format_recursive(value, depth=depth + 1))
            else:
                rows.append([depth, label, value.pk, value.__class__.__name__])
        return rows

    table = []

    for depth, label, pk, class_name in format_recursive(links):
        table.append([f"{' ' * (depth * indent_size)}{label}", pk, class_name])

    result = f'\n{tabulate(table, headers=headers)}'
    tb.PRESERVE_WHITESPACE = False

    return result


def get_calcjob_report(calcjob):
    """
    Return a multi line string representation of the log messages and output of a given calcjob

    :param calcjob: the calcjob node
    :return: a string representation of the log messages and scheduler output
    """
    from aiida import orm
    from aiida.common.datastructures import CalcJobState

    log_messages = orm.Log.collection.get_logs_for(calcjob)
    scheduler_out = calcjob.get_scheduler_stdout()
    scheduler_err = calcjob.get_scheduler_stderr()
    calcjob_state = calcjob.get_state()
    scheduler_state = calcjob.get_scheduler_state()

    report = []

    if calcjob_state == CalcJobState.WITHSCHEDULER:
        state_string = f"{calcjob_state}, scheduler state: {scheduler_state if scheduler_state else '(unknown)'}"
    else:
        state_string = f'{calcjob_state}'

    label_string = f' [{calcjob.label}]' if calcjob.label else ''

    report.append(f'*** {calcjob.pk}{label_string}: {state_string}')

    if scheduler_out is None:
        report.append('*** Scheduler output: N/A')
    elif scheduler_out:
        report.append(f'*** Scheduler output:\n{scheduler_out}')
    else:
        report.append('*** (empty scheduler output file)')

    if scheduler_err is None:
        report.append('*** Scheduler errors: N/A')
    elif scheduler_err:
        report.append(f'*** Scheduler errors:\n{scheduler_err}')
    else:
        report.append('*** (empty scheduler errors file)')

    if log_messages:
        report.append(f'*** {len(log_messages)} LOG MESSAGES:')
    else:
        report.append('*** 0 LOG MESSAGES')

    for log in log_messages:
        report.append(f'+-> {log.levelname} at {log.time}')
        for message in log.message.splitlines():
            report.append(f' | {message}')

    return '\n'.join(report)


def get_process_function_report(node):
    """
    Return a multi line string representation of the log messages and output of a given process function node

    :param node: the node
    :return: a string representation of the log messages
    """
    from aiida import orm

    report = []

    for log in orm.Log.collection.get_logs_for(node):
        report.append(f'{log.time:%Y-%m-%d %H:%M:%S} [{log.pk}]: {log.message}')

    return '\n'.join(report)


def get_workchain_report(node: 'WorkChainNode', levelname, indent_size=4, max_depth=None):
    """
    Return a multi line string representation of the log messages and output of a given workchain

    :param node: the workchain node
    :return: a nested string representation of the log messages
    """
    # pylint: disable=too-many-locals
    import itertools

    from aiida import orm
    from aiida.common.log import LOG_LEVELS

    def get_report_messages(uuid, depth, levelname):
        """Return list of log messages with given levelname and their depth for a node with a given uuid."""
        node_id = orm.load_node(uuid).pk
        filters = {'dbnode_id': node_id}

        entries = orm.Log.collection.find(filters)
        entries = [entry for entry in entries if LOG_LEVELS[entry.levelname] >= LOG_LEVELS[levelname]]
        return [(_, depth) for _ in entries]

    def get_subtree(uuid, level=0):
        """
        Get a nested tree of work calculation nodes and their nesting level starting from this uuid.
        The result is a list of uuid of these nodes.
        """
        builder = orm.QueryBuilder(backend=node.backend)
        builder.append(cls=orm.WorkChainNode, filters={'uuid': uuid}, tag='workcalculation')
        builder.append(
            cls=orm.WorkChainNode,
            project=['uuid'],
            # In the future, we should specify here the type of link
            # for now, CALL links are the only ones allowing calc-calc
            # (we here really want instead to follow CALL links)
            with_incoming='workcalculation',
            tag='subworkchains'
        )
        result = builder.all(flat=True)

        # This will return a single flat list of tuples, where the first element
        # corresponds to the WorkChain pk and the second element is an integer
        # that represents its level of nesting within the chain
        return [(uuid, level)] + list(itertools.chain(*[get_subtree(subuuid, level=level + 1) for subuuid in result]))

    workchain_tree = get_subtree(node.uuid)

    if max_depth:
        report_list = [
            get_report_messages(uuid, depth, levelname) for uuid, depth in workchain_tree if depth < max_depth
        ]
    else:
        report_list = [get_report_messages(uuid, depth, levelname) for uuid, depth in workchain_tree]

    reports = list(itertools.chain(*report_list))
    reports.sort(key=lambda r: r[0].time)

    if not reports:
        return 'No log messages recorded for this entry'

    log_ids = [entry[0].pk for entry in reports]
    levelnames = [len(entry[0].levelname) for entry in reports]
    width_id = len(str(max(log_ids)))
    width_levelname = max(levelnames)
    report = []

    for entry, depth in reports:
        line = '{time:%Y-%m-%d %H:%M:%S} [{id:<{width_id}} | {levelname:>{width_levelname}}]:{indent} {message}'.format(
            id=entry.pk,
            levelname=entry.levelname,
            message=entry.message,
            time=entry.time,
            width_id=width_id,
            width_levelname=width_levelname,
            indent=' ' * (depth * indent_size)
        )
        report.append(line)

    return '\n'.join(report)


def print_process_info(process):
    """Print detailed information about a process class and its process specification.

    :param process: a :py:class:`~aiida.engine.processes.process.Process` class
    """
    docstring = process.__doc__

    if docstring is None or docstring.strip() is None:
        docstring = 'No description available'

    echo.echo('Description:\n', fg=echo.COLORS['report'], bold=True)
    echo.echo(textwrap.indent('\n'.join(textwrap.wrap(docstring, 100)), '    '))
    print_process_spec(process.spec())


def print_process_spec(process_spec):
    """Print the process spec in a human-readable formatted way.

    :param process_spec: a `ProcessSpec` instance
    """

    def build_entries(ports):
        """Build a list of entries to be printed for a `PortNamespace.

        :param ports: the port namespace
        :return: list of tuples with port name, required, valid types and info strings
        """
        result = []

        for name, port in sorted(ports.items(), key=lambda x: (not x[1].required, x[0])):

            if name.startswith('_'):
                continue

            valid_types = port.valid_type if isinstance(port.valid_type, (list, tuple)) else (port.valid_type,)
            valid_types = ', '.join([valid_type.__name__ for valid_type in valid_types if valid_type is not None])
            info = textwrap.wrap(port.help if port.help is not None else '', width=75)
            result.append([name, port.required, valid_types, info])

        return result

    inputs = build_entries(process_spec.inputs)
    outputs = build_entries(process_spec.outputs)

    if process_spec.inputs:
        echo.echo('\nInputs:', fg=echo.COLORS['report'], bold=True)

    table = []

    for name, required, valid_types, info in inputs:
        table.append((style(name, bold=required, fg='red' if required else 'white'), valid_types, '\n'.join(info)))

    if table:
        echo.echo(tabulate(table, tablefmt='plain', colalign=('right',)))
        echo.echo(style('\nRequired inputs are displayed in bold red.\n', italic=True))

    if process_spec.outputs:
        echo.echo('Outputs:', fg=echo.COLORS['report'], bold=True)

    table = []

    for name, required, valid_types, info in outputs:
        table.append((style(name, bold=required, fg='red' if required else 'white'), valid_types, '\n'.join(info)))

    if table:
        echo.echo(tabulate(table, tablefmt='plain', colalign=('right',)))
        echo.echo(style('\nRequired outputs are displayed in bold red.\n', italic=True))

    if process_spec.exit_codes:
        echo.echo('Exit codes:\n', fg=echo.COLORS['report'], bold=True)

        table = [('0', 'The process finished successfully.')]

        for exit_code in sorted(process_spec.exit_codes.values(), key=lambda exit_code: exit_code.status):
            if exit_code.invalidates_cache:
                status = style(exit_code.status, bold=True, fg='red')
            else:
                status = exit_code.status
            table.append((status, '\n'.join(textwrap.wrap(exit_code.message, width=75))))

        echo.echo(tabulate(table, tablefmt='plain'))
        echo.echo(style('\nExit codes that invalidate the cache are marked in bold red.\n', italic=True))


def get_num_workers():
    """
    Get the number of active daemon workers from the circus client
    """
    from aiida.common.exceptions import CircusCallError
    from aiida.manage import get_manager

    manager = get_manager()
    client = manager.get_daemon_client()

    if client.is_daemon_running:
        response = client.get_numprocesses()
        if response['status'] != 'ok':
            if response['status'] == client.DAEMON_ERROR_TIMEOUT:
                raise CircusCallError('verdi thought the daemon was alive, but the call to the daemon timed-out')
            elif response['status'] == client.DAEMON_ERROR_NOT_RUNNING:
                raise CircusCallError('verdi thought the daemon was running, but really it is not')
            else:
                raise CircusCallError
        try:
            return response['numprocesses']
        except KeyError as exc:
            raise CircusCallError('Circus did not return the number of daemon processes') from exc


def check_worker_load(active_slots):
    """Log a message with information on the current daemon worker load.

    If there are daemon workers active, it logs the current load. If that exceeds 90%, a warning is included with the
    suggestion to run ``verdi daemon incr``.

    The purpose of this check is to warn the user if they are close to running out of worker slots which could lead to
    their processes becoming stuck indefinitely.

    :param active_slots: the number of currently active worker slots
    """
    from aiida.common.exceptions import CircusCallError
    from aiida.manage import get_config_option

    warning_threshold = 0.9  # 90%

    slots_per_worker = get_config_option('daemon.worker_process_slots')

    try:
        active_workers = get_num_workers()
    except CircusCallError:
        echo.echo_critical('Could not contact Circus to get the number of active workers.')

    if active_workers is not None:
        available_slots = active_workers * slots_per_worker
        percent_load = 1.0 if not available_slots else (active_slots / available_slots)
        if percent_load > warning_threshold:
            echo.echo('')  # New line
            echo.echo_warning(f'{percent_load * 100:.0f}%% of the available daemon worker slots have been used!')
            echo.echo_warning('Increase the number of workers with `verdi daemon incr`.')
        else:
            echo.echo_report(f'Using {percent_load * 100:.0f}%% of the available daemon worker slots.')
    else:
        echo.echo_report('No active daemon workers.')
