###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module with `Node` sub class for calculation processes."""

import pydantic as pdt

from aiida.common import exceptions
from aiida.common.lang import type_check
from aiida.common.links import LinkType
from aiida.orm.computers import Computer
from aiida.orm.decorators import column
from aiida.orm.models.adapters import EntityPkAdapter
from aiida.orm.nodes.process.process import ProcessNode
from aiida.orm.utils.managers import NodeLinksManager

__all__ = ('CalculationNode',)


class CalculationNode(ProcessNode):
    """Base class for all nodes representing the execution of a calculation process."""

    _storable = True  # Calculation nodes are storable
    _cachable = True  # Calculation nodes can be cached from
    _unstorable_message = 'storing for this node has been disabled'

    @column(
        model_field_info=pdt.fields.FieldInfo(
            description='The PK of the associated computer.',
        ),
        model_adapter=EntityPkAdapter(Computer),
    )
    def computer(self) -> Computer | None:
        """The computer associated with the calculation node."""
        if self._backend_entity.computer:
            return Computer.from_backend_entity(self._backend_entity.computer)

        return None

    @computer.setter
    def computer(self, computer: Computer | None) -> None:
        if self.is_stored:
            raise exceptions.ModificationNotAllowed('cannot set the computer on a stored node')

        type_check(computer, Computer, allow_none=True)
        self._backend_entity.computer = None if computer is None else computer.backend_entity

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
