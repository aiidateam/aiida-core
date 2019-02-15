# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Django implementations for the Comment entity and collection."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=import-error,no-name-in-module,fixme
from datetime import datetime
from aiida.backends.djsite.db import models
from aiida.common import exceptions
from aiida.common import lang

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
        super(DjangoComment, self).__init__(backend)
        lang.type_check(user, users.DjangoUser)  # pylint: disable=no-member

        arguments = {
            'dbnode': node.dbmodel,
            'user': user.dbmodel,
            'content': content,
        }

        if ctime:
            lang.type_check(ctime, datetime, 'the given ctime is of type {}'.format(type(ctime)))
            arguments['ctime'] = ctime

        if mtime:
            lang.type_check(mtime, datetime, 'the given mtime is of type {}'.format(type(mtime)))
            arguments['mtime'] = mtime

        self._dbmodel = ModelWrapper(models.DbComment(**arguments), auto_flush=self._auto_flush)

    def store(self):
        """Can only store if both the node and user are stored as well."""
        from aiida.common.lang import EmptyContextManager
        from aiida.backends.djsite.db.models import suppress_auto_now

        if self._dbmodel.dbnode.id is None or self._dbmodel.user.id is None:
            raise exceptions.ModificationNotAllowed('The corresponding node and/or user are not stored')

        with suppress_auto_now([(models.DbComment, ['mtime'])]) if self.mtime else EmptyContextManager():
            super(DjangoComment, self).store()

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
        # self._dbmodel.save()


class DjangoCommentCollection(BackendCommentCollection):
    """Django implementation for the CommentCollection."""

    def from_dbmodel(self, dbmodel):
        return DjangoComment.from_dbmodel(dbmodel, self.backend)

    def create(self, node, user, content=None, **kwargs):
        """
        Create a Comment for a given node and user

        :param node: a Node instance
        :param user: a User instance
        :param content: the comment content
        :return: a Comment object associated to the given node and user
        """
        return DjangoComment(self.backend, node, user, content, **kwargs)

    def delete(self, comment):
        """
        Remove a Comment from the collection with the given id

        :param comment: the id of the comment to delete
        """
        # pylint: disable=no-name-in-module,import-error
        from django.core.exceptions import ObjectDoesNotExist
        assert comment is not None
        try:
            models.DbComment.objects.get(id=comment).delete()
        except ObjectDoesNotExist:
            raise exceptions.NotExistent("Comment with id '{}' not found".format(comment))
