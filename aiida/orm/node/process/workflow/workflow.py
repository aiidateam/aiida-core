# -*- coding: utf-8 -*-
# pylint: disable=cyclic-import
"""ORM class for WorkflowNode."""
from __future__ import absolute_import

from .. import ProcessNode

__all__ = ('WorkflowNode',)


class WorkflowNode(ProcessNode):
    """Base class for all nodes representing the execution of a workflow process."""

    # pylint: disable=too-few-public-methods

    # Workflow nodes are storable
    _storable = True
