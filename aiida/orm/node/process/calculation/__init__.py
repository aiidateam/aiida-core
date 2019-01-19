# -*- coding: utf-8 -*-
# pylint: disable=cyclic-import
"""Package for calculation process node ORM classes."""
from __future__ import absolute_import

from .. import ProcessNode

__all__ = ('CalculationNode',)


class CalculationNode(ProcessNode):
    """Base class for all nodes representing the execution of a calculation process."""
    # pylint: disable=too-few-public-methods

    _cacheable = True

    # Calculation nodes are storable
    _storable = True
    _unstorable_message = 'storing for this node has been disabled'
