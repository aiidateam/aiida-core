###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module with `Node` sub class for calculation function processes."""

from typing import TYPE_CHECKING

from aiida.common.links import LinkType
from aiida.orm.utils.mixins import FunctionCalculationMixin

from ..process import ProcessNodeLinks
from .calculation import CalculationNode

if TYPE_CHECKING:
    from aiida.orm import Node

__all__ = ('CalcFunctionNode',)


class CalcFunctionNodeLinks(ProcessNodeLinks):
    """Interface for links of a node instance."""

    def validate_outgoing(self, target: 'Node', link_type: LinkType, link_label: str) -> None:
        """Validate adding a link of the given type from ourself to a given node.

        A calcfunction cannot return Data, so if we receive an outgoing link to a stored Data node, that means
        the user created a Data node within our function body and stored it themselves or they are returning an input
        node. The latter use case is reserved for @workfunctions, as they can have RETURN links.

        :param target: the node to which the link is going
        :param link_type: the link type
        :param link_label: the link label
        :raise TypeError: if `target` is not a Node instance or `link_type` is not a `LinkType` enum
        :raise ValueError: if the proposed link is invalid
        """
        super().validate_outgoing(target, link_type, link_label)
        if link_type is LinkType.CREATE and target.is_stored:
            raise ValueError(
                'trying to return an already stored Data node from a @calcfunction, however, @calcfunctions cannot '
                'return data. If you stored the node yourself, simply do not call `store()` yourself. If you want to '
                'return an input node, use a @workfunction instead.'
            )


class CalcFunctionNode(FunctionCalculationMixin, CalculationNode):
    """ORM class for all nodes representing the execution of a calcfunction."""

    _CLS_NODE_LINKS = CalcFunctionNodeLinks
