# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import absolute_import
import numbers
from aiida.orm.data import to_aiida_type
from aiida.orm.data.numeric import NumericType


class Int(NumericType):
    """
    Class to store integer numbers as AiiDA nodes
    """
    _type = int


@to_aiida_type.register(numbers.Integral)
def _(value):
    return Int(value)
