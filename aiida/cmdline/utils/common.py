# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Common utility functions for command line commands."""
# pylint: disable=import-error
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import sys

import click
from tabulate import tabulate


def get_env_with_venv_bin():
    """Create a clone of the current running environment with the AIIDA_PATH variable set directory of the config."""
    from aiida.manage.configuration import get_config

    config = get_config()

    currenv = os.environ.copy()
    currenv['PATH'] = os.path.dirname(sys.executable) + ':' + currenv['PATH']
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
    This function will also print a warning if the daemon is not running.

    :param process_type: optional process type for which to get the latest state change timestamp.
        Valid process types are either 'calculation' or 'work'.
    """
    from aiida.cmdline.utils.echo import echo_info, echo_warning
    from aiida.common import timezone
    from aiida.common.utils import str_timedelta
    from aiida.engine.daemon.client import get_daemon_client
    from aiida.engine.utils import get_process_state_change_timestamp

    client = get_daemon_client()

    timestamp = get_process_state_change_timestamp(process_type)

    if timestamp is None:
        echo_info('last time an entry changed state: never')
    else:
        timedelta = timezone.delta(timestamp, timezone.now())
        formatted = format_local_time(timestamp, format_str='at %H:%M:%S on %Y-%m-%d')
        relative = str_timedelta(timedelta, negative_to_zero=True, max_num_fields=1)
        echo_info('last time an entry changed state: {} ({})'.format(relative, formatted))

    if not client.is_daemon_running:
        echo_warning('the daemon is not running', bold=True)


def get_node_summary(node):
    """
    Return a multi line string with a pretty formatted summary of a Node

    :param node: a Node instance
    :return: a string summary of the node
    """
    from plumpy import ProcessState
    from aiida.orm import ProcessNode

    table_headers = ['Property', 'Value']
    table = []
    table.append(['type', node.__class__.__name__])
    table.append(['pk', str(node.pk)])
    table.append(['uuid', str(node.uuid)])
    table.append(['label', node.label])
    table.append(['description', node.description])
    table.append(['ctime', node.ctime])
    table.append(['mtime', node.mtime])

    if issubclass(node.__class__, ProcessNode):
        try:
            process_state = node.process_state
        except AttributeError:
            process_state = None

        try:
            table.append(['process state', ProcessState(process_state).value.capitalize()])
        except ValueError:
            table.append(['process state', process_state])

        try:
            table.append(['exit status', node.exit_status])
        except AttributeError:
            table.append(['exit status', None])

    try:
        computer = node.computer
    except AttributeError:
        pass
    else:
        if computer is not None:
            table.append(['computer', '[{}] {}'.format(node.computer.pk, node.computer.name)])

    return tabulate(table, headers=table_headers)


def get_node_info(node, include_summary=True):
    """Return a multi line string of information about the given node, such as the incoming and outcoming links.

    :param include_summary: boolean, if True, also include a summary of node properties
    :return: a string summary of the node including a description of all its links and log messages
    """
    from aiida.common.links import LinkType
    from aiida import orm

    if include_summary:
        result = get_node_summary(node)
    else:
        result = ''

    nodes_caller = node.get_incoming(link_type=(LinkType.CALL_CALC, LinkType.CALL_WORK))
    nodes_called = node.get_outgoing(link_type=(LinkType.CALL_CALC, LinkType.CALL_WORK))
    nodes_input = node.get_incoming(link_type=(LinkType.INPUT_CALC, LinkType.INPUT_WORK))
    nodes_output = node.get_outgoing(link_type=(LinkType.CREATE, LinkType.RETURN))

    if nodes_caller:
        result += '\n' + format_nested_links(nodes_caller.nested(), headers=['Called by', 'PK', 'Type'])

    if nodes_input:
        result += '\n' + format_nested_links(nodes_input.nested(), headers=['Inputs', 'PK', 'Type'])

    if nodes_output:
        result += '\n' + format_nested_links(nodes_output.nested(), headers=['Outputs', 'PK', 'Type'])

    if nodes_called:
        result += '\n' + format_nested_links(nodes_called.nested(), headers=['Called', 'PK', 'Type'])

    log_messages = orm.Log.objects.get_logs_for(node)

    if log_messages:
        table = []
        table_headers = ['Log messages']
        table.append(['There are {} log messages for this calculation'.format(len(log_messages))])
        table.append(["Run 'verdi process report {}' to see them".format(node.pk)])
        result += '\n\n{}'.format(tabulate(table, headers=table_headers))

    return result


def format_nested_links(links, headers):
    """Given a nested dictionary of nodes, return a nested string representation.

    :param links: a nested dictionary of nodes
    :param headers: headers to use
    :return: nested formatted string
    """
    import collections
    import tabulate as tb

    tb.PRESERVE_WHITESPACE = True

    indent_size = 4

    def format_recursive(links, depth=0):
        """Recursively format a dictionary of nodes into indented strings."""
        rows = []
        for label, value in links.items():
            if isinstance(value, collections.Mapping):
                rows.append([depth, label, '', ''])
                rows.extend(format_recursive(value, depth=depth + 1))
            else:
                rows.append([depth, label, value.pk, value.__class__.__name__])
        return rows

    table = []

    for depth, label, pk, class_name in format_recursive(links):
        table.append(['{indent}{label}'.format(indent=' ' * (depth * indent_size), label=label), pk, class_name])

    result = '\n{}'.format(tabulate(table, headers=headers))
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

    log_messages = orm.Log.objects.get_logs_for(calcjob)
    scheduler_out = calcjob.get_scheduler_stdout()
    scheduler_err = calcjob.get_scheduler_stderr()
    calcjob_state = calcjob.get_state()
    scheduler_state = calcjob.get_scheduler_state()

    report = []

    if calcjob_state == CalcJobState.WITHSCHEDULER:
        state_string = '{}, scheduler state: {}'.format(calcjob_state,
                                                        scheduler_state if scheduler_state else '(unknown)')
    else:
        state_string = '{}'.format(calcjob_state)

    label_string = ' [{}]'.format(calcjob.label) if calcjob.label else ''

    report.append('*** {}{}: {}'.format(calcjob.pk, label_string, state_string))

    if scheduler_out is None:
        report.append('*** Scheduler output: N/A')
    elif scheduler_out:
        report.append('*** Scheduler output:\n{}'.format(scheduler_out))
    else:
        report.append('*** (empty scheduler output file)')

    if scheduler_err is None:
        report.append('*** Scheduler errors: N/A')
    elif scheduler_err:
        report.append('*** Scheduler errors:\n{}'.format(scheduler_err))
    else:
        report.append('*** (empty scheduler errors file)')

    if log_messages:
        report.append('*** {} LOG MESSAGES:'.format(len(log_messages)))
    else:
        report.append('*** 0 LOG MESSAGES')

    for log in log_messages:
        report.append('+-> {} at {}'.format(log.levelname, log.time))
        for message in log.message.splitlines():
            report.append(' | {}'.format(message))

    return '\n'.join(report)


def get_process_function_report(node):
    """
    Return a multi line string representation of the log messages and output of a given process function node

    :param node: the node
    :return: a string representation of the log messages
    """
    from aiida import orm

    report = []

    for log in orm.Log.objects.get_logs_for(node):
        report.append('{time:%Y-%m-%d %H:%M:%S} [{id}]: {msg}'.format(id=log.id, msg=log.message, time=log.time))

    return '\n'.join(report)


def get_workchain_report(node, levelname, indent_size=4, max_depth=None):
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
        node_id = orm.load_node(uuid).id
        filters = {'dbnode_id': node_id}

        entries = orm.Log.objects.find(filters)
        entries = [entry for entry in entries if LOG_LEVELS[entry.levelname] >= LOG_LEVELS[levelname]]
        return [(_, depth) for _ in entries]

    def get_subtree(uuid, level=0):
        """
        Get a nested tree of work calculation nodes and their nesting level starting from this uuid.
        The result is a list of uuid of these nodes.
        """
        builder = orm.QueryBuilder()
        builder.append(cls=orm.WorkChainNode, filters={'uuid': uuid}, tag='workcalculation')
        builder.append(
            cls=orm.WorkChainNode,
            project=['uuid'],
            # In the future, we should specify here the type of link
            # for now, CALL links are the only ones allowing calc-calc
            # (we here really want instead to follow CALL links)
            with_incoming='workcalculation',
            tag='subworkchains')
        result = list(itertools.chain(*builder.distinct().all()))

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

    log_ids = [entry[0].id for entry in reports]
    levelnames = [len(entry[0].levelname) for entry in reports]
    width_id = len(str(max(log_ids)))
    width_levelname = max(levelnames)
    report = []

    for entry, depth in reports:
        line = '{time:%Y-%m-%d %H:%M:%S} [{id:<{width_id}} | {levelname:>{width_levelname}}]:{indent} {message}'.format(
            id=entry.id,
            levelname=entry.levelname,
            message=entry.message,
            time=entry.time,
            width_id=width_id,
            width_levelname=width_levelname,
            indent=' ' * (depth * indent_size))
        report.append(line)

    return '\n'.join(report)


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
            required = 'required' if port.required else 'optional'
            info = port.help if port.help is not None else ''
            info = info[:75] + ' ...' if len(info) > 75 else info
            result.append([name, required, valid_types, info])

        return result

    template = '{:>{width_name}s}:  {:10s}{:{width_type}}{}'
    inputs = build_entries(process_spec.inputs)
    outputs = build_entries(process_spec.outputs)
    max_width_name = max([len(entry[0]) for entry in inputs + outputs]) + 2
    max_width_type = max([len(entry[2]) for entry in inputs + outputs]) + 2

    if process_spec.inputs:
        click.secho('Inputs', fg='red', bold=True)
    for entry in inputs:
        if entry[1] == 'required':
            click.secho(template.format(*entry, width_name=max_width_name, width_type=max_width_type), bold=True)
        else:
            click.secho(template.format(*entry, width_name=max_width_name, width_type=max_width_type))

    if process_spec.outputs:
        click.secho('Outputs', fg='red', bold=True)
    for entry in outputs:
        if entry[1] == 'required':
            click.secho(template.format(*entry, width_name=max_width_name, width_type=max_width_type), bold=True)
        else:
            click.secho(template.format(*entry, width_name=max_width_name, width_type=max_width_type))

    if process_spec.exit_codes:
        click.secho('Exit codes', fg='red', bold=True)
    for exit_code in sorted(process_spec.exit_codes.values(), key=lambda exit_code: exit_code.status):
        message = exit_code.message.capitalize()
        click.secho('{:>{width_name}d}:  {}'.format(exit_code.status, message, width_name=max_width_name))


def get_num_workers():  #pylint: disable=inconsistent-return-statements
    """
    Get the number of active daemon workers from the circus client
    """
    from aiida.common.exceptions import CircusCallError
    from aiida.manage.manager import get_manager

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
        except KeyError:
            raise CircusCallError('Circus did not return the number of daemon processes')


def check_worker_load(active_slots):
    """
    Check if the percentage usage of the daemon worker slots exceeds a threshold.
    If it does, print a warning.

    The purpose of this check is to warn the user if they are close to running out of worker slots
    which could lead to their processes becoming stuck indefinitely.

    :param active_slots: the number of currently active worker slots
    """
    from aiida.common.exceptions import CircusCallError
    from aiida.cmdline.utils import echo
    from aiida.manage.external.rmq import _RMQ_TASK_PREFETCH_COUNT

    warning_threshold = 0.9  # 90%

    slots_per_worker = _RMQ_TASK_PREFETCH_COUNT

    try:
        active_workers = get_num_workers()
    except CircusCallError:
        echo.echo_critical("Could not contact Circus to get the number of active workers")

    if active_workers is not None:
        available_slots = active_workers * slots_per_worker
        percent_load = (active_slots / available_slots)
        if percent_load > warning_threshold:
            echo.echo('')  # New line
            echo.echo_warning("{:.0f}% of the available daemon worker slots have been used!".format(percent_load * 100))
            echo.echo_warning("Increase the number of workers with 'verdi daemon incr'.\n")
