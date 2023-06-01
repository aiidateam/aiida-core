# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=too-many-lines,too-many-arguments
"""Interface to the extras of a node instance."""
import copy
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Tuple, Union

if TYPE_CHECKING:
    from .groups import Group
    from .nodes.node import Node

__all__ = ('EntityExtras',)

_NO_DEFAULT: Any = tuple()


class EntityExtras:
    """Interface to the extras of a node or group instance.

    Extras are a JSONable dictionary, stored on each entity,
    allowing for arbitrary data to be stored by users.

    Extras are mutable, even after storing the entity,
    and as such are not deemed a core part of the provenance graph.
    """

    def __init__(self, entity: Union['Node', 'Group']) -> None:
        """Initialize the interface."""
        self._entity = entity
        self._backend_entity = entity.backend_entity

    def __contains__(self, key: str) -> bool:
        """Check if the extras contain the given key."""
        return key in self._backend_entity.extras

    @property
    def all(self) -> Dict[str, Any]:
        """Return the complete extras dictionary.

        .. warning:: While the entity is unstored, this will return references of the extras on the database model,
            meaning that changes on the returned values (if they are mutable themselves, e.g. a list or dictionary) will
            automatically be reflected on the database model as well. As soon as the entity is stored, the returned
            extras will be a deep copy and mutations of the database extras will have to go through the appropriate set
            methods. Therefore, once stored, retrieving a deep copy can be a heavy operation. If you only need the keys
            or some values, use the iterators `extras_keys` and `extras_items`, or the getters `get_extra` and
            `get_extra_many` instead.

        :return: the extras as a dictionary
        """
        extras = self._backend_entity.extras

        if self._entity.is_stored:
            extras = copy.deepcopy(extras)

        return extras

    def get(self, key: str, default: Any = _NO_DEFAULT) -> Any:
        """Return the value of an extra.

        .. warning:: While the entity is unstored, this will return a reference of the extra on the database model,
            meaning that changes on the returned value (if they are mutable themselves, e.g. a list or dictionary) will
            automatically be reflected on the database model as well. As soon as the entity is stored, the returned
            extra will be a deep copy and mutations of the database extras will have to go through the appropriate set
            methods.

        :param key: name of the extra
        :param default: return this value instead of raising if the attribute does not exist
        :return: the value of the extra
        :raises AttributeError: if the extra does not exist and no default is specified
        """
        try:
            extra = self._backend_entity.get_extra(key)
        except AttributeError:
            if default is _NO_DEFAULT:
                raise
            extra = default

        if self._entity.is_stored:
            extra = copy.deepcopy(extra)

        return extra

    def get_many(self, keys: List[str]) -> List[Any]:
        """Return the values of multiple extras.

        .. warning:: While the entity is unstored, this will return references of the extras on the database model,
            meaning that changes on the returned values (if they are mutable themselves, e.g. a list or dictionary) will
            automatically be reflected on the database model as well. As soon as the entity is stored, the returned
            extras will be a deep copy and mutations of the database extras will have to go through the appropriate set
            methods. Therefore, once stored, retrieving a deep copy can be a heavy operation. If you only need the keys
            or some values, use the iterators `extras_keys` and `extras_items`, or the getters `get_extra` and
            `get_extra_many` instead.

        :param keys: a list of extra names
        :return: a list of extra values
        :raises AttributeError: if at least one extra does not exist
        """
        extras = self._backend_entity.get_extra_many(keys)

        if self._entity.is_stored:
            extras = copy.deepcopy(extras)

        return extras

    def set(self, key: str, value: Any) -> None:
        """Set an extra to the given value.

        :param key: name of the extra
        :param value: value of the extra
        :raise aiida.common.ValidationError: if the key is invalid, i.e. contains periods
        """
        self._backend_entity.set_extra(key, value)

    def set_many(self, extras: Dict[str, Any]) -> None:
        """Set multiple extras.

        .. note:: This will override any existing extras that are present in the new dictionary.

        :param extras: a dictionary with the extras to set
        :raise aiida.common.ValidationError: if any of the keys are invalid, i.e. contain periods
        """
        self._backend_entity.set_extra_many(extras)

    def reset(self, extras: Dict[str, Any]) -> None:
        """Reset the extras.

        .. note:: This will completely clear any existing extras and replace them with the new dictionary.

        :param extras: a dictionary with the extras to set
        :raise aiida.common.ValidationError: if any of the keys are invalid, i.e. contain periods
        """
        self._backend_entity.reset_extras(extras)

    def delete(self, key: str) -> None:
        """Delete an extra.

        :param key: name of the extra
        :raises AttributeError: if the extra does not exist
        """
        self._backend_entity.delete_extra(key)

    def delete_many(self, keys: List[str]) -> None:
        """Delete multiple extras.

        :param keys: names of the extras to delete
        :raises AttributeError: if at least one of the extra does not exist
        """
        self._backend_entity.delete_extra_many(keys)

    def clear(self) -> None:
        """Delete all extras."""
        self._backend_entity.clear_extras()

    def items(self) -> Iterable[Tuple[str, Any]]:
        """Return an iterator over the extras.

        :return: an iterator with extra key value pairs
        """
        return self._backend_entity.extras_items()

    def keys(self) -> Iterable[str]:
        """Return an iterator over the extra keys.

        :return: an iterator with extra keys
        """
        return self._backend_entity.extras_keys()
