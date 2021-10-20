# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Comment objects and functions"""
from typing import List, Type

from aiida.common.lang import classproperty
from aiida.manage.manager import get_manager

from . import entities, users

__all__ = ('Comment',)


class CommentCollection(entities.Collection['Comment']):
    """The collection of Comment entries."""

    @staticmethod
    def _entity_base_cls() -> Type['Comment']:
        return Comment

    def delete(self, pk: int) -> None:
        """
        Remove a Comment from the collection with the given id

        :param pk: the id of the comment to delete

        :raises TypeError: if ``comment_id`` is not an `int`
        :raises `~aiida.common.exceptions.NotExistent`: if Comment with ID ``comment_id`` is not found
        """
        self._backend.comments.delete(pk)

    def delete_all(self) -> None:
        """
        Delete all Comments from the Collection

        :raises `~aiida.common.exceptions.IntegrityError`: if all Comments could not be deleted
        """
        self._backend.comments.delete_all()

    def delete_many(self, filters) -> List[int]:
        """
        Delete Comments from the Collection based on ``filters``

        :param filters: similar to QueryBuilder filter
        :type filters: dict

        :return: (former) ``PK`` s of deleted Comments

        :raises TypeError: if ``filters`` is not a `dict`
        :raises `~aiida.common.exceptions.ValidationError`: if ``filters`` is empty
        """
        return self._backend.comments.delete_many(filters)


class Comment(entities.Entity):
    """Base class to map a DbComment that represents a comment attached to a certain Node."""

    Collection = CommentCollection

    @classproperty
    def objects(cls) -> CommentCollection:  # pylint: disable=no-self-argument
        return CommentCollection.get_cached(cls, get_manager().get_backend())

    def __init__(self, node, user, content=None, backend=None):
        """
        Create a Comment for a given node and user

        :param node: a Node instance
        :type node: :class:`aiida.orm.Node`

        :param user: a User instance
        :type user: :class:`aiida.orm.User`

        :param content: the comment content
        :type content: str

        :return: a Comment object associated to the given node and user
        :rtype: :class:`aiida.orm.Comment`
        """
        backend = backend or get_manager().get_backend()
        model = backend.comments.create(node=node.backend_entity, user=user.backend_entity, content=content)
        super().__init__(model)

    def __str__(self):
        arguments = [self.uuid, self.node.pk, self.user.email, self.content]
        return 'Comment<{}> for node<{}> and user<{}>: {}'.format(*arguments)

    @property
    def ctime(self):
        return self._backend_entity.ctime

    @property
    def mtime(self):
        return self._backend_entity.mtime

    def set_mtime(self, value):
        return self._backend_entity.set_mtime(value)

    @property
    def node(self):
        return self._backend_entity.node

    @property
    def user(self):
        return users.User.from_backend_entity(self._backend_entity.user)

    def set_user(self, value):
        self._backend_entity.user = value.backend_entity

    @property
    def content(self):
        return self._backend_entity.content

    def set_content(self, value):
        return self._backend_entity.set_content(value)
