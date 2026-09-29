###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`Data` sub class to represent an integer value."""

from __future__ import annotations

import numbers

import pydantic as pdt

from aiida.orm.decorators import attribute
from aiida.orm.nodes.data.base import to_aiida_type
from aiida.orm.nodes.data.numeric import NumericType

__all__ = ('Int',)


class Int(NumericType):
    """`Data` sub class to represent an integer value."""

    _type = int

    @attribute(model_field_info=pdt.fields.FieldInfo(title='Integer value'))
    def value(self) -> int:
        """The integer value stored in this node."""
        return self.base.attributes.get('value', 0)

    @value.setter
    def value(self, value: int) -> None:
        self.base.attributes.set('value', int(value))


@to_aiida_type.register(numbers.Integral)
def _(value):
    return Int(value=int(value))
