# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Classes and methods for Django specific backend entities"""
from typing import Generic, Set, TypeVar

from aiida.common.lang import type_check
from aiida.storage.psql_dos.models.base import Base

from . import utils

ModelType = TypeVar('ModelType')  # pylint: disable=invalid-name
SelfType = TypeVar('SelfType', bound='SqlaModelEntity')


class SqlaModelEntity(Generic[ModelType]):
    """A mixin that adds some common SQLA backend entity methods"""

    MODEL_CLASS = None
    _model: utils.ModelWrapper

    @classmethod
    def _class_check(cls):
        """Assert that the class is correctly configured"""
        assert issubclass(cls.MODEL_CLASS, Base), 'Must set the MODEL_CLASS in the derived class to a SQLA model'

    @classmethod
    def from_dbmodel(cls, dbmodel, backend):
        """Create an AiiDA Entity from the corresponding SQLA ORM model and storage backend

        :param dbmodel: the SQLAlchemy model to create the entity from
        :param backend: the corresponding storage backend
        :return: the AiiDA entity
        """
        from ..backend import PsqlDosBackend  # pylint: disable=cyclic-import
        cls._class_check()
        type_check(dbmodel, cls.MODEL_CLASS)
        type_check(backend, PsqlDosBackend)
        entity = cls.__new__(cls)
        super(SqlaModelEntity, entity).__init__(backend)
        entity._model = utils.ModelWrapper(dbmodel, backend)  # pylint: disable=protected-access
        return entity

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._class_check()

    @property
    def model(self) -> utils.ModelWrapper:
        """Return an ORM model that correctly updates and flushes the data when getting or setting a field."""
        return self._model

    @property
    def bare_model(self):
        """Return the underlying SQLA ORM model for this entity.

        .. warning:: Getting/setting attributes on this model bypasses AiiDA's internal update/flush mechanisms.
        """
        return self.model._model  # pylint: disable=protected-access

    @property
    def id(self) -> int:  # pylint: disable=redefined-builtin, invalid-name
        """
        Get the id of this entity

        :return: the entity id
        """
        return self.model.id

    @property
    def is_stored(self) -> bool:
        """
        Is this entity stored?

        :return: True if stored, False otherwise
        """
        return self.model.id is not None

    def store(self: SelfType) -> SelfType:
        """
        Store this entity

        :return: the entity itself
        """
        self.model.save()
        return self

    def _flush_if_stored(self, fields: Set[str]) -> None:
        if self.model.is_saved():
            self.model._flush(fields)  # pylint: disable=protected-access
