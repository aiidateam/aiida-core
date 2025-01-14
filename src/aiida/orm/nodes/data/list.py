###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`Data` sub class to represent a list."""

from collections.abc import MutableSequence
from typing import Any

from .base import to_aiida_type
from .data import Data

__all__ = ('List',)


class List(Data, MutableSequence):
    """`Data` sub class to represent a list."""

    _LIST_KEY = 'list'

    def __init__(self, value=None, **kwargs):
        """Initialise a ``List`` node instance.

        :param value: list to initialise the ``List`` node from
        """
        data = value or kwargs.pop('list', [])
        super().__init__(**kwargs)
        self.set_list(data)

    def __getitem__(self, item):
        return self.get_list()[item]

    def __setitem__(self, key, value):
        data = self.get_list()
        data[key] = value
        if not self._using_list_reference():
            self.set_list(data)

    def __delitem__(self, key):
        data = self.get_list()
        del data[key]
        if not self._using_list_reference():
            self.set_list(data)

    def __len__(self):
        return len(self.get_list())

    def __str__(self):
        return f'{super().__str__()} value: {self.get_list()}'

    def __eq__(self, other):
        if isinstance(other, List):
            return self.get_list() == other.get_list()
        return self.get_list() == other

    def append(self, value):
        data = self.get_list()
        data.append(value)
        if not self._using_list_reference():
            self.set_list(data)

    def extend(self, value):
        data = self.get_list()
        data.extend(value)
        if not self._using_list_reference():
            self.set_list(data)

    def insert(self, i, value):
        data = self.get_list()
        data.insert(i, value)
        if not self._using_list_reference():
            self.set_list(data)

    def remove(self, value):
        data = self.get_list()
        item = data.remove(value)
        if not self._using_list_reference():
            self.set_list(data)
        return item

    def pop(self, index: int = -1) -> Any:
        """Remove and return item at index (default last)."""
        data = self.get_list()
        item = data.pop(index)
        if not self._using_list_reference():
            self.set_list(data)
        return item

    def index(self, value: Any, start: int = 0, stop: int = 0) -> int:
        """Return first index of value.."""
        return self.get_list().index(value)

    def count(self, value):
        """Return number of occurrences of value."""
        return self.get_list().count(value)

    def sort(self, key=None, reverse=False):
        data = self.get_list()
        data.sort(key=key, reverse=reverse)
        if not self._using_list_reference():
            self.set_list(data)

    def reverse(self):
        data = self.get_list()
        data.reverse()
        if not self._using_list_reference():
            self.set_list(data)

    def get_list(self):
        """Return the contents of this node.

        :return: a list
        """
        try:
            return self.base.attributes.get(self._LIST_KEY)
        except AttributeError:
            self.set_list([])
            return self.base.attributes.get(self._LIST_KEY)

    def set_list(self, data):
        """Set the contents of this node.

        :param data: the list to set
        """
        if not isinstance(data, list):
            raise TypeError('Must supply list type')
        self.base.attributes.set(self._LIST_KEY, data.copy())

    def _using_list_reference(self):
        """This function tells the class if we are using a list reference.  This
        means that calls to self.get_list return a reference rather than a copy
        of the underlying list and therefore self.set_list need not be called.
        This knwoledge is essential to make sure this class is performant.

        Currently the implementation assumes that if the node needs to be
        stored then it is using the attributes cache which is a reference.

        :return: True if using self.get_list returns a reference to the
            underlying sequence.  False otherwise.
        :rtype: bool
        """
        return not self.is_stored


@to_aiida_type.register(list)
def _(value):
    return List(value)
