# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""SQLA implementations for the Comment entity and collection."""
# pylint: disable=import-error,no-name-in-module

from datetime import datetime

from sqlalchemy.orm.exc import NoResultFound

from aiida.backends.sqlalchemy.models import comment as models
from aiida.common import exceptions, lang

from . import entities, users, utils
from ..comments import BackendComment, BackendCommentCollection


class SqlaComment(entities.SqlaModelEntity[models.DbComment], BackendComment):
    """Comment implementation for Sqla."""

    MODEL_CLASS = models.DbComment

    # pylint: disable=too-many-arguments
    def __init__(self, backend, node, user, content=None, ctime=None, mtime=None):
        """
        Construct a SqlaComment.

        :param node: a Node instance
        :param user: a User instance
        :param content: the comment content
        :param ctime: The creation time as datetime object
        :param mtime: The modification time as datetime object
        :return: a Comment object associated to the given node and user
        """
        super().__init__(backend)
        lang.type_check(user, users.SqlaUser)  # pylint: disable=no-member

        arguments = {
            'dbnode': node.dbmodel,
            'user': user.dbmodel,
            'content': content,
        }

        if ctime:
            lang.type_check(ctime, datetime, f'the given ctime is of type {type(ctime)}')
            arguments['ctime'] = ctime

        if mtime:
            lang.type_check(mtime, datetime, f'the given mtime is of type {type(mtime)}')
            arguments['mtime'] = mtime

        self._dbmodel = utils.ModelWrapper(models.DbComment(**arguments), backend)

    def store(self):
        """Can only store if both the node and user are stored as well."""
        if self._dbmodel.dbnode.id is None or self._dbmodel.user.id is None:
            self._dbmodel.dbnode = None
            raise exceptions.ModificationNotAllowed('The corresponding node and/or user are not stored')

        super().store()

    @property
    def uuid(self) -> str:
        return str(self._dbmodel.uuid)

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
        return self.backend.nodes.from_dbmodel(self.dbmodel.dbnode)

    @property
    def user(self):
        return self.backend.users.from_dbmodel(self.dbmodel.user)

    def set_user(self, value):
        self._dbmodel.user = value

    @property
    def content(self):
        return self._dbmodel.content

    def set_content(self, value):
        self._dbmodel.content = value


class SqlaCommentCollection(BackendCommentCollection):
    """SqlAlchemy implementation for the CommentCollection."""

    ENTITY_CLASS = SqlaComment

    def from_dbmodel(self, dbmodel) -> SqlaComment:
        """Create an entity from the SQLA ORM model"""
        return self.ENTITY_CLASS.from_dbmodel(dbmodel, self.backend)

    def create(self, node, user, content=None, **kwargs):
        """
        Create a Comment for a given node and user

        :param node: a Node instance
        :param user: a User instance
        :param content: the comment content
        :return: a Comment object associated to the given node and user
        """
        return SqlaComment(self.backend, node, user, content, **kwargs)  # pylint: disable=abstract-class-instantiated

    def delete(self, comment_id):
        """
        Remove a Comment from the collection with the given id

        :param comment_id: the id of the comment to delete
        :type comment_id: int

        :raises TypeError: if ``comment_id`` is not an `int`
        :raises `~aiida.common.exceptions.NotExistent`: if Comment with ID ``comment_id`` is not found
        """
        if not isinstance(comment_id, int):
            raise TypeError('comment_id must be an int')

        session = self.backend.get_session()

        try:
            row = session.query(models.DbComment).filter_by(id=comment_id).one()
            session.delete(row)
            session.commit()
        except NoResultFound:
            session.rollback()
            raise exceptions.NotExistent(f"Comment with id '{comment_id}' not found")

    def delete_all(self):
        """
        Delete all Comment entries.

        :raises `~aiida.common.exceptions.IntegrityError`: if all Comments could not be deleted
        """
        session = self.backend.get_session()

        try:
            session.query(models.DbComment).delete()
            session.commit()
        except Exception as exc:
            session.rollback()
            raise exceptions.IntegrityError(f'Could not delete all Comments. Full exception: {exc}')

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
        from aiida.orm import Comment, QueryBuilder

        # Checks
        if not isinstance(filters, dict):
            raise TypeError('filters must be a dictionary')
        if not filters:
            raise exceptions.ValidationError('filters must not be empty')

        # Apply filter and delete found entities
        builder = QueryBuilder(backend=self.backend).append(Comment, filters=filters, project='id')
        entities_to_delete = builder.all(flat=True)
        for entity in entities_to_delete:
            self.delete(entity)

        # Return list of deleted entities' (former) PKs for checking
        return entities_to_delete
