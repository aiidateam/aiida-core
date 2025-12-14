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

import copy
import typing as t

from aiida.common import exceptions
from aiida.common.pydantic import MetadataField

from .base import to_aiida_type
from .data import Data

__all__ = ('Dict',)


class Dict(Data):
    """`Data` sub class to represent a dictionary.

    The dictionary contents of a `Dict` node are stored in the database as attributes. The dictionary
    can be initialized through the `dict` argument in the constructor. After construction, values can
    be retrieved and updated through the item getters and setters, respectively:

        node['key'] = 'value'

    Alternatively, the `dict` property returns an instance of the `AttributeManager` that can be used
    to get and set values through attribute notation:

        node.dict.key = 'value'

    Note that trying to set dictionary values directly on the node, e.g. `node.key = value`, will not
    work as intended. It will merely set the `key` attribute on the node instance, but will not be
    stored in the database. As soon as the node goes out of scope, the value will be lost.

    It is also relevant to note here the difference in something being an "attribute of a node" (in
    the sense that it is stored in the "attribute" column of the database when the node is stored)
    and something being an "attribute of a python object" (in the sense of being able to modify and
    access it as if it was a property of the variable, e.g. `node.key = value`). This is true of all
    types of nodes, but it becomes more relevant for `Dict` nodes where one is constantly manipulating
    these attributes.

    Finally, all dictionary mutations will be forbidden once the node is stored.
    """

    class AttributesModel(Data.AttributesModel):
        model_config = {
            'arbitrary_types_allowed': True,
            'json_schema_extra': {
                'additionalProperties': True,
            },
        }

        value: t.Dict[str, t.Any] = MetadataField(
            description='The dictionary content',
            write_only=True,
        )

    def __init__(self, value=None, **kwargs):
        """Initialise a ``Dict`` node instance.

        Usual rules for attribute names apply, in particular, keys cannot start with an underscore, or a ``ValueError``
        will be raised.

        Initial attributes can be changed, deleted or added as long as the node is not stored.

        :param value: dictionary to initialise the ``Dict`` node from
        """
        dictionary = value or kwargs.pop('dict', None) or kwargs.get('attributes', {}).pop('value', None)

        super().__init__(**kwargs)

        if dictionary:
            self.set_dict(dictionary)

    def __getitem__(self, key):
        try:
            return self.base.attributes.get(key)
        except AttributeError as exc:
            raise KeyError from exc

    def __setitem__(self, key, value):
        self.base.attributes.set(key, value)

    def __eq__(self, other):
        if isinstance(other, Dict):
            return self.get_dict() == other.get_dict()
        return self.get_dict() == other

    def __contains__(self, key: str) -> bool:
        """Return whether the node contains a key."""
        return key in self.base.attributes

    def get(self, key: str, default: t.Any | None = None, /):  # type: ignore[override]
        """Return the value for key if key is in the dictionary, else default.

        :param key: The key whose value to return.
        :param default: Optional default to return in case the key does not exist.
        :returns: The value if the key exists, otherwise the ``default``.
        """
        return self.base.attributes.get(key, default)

    def set_dict(self, dictionary):
        """Replace the current dictionary with another one.

        :param dictionary: dictionary to set
        """
        dictionary_backup = copy.deepcopy(self.get_dict())

        try:
            # Clear existing attributes and set the new dictionary
            self.base.attributes.clear()
            self.update_dict(dictionary)
        except exceptions.ModificationNotAllowed:
            # I reraise here to avoid to go in the generic 'except' below that would raise the same exception again
            raise
        except Exception:
            # Try to restore the old data
            self.base.attributes.clear()
            self.update_dict(dictionary_backup)
            raise

    def update_dict(self, dictionary):
        """Update the current dictionary with the keys provided in the dictionary.

        .. note:: works exactly as `dict.update()` where new keys are simply added and existing keys are overwritten.

        :param dictionary: a dictionary with the keys to substitute
        """
        for key, value in dictionary.items():
            self.base.attributes.set(key, value)

    def get_dict(self):
        """Return a dictionary with the parameters currently set.

        :return: dictionary
        """
        return dict(self.base.attributes.all)

    def keys(self):
        """Iterator of valid keys stored in the Dict object.

        :return: iterator over the keys of the current dictionary
        """
        for key in self.base.attributes.keys():
            yield key

    def items(self):
        """Iterator of all items stored in the Dict node."""
        for key, value in self.base.attributes.items():
            yield key, value

    @property
    def value(self) -> dict[str, t.Any]:
        """Return the value of this node, which is the dictionary content.

        :return: The dictionary content.
        """
        return self.base.attributes.all

    @property
    def dict(self):
        """Return an instance of `AttributeManager` that transforms the dictionary into an attribute dict.

        .. note:: this will allow one to do `node.dict.key` as well as `node.dict[key]`.

        :return: an instance of the `AttributeResultManager`.
        """
        from aiida.orm.utils.managers import AttributeManager

        return AttributeManager(self)


@to_aiida_type.register(dict)
def _(value):
    return Dict(value)
