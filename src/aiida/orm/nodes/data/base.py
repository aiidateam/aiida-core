###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`Data` sub class to be used as a base for data containers that represent base python data types."""

from __future__ import annotations

import typing as t
from enum import Enum
from functools import singledispatch, wraps

from aiida.orm.nodes.data.data import Data
from aiida.orm.pydantic import OrmMetadataField

__all__ = ('BaseType', 'to_aiida_type')


if t.TYPE_CHECKING:
    from functools import _SingleDispatchCallable


def _enum_first(dispatcher: _SingleDispatchCallable[Data]) -> _SingleDispatchCallable[Data]:
    """Prefer enum converters to converters for their primitive mixins."""

    def dispatch(cls: type) -> t.Callable[..., Data]:
        if issubclass(cls, Enum):
            for base in cls.__mro__:
                if issubclass(base, Enum) and base in dispatcher.registry:
                    return dispatcher.registry[base]
        return dispatcher.dispatch(cls)

    @wraps(dispatcher)
    def wrapper(value: object) -> Data:
        return dispatch(type(value))(value)

    wrapper.__dict__['dispatch'] = dispatch
    return t.cast('_SingleDispatchCallable[Data]', wrapper)


@_enum_first
@singledispatch
def to_aiida_type(value: object) -> Data:
    """Turn Python values into AiiDA types, preserving enums before their primitive mixins.

    :param value: The value to serialize.
    :return: The corresponding AiiDA data node.
    :raises TypeError: If no converter is registered for the value's type.
    """
    msg = f'Cannot convert value of type {type(value)} to AiiDA type.'
    raise TypeError(msg)


class BaseType(Data):
    """`Data` sub class to be used as a base for data containers that represent base python data types."""

    class AttributesModel(Data.AttributesModel):
        value: t.Any = OrmMetadataField(
            title='Data value',
            description='The value of the data',
        )

    def __init__(self, value=None, **kwargs):
        try:
            getattr(self, '_type')
        except AttributeError:
            raise RuntimeError('Derived class must define the `_type` class member')
        super().__init__(**kwargs)
        self.value = value if value is not None else self._type()

    @property
    def value(self):
        return self.base.attributes.get('value', None)

    @value.setter
    def value(self, value):
        self.base.attributes.set('value', self._type(value))

    def __str__(self):
        return f'{super().__str__()} value: {self.value}'

    def __eq__(self, other):
        if isinstance(other, BaseType):
            return self.value == other.value
        return self.value == other

    def new(self, value=None):
        return self.__class__(value)
