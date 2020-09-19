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

from .entities import BackendEntity, BackendCollection

__all__ = ('BackendComment', 'BackendCommentCollection')


class BackendComment(BackendEntity):
    """Base class for a node comment."""

    @property
    def uuid(self):
        return str(self._dbmodel.uuid)

    @abc.abstractproperty
    def ctime(self):
        pass

    @abc.abstractproperty
    def mtime(self):
        pass

    @abc.abstractmethod
    def set_mtime(self, value):
        pass

    @abc.abstractproperty
    def node(self):
        pass

    @abc.abstractproperty
    def user(self):
        pass

    @abc.abstractmethod
    def set_user(self, value):
        pass

    @abc.abstractproperty
    def content(self):
        pass

    @abc.abstractmethod
    def set_content(self, value):
        pass


class BackendCommentCollection(BackendCollection[BackendComment]):
    """The collection of Comment entries."""

    ENTITY_CLASS = BackendComment

    @abc.abstractmethod
    def create(self, node, user, content=None, **kwargs):  # pylint: disable=arguments-differ
        """
        Create a Comment for a given node and user

        :param node: a Node instance
        :param user: a User instance
        :param content: the comment content
        :return: a Comment object associated to the given node and user
        """

    @abc.abstractmethod
    def delete(self, comment_id):
        """
        Remove a Comment from the collection with the given id

        :param comment_id: the id of the comment to delete
        :type comment_id: int

        :raises TypeError: if ``comment_id`` is not an `int`
        :raises `~aiida.common.exceptions.NotExistent`: if Comment with ID ``comment_id`` is not found
        """

    @abc.abstractmethod
    def delete_all(self):
        """
        Delete all Comment entries.

        :raises `~aiida.common.exceptions.IntegrityError`: if all Comments could not be deleted
        """

    @abc.abstractmethod
    def delete_many(self, filters):
        """
        Delete Comments based on ``filters``

        :param filters: similar to QueryBuilder filter
        :type filters: dict

        :return: (former) ``PK`` s of deleted Comments
        :rtype: list

        :raises TypeError: if ``filters`` is not a `dict`
        :raises `~aiida.common.exceptions.ValidationError`: if ``filters`` is empty
        """
