from __future__ import annotations

import builtins
import typing as t
from collections.abc import MutableSequence
from copy import deepcopy

import pydantic as pdt

from aiida.common.lang import type_check
from aiida.orm.decorators import attribute
from aiida.orm.nodes.data.base import to_aiida_type
from aiida.orm.nodes.data.data import Data, DataInterface

__all__ = ('List',)


class List(Data):
    """ORM representation of a list node."""

    @attribute(model_field_info=pdt.fields.FieldInfo(default_factory=builtins.list))
    def list(self) -> builtins.list[t.Any]:
        """The list content."""
        return self.base.attributes.get('list')

    @list.setter
    def list(self, value: builtins.list[t.Any]) -> None:
        type_check(value, builtins.list)
        self.base.attributes.set('list', value.copy())  # TODO why copy?


class ListInterface(DataInterface[List], MutableSequence[t.Any]):
    """Interface for list-like data nodes."""

    _orm_cls = List

    def __init__(self, list: builtins.list[t.Any] | None = None) -> None:
        self.list = deepcopy(list) if list is not None else []

    def __getitem__(self, item: t.Any) -> t.Any:
        return self.list[item]

    def __setitem__(self, key: t.Any, value: t.Any) -> None:
        self.list[key] = value

    def __delitem__(self, item: t.Any) -> None:
        del self.list[item]

    def __len__(self) -> int:
        return len(self.list)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.list!r})'

    def insert(self, i: int, value: t.Any) -> None:
        """Insert value at index i."""
        self.list.insert(i, value)

    def sort(self, *, key: t.Callable[[t.Any], t.Any] | None = None, reverse: bool = False) -> None:
        """Sort the list in place."""
        self.list.sort(key=key, reverse=reverse)


@to_aiida_type.register(list)
def _(value: list[t.Any]) -> List:
    return List(attributes={'list': deepcopy(value)})
