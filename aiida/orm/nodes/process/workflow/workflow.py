# -*- coding: utf-8 -*-
"""Module with `Node` sub class for workflow processes."""
from __future__ import absolute_import

from ..process import ProcessNode

__all__ = ('WorkflowNode',)


class WorkflowNode(ProcessNode):
    """Base class for all nodes representing the execution of a workflow process."""

    # pylint: disable=too-few-public-methods

    # Workflow nodes are storable
    _storable = True
    _unstorable_message = 'storing for this node has been disabled'
