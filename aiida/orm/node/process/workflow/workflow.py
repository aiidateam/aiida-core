# -*- coding: utf-8 -*-
"""ORM class for WorkflowNode."""
from __future__ import absolute_import

from .. import ProcessNode

__all__ = ('WorkflowNode',)


class WorkflowNode(ProcessNode):
    """Base class for all nodes representing the execution of a workflow process."""
    # pylint: disable=too-few-public-methods,abstract-method
    pass
