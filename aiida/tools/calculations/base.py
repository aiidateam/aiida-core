# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Base class for CalculationTools

Sub-classes can be registered in the `aiida.tools.calculations` category to enable the `CalcJobNode` class from being
able to find the tools plugin, load it and expose it through the `tools` property of the `CalcJobNode`.
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__all__ = ('CalculationTools',)


class CalculationTools(object):
    """Base class for CalculationTools."""

    # pylint: disable=too-few-public-methods,useless-object-inheritance

    def __init__(self, node):
        self._node = node
