###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`Data` sub class to represent a string value."""

from aiida.common.pydantic import MetadataField

from .base import BaseType, to_aiida_type
from .numeric import NumericType

__all__ = ('Str',)


class Str(BaseType):
    """`Data` sub class to represent a string value."""

    _type = str

    class Model(NumericType.Model):
        value: str = MetadataField(
            title='String value.',
            description='The value of the string',
        )


@to_aiida_type.register(str)
def _(value):
    return Str(value)
