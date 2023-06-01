# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Abstract BackendNode and BackendNodeCollection implementation."""
import abc
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Sequence, Tuple, TypeVar

from .entities import BackendCollection, BackendEntity, BackendEntityExtrasMixin

if TYPE_CHECKING:
    from ..utils import LinkTriple
    from .computers import BackendComputer
    from .users import BackendUser

__all__ = ('BackendNode', 'BackendNodeCollection')

BackendNodeType = TypeVar('BackendNodeType', bound='BackendNode')


class BackendNode(BackendEntity, BackendEntityExtrasMixin, metaclass=abc.ABCMeta):
    """Backend implementation for the `Node` ORM class.

    A node stores data input or output from a computation.
    """

    # pylint: disable=too-many-public-methods

    @abc.abstractmethod
    def clone(self: BackendNodeType) -> BackendNodeType:
        """Return an unstored clone of ourselves.

        :return: an unstored `BackendNode` with the exact same attributes and extras as self
        """

    @property
    @abc.abstractmethod
    def uuid(self) -> str:
        """Return the node UUID.

        :return: the string representation of the UUID
        """

    @property
    @abc.abstractmethod
    def node_type(self) -> str:
        """Return the node type.

        :return: the node type
        """

    @property
    @abc.abstractmethod
    def process_type(self) -> Optional[str]:
        """Return the node process type.

        :return: the process type
        """

    @process_type.setter
    @abc.abstractmethod
    def process_type(self, value: Optional[str]) -> None:
        """Set the process type.

        :param value: the new value to set
        """

    @property
    @abc.abstractmethod
    def label(self) -> str:
        """Return the node label.

        :return: the label
        """

    @label.setter
    @abc.abstractmethod
    def label(self, value: str) -> None:
        """Set the label.

        :param value: the new value to set
        """

    @property
    @abc.abstractmethod
    def description(self) -> str:
        """Return the node description.

        :return: the description
        """

    @description.setter
    @abc.abstractmethod
    def description(self, value: str) -> None:
        """Set the description.

        :param value: the new value to set
        """

    @property
    @abc.abstractmethod
    def repository_metadata(self) -> Dict[str, Any]:
        """Return the node repository metadata.

        :return: the repository metadata
        """

    @repository_metadata.setter
    @abc.abstractmethod
    def repository_metadata(self, value: Dict[str, Any]) -> None:
        """Set the repository metadata.

        :param value: the new value to set
        """

    @property
    @abc.abstractmethod
    def computer(self) -> Optional['BackendComputer']:
        """Return the computer of this node.

        :return: the computer or None
        """

    @computer.setter
    @abc.abstractmethod
    def computer(self, computer: Optional['BackendComputer']) -> None:
        """Set the computer of this node.

        :param computer: a `BackendComputer`
        """

    @property
    @abc.abstractmethod
    def user(self) -> 'BackendUser':
        """Return the user of this node.

        :return: the user
        """

    @user.setter
    @abc.abstractmethod
    def user(self, user: 'BackendUser') -> None:
        """Set the user of this node.

        :param user: a `BackendUser`
        """

    @property
    @abc.abstractmethod
    def ctime(self) -> datetime:
        """Return the node ctime.

        :return: the ctime
        """

    @property
    @abc.abstractmethod
    def mtime(self) -> datetime:
        """Return the node mtime.

        :return: the mtime
        """

    @abc.abstractmethod
    def add_incoming(self, source: 'BackendNode', link_type, link_label):
        """Add a link of the given type from a given node to ourself.

        :param source: the node from which the link is coming
        :param link_type: the link type
        :param link_label: the link label
        :return: True if the proposed link is allowed, False otherwise
        :raise TypeError: if `source` is not a Node instance or `link_type` is not a `LinkType` enum
        :raise ValueError: if the proposed link is invalid
        :raise aiida.common.ModificationNotAllowed: if either source or target node is not stored
        """

    @abc.abstractmethod
    def store(  # pylint: disable=arguments-differ
        self: BackendNodeType,
        links: Optional[Sequence['LinkTriple']] = None,
        with_transaction: bool = True,
        clean: bool = True
    ) -> BackendNodeType:
        """Store the node in the database.

        :param links: optional links to add before storing
        :param with_transaction: if False, do not use a transaction because the caller will already have opened one.
        :param clean: boolean, if True, will clean the attributes and extras before attempting to store
        """

    @abc.abstractmethod
    def clean_values(self):
        """Clean the values of the node fields.

        This method is called before storing the node.
        The purpose of this method is to convert data to a type which can be serialized and deserialized
        for storage in the DB without its value changing.
        """

    # attributes methods

    @property
    @abc.abstractmethod
    def attributes(self) -> Dict[str, Any]:
        """Return the complete attributes dictionary.

        .. warning:: While the entity is unstored, this will return references of the attributes on the database model,
            meaning that changes on the returned values (if they are mutable themselves, e.g. a list or dictionary) will
            automatically be reflected on the database model as well. As soon as the entity is stored, the returned
            attributes will be a deep copy and mutations of the database attributes will have to go through the
            appropriate set methods. Therefore, once stored, retrieving a deep copy can be a heavy operation. If you
            only need the keys or some values, use the iterators `attributes_keys` and `attributes_items`, or the
            getters `get_attribute` and `get_attribute_many` instead.

        :return: the attributes as a dictionary
        """

    @abc.abstractmethod
    def get_attribute(self, key: str) -> Any:
        """Return the value of an attribute.

        .. warning:: While the entity is unstored, this will return a reference of the attribute on the database model,
            meaning that changes on the returned value (if they are mutable themselves, e.g. a list or dictionary) will
            automatically be reflected on the database model as well. As soon as the entity is stored, the returned
            attribute will be a deep copy and mutations of the database attributes will have to go through the
            appropriate set methods.

        :param key: name of the attribute
        :return: the value of the attribute
        :raises AttributeError: if the attribute does not exist
        """

    def get_attribute_many(self, keys: Iterable[str]) -> List[Any]:
        """Return the values of multiple attributes.

        .. warning:: While the entity is unstored, this will return references of the attributes on the database model,
            meaning that changes on the returned values (if they are mutable themselves, e.g. a list or dictionary) will
            automatically be reflected on the database model as well. As soon as the entity is stored, the returned
            attributes will be a deep copy and mutations of the database attributes will have to go through the
            appropriate set methods. Therefore, once stored, retrieving a deep copy can be a heavy operation. If you
            only need the keys or some values, use the iterators `attributes_keys` and `attributes_items`, or the
            getters `get_attribute` and `get_attribute_many` instead.

        :param keys: a list of attribute names
        :return: a list of attribute values
        :raises AttributeError: if at least one attribute does not exist
        """
        try:
            return [self.get_attribute(key) for key in keys]
        except KeyError as exception:
            raise AttributeError(f'attribute `{exception}` does not exist') from exception

    @abc.abstractmethod
    def set_attribute(self, key: str, value: Any) -> None:
        """Set an attribute to the given value.

        :param key: name of the attribute
        :param value: value of the attribute
        """

    def set_attribute_many(self, attributes: Dict[str, Any]) -> None:
        """Set multiple attributes.

        .. note:: This will override any existing attributes that are present in the new dictionary.

        :param attributes: a dictionary with the attributes to set
        """
        for key, value in attributes.items():
            self.set_attribute(key, value)

    @abc.abstractmethod
    def reset_attributes(self, attributes: Dict[str, Any]) -> None:
        """Reset the attributes.

        .. note:: This will completely clear any existing attributes and replace them with the new dictionary.

        :param attributes: a dictionary with the attributes to set
        """

    @abc.abstractmethod
    def delete_attribute(self, key: str) -> None:
        """Delete an attribute.

        :param key: name of the attribute
        :raises AttributeError: if the attribute does not exist
        """

    def delete_attribute_many(self, keys: Iterable[str]) -> None:
        """Delete multiple attributes.

        :param keys: names of the attributes to delete
        :raises AttributeError: if at least one of the attribute does not exist
        """
        for key in keys:
            self.delete_attribute(key)

    @abc.abstractmethod
    def clear_attributes(self):
        """Delete all attributes."""

    @abc.abstractmethod
    def attributes_items(self) -> Iterable[Tuple[str, Any]]:
        """Return an iterator over the attributes.

        :return: an iterator with attribute key value pairs
        """

    @abc.abstractmethod
    def attributes_keys(self) -> Iterable[str]:
        """Return an iterator over the attribute keys.

        :return: an iterator with attribute keys
        """


class BackendNodeCollection(BackendCollection[BackendNode]):
    """The collection of `BackendNode` entries."""

    ENTITY_CLASS = BackendNode

    @abc.abstractmethod
    def get(self, pk: int):
        """Return a Node entry from the collection with the given id

        :param pk: id of the node
        """

    @abc.abstractmethod
    def delete(self, pk: int) -> None:
        """Remove a Node entry from the collection with the given id

        :param pk: id of the node to delete
        """
