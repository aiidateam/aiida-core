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

import pydantic as pdt

from aiida.orm.decorators import attribute
from aiida.orm.nodes.data.base import to_aiida_type
from aiida.orm.nodes.data.numeric import NumericType

__all__ = ('Float',)


class Float(NumericType):
    """`Data` sub class to represent a float value."""

    _type = float

    @attribute(model_field_info=pdt.fields.FieldInfo(title='Float value'))
    def value(self) -> float:
        """The float value stored in this node."""
        return self.base.attributes.get('value', 0.0)

    @value.setter
    def value(self, value: float) -> None:
        self.base.attributes.set('value', float(value))


@to_aiida_type.register(numbers.Real)
def _(value):
    return Float(value=float(value))
