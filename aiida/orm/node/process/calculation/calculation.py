# -*- coding: utf-8 -*-
"""ORM class for CalculationNode."""
from __future__ import absolute_import

from .. import ProcessNode

__all__ = ('CalculationNode',)


class CalculationNode(ProcessNode):
    """Base class for all nodes representing the execution of a calculation process."""
    # pylint: disable=too-few-public-methods,abstract-method
    pass
