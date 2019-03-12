# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Classes and methods for Django specific backend entities"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import typing

from aiida.backends.sqlalchemy.models.base import Base
from aiida.common.lang import type_check
from . import utils

ModelType = typing.TypeVar('ModelType')  # pylint: disable=invalid-name


class SqlaModelEntity(typing.Generic[ModelType]):
    """A mixin that adds some common SQLA backend entity methods"""

    MODEL_CLASS = None
    _dbmodel = None

    @classmethod
    def _class_check(cls):
        """Assert that the class is correctly configured"""
        assert issubclass(cls.MODEL_CLASS, Base), 'Must set the MODEL_CLASS in the derived class to a SQLA model'

    @classmethod
    def from_dbmodel(cls, dbmodel, backend):
        """
        Create a DjangoEntity from the corresponding db model class

        :param dbmodel: the model to create the entity from
        :param backend: the corresponding backend
        :return: the Django entity
        """
        from .backend import SqlaBackend  # pylint: disable=cyclic-import
        cls._class_check()
        type_check(dbmodel, cls.MODEL_CLASS)
        type_check(backend, SqlaBackend)
        entity = cls.__new__(cls)
        super(SqlaModelEntity, entity).__init__(backend)
        entity._dbmodel = utils.ModelWrapper(dbmodel)  # pylint: disable=protected-access
        return entity

    @classmethod
    def get_dbmodel_attribute_name(cls, attr_name):
        """
        Given the name of an attribute of the entity class give the corresponding name of the attribute
        in the db model.  It if doesn't exit this raises a ValueError

        :param attr_name:
        :return: the dbmodel attribute name
        :rtype: str
        """
        if hasattr(cls.MODEL_CLASS, attr_name):
            return attr_name

        raise ValueError("Unknown attribute '{}'".format(attr_name))

    def __init__(self, *args, **kwargs):
        super(SqlaModelEntity, self).__init__(*args, **kwargs)
        self._class_check()

    @property
    def dbmodel(self):
        """
        Get the underlying database model instance

        :return: the database model instance
        """
        return self._dbmodel._model  # pylint: disable=protected-access

    @property
    def id(self):  # pylint: disable=redefined-builtin, invalid-name
        """
        Get the id of this entity

        :return: the entity id
        """
        return self._dbmodel.id

    @property
    def pk(self):
        """
        Get the principal key for this entry

        :return: the principal key
        """
        return self._dbmodel.id

    @property
    def is_stored(self):
        """
        Is this entity stored?

        :return: True if stored, False otherwise
        """
        return self._dbmodel.id is not None

    def store(self):
        """
        Store this entity

        :return: the entity itself
        """
        self._dbmodel.save()
        return self
