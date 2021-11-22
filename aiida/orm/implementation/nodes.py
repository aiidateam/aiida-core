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
from typing import TYPE_CHECKING, Any, Dict, Optional, Sequence, TypeVar

from .entities import BackendCollection, BackendEntity, BackendEntityAttributesMixin, BackendEntityExtrasMixin

if TYPE_CHECKING:
    from ..utils import LinkTriple
    from .computers import BackendComputer
    from .users import BackendUser

__all__ = ('BackendNode', 'BackendNodeCollection')

BackendNodeType = TypeVar('BackendNodeType', bound='BackendNode')


class BackendNode(BackendEntity, BackendEntityExtrasMixin, BackendEntityAttributesMixin, metaclass=abc.ABCMeta):
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

    @property  # type: ignore[misc]
    @abc.abstractmethod
    def process_type(self) -> Optional[str]:
        """Return the node process type.

        :return: the process type
        """

    @process_type.setter  # type: ignore[misc]
    @abc.abstractmethod
    def process_type(self, value: Optional[str]) -> None:
        """Set the process type.

        :param value: the new value to set
        """

    @property  # type: ignore[misc]
    @abc.abstractmethod
    def label(self) -> str:
        """Return the node label.

        :return: the label
        """

    @label.setter  # type: ignore[misc]
    @abc.abstractmethod
    def label(self, value: str) -> None:
        """Set the label.

        :param value: the new value to set
        """

    @property  # type: ignore[misc]
    @abc.abstractmethod
    def description(self) -> str:
        """Return the node description.

        :return: the description
        """

    @description.setter  # type: ignore[misc]
    @abc.abstractmethod
    def description(self, value: str) -> None:
        """Set the description.

        :param value: the new value to set
        """

    @property  # type: ignore[misc]
    @abc.abstractmethod
    def repository_metadata(self) -> Dict[str, Any]:
        """Return the node repository metadata.

        :return: the repository metadata
        """

    @repository_metadata.setter  # type: ignore[misc]
    @abc.abstractmethod
    def repository_metadata(self, value: Dict[str, Any]) -> None:
        """Set the repository metadata.

        :param value: the new value to set
        """

    @property  # type: ignore[misc]
    @abc.abstractmethod
    def computer(self) -> Optional['BackendComputer']:
        """Return the computer of this node.

        :return: the computer or None
        """

    @computer.setter  # type: ignore[misc]
    @abc.abstractmethod
    def computer(self, computer: Optional['BackendComputer']) -> None:
        """Set the computer of this node.

        :param computer: a `BackendComputer`
        """

    @property  # type: ignore[misc]
    @abc.abstractmethod
    def user(self) -> 'BackendUser':
        """Return the user of this node.

        :return: the user
        """

    @user.setter  # type: ignore[misc]
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
