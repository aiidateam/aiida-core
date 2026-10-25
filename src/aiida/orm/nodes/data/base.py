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

import abc
import typing as t
from functools import singledispatch

from typing_extensions import Self

from aiida.orm.nodes.data.data import Data, DataInterface

__all__ = ('BaseType', 'BaseTypeInterface', 'to_aiida_type')

_ValueT = t.TypeVar('_ValueT')


class BaseType(Data, abc.ABC, t.Generic[_ValueT]):
    """Base class for AiiDA data types wrapping Python primitives."""

    value: _ValueT

    def __str__(self) -> str:
        return f'{super().__str__()} value: {self.value}'


class BaseTypeInterface(DataInterface[BaseType[_ValueT]], abc.ABC, t.Generic[_ValueT]):
    """Interface for AiiDA data types wrapping Python primitives."""

    _orm_cls = BaseType[_ValueT]

    _type: type[_ValueT]

    def __init__(self, value: _ValueT | None = None) -> None:
        self.value = value if value is not None else self._type()

    def __eq__(self, other: object) -> bool:
        if isinstance(other, BaseType):
            return self.value == other.value
        return self.value == other

    def new(self, value: t.Any | None = None) -> Self:
        return type(self)(value=self.value if value is None else value)


@singledispatch
def to_aiida_type(value):
    """Turns basic Python types (str, int, float, bool) into the corresponding AiiDA types."""
    msg = f'Cannot convert value of type {type(value)} to AiiDA type.'
    raise TypeError(msg)
