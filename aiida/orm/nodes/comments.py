# -*- coding: utf-8 -*-
"""Interface for comments of a node instance."""
from __future__ import annotations

import typing as t

from ..comments import Comment
from ..users import User


class NodeComments:
    """Interface for comments of a node instance."""

    def __init__(self, node: 'Node') -> None:
        """Initialize the comments interface."""
        self._node = node

    def add(self, content: str, user: t.Optional[User] = None) -> Comment:
        """Add a new comment.

        :param content: string with comment
        :param user: the user to associate with the comment, will use default if not supplied
        :return: the newly created comment
        """
        user = user or User.collection(self._node.backend).get_default()
        return Comment(node=self._node, user=user, content=content).store()

    def get(self, identifier: int) -> Comment:
        """Return a comment corresponding to the given identifier.

        :param identifier: the comment pk
        :raise aiida.common.NotExistent: if the comment with the given id does not exist
        :raise aiida.common.MultipleObjectsError: if the id cannot be uniquely resolved to a comment
        :return: the comment
        """
        return Comment.collection(self._node.backend).get(dbnode_id=self._node.pk, id=identifier)

    def all(self) -> list[Comment]:
        """Return a sorted list of comments for this node.

        :return: the list of comments, sorted by pk
        """
        return Comment.collection(self._node.backend
                                  ).find(filters={'dbnode_id': self._node.pk}, order_by=[{
                                      'id': 'asc'
                                  }])

    def update(self, identifier: int, content: str) -> None:
        """Update the content of an existing comment.

        :param identifier: the comment pk
        :param content: the new comment content
        :raise aiida.common.NotExistent: if the comment with the given id does not exist
        :raise aiida.common.MultipleObjectsError: if the id cannot be uniquely resolved to a comment
        """
        comment = Comment.collection(self._node.backend).get(dbnode_id=self._node.pk, id=identifier)
        comment.set_content(content)

    def remove(self, identifier: int) -> None:  # pylint: disable=no-self-use
        """Delete an existing comment.

        :param identifier: the comment pk
        """
        Comment.collection(self._node.backend).delete(identifier)
