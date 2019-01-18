# -*- coding: utf-8 -*-
# pylint: disable=cyclic-import
"""Package for workflow process node ORM classes."""
from __future__ import absolute_import

from .. import ProcessNode

__all__ = ('WorkflowNode',)


class WorkflowNode(ProcessNode):
    """Base class for all nodes representing the execution of a workflow process."""

    # pylint: disable=too-few-public-methods

    # Workflow nodes are storable
    _storable = True
    _unstorable_message = 'storing for this node has been disabled'
