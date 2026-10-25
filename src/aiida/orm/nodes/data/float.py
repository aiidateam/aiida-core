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
from aiida.orm.nodes.data.numeric import NumericType, NumericTypeInterface

__all__ = ('Float', 'FloatInterface')


class Float(NumericType[float]):
    """`Data` sub class to represent a float value."""

    @attribute(model_field_info=pdt.fields.FieldInfo(default=0.0))
    def value(self) -> float:
        """The float value stored in this node."""
        return self.base.attributes.get('value')

    @value.setter
    def value(self, value: float) -> None:
        self.base.attributes.set('value', float(value))


class FloatInterface(NumericTypeInterface[float]):
    """Interface for the `Float` data type."""

    _orm_cls = Float
    _type = float


@to_aiida_type.register(numbers.Real)
def _(value: float) -> Float:
    return Float(attributes={'value': value})
