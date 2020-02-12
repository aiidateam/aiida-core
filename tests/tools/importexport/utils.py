# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utility functions for tests for the export and import routines"""

from aiida.orm import QueryBuilder, Node


def get_all_node_links():
    """ Get all Node links currently in the DB """
    builder = QueryBuilder()
    builder.append(Node, project='uuid', tag='input')
    builder.append(Node, project='uuid', tag='output', edge_project=['label', 'type'], with_incoming='input')
    return builder.all()
