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

from . import base
from .base import to_aiida_type

__all__ = ('Str',)


class StrModel(base.BaseTypeModel):
    value: str = MetadataField(
        title='String value',
        description='The value of the string',
    )


class Str(base.BaseType):
    """`Data` sub class to represent a string value."""

    Model = StrModel

    _type = str


@to_aiida_type.register(str)
def _(value):
    return Str(value)
