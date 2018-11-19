# -*- coding: utf-8 -*-
"""ORM class for CalcFunctionNode."""
from __future__ import absolute_import

from aiida.orm.mixins import FunctionCalculationMixin
from .calculation import CalculationNode

__all__ = ('CalcFunctionNode',)


class CalcFunctionNode(FunctionCalculationMixin, CalculationNode):
    """ORM class for all nodes representing the execution of a calcfunction."""
    # pylint: disable=too-few-public-methods,abstract-method
    pass
