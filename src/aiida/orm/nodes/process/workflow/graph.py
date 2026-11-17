###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module with `Node` sub class for the execution of a graph of tasks."""

import typing as t

from aiida.common.lang import override
from aiida.common.links import LinkType
from aiida.orm.nodes.data.dict import Dict
from aiida.orm.nodes.process.workflow.workflow import WorkflowNode
from aiida.orm.utils.managers import NodeLinksManager

if t.TYPE_CHECKING:
    from aiida.engine.processes.builder import ProcessBuilder

__all__ = ('GraphNode',)


class GraphNode(WorkflowNode):
    """ORM class for all nodes representing the execution of a graph of tasks.

    Graphs share one process class with the definition recorded on the node, so the node records which workflow
    ran where `process_type` alone cannot.
    """

    GRAPH_DEFINITION_KEY = 'graph_definition'
    TASK_METADATA_KEY = 'graph_task_metadata'

    @property
    @override
    def inputs(self) -> NodeLinksManager:
        """Return declared workflow arguments, including the projected view of legacy nodes.

        :return: link manager over workflow arguments only.
        """
        namespace = None if self.GRAPH_DEFINITION_KEY in self.base.attributes else 'graph_inputs'
        return NodeLinksManager(node=self, link_type=LinkType.INPUT_WORK, incoming=True, namespace=namespace)

    @override
    def get_builder_restart(self) -> 'ProcessBuilder':
        """Reconstruct the launch envelope without exposing it as scientific input links.

        :return: builder populated with the recorded definition, arguments and launch configuration.
        """
        if self.GRAPH_DEFINITION_KEY not in self.base.attributes:
            return super().get_builder_restart()
        builder = self.process_class.get_builder()
        builder['graph'] = Dict(dict=self.base.attributes.get(self.GRAPH_DEFINITION_KEY))
        builder['graph_inputs'] = self.base.links.get_incoming(link_type=LinkType.INPUT_WORK).nested()
        if self.TASK_METADATA_KEY in self.base.attributes:
            builder['task_metadata'] = Dict(dict=self.base.attributes.get(self.TASK_METADATA_KEY))
        for name, value in (self.get_metadata_inputs() or {}).items():
            builder[name] = value
        return builder
