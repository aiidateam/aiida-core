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

from aiida.common import exceptions, lang
from aiida.orm.implementation.comments import BackendComment, BackendCommentCollection
from aiida.storage.psql_dos.models import comment as models

from . import entities, users, utils


class SqlaComment(entities.SqlaModelEntity[models.DbComment], BackendComment):
    """Comment implementation for Sqla."""

    MODEL_CLASS = models.DbComment
    USER_CLASS = users.SqlaUser

    # pylint: disable=too-many-arguments
    def __init__(self, backend, node, user, content=None, ctime=None, mtime=None):
        """Construct a SqlaComment.

        :param node: a Node instance
        :param user: a User instance
        :param content: the comment content
        :param ctime: The creation time as datetime object
        :param mtime: The modification time as datetime object
        """
        super().__init__(backend)
        lang.type_check(user, self.USER_CLASS)  # pylint: disable=no-member

        arguments = {
            'dbnode': node.bare_model,
            'user': user.bare_model,
            'content': content,
        }

        if ctime:
            lang.type_check(ctime, datetime, f'the given ctime is of type {type(ctime)}')
            arguments['ctime'] = ctime

        if mtime:
            lang.type_check(mtime, datetime, f'the given mtime is of type {type(mtime)}')
            arguments['mtime'] = mtime

        self._model = utils.ModelWrapper(self.MODEL_CLASS(**arguments), backend)

    def store(self):
        """Can only store if both the node and user are stored as well."""
        if self.model.dbnode.id is None or self.model.user.id is None:
            self.model.dbnode = None
            raise exceptions.ModificationNotAllowed('The corresponding node and/or user are not stored')

        super().store()

    @property
    def uuid(self) -> str:
        return str(self.model.uuid)

    @property
    def ctime(self):
        return self.model.ctime

    @property
    def mtime(self):
        return self.model.mtime

    def set_mtime(self, value):
        self.model.mtime = value

    @property
    def node(self):
        return self.backend.nodes.ENTITY_CLASS.from_dbmodel(self.model.dbnode, self.backend)

    @property
    def user(self):
        return self.backend.users.ENTITY_CLASS.from_dbmodel(self.model.user, self.backend)

    def set_user(self, value):
        self.model.user = value

    @property
    def content(self):
        return self.model.content

    def set_content(self, value):
        self.model.content = value


class SqlaCommentCollection(BackendCommentCollection):
    """SqlAlchemy implementation for the CommentCollection."""

    ENTITY_CLASS = SqlaComment

    def create(self, node, user, content=None, **kwargs):
        """
        Create a Comment for a given node and user

        :param node: a Node instance
        :param user: a User instance
        :param content: the comment content
        :return: a Comment object associated to the given node and user
        """
        return self.ENTITY_CLASS(self.backend, node, user, content, **kwargs)

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
            row = session.query(self.ENTITY_CLASS.MODEL_CLASS).filter_by(id=comment_id).one()
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
            session.query(self.ENTITY_CLASS.MODEL_CLASS).delete()
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
