from __future__ import annotations

import builtins
import typing as t
from collections.abc import MutableSequence

import pydantic as pdt

from aiida.orm.decorators import attribute
from aiida.orm.nodes.data.base import to_aiida_type
from aiida.orm.nodes.data.data import Data

__all__ = ('List',)


class List(Data, MutableSequence[t.Any]):
    """ORM representation of a list node."""

    def __getitem__(self, item: t.Any) -> t.Any:
        return self.list[item]

    def __setitem__(self, key: t.Any, value: t.Any) -> None:
        data = self.list
        data[key] = value
        if not self._using_list_reference():
            self.list(data)

    def __delitem__(self, key: t.Any) -> None:
        data = self.list
        del data[key]
        if not self._using_list_reference():
            self.list(data)

    def __len__(self) -> int:
        return len(self.list)

    def __str__(self) -> str:
        return f'{super().__str__()} value: {self.list}'

    def __eq__(self, other: object) -> bool:
        if isinstance(other, List):
            return self.list == other.list
        return self.list == other

    @attribute(model_field_info=pdt.fields.FieldInfo(title='List contents'))
    def list(self) -> builtins.list[t.Any]:
        """The list content."""
        return self.base.attributes.get('list', [])

    @list.setter
    def list(self, value: builtins.list[t.Any]) -> None:
        if not isinstance(value, list):
            raise TypeError('Must supply list type')
        self.base.attributes.set('list', value.copy())

    @property
    def value(self) -> builtins.list[t.Any]:
        """Return the value of this node, which is the list content."""
        return self.list

    def append(self, value: t.Any) -> None:
        """Append an item to the list."""
        data = self.list
        data.append(value)
        if not self._using_list_reference():
            self.list(data)

    def extend(self, value: t.Iterable[t.Any]) -> None:
        """Extend the list by appending all the items from the iterable."""
        data = self.list
        data.extend(value)
        if not self._using_list_reference():
            self.list(data)

    def insert(self, i: int, value: t.Any) -> None:
        """Insert value at index i."""
        data = self.list
        data.insert(i, value)
        if not self._using_list_reference():
            self.list(data)

    def remove(self, value: t.Any) -> None:
        """Remove first occurrence of value."""
        data = self.list
        data.remove(value)
        if not self._using_list_reference():
            self.list(data)

    def pop(self, index: int = -1) -> t.Any:
        """Remove and return item at index (default last)."""
        data = self.list
        item = data.pop(index)
        if not self._using_list_reference():
            self.list(data)
        return item

    def index(self, value: t.Any, start: int = 0, stop: int | None = None) -> int:
        """Return first index of value."""
        if stop is None:
            return self.list.index(value, start)
        return self.list.index(value, start, stop)

    def count(self, value: t.Any) -> int:
        """Return number of occurrences of value."""
        return self.list.count(value)

    def sort(self, *, key: t.Callable[[t.Any], t.Any] | None = None, reverse: bool = False) -> None:
        """Sort the list in place."""
        data = self.list
        data.sort(key=key, reverse=reverse)
        if not self._using_list_reference():
            self.list(data)

    def reverse(self) -> None:
        """Reverse the list in place."""
        data = self.list
        data.reverse()
        if not self._using_list_reference():
            self.list(data)

    def _using_list_reference(self) -> bool:
        """This function tells the class if we are using a list reference. This
        means that calls to self.get_list return a reference rather than a copy
        of the underlying list and therefore self.set_list need not be called.
        This knowledge is essential to make sure this class is performant.

        Currently the implementation assumes that if the node needs to be
        stored then it is using the attributes cache which is a reference.

        :return: True if using self.get_list returns a reference to the underlying sequence. False otherwise.
        :rtype: bool
        """
        return not self.is_stored

    # TODO the following methods are handled above via property operations - consider removing

    def get_list(self) -> builtins.list[t.Any]:
        """Return the list content of this node.

        :return: a list
        """
        return self.list

    def set_list(self, data: builtins.list[t.Any]) -> None:
        """Set the list content of this node.

        :param data: the list to set
        """
        self.list = data


@to_aiida_type.register(list)
def _(value: list[t.Any]) -> List:
    return List(list=value)
