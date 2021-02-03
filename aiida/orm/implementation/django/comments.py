# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Django implementations for the Comment entity and collection."""
# pylint: disable=import-error,no-name-in-module
import contextlib

from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist

from aiida.backends.djsite.db import models
from aiida.common import exceptions, lang

from ..comments import BackendComment, BackendCommentCollection
from .utils import ModelWrapper
from . import entities
from . import users


class DjangoComment(entities.DjangoModelEntity[models.DbComment], BackendComment):
    """Comment implementation for Django."""

    MODEL_CLASS = models.DbComment
    _auto_flush = ('mtime',)

    # pylint: disable=too-many-arguments
    def __init__(self, backend, node, user, content=None, ctime=None, mtime=None):
        """
        Construct a DjangoComment.

        :param node: a Node instance
        :param user: a User instance
        :param content: the comment content
        :param ctime: The creation time as datetime object
        :param mtime: The modification time as datetime object
        :return: a Comment object associated to the given node and user
        """
        super().__init__(backend)
        lang.type_check(user, users.DjangoUser)  # pylint: disable=no-member

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

        self._dbmodel = ModelWrapper(models.DbComment(**arguments), auto_flush=self._auto_flush)

    def store(self):
        """Can only store if both the node and user are stored as well."""
        from aiida.backends.djsite.db.models import suppress_auto_now

        if self._dbmodel.dbnode.id is None or self._dbmodel.user.id is None:
            raise exceptions.ModificationNotAllowed('The corresponding node and/or user are not stored')

        # `contextlib.suppress` provides empty context and can be replaced with `contextlib.nullcontext` after we drop
        # support for python 3.6
        with suppress_auto_now([(models.DbComment, ['mtime'])]) if self.mtime else contextlib.suppress():
            super().store()

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
        return self._backend.nodes.from_dbmodel(self._dbmodel.dbnode)

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


class DjangoCommentCollection(BackendCommentCollection):
    """Django implementation for the CommentCollection."""

    ENTITY_CLASS = DjangoComment

    def create(self, node, user, content=None, **kwargs):
        """
        Create a Comment for a given node and user

        :param node: a Node instance
        :param user: a User instance
        :param content: the comment content
        :return: a Comment object associated to the given node and user
        """
        return DjangoComment(self.backend, node, user, content, **kwargs)

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

        try:
            models.DbComment.objects.get(id=comment_id).delete()
        except ObjectDoesNotExist:
            raise exceptions.NotExistent(f"Comment with id '{comment_id}' not found")

    def delete_all(self):
        """
        Delete all Comment entries.

        :raises `~aiida.common.exceptions.IntegrityError`: if all Comments could not be deleted
        """
        from django.db import transaction
        try:
            with transaction.atomic():
                models.DbComment.objects.all().delete()
        except Exception as exc:
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
        builder = QueryBuilder().append(Comment, filters=filters, project='id').all()
        entities_to_delete = [_[0] for _ in builder]
        for entity in entities_to_delete:
            self.delete(entity)

        # Return list of deleted entities' (former) PKs for checking
        return entities_to_delete
