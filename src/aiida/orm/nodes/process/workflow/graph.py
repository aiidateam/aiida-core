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

from aiida.common.lang import classproperty, override
from aiida.common.links import LinkType
from aiida.orm.nodes.data.dict import Dict
from aiida.orm.nodes.process.workflow.workflow import WorkflowNode, WorkflowNodeLinks
from aiida.orm.utils.managers import NodeLinksManager

if t.TYPE_CHECKING:
    from aiida.engine.processes.builder import ProcessBuilder
    from aiida.orm import Node

__all__ = ('GraphNode',)


class GraphNodeLinks(WorkflowNodeLinks):
    """Link constraints for graphs, which can create their own inline outputs."""

    @override
    def validate_outgoing(self, target: 'Node', link_type: LinkType, link_label: str) -> None:
        """Only claim creation of data that has not already been stored."""
        super().validate_outgoing(target, link_type, link_label)
        if link_type is LinkType.CREATE and target.is_stored:
            msg = 'a graph cannot create an already stored node; return it instead.'
            raise ValueError(msg)


class GraphNode(WorkflowNode):
    """ORM class for all nodes representing the execution of a graph of tasks.

    Graphs share one process class with the definition recorded on the node, so the node records which workflow
    ran where `process_type` alone cannot.
    """

    _CLS_NODE_LINKS = GraphNodeLinks

    GRAPH_DEFINITION_KEY = 'graph_definition'
    EXECUTOR_UUID_KEY = 'graph_executor_uuid'
    RUNTIME_CONFIG_KEY = 'graph_runtime_config_v1'
    EXECUTION_POLICY_KEY = 'graph_execution_policy_v1'
    PROTOCOL_KEY = 'graph_protocol_v1'
    ATTEMPTS_KEY = 'graph_attempts_v1'

    @classproperty
    def _updatable_attributes(cls) -> tuple[str, ...]:  # noqa: N805
        return super()._updatable_attributes + (cls.ATTEMPTS_KEY,)

    @property
    def execution_attempts(self) -> dict[str, list[dict[str, t.Any]]]:
        """Return the recorded attempts and recovery decisions keyed by logical task instance."""
        return self.base.attributes.get(self.ATTEMPTS_KEY, {})

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
        if self.RUNTIME_CONFIG_KEY in self.base.attributes:
            from aiida.orm.utils.serialize import deserialize_unsafe

            builder['runtime_config'] = deserialize_unsafe(self.base.attributes.get(self.RUNTIME_CONFIG_KEY))
        for key, channel in (
            (self.EXECUTION_POLICY_KEY, 'execution_policy'),
            (self.PROTOCOL_KEY, 'protocol_record'),
        ):
            if key in self.base.attributes:
                builder[channel] = self.base.attributes.get(key)
        for name, value in (self.get_metadata_inputs() or {}).items():
            builder[name] = value
        return builder
