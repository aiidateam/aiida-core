# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Sqla implementations for the Comment entity and collection."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import six

from aiida.backends.sqlalchemy.models import comment as models
from aiida.common import exceptions
from aiida.common import lang

from ..comments import BackendComment, BackendCommentCollection
from .utils import ModelWrapper
from . import entities
from . import users


class SqlaComment(entities.SqlaModelEntity[models.DbComment], BackendComment):
    """Comment implementation for Sqla."""

    MODEL_CLASS = models.DbComment

    def __init__(self, backend, node, user, content=None):
        """
        Construct a SqlaComment.

        :param node: a Node instance
        :param user: a User instance
        :param content: the comment content
        :return: a Comment object associated to the given node and user
        """
        super(SqlaComment, self).__init__(backend)
        lang.type_check(user, users.SqlaUser)  # pylint: disable=no-member
        self._dbmodel = ModelWrapper(models.DbComment(dbnode=node.dbnode, user=user.dbmodel, content=content))

    def store(self):
        """Can only store if both the node and user are stored as well."""
        if self._dbmodel.dbnode.id is None or self._dbmodel.user.id is None:
            self._dbmodel.dbnode = None
            raise exceptions.ModificationNotAllowed('The corresponding node and/or user are not stored')

        super(SqlaComment, self).store()

    @property
    def uuid(self):
        return six.text_type(self._dbmodel.uuid)

    @property
    def ctime(self):
        return self._dbmodel.ctime

    @property
    def mtime(self):
        return self._dbmodel.mtime

    def set_mtime(self, value):
        self._dbmodel.mtime = value

    @property
    def node(self):
        from aiida.orm import Node
        return Node(dbnode=self._dbmodel.dbnode)

    @property
    def user(self):
        return self._backend.users.from_dbmodel(self._dbmodel.user)

    def set_user(self, value):
        self._dbmodel.user = value

    @property
    def content(self):
        return self._dbmodel.content

    def set_content(self, value):
        self._dbmodel.content = value


class SqlaCommentCollection(BackendCommentCollection):
    """SqlAlchemy implementation for the CommentCollection."""

    def from_dbmodel(self, dbmodel):
        return SqlaComment.from_dbmodel(dbmodel, self.backend)

    def create(self, node, user, content=None):
        """
        Create a Comment for a given node and user

        :param node: a Node instance
        :param user: a User instance
        :param content: the comment content
        :return: a Comment object associated to the given node and user
        """
        return SqlaComment(self.backend, node, user, content)

    def delete(self, comment):
        """
        Remove a Comment from the collection with the given id

        :param comment: the id of the comment to delete
        """
        # pylint: disable=no-name-in-module,import-error
        from sqlalchemy.orm.exc import NoResultFound
        from aiida.backends.sqlalchemy import get_scoped_session
        session = get_scoped_session()

        try:
            session.query(models.DbComment).filter_by(id=comment).one().delete()
            session.commit()
        except NoResultFound:
            raise exceptions.NotExistent("Comment with id '{}' not found".format(comment))
