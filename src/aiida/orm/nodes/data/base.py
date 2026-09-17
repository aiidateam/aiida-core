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
from functools import singledispatch

from aiida.orm.nodes.data.data import Data
from aiida.orm.pydantic import OrmMetadataField

__all__ = ('BaseType', 'to_aiida_type')

# ``singledispatch`` resolves by method resolution order, and ``Enum`` is the one registered type meant to be mixed
# into another: a member of ``class Spin(str, Enum)`` is a ``str`` before it is an ``Enum``. A class named here is
# asked ahead of whatever a value inherits from outside it.
_DISPATCH_PRECEDENCE: t.Final[tuple[type, ...]] = (Enum,)

_Conversion: t.TypeAlias = t.Callable[[t.Any], Data]
_ConversionT = t.TypeVar('_ConversionT', bound=t.Callable[..., Data])


class _Dispatcher(t.Protocol):
    """What ``to_aiida_type`` exposes: a call that converts a value, and ``register`` to add a conversion."""

    @property
    def registry(self) -> t.Mapping[type, _Conversion]: ...

    def __call__(self, value: t.Any) -> Data: ...

    def dispatch(self, cls: type) -> _Conversion: ...

    @t.overload
    def register(self, cls: type, func: None = None) -> t.Callable[[_ConversionT], _ConversionT]: ...

    @t.overload
    def register(self, cls: _ConversionT, func: None = None) -> _ConversionT: ...

    @t.overload
    def register(self, cls: type, func: _ConversionT) -> _ConversionT: ...


@singledispatch
def _dispatch(value: t.Any) -> Data:
    """Raise for a value whose type has no registered conversion."""
    raise TypeError(f'Cannot convert value of type {type(value)} to AiiDA type.')


def _conversion_below(cls: type, branch: type) -> _Conversion:
    """Return the conversion registered closest to ``cls`` among the bases of ``cls`` that are ``branch``."""
    below = (base for base in cls.__mro__ if base in _dispatch.registry and issubclass(base, branch))
    return _dispatch.dispatch(next(below, branch))


def _implementation_for(cls: type) -> _Conversion:
    """Return the conversion that turns a value of this type into a node."""
    for branch in _DISPATCH_PRECEDENCE:
        if issubclass(cls, branch):
            return _conversion_below(cls, branch)

    return _dispatch.dispatch(cls)


def _to_aiida_type(value: t.Any) -> Data:
    """Turns basic Python types (str, int, float, bool) into the corresponding AiiDA types.

    :param value: the value to convert.
    :return: the node holding it.
    :raises TypeError: if no conversion is registered for the type of the value.
    """
    return _implementation_for(type(value))(value)


_to_aiida_type.register = _dispatch.register  # type: ignore[attr-defined]
_to_aiida_type.dispatch = _implementation_for  # type: ignore[attr-defined]
_to_aiida_type.registry = _dispatch.registry  # type: ignore[attr-defined]

to_aiida_type: _Dispatcher = t.cast(_Dispatcher, _to_aiida_type)


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
