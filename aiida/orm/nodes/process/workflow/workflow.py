# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module with `Node` sub class for workflow processes."""
from typing import TYPE_CHECKING

from aiida.common.links import LinkType
from aiida.orm.utils.managers import NodeLinksManager

from ..process import ProcessNode, ProcessNodeLinks

if TYPE_CHECKING:
    from aiida.orm import Node

__all__ = ('WorkflowNode',)


class WorkflowNodeLinks(ProcessNodeLinks):
    """Interface for links of a node instance."""

    def validate_outgoing(self, target: 'Node', link_type: LinkType, link_label: str) -> None:
        """Validate adding a link of the given type from ourself to a given node.

        A workflow cannot 'create' Data, so if we receive an outgoing link to an unstored Data node, that means
        the user created a Data node within our function body and tries to attach it as an output. This is strictly
        forbidden and can cause provenance to be lost.

        :param target: the node to which the link is going
        :param link_type: the link type
        :param link_label: the link label
        :raise TypeError: if `target` is not a Node instance or `link_type` is not a `LinkType` enum
        :raise ValueError: if the proposed link is invalid
        """
        super().validate_outgoing(target, link_type, link_label)
        if link_type is LinkType.RETURN and not target.is_stored:
            raise ValueError(
                'Workflow<{}> tried returning an unstored `Data` node. This likely means new `Data` is being created '
                'inside the workflow. In order to preserve data provenance, use a `calcfunction` to create this node '
                'and return its output from the workflow'.format(self._node.process_label)
            )


class WorkflowNode(ProcessNode):
    """Base class for all nodes representing the execution of a workflow process."""

    _CLS_NODE_LINKS = WorkflowNodeLinks

    # Workflow nodes are storable
    _storable = True
    _unstorable_message = 'storing for this node has been disabled'

    @property
    def inputs(self) -> NodeLinksManager:
        """Return an instance of `NodeLinksManager` to manage incoming INPUT_WORK links

        The returned Manager allows you to easily explore the nodes connected to this node
        via an incoming INPUT_WORK link.
        The incoming nodes are reachable by their link labels which are attributes of the manager.

        :return: `NodeLinksManager`
        """
        return NodeLinksManager(node=self, link_type=LinkType.INPUT_WORK, incoming=True)

    @property
    def outputs(self) -> NodeLinksManager:
        """Return an instance of `NodeLinksManager` to manage outgoing RETURN links

        The returned Manager allows you to easily explore the nodes connected to this node
        via an outgoing RETURN link.
        The outgoing nodes are reachable by their link labels which are attributes of the manager.

        :return: `NodeLinksManager`
        """
        return NodeLinksManager(node=self, link_type=LinkType.RETURN, incoming=False)
