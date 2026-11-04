###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Declare source graphs and execute their static task dependencies."""

from aiida.engine.processes.graphs.lowering import Forward, GraphHandle, graph, task

__all__ = (
    'Forward',
    'GraphHandle',
    'graph',
    'task',
)
