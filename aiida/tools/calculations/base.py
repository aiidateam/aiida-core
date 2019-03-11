# -*- coding: utf-8 -*-
"""Base class for CalculationTools

Sub-classes can be registered in the `aiida.tools.calculations` category to enable the `CalcJobNode` class from being
able to find the tools plugin, load it and expose it through the `tools` property of the `CalcJobNode`.
"""

__all__ = ('CalculationTools',)


class CalculationTools(object):
    """Base class for CalculationTools."""

    # pylint: disable=too-few-public-methods,useless-object-inheritance

    def __init__(self, node):
        self._node = node
