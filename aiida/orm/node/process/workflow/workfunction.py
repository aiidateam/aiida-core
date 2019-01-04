# -*- coding: utf-8 -*-
# pylint: disable=cyclic-import
"""ORM class for WorkFunctionNode."""
from __future__ import absolute_import

from aiida.common.links import LinkType
from aiida.orm.mixins import FunctionCalculationMixin
from .workflow import WorkflowNode

__all__ = ('WorkFunctionNode',)


class WorkFunctionNode(FunctionCalculationMixin, WorkflowNode):
    """ORM class for all nodes representing the execution of a workfunction."""

    # pylint: disable=too-few-public-methods

    def validate_outgoing(self, target, link_type, link_label):
        """
        Validate adding a link of the given type from ourself to a given node.

        A workfunction cannot create Data, so if we receive an outgoing RETURN link to an unstored Data node, that means
        the user created a Data node within our function body and is trying to return it. This use case should be
        reserved for @calcfunctions, as they can have CREATE links.

        :param target: the node to which the link is going
        :param link_type: the link type
        :param link_label: the link label
        :raise TypeError: if `target` is not a Node instance or `link_type` is not a `LinkType` enum
        :raise ValueError: if the proposed link is invalid
        """
        super(WorkFunctionNode, self).validate_outgoing(target, link_type, link_label)
        if link_type is LinkType.RETURN and not target.is_stored:
            raise ValueError(
                'trying to return an unstored Data node from a @workfunction, however, @workfunctions cannot create '
                'data. You probably want to use a @calcfunction instead.')
