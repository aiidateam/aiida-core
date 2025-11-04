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

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional, Type, cast
from uuid import UUID

from aiida.common.pydantic import MetadataField
from aiida.manage import get_manager

from . import entities

if TYPE_CHECKING:
    from aiida.orm.implementation import BackendComment, BackendNode, StorageBackend

    from .nodes.node import Node
    from .users import User

__all__ = ('Comment',)


class CommentCollection(entities.Collection['Comment']):
    """The collection of Comment entries."""

    @staticmethod
    def _entity_base_cls() -> Type[Comment]:
        return Comment

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

    def delete_many(self, filters: dict) -> List[int]:
        """Delete Comments from the Collection based on ``filters``

        :param filters: similar to QueryBuilder filter

        :return: (former) ``PK`` s of deleted Comments

        :raises TypeError: if ``filters`` is not a `dict`
        :raises `~aiida.common.exceptions.ValidationError`: if ``filters`` is empty
        """
        return self._backend.comments.delete_many(filters)


class Comment(entities.Entity['BackendComment', CommentCollection]):
    """Base class to map a DbComment that represents a comment attached to a certain Node."""

    _CLS_COLLECTION = CommentCollection

    class Model(entities.Entity.Model):
        uuid: UUID = MetadataField(
            description='The UUID of the comment',
            is_attribute=False,
            exclude_to_orm=True,
        )
        ctime: datetime = MetadataField(
            description='Creation time of the comment',
            is_attribute=False,
            exclude_to_orm=True,
        )
        mtime: datetime = MetadataField(
            description='Modified time of the comment',
            is_attribute=False,
            exclude_to_orm=True,
        )
        node: int = MetadataField(
            description='Node PK that the comment is attached to',
            is_attribute=False,
            orm_class='core.node',
            orm_to_model=lambda comment: cast(Comment, comment).node.pk,
        )
        user: int = MetadataField(
            description='User PK that created the comment',
            is_attribute=False,
            orm_class='core.user',
            orm_to_model=lambda comment: cast(Comment, comment).user.pk,
        )
        content: str = MetadataField(
            description='Content of the comment',
            is_attribute=False,
        )

    def __init__(
        self, node: 'Node', user: 'User', content: Optional[str] = None, backend: Optional['StorageBackend'] = None
    ):
        """Create a Comment for a given node and user

        :param node: a Node instance
        :param user: a User instance
        :param content: the comment content
        :param backend: the backend to use for the instance, or use the default backend if None

        :return: a Comment object associated to the given node and user
        """
        backend = backend or get_manager().get_profile_storage()
        model = backend.comments.create(node=node.backend_entity, user=user.backend_entity, content=content)
        super().__init__(model)

    def __str__(self) -> str:
        arguments = [self.uuid, self.node.pk, self.user.email, self.content]
        return 'Comment<{}> for node<{}> and user<{}>: {}'.format(*arguments)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Comment):
            return False

        return self.uuid == other.uuid

    @property
    def uuid(self) -> str:
        """Return the UUID for this comment.

        This identifier is unique across all entities types and backend instances.

        :return: the entity uuid
        """
        return self._backend_entity.uuid

    @property
    def ctime(self) -> datetime:
        return self._backend_entity.ctime

    @property
    def mtime(self) -> datetime:
        return self._backend_entity.mtime

    def set_mtime(self, value: datetime) -> None:
        return self._backend_entity.set_mtime(value)

    @property
    def node(self) -> 'BackendNode':
        return self._backend_entity.node

    @property
    def user(self) -> 'User':
        from aiida.orm.users import User

        return entities.from_backend_entity(User, self._backend_entity.user)

    def set_user(self, value: 'User') -> None:
        # mypy error: Property "user" defined in "BackendComment" is read-only
        self._backend_entity.user = value.backend_entity  # type: ignore[misc]

    @property
    def content(self) -> str:
        return self._backend_entity.content

    def set_content(self, value: str) -> None:
        return self._backend_entity.set_content(value)
