# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for comment backend classes."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import abc
import six

from . import backends

__all__ = ('BackendComment', 'BackendCommentCollection')


@six.add_metaclass(abc.ABCMeta)
class BackendComment(backends.BackendEntity):
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


@six.add_metaclass(abc.ABCMeta)
class BackendCommentCollection(backends.BackendCollection[BackendComment]):
    """The collection of Comment entries."""

    ENTITY_CLASS = BackendComment

    @abc.abstractmethod
    def create(self, node, user, content=None, **kwargs):
        """
        Create a Comment for a given node and user

        :param node: a Node instance
        :param user: a User instance
        :param content: the comment content
        :return: a Comment object associated to the given node and user
        """

    @abc.abstractmethod
    def delete(self, comment):
        """
        Remove a Comment from the collection with the given id

        :param comment: the id of the comment to delete
        """
