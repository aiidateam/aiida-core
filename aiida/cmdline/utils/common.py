# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import os
import sys
from tabulate import tabulate


def get_env_with_venv_bin():
    """
    Create a clone of the current running environment with the AIIDA_PATH variable set to the
    value configured in the AIIDA_CONFIG_FOLDER variable
    """
    from aiida.common import setup

    currenv = os.environ.copy()
    currenv['PATH'] = os.path.dirname(sys.executable) + ':' + currenv['PATH']
    currenv['AIIDA_PATH'] = os.path.abspath(os.path.expanduser(setup.AIIDA_CONFIG_FOLDER))
    currenv['PYTHONUNBUFFERED'] = 'True'

    return currenv


def format_local_time(timestamp, format_str='%Y-%m-%d %H:%M:%S'):
    """
    Format a datetime object or UNIX timestamp in a human readable format

    :param timestamp: a datetime object or a float representing a UNIX timestamp
    :param format_str: optional string format to pass to strftime
    """
    from aiida.utils import timezone

    if isinstance(timestamp, float):
        return timezone.datetime.fromtimestamp(timestamp).strftime(format_str)
    else:
        return timestamp.strftime(format_str)


def print_last_process_state_change(process_type='calculation'):
    """
    Print the last time that a process of the specified type has changed its state.
    This function will also print a warning if the daemon is not running.

    :param process_type: the process type for which to get the latest state change timestamp.
        Valid process types are either 'calculation' or 'work'.
    """
    from aiida.cmdline.utils.common import format_local_time
    from aiida.cmdline.utils.echo import echo_info, echo_warning
    from aiida.daemon.client import DaemonClient
    from aiida.utils import timezone
    from aiida.common.utils import str_timedelta
    from aiida.work.utils import get_process_state_change_timestamp

    client = DaemonClient()

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


def print_node_summary(node):
    """
    Output a pretty printed summary of a Node

    :params node: a Node instance
    """
    from plumpy import ProcessState
    from aiida.orm.implementation.general.calculation import AbstractCalculation

    table_headers = ['Property', 'Value']
    table = []
    table.append(['type', node.__class__.__name__])
    table.append(['pk', str(node.pk)])
    table.append(['uuid', str(node.uuid)])
    table.append(['label', node.label])
    table.append(['description', node.description])
    table.append(['ctime', node.ctime])
    table.append(['mtime', node.mtime])

    if issubclass(node.__class__, AbstractCalculation):
        try:
            process_state = node.process_state
        except AttributeError:
            process_state = None

        try:
            table.append(['process state', ProcessState(process_state)])
        except ValueError:
            table.append(['process state', process_state])

        try:
            table.append(['finish status', node.finish_status])
        except AttributeError:
            table.append(['finish status', None])

    try:
        computer = node.get_computer()
    except AttributeError:
        pass
    else:
        if computer is not None:
            table.append(['computer', '[{}] {}'.format(node.get_computer().pk, node.get_computer().name)])

    try:
        code = node.get_code()
    except AttributeError:
        pass
    else:
        if code is not None:
            table.append(['code', code.label])

    print(tabulate(table, headers=table_headers))


def print_node_info(node, print_summary=True):
    """
    Print information about the given node, such as the incoming and outcoming links

    :param print_summary: also print out a summary of node properties
    """
    from aiida.backends.utils import get_log_messages
    from aiida.common.links import LinkType
    from aiida.orm.calculation.work import WorkCalculation

    if print_summary:
        print_node_summary(node)

    nodes_input = node.get_inputs(link_type=LinkType.INPUT, also_labels=True)
    nodes_caller = node.get_inputs(link_type=LinkType.CALL, also_labels=True)
    nodes_create = node.get_outputs(link_type=LinkType.CREATE, also_labels=True)
    nodes_return = node.get_outputs(link_type=LinkType.RETURN, also_labels=True)
    nodes_called = node.get_outputs(link_type=LinkType.CALL, also_labels=True)
    nodes_output = nodes_create + nodes_return

    if nodes_caller:
        table = []
        table_headers = ['Called by', 'PK', 'Type']
        for k, v in nodes_caller:
            table.append([k, v.pk, v.__class__.__name__])
        print('\n{}'.format(tabulate(table, headers=table_headers)))

    if nodes_input:
        table = []
        table_headers = ['Inputs', 'PK', 'Type']
        for k, v in nodes_input:
            if k == 'code': continue
            table.append([k, v.pk, v.__class__.__name__])
        print('\n{}'.format(tabulate(table, headers=table_headers)))


    if nodes_output:
        table = []
        table_headers = ['Outputs', 'PK', 'Type']
        for k, v in nodes_output:
            table.append([k, v.pk, v.__class__.__name__])
        print('\n{}'.format(tabulate(table, headers=table_headers)))


    if nodes_called:
        table = []
        table_headers = ['Called', 'PK', 'Type']
        for k, v in nodes_called:
            table.append([k, v.pk, v.__class__.__name__])
        print('\n{}'.format(tabulate(table, headers=table_headers)))

    log_messages = get_log_messages(node)
    if log_messages:
        table = []
        table_headers = ['Log messages']
        table.append(['There are {} log messages for this calculation'.format(len(log_messages))])
        if isinstance(node, WorkCalculation):
            table.append(["Run 'verdi work report {}' to see them".format(node.pk)])
        else:
            table.append(["Run 'verdi calculation logshow {}' to see them".format(node.pk)])
        print('\n{}'.format(tabulate(table, headers=table_headers)))
