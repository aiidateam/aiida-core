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

from django.db.models import Model  # pylint: disable=import-error, no-name-in-module

from aiida.common.lang import type_check
from . import utils

ModelType = typing.TypeVar('ModelType')  # pylint: disable=invalid-name


class DjangoModelEntity(typing.Generic[ModelType]):
    """A mixin that adds some common Django backend entity methods"""

    MODEL_CLASS = None
    _dbmodel = None
    _auto_flush = ()

    @classmethod
    def _class_check(cls):
        """Assert that the class is correctly configured"""
        assert issubclass(cls.MODEL_CLASS, Model), 'Must set the MODEL_CLASS in the derived class to a SQLA model'

    @classmethod
    def from_dbmodel(cls, dbmodel, backend):
        """
        Create a DjangoEntity from the corresponding db model class

        :param dbmodel: the model to create the entity from
        :param backend: the corresponding backend
        :return: the Django entity
        """
        from .backend import DjangoBackend  # pylint: disable=cyclic-import
        cls._class_check()
        type_check(dbmodel, cls.MODEL_CLASS)
        type_check(backend, DjangoBackend)
        entity = cls.__new__(cls)
        super(DjangoModelEntity, entity).__init__(backend)
        entity._dbmodel = utils.ModelWrapper(dbmodel, auto_flush=cls._auto_flush)  # pylint: disable=protected-access
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
        super(DjangoModelEntity, self).__init__(*args, **kwargs)
        self._class_check()

    @property
    def dbmodel(self):
        return self._dbmodel._model  # pylint: disable=protected-access

    @property
    def id(self):  # pylint: disable=invalid-name
        return self._dbmodel.pk

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
        Store the entity

        :return: the entity itself
        """
        self._dbmodel.save()
        return self
