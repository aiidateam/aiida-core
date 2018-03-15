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
    Format a timestamp in a human readable format

    :param timestamp: UNIX timestamp
    :param format_str: optional string format to pass to strftime
    """
    from aiida.utils import timezone
    return timezone.datetime.fromtimestamp(timestamp).strftime(format_str)


def print_node_summary(node):
    """
    Output a pretty printed summary of a Node

    :params node: a Node instance
    """
    table = []
    table.append(['type', node.__class__.__name__])
    table.append(['pk', str(node.pk)])
    table.append(['uuid', str(node.uuid)])
    table.append(['label', node.label])
    table.append(['description', node.description])
    table.append(['ctime', node.ctime])
    table.append(['mtime', node.mtime])

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

    print(tabulate(table))


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
