# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Backend group module"""
import abc
from typing import TYPE_CHECKING, List, Optional, Protocol, Sequence, Union

from .entities import BackendCollection, BackendEntity, BackendEntityExtrasMixin
from .nodes import BackendNode

if TYPE_CHECKING:
    from .users import BackendUser

__all__ = ('BackendGroup', 'BackendGroupCollection')


class NodeIterator(Protocol):
    """Protocol for iterating over nodes in a group"""

    def __iter__(self) -> 'NodeIterator':  # pylint: disable=non-iterator-returned
        """Return an iterator over the nodes in the group."""
        ...

    def __next__(self) -> BackendNode:
        """Return the next node in the group."""
        ...

    def __getitem__(self, value: Union[int, slice]) -> Union[BackendNode, List[BackendNode]]:
        """Index node(s) from the group."""
        ...

    def __len__(self) -> int:  # pylint: disable=invalid-length-returned
        """Return the number of nodes in the group."""
        ...


class BackendGroup(BackendEntity, BackendEntityExtrasMixin):
    """Backend implementation for the `Group` ORM class.

    A group is a collection of nodes.
    """

    @property
    @abc.abstractmethod
    def label(self) -> str:
        """Return the name of the group as a string."""

    @label.setter
    @abc.abstractmethod
    def label(self, name: str) -> None:
        """
        Attempt to change the name of the group instance. If the group is already stored
        and the another group of the same type already exists with the desired name, a
        UniquenessError will be raised

        :param name: the new group name
        :raises aiida.common.UniquenessError: if another group of same type and name already exists
        """

    @property
    @abc.abstractmethod
    def description(self) -> Optional[str]:
        """Return the description of the group as a string."""

    @description.setter
    @abc.abstractmethod
    def description(self, value: Optional[str]):
        """Return the description of the group as a string."""

    @property
    @abc.abstractmethod
    def type_string(self) -> str:
        """Return the string defining the type of the group."""

    @property
    @abc.abstractmethod
    def user(self) -> 'BackendUser':
        """Return a backend user object, representing the user associated to this group."""

    @user.setter
    @abc.abstractmethod
    def user(self, user: 'BackendUser') -> None:
        """Set the user of this group."""

    @property
    @abc.abstractmethod
    def uuid(self) -> str:
        """Return the UUID of the group."""

    @property
    @abc.abstractmethod
    def nodes(self) -> NodeIterator:
        """
        Return a generator/iterator that iterates over all nodes and returns
        the respective AiiDA subclasses of Node, and also allows to ask for
        the number of nodes in the group using len().
        """

    @abc.abstractmethod
    def count(self) -> int:
        """Return the number of entities in this group.

        :return: integer number of entities contained within the group
        """

    @abc.abstractmethod
    def clear(self) -> None:
        """Remove all the nodes from this group."""

    def add_nodes(self, nodes: Sequence[BackendNode], **kwargs):  # pylint: disable=unused-argument
        """Add a set of nodes to the group.

        :note: all the nodes *and* the group itself have to be stored.

        :param nodes: a list of `BackendNode` instances to be added to this group
        """
        if not self.is_stored:
            raise ValueError('group has to be stored before nodes can be added')

        if not isinstance(nodes, (list, tuple)):
            raise TypeError('nodes has to be a list or tuple')

        if any(not isinstance(node, BackendNode) for node in nodes):
            raise TypeError(f'nodes have to be of type {BackendNode}')

    def remove_nodes(self, nodes: Sequence[BackendNode]) -> None:
        """Remove a set of nodes from the group.

        :note: all the nodes *and* the group itself have to be stored.

        :param nodes: a list of `BackendNode` instances to be removed from this group
        """
        if not self.is_stored:
            raise ValueError('group has to be stored before nodes can be removed')

        if not isinstance(nodes, (list, tuple)):
            raise TypeError('nodes has to be a list or tuple')

        if any(not isinstance(node, BackendNode) for node in nodes):
            raise TypeError(f'nodes have to be of type {BackendNode}')

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}: {str(self)}>'

    def __str__(self) -> str:
        if self.type_string:
            return f'"{self.label}" [type {self.type_string}], of user {self.user.email}'

        return f'"{self.label}" [user-defined], of user {self.user.email}'


class BackendGroupCollection(BackendCollection[BackendGroup]):
    """The collection of Group entries."""

    ENTITY_CLASS = BackendGroup

    @abc.abstractmethod
    def delete(self, id: int) -> None:  # pylint: disable=redefined-builtin, invalid-name
        """
        Delete a group with the given id

        :param id: the id of the group to delete
        """
