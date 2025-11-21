###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`Data` sub class to represent a float value."""

import numbers

from aiida.common.pydantic import MetadataField

from . import numeric
from .base import to_aiida_type

__all__ = ('Float',)


class FloatModel(numeric.NumericTypeModel):
    value: float = MetadataField(
        title='Float value',
        description='The value of the float',
    )


class Float(numeric.NumericType):
    """`Data` sub class to represent a float value."""

    Model = FloatModel

    _type = float


@to_aiida_type.register(numbers.Real)
def _(value):
    return Float(value)
