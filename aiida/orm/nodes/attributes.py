# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Interface to the attributes of a node instance."""
import copy
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Tuple

if TYPE_CHECKING:
    from .node import Node

__all__ = ('NodeAttributes',)

_NO_DEFAULT: Any = tuple()


class NodeAttributes:
    """Interface to the attributes of a node instance.

    Attributes are a JSONable dictionary, stored on each node,
    allowing for arbitrary data to be stored by node subclasses (and thus data plugins).

    Once the node is stored, the attributes are generally deemed immutable
    (except for some updatable keys on process nodes, which can be mutated whilst the node is not "sealed").
    """

    def __init__(self, node: 'Node') -> None:
        """Initialize the interface."""
        self._node = node
        self._backend_node = node.backend_entity

    def __contains__(self, key: str) -> bool:
        """Check if the node contains an attribute with the given key."""
        return key in self._backend_node.attributes

    @property
    def all(self) -> Dict[str, Any]:
        """Return the complete attributes dictionary.

        .. warning:: While the entity is unstored, this will return references of the attributes on the database model,
            meaning that changes on the returned values (if they are mutable themselves, e.g. a list or dictionary) will
            automatically be reflected on the database model as well. As soon as the entity is stored, the returned
            attributes will be a deep copy and mutations of the database attributes will have to go through the
            appropriate set methods. Therefore, once stored, retrieving a deep copy can be a heavy operation. If you
            only need the keys or some values, use the iterators `keys` and `items`, or the
            getters `get` and `get_many` instead.

        :return: the attributes as a dictionary
        """
        attributes = self._backend_node.attributes

        if self._node.is_stored:
            attributes = copy.deepcopy(attributes)

        return attributes

    def get(self, key: str, default=_NO_DEFAULT) -> Any:
        """Return the value of an attribute.

        .. warning:: While the entity is unstored, this will return a reference of the attribute on the database model,
            meaning that changes on the returned value (if they are mutable themselves, e.g. a list or dictionary) will
            automatically be reflected on the database model as well. As soon as the entity is stored, the returned
            attribute will be a deep copy and mutations of the database attributes will have to go through the
            appropriate set methods.

        :param key: name of the attribute
        :param default: return this value instead of raising if the attribute does not exist
        :return: the value of the attribute
        :raises AttributeError: if the attribute does not exist and no default is specified
        """
        try:
            attribute = self._backend_node.get_attribute(key)
        except AttributeError:
            if default is _NO_DEFAULT:
                raise
            attribute = default

        if self._node.is_stored:
            attribute = copy.deepcopy(attribute)

        return attribute

    def get_many(self, keys: List[str]) -> List[Any]:
        """Return the values of multiple attributes.

        .. warning:: While the entity is unstored, this will return references of the attributes on the database model,
            meaning that changes on the returned values (if they are mutable themselves, e.g. a list or dictionary) will
            automatically be reflected on the database model as well. As soon as the entity is stored, the returned
            attributes will be a deep copy and mutations of the database attributes will have to go through the
            appropriate set methods. Therefore, once stored, retrieving a deep copy can be a heavy operation. If you
            only need the keys or some values, use the iterators `keys` and `items`, or the
            getters `get` and `get_many` instead.

        :param keys: a list of attribute names
        :return: a list of attribute values
        :raises AttributeError: if at least one attribute does not exist
        """
        attributes = self._backend_node.get_attribute_many(keys)

        if self._node.is_stored:
            attributes = copy.deepcopy(attributes)

        return attributes

    def set(self, key: str, value: Any) -> None:
        """Set an attribute to the given value.

        :param key: name of the attribute
        :param value: value of the attribute
        :raise aiida.common.ValidationError: if the key is invalid, i.e. contains periods
        :raise aiida.common.ModificationNotAllowed: if the entity is stored
        """
        self._node._check_mutability_attributes([key])  # pylint: disable=protected-access
        self._backend_node.set_attribute(key, value)

    def set_many(self, attributes: Dict[str, Any]) -> None:
        """Set multiple attributes.

        .. note:: This will override any existing attributes that are present in the new dictionary.

        :param attributes: a dictionary with the attributes to set
        :raise aiida.common.ValidationError: if any of the keys are invalid, i.e. contain periods
        :raise aiida.common.ModificationNotAllowed: if the entity is stored
        """
        self._node._check_mutability_attributes(list(attributes))  # pylint: disable=protected-access
        self._backend_node.set_attribute_many(attributes)

    def reset(self, attributes: Dict[str, Any]) -> None:
        """Reset the attributes.

        .. note:: This will completely clear any existing attributes and replace them with the new dictionary.

        :param attributes: a dictionary with the attributes to set
        :raise aiida.common.ValidationError: if any of the keys are invalid, i.e. contain periods
        :raise aiida.common.ModificationNotAllowed: if the entity is stored
        """
        self._node._check_mutability_attributes()  # pylint: disable=protected-access
        self._backend_node.reset_attributes(attributes)

    def delete(self, key: str) -> None:
        """Delete an attribute.

        :param key: name of the attribute
        :raises AttributeError: if the attribute does not exist
        :raise aiida.common.ModificationNotAllowed: if the entity is stored
        """
        self._node._check_mutability_attributes([key])  # pylint: disable=protected-access
        self._backend_node.delete_attribute(key)

    def delete_many(self, keys: List[str]) -> None:
        """Delete multiple attributes.

        :param keys: names of the attributes to delete
        :raises AttributeError: if at least one of the attribute does not exist
        :raise aiida.common.ModificationNotAllowed: if the entity is stored
        """
        self._node._check_mutability_attributes(keys)  # pylint: disable=protected-access
        self._backend_node.delete_attribute_many(keys)

    def clear(self) -> None:
        """Delete all attributes."""
        self._node._check_mutability_attributes()  # pylint: disable=protected-access
        self._backend_node.clear_attributes()

    def items(self) -> Iterable[Tuple[str, Any]]:
        """Return an iterator over the attributes.

        :return: an iterator with attribute key value pairs
        """
        return self._backend_node.attributes_items()

    def keys(self) -> Iterable[str]:
        """Return an iterator over the attribute keys.

        :return: an iterator with attribute keys
        """
        return self._backend_node.attributes_keys()
