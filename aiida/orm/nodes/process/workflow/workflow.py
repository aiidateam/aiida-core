# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module with `Node` sub class for workflow processes."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.common.links import LinkType
from aiida.orm.utils.managers import NodeLinksManager

from ..process import ProcessNode

__all__ = ('WorkflowNode',)


class WorkflowNode(ProcessNode):
    """Base class for all nodes representing the execution of a workflow process."""

    # pylint: disable=too-few-public-methods

    # Workflow nodes are storable
    _storable = True
    _unstorable_message = 'storing for this node has been disabled'

    @property
    def inputs(self):
        """Return an instance of `NodeLinksManager` to manage incoming INPUT_WORK links

        The returned Manager allows you to easily explore the nodes connected to this node
        via an incoming INPUT_WORK link.
        The incoming nodes are reachable by their link labels which are attributes of the manager.

        :return: `NodeLinksManager`
        """
        return NodeLinksManager(node=self, link_type=LinkType.INPUT_WORK, incoming=True)

    @property
    def outputs(self):
        """Return an instance of `NodeLinksManager` to manage outgoing RETURN links

        The returned Manager allows you to easily explore the nodes connected to this node
        via an outgoing RETURN link.
        The outgoing nodes are reachable by their link labels which are attributes of the manager.

        :return: `NodeLinksManager`
        """
        return NodeLinksManager(node=self, link_type=LinkType.RETURN, incoming=False)
