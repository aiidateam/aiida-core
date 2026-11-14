###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module with `Node` sub class for the execution of a graph of tasks."""

from aiida.common.lang import override
from aiida.common.links import LinkType
from aiida.orm.nodes.process.workflow.workflow import WorkflowNode
from aiida.orm.utils.managers import NodeLinksManager

__all__ = ('GraphNode',)


class GraphNode(WorkflowNode):
    """ORM class for all nodes representing the execution of a graph of tasks.

    Graphs share one process class with the executed graph carried in inputs, so the node records which workflow
    ran where `process_type` alone cannot.
    """

    @property
    @override
    def inputs(self) -> NodeLinksManager:
        """Return the declared workflow arguments, flattened from the stored `graph_inputs` namespace.

        Incoming `INPUT_WORK` links keep the engine layout (`graph`, `graph_inputs`, and optional `task_metadata`),
        so previously stored nodes and checkpoints need no migration; this view only hides those engine keys unless
        the workflow itself declares an input with the same name. Low-level `base.links` querying still exposes the
        stored layout for engine introspection.

        :return: scoped `NodeLinksManager` over the flattened workflow arguments.
        """
        return NodeLinksManager(node=self, link_type=LinkType.INPUT_WORK, incoming=True, namespace='graph_inputs')
