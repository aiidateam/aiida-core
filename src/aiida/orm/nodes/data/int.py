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

from .base import to_aiida_type
from .numeric import NumericType

__all__ = ('Int',)


class Int(NumericType):
    """`Data` sub class to represent an integer value."""

    _type = int

    class Model(NumericType.Model):
        value: int = MetadataField(
            title='Integer value',
            description='The value of the integer',
        )


@to_aiida_type.register(numbers.Integral)
def _(value):
    return Int(value)
