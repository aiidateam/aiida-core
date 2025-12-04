###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`Data` sub class to represent an integer value."""

import numbers

from aiida.common.pydantic import MetadataField

from . import numeric
from .base import to_aiida_type

__all__ = ('Int',)


class IntModel(numeric.NumericTypeModel):
    value: int = MetadataField(
        title='Integer value',
        description='The value of the integer',
    )


class Int(numeric.NumericType):
    """`Data` sub class to represent an integer value."""

    Model = IntModel

    _type = int


@to_aiida_type.register(numbers.Integral)
def _(value):
    return Int(value)
