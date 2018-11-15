# -*- coding: utf-8 -*-
# pylint: disable=abstract-method
"""ORM class for WorkFunctionNode."""
from __future__ import absolute_import

from aiida.orm.mixins import FunctionCalculationMixin
from .workflow import WorkflowNode

__all__ = ('WorkFunctionNode',)


class WorkFunctionNode(FunctionCalculationMixin, WorkflowNode):
    """ORM class for all nodes representing the execution of a workfunction."""
    # pylint: disable=too-few-public-methods
    pass
