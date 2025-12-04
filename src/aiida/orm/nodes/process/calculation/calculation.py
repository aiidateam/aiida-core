###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module with `Node` sub class for calculation processes."""

from aiida.common.links import LinkType
from aiida.orm.utils.managers import NodeLinksManager

from .. import process

__all__ = ('CalculationNode',)


class CalculationNodeModel(process.ProcessNodeModel):
    """Placeholder model."""


class CalculationNode(process.ProcessNode):
    """Base class for all nodes representing the execution of a calculation process."""

    Model = CalculationNodeModel

    _storable = True  # Calculation nodes are storable
    _cachable = True  # Calculation nodes can be cached from
    _unstorable_message = 'storing for this node has been disabled'

    @property
    def inputs(self) -> NodeLinksManager:
        """Return an instance of `NodeLinksManager` to manage incoming INPUT_CALC links

        The returned Manager allows you to easily explore the nodes connected to this node
        via an incoming INPUT_CALC link.
        The incoming nodes are reachable by their link labels which are attributes of the manager.

        """
        return NodeLinksManager(node=self, link_type=LinkType.INPUT_CALC, incoming=True)

    @property
    def outputs(self) -> NodeLinksManager:
        """Return an instance of `NodeLinksManager` to manage outgoing CREATE links

        The returned Manager allows you to easily explore the nodes connected to this node
        via an outgoing CREATE link.
        The outgoing nodes are reachable by their link labels which are attributes of the manager.

        """
        return NodeLinksManager(node=self, link_type=LinkType.CREATE, incoming=False)
