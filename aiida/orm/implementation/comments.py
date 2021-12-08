# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for comment backend classes."""
import abc
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from .entities import BackendCollection, BackendEntity

if TYPE_CHECKING:
    from .nodes import BackendNode
    from .users import BackendUser

__all__ = ('BackendComment', 'BackendCommentCollection')


class BackendComment(BackendEntity):
    """Backend implementation for the `Comment` ORM class.

    A comment is a text that can be attached to a node.
    """

    @property
    @abc.abstractmethod
    def uuid(self) -> str:
        """Return the UUID of the comment."""

    @property
    @abc.abstractmethod
    def ctime(self) -> datetime:
        """Return the creation time of the comment."""

    @property
    @abc.abstractmethod
    def mtime(self) -> datetime:
        """Return the modified time of the comment."""

    @abc.abstractmethod
    def set_mtime(self, value: datetime) -> None:
        """Set the modified time of the comment."""

    @property
    @abc.abstractmethod
    def node(self) -> 'BackendNode':
        """Return the comment's node."""

    @property
    @abc.abstractmethod
    def user(self) -> 'BackendUser':
        """Return the comment owner."""

    @abc.abstractmethod
    def set_user(self, value: 'BackendUser') -> None:
        """Set the comment owner."""

    @property
    @abc.abstractmethod
    def content(self) -> str:
        """Return the comment content."""

    @abc.abstractmethod
    def set_content(self, value: str):
        """Set the comment content."""


class BackendCommentCollection(BackendCollection[BackendComment]):
    """The collection of Comment entries."""

    ENTITY_CLASS = BackendComment

    @abc.abstractmethod
    def create(  # type: ignore[override]  # pylint: disable=arguments-differ
        self, node: 'BackendNode', user: 'BackendUser', content: Optional[str] = None, **kwargs):
        """
        Create a Comment for a given node and user

        :param node: a Node instance
        :param user: a User instance
        :param content: the comment content
        :return: a Comment object associated to the given node and user
        """

    @abc.abstractmethod
    def delete(self, comment_id: int) -> None:
        """
        Remove a Comment from the collection with the given id

        :param comment_id: the id of the comment to delete

        :raises TypeError: if ``comment_id`` is not an `int`
        :raises `~aiida.common.exceptions.NotExistent`: if Comment with ID ``comment_id`` is not found
        """

    @abc.abstractmethod
    def delete_all(self) -> None:
        """
        Delete all Comment entries.

        :raises `~aiida.common.exceptions.IntegrityError`: if all Comments could not be deleted
        """

    @abc.abstractmethod
    def delete_many(self, filters: dict) -> List[int]:
        """
        Delete Comments based on ``filters``

        :param filters: similar to QueryBuilder filter

        :return: (former) ``PK`` s of deleted Comments

        :raises TypeError: if ``filters`` is not a `dict`
        :raises `~aiida.common.exceptions.ValidationError`: if ``filters`` is empty
        """
