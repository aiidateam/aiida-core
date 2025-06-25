###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module with `Node` sub class for workflow function processes."""

from typing import TYPE_CHECKING

from aiida.common.links import LinkType
from aiida.orm.utils.mixins import FunctionCalculationMixin

from .workflow import WorkflowNode, WorkflowNodeLinks

if TYPE_CHECKING:
    from aiida.orm import Node

__all__ = ('WorkFunctionNode',)


class WorkFunctionNodeLinks(WorkflowNodeLinks):
    """Interface for links of a node instance."""

    def validate_outgoing(self, target: 'Node', link_type: LinkType, link_label: str) -> None:
        """Validate adding a link of the given type from ourself to a given node.

        A workfunction cannot create Data, so if we receive an outgoing RETURN link to an unstored Data node, that means
        the user created a Data node within our function body and is trying to return it. This use case should be
        reserved for @calcfunctions, as they can have CREATE links.

        :param target: the node to which the link is going
        :param link_type: the link type
        :param link_label: the link label
        :raise TypeError: if `target` is not a Node instance or `link_type` is not a `LinkType` enum
        :raise ValueError: if the proposed link is invalid
        """
        super().validate_outgoing(target, link_type, link_label)
        if link_type is LinkType.RETURN and not target.is_stored:
            raise ValueError(
                'trying to return an unstored Data node from a @workfunction, however, @workfunctions cannot create '
                'data. You probably want to use a @calcfunction instead.'
            )


class WorkFunctionNode(FunctionCalculationMixin, WorkflowNode):
    """ORM class for all nodes representing the execution of a workfunction."""

    _CLS_NODE_LINKS = WorkFunctionNodeLinks
