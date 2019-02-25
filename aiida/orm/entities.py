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
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import typing

from plumpy.base.utils import super_check, call_with_super_check

from aiida.common import exceptions
from aiida.common import datastructures
from aiida.common.lang import classproperty, type_check
from aiida.manage.manager import get_manager

__all__ = ('Entity', 'Collection')

EntityType = typing.TypeVar('EntityType')  # pylint: disable=invalid-name


class Collection(typing.Generic[EntityType]):
    """Container class that represents the collection of objects of a particular type."""

    # A store for any backend specific collections that already exist
    _COLLECTIONS = datastructures.LazyStore()

    @classmethod
    def get_collection(cls, entity_type, backend):
        """
        Get the collection for a given entity type and backend instance

        :param entity_type: the entity type e.g. User, Computer, etc
        :param backend: the backend instance to get the collection for
        :return: the collection instance
        """
        # Lazily get the collection i.e. create only if we haven't done so yet
        return cls._COLLECTIONS.get((entity_type, backend), lambda: entity_type.Collection(backend, entity_type))

    def __init__(self, backend, entity_class):
        """Construct a new entity collection"""
        assert issubclass(entity_class, Entity), "Must provide an entity type"
        self._backend = backend or get_manager().get_backend()
        self._entity_type = entity_class

    def __call__(self, backend):
        """
        Create a new objects collection using a different backend

        :param backend: the backend to use
        :return: a new collection with the different backend
        """
        if backend is self._backend:
            # Special case if they actually want the same collection
            return self

        return self.get_collection(self.entity_type, backend)

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
        # pylint: disable=no-self-use
        from . import querybuilder

        query = querybuilder.QueryBuilder()
        query.append(self._entity_type, project='*')
        return query

    def get(self, **filters):
        """
        Get a single collection entry that matches the filter criteria

        :param filters: the filters identifying the object to get
        :return: the entry
        """
        res = self.find(filters=filters)
        if not res:
            raise exceptions.NotExistent("No {} with filter '{}' found".format(self.entity_type.__name__, filters))
        if len(res) > 1:
            raise exceptions.MultipleObjectsError("Multiple {}s found with the same id '{}'".format(
                self.entity_type.__name__, id))

        return res[0]

    def find(self, filters=None, order_by=None, limit=None):
        """
        Find collection entries matching the filter criteria

        :param filters: the keyword value pair filters to match
        :param order_by: a list of (key, direction) pairs specifying the sort order
        :type order_by: list
        :param limit: the maximum number of results to return
        :type limit: int
        :return: a list of resulting matches
        :rtype: list
        """
        query = self.query()
        filters = filters or {}
        query.add_filter(self.entity_type, filters)
        if order_by:
            query.order_by({self.entity_type: order_by})
        if limit:
            query.limit(limit)

        return [_[0] for _ in query.all()]

    def all(self):
        """
        Get all entities in this collection

        :return: A collection of users matching the criteria
        """
        return [_[0] for _ in self.query().all()]


class Entity(object):  # pylint: disable=useless-object-inheritance
    """An AiiDA entity"""

    _objects = None

    # Define our collection type
    Collection = Collection

    @classproperty
    def objects(cls, backend=None):  # pylint: disable=no-self-use, no-self-argument
        """
        Get an collection for objects of this type.

        :param backend: the optional backend to use (otherwise use default)
        :return: an object that can be used to access entities of this type
        """
        backend = backend or get_manager().get_backend()
        return cls.Collection.get_collection(cls, backend)

    @classmethod
    def get(cls, **kwargs):
        # pylint: disable=redefined-builtin, invalid-name
        return cls.objects.get(**kwargs)  # pylint: disable=no-member

    @classmethod
    def from_backend_entity(cls, backend_entity):
        """
        Construct an entity from a backend entity instance

        :param backend_entity: the backend entity
        :return: an AiiDA entity instance
        """
        from . import implementation

        type_check(backend_entity, implementation.BackendEntity)
        entity = cls.__new__(cls)
        entity.init_from_backend(backend_entity)
        call_with_super_check(entity.initialize)
        return entity

    def __init__(self, backend_entity):
        """
        :param backend_entity: the backend model supporting this entity
        :type backend_entity: :class:`aiida.orm.implementation.BackendEntity`
        """
        self._backend_entity = backend_entity
        call_with_super_check(self.initialize)

    def init_from_backend(self, backend_entity):
        """
        :param backend_entity: the backend model supporting this entity
        :type backend_entity: :class:`aiida.orm.implementation.BackendEntity`
        """
        self._backend_entity = backend_entity

    @super_check
    def initialize(self):
        """Initialize instance attributes.

        This will be called after the constructor is called or an entity is created from an existing backend entity.
        """

    @property
    def id(self):
        """
        Get the id for this entity.  This is unique only amongst entities of this type
        for a particular backend

        :return: the entity id
        """
        # pylint: disable=redefined-builtin, invalid-name
        return self._backend_entity.id

    @property
    def pk(self):
        """
        Get the primary key for this entity

        .. note:: Deprecated because the backend need not be a database and so principle key doesn't
            always make sense.  Use `id()` instead.

        :return: the principal key
        """
        return self.id

    @property
    def uuid(self):
        """
        Get the UUID for this entity.  This is unique across all entities types and backends

        :return: the entity uuid
        :rtype: :class:`uuid.UUID`
        """
        return self._backend_entity.uuid

    def store(self):
        """
        Store the entity.
        """
        self._backend_entity.store()
        return self

    @property
    def is_stored(self):
        """
        Is the computer stored?

        :return: True if stored, False otherwise
        :rtype: bool
        """
        return self._backend_entity.is_stored

    @property
    def backend(self):
        """
        Get the backend for this entity
        :return: the backend instance
        """
        return self._backend_entity.backend

    @property
    def backend_entity(self):
        """
        Get the implementing class for this object

        :return: the class model
        """
        return self._backend_entity
