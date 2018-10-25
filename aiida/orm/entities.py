# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for all common top level AiiDA entity classes and methods"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.common import exceptions
from aiida.common.utils import classproperty
from . import backends

__all__ = ('Entity',)


class Collection(object):
    """Container class that represents the collection of objects of a particular type."""

    def __init__(self, backend, entity_class):
        # assert issubclass(entity_class, Entity), "Must provide an entity type"
        self._backend = backend
        self._entity_type = entity_class

    @property
    def backend(self):
        """Return the backend."""
        return self._backend

    @property
    def entity_type(self):
        return self._entity_type

    def query(self):
        """
        Get a query builder for the objects of this collection

        :return: a new query builder instance
        :rtype: :class:`aiida.orm.QueryBuilder`
        """
        # pylint: disable=no-self-use, fixme
        from . import querybuilder

        query = querybuilder.QueryBuilder()
        # TODO: Figure out how to limit to only classes of self.entity_type
        return query

    def get(self, id=None, uuid=None):
        """
        Get a collection entry from an id or a UUID

        :param id: the id of the entry to get
        :param uuid: the uuid of the entry to get
        :return: the entry
        """
        # pylint: disable=redefined-builtin, invalid-name
        query = self.query()
        filters = {}
        if id is not None:
            filters['id'] = {'==': id}
        if uuid is not None:
            filters['uuid'] = {'==': uuid}

        query.append(cls=self.entity_type, filters=filters)
        res = [_[0] for _ in query.all()]
        if not res:
            raise exceptions.NotExistent("No {} with filter '{}' found".format(self.entity_type.__name__, filters))
        if len(res) > 1:
            raise exceptions.MultipleObjectsError("Multiple {}s found with the same id '{}'".format(
                self.entity_type.__name__, id))

        return res[0]


class Entity(object):
    """An AiiDA entity"""

    _BACKEND = None
    _OBJECTS = None

    # Define out collection type
    Collection = Collection

    @classproperty
    def objects(cls, backend=None):  # pylint: disable=no-self-use, no-self-argument
        """
        Get an collection for objects of this type.

        :param backend: the optional backend to use (otherwise use default)
        :return: an object that can be used to access entites of this type
        """
        backend = backend or backends.construct_backend()
        return cls.Collection(backend, cls)

    @classmethod
    def get(cls, id=None, uuid=None):
        # pylint: disable=redefined-builtin, invalid-name
        return cls.objects.get(id=id, uuid=uuid)  # pylint: disable=no-member

    def __init__(self, model):
        """
        :param model: the backend model supporting this entity
        :type model: :class:`aiida.orm.implementation.BackendEntity`
        """
        self._model = model

    @property
    def id(self):
        """
        Get the id for this entity.  This is unique only amongst entities of this type
        for a particular backend

        :return: the entity id
        """
        # pylint: disable=redefined-builtin, invalid-name
        return self._model.id

    @property
    def pk(self):
        """
        Get the principal key for this entity

        .. note:: Deprecated because the backend need not be a database and so principle key doesn't
            always make sense.  Use `id()` instead.

        :return: the principal key
        """
        return self.id

    @property
    def uuid(self):
        """
        Get the UUID for this entity.  This is unique across all entities types and backends
        :return: the eneity uuid
        :rtype: :class:`uuid.UUID`
        """
        return self._model.uuid

    @property
    def backend(self):
        """
        Get the backend for this entity
        :return: the backend instance
        """
        return self._model.backend

    @property
    def backend_entity(self):
        """
        Get the implementing class for this object

        :return: the class model
        """
        return self._model
