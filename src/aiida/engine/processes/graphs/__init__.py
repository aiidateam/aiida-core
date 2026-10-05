###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Declare source graphs and execute their static task dependencies."""

from aiida.engine.processes.graphs.build_source import UnsupportedSyntax, build_from_source, graph, task
from aiida.engine.processes.graphs.interface import GraphHandle
from aiida.engine.processes.graphs.process import GraphProcess, TaskProcess
from aiida.engine.processes.graphs.spec import Dependency, Endpoint, GraphSpec, TaskSpec
from aiida.engine.processes.graphs.tasks import TaskHandle

__all__ = (
    'Dependency',
    'Endpoint',
    'GraphHandle',
    'GraphProcess',
    'GraphSpec',
    'TaskHandle',
    'TaskProcess',
    'TaskSpec',
    'UnsupportedSyntax',
    'build_from_source',
    'graph',
    'task',
)
