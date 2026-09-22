###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`Data` sub class to represent a dictionary."""

from __future__ import annotations

import builtins
import typing as t

import pydantic as pdt

from aiida.orm.nodes.data.base import to_aiida_type
from aiida.orm.nodes.data.data import Data

__all__ = ('Dict',)


class Dict(Data):
    """ORM representation of a dictionary node.

    The dictionary contents of a `Dict` node are stored directly as node attributes. The dictionary
    can be initialized with keyword arguments directly:

        d = Dict(key='value')

    After construction, values can be retrieved and updated through the item getters and setters,
    respectively:

        node['key'] = 'value'

    Alternatively, the `dict` property returns an instance of the `AttributeManager` that can be used
    to get and set values through attribute notation:

        node.dict.key = 'value'

    Note that trying to set dictionary values directly on the node, e.g. `node.key = value`, will not
    work as intended. It will merely set the `key` attribute on the node instance, but will not be
    stored in the database. As soon as the node goes out of scope, the value will be lost.

    Finally, all dictionary mutations will be forbidden once the node is stored.
    """

    _attributes_model_config = pdt.ConfigDict(extra='allow')

    def __getitem__(self, key: str) -> t.Any:
        try:
            return self.base.attributes.get(key)
        except AttributeError as exc:
            raise KeyError(key) from exc

    def __setitem__(self, key: str, value: t.Any) -> None:
        self.base.attributes.set(key, value)

    def __delitem__(self, key):
        if key not in self.base.attributes:
            raise KeyError(key)
        self.base.attributes.delete(key)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Dict):
            return self.value == other.value
        return self.value == other

    def __contains__(self, key: str) -> bool:
        """Return whether the node contains a key."""
        return key in self.base.attributes

    @property
    def value(self) -> builtins.dict[str, t.Any]:
        """The dictionary content."""
        return dict(self.base.attributes.all)

    @value.setter
    def value(self, value: builtins.dict[str, t.Any]) -> None:
        if not isinstance(value, dict):
            raise TypeError('Must supply dict type')
        self.set_dict(value)

    @property
    def dict(self) -> t.Any:
        """Return an instance of `AttributeManager` that transforms the dictionary into an attribute dict.

        .. note:: this will allow one to do `node.dict.key` as well as `node.dict[key]`.

        :return: an instance of the `AttributeResultManager`.
        """
        from aiida.orm.utils.managers import AttributeManager

        return AttributeManager(self)

    def get(self, key: str, default: t.Any | None = None, /) -> t.Any:
        """Return the value for key if key is in the dictionary, else default.

        :param key: The key whose value to return.
        :param default: Optional default to return in case the key does not exist.
        :returns: The value if the key exists, otherwise the ``default``.
        """
        return self.base.attributes.get(key, default)

    def update(self, dictionary: builtins.dict[str, t.Any]) -> None:
        """Update the current dictionary with the keys provided in the dictionary.

        .. note:: works exactly as `dict.update()` where new keys are simply added and existing keys are overwritten.

        :param dictionary: a dictionary with the keys to substitute
        """
        for key, value in dictionary.items():
            self.base.attributes.set(key, value)

    def keys(self) -> t.Iterator[str]:
        """Iterator of valid keys stored in the Dict object.

        :return: iterator over the keys of the current dictionary
        """
        yield from self.base.attributes.keys()

    def items(self) -> t.Iterator[tuple[str, t.Any]]:
        """Iterator of all items stored in the Dict node."""
        yield from self.base.attributes.items()

    def get_dict(self) -> builtins.dict[str, t.Any]:
        """Return a dictionary with the parameters currently set.

        :return: dictionary
        """
        return self.value

    def set_dict(self, dictionary: builtins.dict[str, t.Any]) -> None:
        """Replace the current dictionary with another one.

        :param dictionary: dictionary to set
        """
        if not isinstance(dictionary, dict):
            raise TypeError('Must supply dict type')

        self.base.attributes.clear()
        self.base.attributes.set_many(dictionary)


@to_aiida_type.register(dict)
def _(value: dict[str, t.Any]) -> Dict:
    return Dict(**value)
