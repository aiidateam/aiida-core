###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Declare source graphs and execute their static task dependencies.

See :func:`graph` for inline orchestration and retry examples, and :func:`task`
for provenance-bearing calculations.
"""

from aiida.engine.processes.graphs.lowering import GraphHandle, expose, forward_outputs, graph, par_map, task
from aiida.engine.processes.graphs.results import Err, Ok, RestartErrors, Result

__all__ = (
    'Err',
    'GraphHandle',
    'Ok',
    'RestartErrors',
    'Result',
    'expose',
    'forward_outputs',
    'graph',
    'par_map',
    'task',
)
