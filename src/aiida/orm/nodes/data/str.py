###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`Data` sub class to represent a string value."""

import pydantic as pdt

from aiida.orm.decorators import attribute
from aiida.orm.nodes.data.base import PrimitiveType, to_aiida_type

__all__ = ('Str',)


class Str(PrimitiveType):
    """`Data` sub class to represent a string value."""

    _type = str

    @attribute(model_field_info=pdt.fields.FieldInfo(title='String value'))
    def value(self) -> str:
        """The string value stored in this node."""
        return self.base.attributes.get('value', '')

    @value.setter
    def value(self, value: str) -> None:
        self.base.attributes.set('value', str(value))


@to_aiida_type.register(str)
def _(value):
    return Str(value=str(value))
