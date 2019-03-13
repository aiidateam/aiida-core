# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`Data` sub class to represent a float value."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import numbers

from .base import to_aiida_type
from .numeric import NumericType

__all__ = ('Float',)


class Float(NumericType):
    """`Data` sub class to represent a float value."""

    _type = float


@to_aiida_type.register(numbers.Real)
def _(value):
    return Float(value)
