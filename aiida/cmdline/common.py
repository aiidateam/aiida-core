# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################




def print_node_summary(node):
    from tabulate import tabulate

    table = []
    table.append(["type", node.__class__.__name__])
    table.append(["pk", str(node.pk)])
    table.append(["uuid", str(node.uuid)])
    table.append(["label", node.label])
    table.append(["description", node.description])
    table.append(["ctime", node.ctime])
    table.append(["mtime", node.mtime])

    try:
        computer = node.get_computer()
    except AttributeError:
        pass
    else:
        if computer is not None:
            table.append(["computer",
                          "[{}] {}".format(node.get_computer().pk,
                                           node.get_computer().name)])
    try:
        code = node.get_code()
    except AttributeError:
        pass
    else:
        if code is not None:
            table.append(["code", code.label])

    print(tabulate(table))


def print_node_info(node, print_summary=True):
    from aiida.backends.utils import get_log_messages
    from tabulate import tabulate

    if print_summary:
        print_node_summary(node)

    table_headers = ['Link label', 'PK', 'Type']

    table = []
    print "##### INPUTS:"
    for k, v in node.get_inputs_dict().iteritems():
        if k == 'code': continue
        table.append([k, v.pk, v.__class__.__name__])
    print(tabulate(table, headers=table_headers))

    table = []
    print "##### OUTPUTS:"
    for k, v in node.get_outputs(also_labels=True):
        table.append([k, v.pk, v.__class__.__name__])
    print(tabulate(table, headers=table_headers))

    log_messages = get_log_messages(node)
    if log_messages:
        print ("##### NOTE! There are {} log messages for this "
               "calculation.".format(len(log_messages)))
        print "      Use the 'calculation logshow' command to see them."

