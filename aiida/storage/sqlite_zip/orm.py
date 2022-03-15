# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""This module contains the AiiDA backend ORM classes for the SQLite backend.

It re-uses the classes already defined in ``psql_dos`` backend (for PostGresQL),
but redefines the SQLAlchemy models to the SQLite compatible ones.
"""
from functools import singledispatch
from typing import Any

from aiida.common.lang import type_check
from aiida.storage.psql_dos.orm import authinfos, comments, computers, entities, groups, logs, nodes, users, utils

from . import models
from .utils import ReadOnlyError


class SqliteEntityOverride:
    """Overrides type-checking of psql_dos ``Entity``."""

    MODEL_CLASS: Any
    _model: utils.ModelWrapper

    @classmethod
    def _class_check(cls):
        """Assert that the class is correctly configured"""
        assert issubclass(
            cls.MODEL_CLASS, models.SqliteBase
        ), 'Must set the MODEL_CLASS in the derived class to a SQLA model'

    @classmethod
    def from_dbmodel(cls, dbmodel, backend):
        """Create an AiiDA Entity from the corresponding SQLA ORM model and storage backend

        :param dbmodel: the SQLAlchemy model to create the entity from
        :param backend: the corresponding storage backend
        :return: the AiiDA entity
        """
        cls._class_check()
        type_check(dbmodel, cls.MODEL_CLASS)
        entity = cls.__new__(cls)
        super(entities.SqlaModelEntity, entity).__init__(backend)  # type: ignore # # pylint: disable=bad-super-call
        entity._model = utils.ModelWrapper(dbmodel, backend)  # pylint: disable=protected-access
        return entity

    def store(self, *args, **kwargs):
        backend = self._model._backend  # pylint: disable=protected-access
        if getattr(backend, '_read_only', False):
            raise ReadOnlyError(f'Cannot store entity in read-only backend: {backend}')
        super().store(*args, **kwargs)  # type: ignore # pylint: disable=no-member


class SqliteUser(SqliteEntityOverride, users.SqlaUser):

    MODEL_CLASS = models.DbUser


class SqliteUserCollection(users.SqlaUserCollection):

    ENTITY_CLASS = SqliteUser


class SqliteComputer(SqliteEntityOverride, computers.SqlaComputer):

    MODEL_CLASS = models.DbComputer


class SqliteComputerCollection(computers.SqlaComputerCollection):

    ENTITY_CLASS = SqliteComputer


class SqliteAuthInfo(SqliteEntityOverride, authinfos.SqlaAuthInfo):

    MODEL_CLASS = models.DbAuthInfo
    USER_CLASS = SqliteUser
    COMPUTER_CLASS = SqliteComputer


class SqliteAuthInfoCollection(authinfos.SqlaAuthInfoCollection):

    ENTITY_CLASS = SqliteAuthInfo


class SqliteComment(SqliteEntityOverride, comments.SqlaComment):

    MODEL_CLASS = models.DbComment
    USER_CLASS = SqliteUser


class SqliteCommentCollection(comments.SqlaCommentCollection):

    ENTITY_CLASS = SqliteComment


class SqliteGroup(SqliteEntityOverride, groups.SqlaGroup):

    MODEL_CLASS = models.DbGroup
    USER_CLASS = SqliteUser


class SqliteGroupCollection(groups.SqlaGroupCollection):

    ENTITY_CLASS = SqliteGroup


class SqliteLog(SqliteEntityOverride, logs.SqlaLog):

    MODEL_CLASS = models.DbLog


class SqliteLogCollection(logs.SqlaLogCollection):

    ENTITY_CLASS = SqliteLog


class SqliteNode(SqliteEntityOverride, nodes.SqlaNode):
    """SQLA Node backend entity"""

    MODEL_CLASS = models.DbNode
    USER_CLASS = SqliteUser
    COMPUTER_CLASS = SqliteComputer
    LINK_CLASS = models.DbLink


class SqliteNodeCollection(nodes.SqlaNodeCollection):

    ENTITY_CLASS = SqliteNode


@singledispatch
def get_backend_entity(dbmodel, backend):  # pylint: disable=unused-argument
    raise TypeError(f"No corresponding AiiDA backend class exists for the model class '{dbmodel.__class__.__name__}'")


@get_backend_entity.register(models.DbUser)  # type: ignore[call-overload]
def _(dbmodel, backend):
    return SqliteUser.from_dbmodel(dbmodel, backend)


@get_backend_entity.register(models.DbGroup)  # type: ignore[call-overload]
def _(dbmodel, backend):
    return SqliteGroup.from_dbmodel(dbmodel, backend)


@get_backend_entity.register(models.DbComputer)  # type: ignore[call-overload]
def _(dbmodel, backend):
    return SqliteComputer.from_dbmodel(dbmodel, backend)


@get_backend_entity.register(models.DbNode)  # type: ignore[call-overload]
def _(dbmodel, backend):
    return SqliteNode.from_dbmodel(dbmodel, backend)


@get_backend_entity.register(models.DbAuthInfo)  # type: ignore[call-overload]
def _(dbmodel, backend):
    return SqliteAuthInfo.from_dbmodel(dbmodel, backend)


@get_backend_entity.register(models.DbComment)  # type: ignore[call-overload]
def _(dbmodel, backend):
    return SqliteComment.from_dbmodel(dbmodel, backend)


@get_backend_entity.register(models.DbLog)  # type: ignore[call-overload]
def _(dbmodel, backend):
    return SqliteLog.from_dbmodel(dbmodel, backend)


@get_backend_entity.register(models.DbLink)  # type: ignore[call-overload]
def _(dbmodel, backend):
    from aiida.orm.utils.links import LinkQuadruple
    return LinkQuadruple(dbmodel.input_id, dbmodel.output_id, dbmodel.type, dbmodel.label)
