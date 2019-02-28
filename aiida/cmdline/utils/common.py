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
    from aiida.orm import Code, ProcessNode

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
            table.append(['process state', ProcessState(process_state)])
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

    try:
        code = node.get_incoming(node_class=Code).first()
    except ValueError:
        pass
    else:
        table.append(['code', code.node.label])

    return tabulate(table, headers=table_headers)


def get_node_info(node, include_summary=True):
    # pylint: disable=too-many-branches
    """
    Return a multi line string of information about the given node, such as the incoming and outcoming links

    :param include_summary: also include a summary of node properties
    :return: a string summary of the node including a description of all its links and log messages
    """
    from aiida.common.links import LinkType
    from aiida import orm

    if include_summary:
        result = get_node_summary(node)
    else:
        result = ''

    nodes_input_calc = node.get_incoming(link_type=LinkType.INPUT_CALC).all()
    nodes_input_work = node.get_incoming(link_type=LinkType.INPUT_WORK).all()
    nodes_caller = node.get_incoming(link_type=(LinkType.CALL_CALC, LinkType.CALL_WORK)).all()
    nodes_create = node.get_outgoing(link_type=LinkType.CREATE).all()
    nodes_return = node.get_outgoing(link_type=LinkType.RETURN).all()
    nodes_called = node.get_outgoing(link_type=(LinkType.CALL_CALC, LinkType.CALL_WORK)).all()
    nodes_input = nodes_input_calc + nodes_input_work
    nodes_output = nodes_create + nodes_return

    if nodes_caller:
        table = []
        table_headers = ['Called by', 'PK', 'Type']
        for entry in nodes_caller:
            table.append([entry.link_label, entry.node.pk, entry.node.__class__.__name__])
        result += '\n{}'.format(tabulate(table, headers=table_headers))

    if nodes_input:
        table = []
        table_headers = ['Inputs', 'PK', 'Type']
        for entry in nodes_input:
            if entry.link_label == 'code':
                continue
            table.append([entry.link_label, entry.node.pk, entry.node.__class__.__name__])
        result += '\n{}'.format(tabulate(table, headers=table_headers))

    if nodes_output:
        table = []
        table_headers = ['Outputs', 'PK', 'Type']
        for entry in nodes_output:
            table.append([entry.link_label, entry.node.pk, entry.node.__class__.__name__])
        result += '\n{}'.format(tabulate(table, headers=table_headers))

    if nodes_called:
        table = []
        table_headers = ['Called', 'PK', 'Type']
        for entry in nodes_called:
            table.append([entry.link_label, entry.node.pk, entry.node.__class__.__name__])
        result += '\n{}'.format(tabulate(table, headers=table_headers))

    log_messages = orm.Log.objects.get_logs_for(node)

    if log_messages:
        table = []
        table_headers = ['Log messages']
        table.append(['There are {} log messages for this calculation'.format(len(log_messages))])
        table.append(["Run 'verdi process report {}' to see them".format(node.pk)])
        result += '\n{}'.format(tabulate(table, headers=table_headers))

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
