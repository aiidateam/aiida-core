###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module with `Node` sub class for the execution of a graph of tasks."""

from aiida.orm.nodes.process.workflow.workflow import WorkflowNode

__all__ = ('GraphNode',)


class GraphNode(WorkflowNode):
    """ORM class for all nodes representing the execution of a graph of tasks.

    Graphs share one process class with the executed graph carried in inputs, so the node records which workflow
    ran where `process_type` alone cannot.
    """
