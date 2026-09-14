###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Comment objects and functions"""

from __future__ import annotations

import typing as t
from datetime import datetime

from aiida.manage import get_manager
from aiida.orm import entities, nodes
from aiida.orm.decorators import column
from aiida.orm.implementation import BackendNode
from aiida.orm.models.adapters import BackendEntityPkAdapter, EntityPkAdapter
from aiida.orm.users import User

if t.TYPE_CHECKING:
    from aiida.orm.implementation import BackendComment, StorageBackend
    from aiida.orm.nodes.node import Node

__all__ = ('Comment',)


class CommentCollection(entities.EntityCollection['Comment']):
    """The collection of Comment entries."""

    collection_type: t.ClassVar[str] = 'comments'

    def delete(self, pk: int) -> None:
        """Remove a Comment from the collection with the given id

        :param pk: the id of the comment to delete

        :raises TypeError: if ``comment_id`` is not an `int`
        :raises `~aiida.common.exceptions.NotExistent`: if Comment with ID ``comment_id`` is not found
        """
        self._backend.comments.delete(pk)

    def delete_all(self) -> None:
        """Delete all Comments from the Collection

        :raises `~aiida.common.exceptions.IntegrityError`: if all Comments could not be deleted
        """
        self._backend.comments.delete_all()

    def delete_many(self, filters: dict) -> list[int]:
        """Delete Comments from the Collection based on ``filters``

        :param filters: similar to QueryBuilder filter

        :return: (former) ``PK`` s of deleted Comments

        :raises TypeError: if ``filters`` is not a `dict`
        :raises `~aiida.common.exceptions.ValidationError`: if ``filters`` is empty
        """
        return self._backend.comments.delete_many(filters)

    @staticmethod
    def _entity_base_cls() -> type[Comment]:
        return Comment


class Comment(entities.Entity['BackendComment', CommentCollection]):
    """ORM representation of a comment attached to a Node."""

    identity_field = 'uuid'

    _CLS_COLLECTION = CommentCollection

    def __init__(
        self,
        node: Node,
        user: User,
        content: str | None = None,
        backend: StorageBackend | None = None,
    ):
        """Create a Comment for a given node and user

        :param node: a Node instance
        :param user: a User instance
        :param content: the comment content
        :param backend: the backend to use for the instance, or use the default backend if None

        :return: a Comment object associated to the given node and user
        """
        backend = backend or get_manager().get_profile_storage()
        model = backend.comments.create(
            node=node.backend_entity,
            user=user.backend_entity,
            content=content,
        )
        super().__init__(model)

    def __str__(self) -> str:
        arguments = [self.uuid, self.node.pk, self.user.email, self.content]
        return 'Comment<{}> for node<{}> and user<{}>: {}'.format(*arguments)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Comment):
            return False

        return self.uuid == other.uuid

    @column(readonly=True)
    def uuid(self) -> str:
        """The UUID for this comment."""
        return self._backend_entity.uuid

    @column(readonly=True)
    def ctime(self) -> datetime:
        """The creation time of this comment."""
        return self._backend_entity.ctime

    @column(readonly=True)
    def mtime(self) -> datetime:
        """The last modification time of this comment."""
        return self._backend_entity.mtime

    @column(
        model_adapter=BackendEntityPkAdapter(BackendNode, nodes.Node),
    )
    def node(self) -> BackendNode:
        """The node associated with this comment."""
        return self._backend_entity.node

    @node.setter
    def node(self, value: BackendNode) -> None:
        self._backend_entity.node = value

    @column(
        model_adapter=EntityPkAdapter(User),
    )
    def user(self) -> User:
        """The user associated with this comment."""
        from aiida.orm.users import User

        return entities.from_backend_entity(User, self._backend_entity.user)

    @user.setter
    def user(self, value: User) -> None:
        self._backend_entity.user = value.backend_entity

    @column
    def content(self) -> str:
        """The content of this comment."""
        return self._backend_entity.content

    @content.setter
    def content(self, value: str) -> None:
        return self._backend_entity.set_content(value)

    def set_mtime(self, value: datetime) -> None:
        return self._backend_entity.set_mtime(value)

    # TODO the following methods are handled above via property operations - consider removing

    def set_user(self, value: User) -> None:
        self.user = value

    def set_content(self, value: str) -> None:
        self.content = value
