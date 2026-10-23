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

    A graph is run by one process class for every graph there is, since what to run is an input rather than a
    subclass, so the kind of workflow a run was is what this says and the process type cannot.
    """
