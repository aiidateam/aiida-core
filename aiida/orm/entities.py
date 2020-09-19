# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for all common top level AiiDA entity classes and methods"""
import typing

from plumpy.base.utils import super_check, call_with_super_check

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
        :type entity_type: :class:`aiida.orm.Entity`

        :param backend: the backend instance to get the collection for
        :type backend: :class:`aiida.orm.implementation.Backend`

        :return: a new collection with the new backend
        :rtype: :class:`aiida.orm.Collection`
        """
        # Lazily get the collection i.e. create only if we haven't done so yet
        return cls._COLLECTIONS.get((entity_type, backend), lambda: entity_type.Collection(backend, entity_type))

    def __init__(self, backend, entity_class):
        """ Construct a new entity collection.

        :param backend: the backend instance to get the collection for
        :type backend: :class:`aiida.orm.implementation.Backend`

        :param entity_class: the entity type e.g. User, Computer, etc
        :type entity_class: :class:`aiida.orm.Entity`

        """
        assert issubclass(entity_class, Entity), 'Must provide an entity type'
        self._backend = backend or get_manager().get_backend()
        self._entity_type = entity_class

    def __call__(self, backend):
        """ Create a new objects collection using a new backend.

        :param backend: the backend instance to get the collection for
        :type backend: :class:`aiida.orm.implementation.Backend`

        :return: a new collection with the new backend
        :rtype: :class:`aiida.orm.Collection`
        """
        if backend is self._backend:
            # Special case if they actually want the same collection
            return self

        return self.get_collection(self.entity_type, backend)

    @property
    def backend(self):
        """Return the backend.

        :return: the backend instance of this collection
        :rtype: :class:`aiida.orm.implementation.Backend`
        """
        return self._backend

    @property
    def entity_type(self):
        """The entity type.

        :rtype: :class:`aiida.orm.Entity`
        """
        return self._entity_type

    def query(self, filters=None, order_by=None, limit=None, offset=None):
        """
        Get a query builder for the objects of this collection

        :param filters: the keyword value pair filters to match
        :type filters: dict

        :param order_by: a list of (key, direction) pairs specifying the sort order
        :type order_by: list

        :param limit: the maximum number of results to return
        :type limit: int

        :param offset: number of initial results to be skipped
        :type offset: int

        :return: a new query builder instance
        :rtype: :class:`aiida.orm.QueryBuilder`
        """
        from . import querybuilder

        filters = filters or {}
        order_by = {self.entity_type: order_by} if order_by else {}

        query = querybuilder.QueryBuilder(limit=limit, offset=offset)
        query.append(self.entity_type, project='*', filters=filters)
        query.order_by([order_by])
        return query

    def get(self, **filters):
        """
        Get a single collection entry that matches the filter criteria

        :param filters: the filters identifying the object to get
        :type filters: dict

        :return: the entry
        """
        res = self.query(filters=filters)
        return res.one()[0]

    def find(self, filters=None, order_by=None, limit=None):
        """
        Find collection entries matching the filter criteria

        :param filters: the keyword value pair filters to match
        :type filters: dict

        :param order_by: a list of (key, direction) pairs specifying the sort order
        :type order_by: list

        :param limit: the maximum number of results to return
        :type limit: int

        :return: a list of resulting matches
        :rtype: list
        """
        query = self.query(filters=filters, order_by=order_by, limit=limit)
        return query.all(flat=True)

    def all(self):
        """
        Get all entities in this collection

        :return: A list of all entities
        :rtype: list
        """
        return self.query().all(flat=True)  # pylint: disable=no-member

    def count(self, filters=None):
        """Count entities in this collection according to criteria

        :param filters: the keyword value pair filters to match
        :type filters: dict

        :return: The number of entities found using the supplied criteria
        :rtype: int
        """
        return self.query(filters=filters).count()


class Entity:
    """An AiiDA entity"""

    _objects = None

    # Define our collection type
    Collection = Collection

    @classproperty
    def objects(cls, backend=None):  # pylint: disable=no-self-argument
        """
        Get a collection for objects of this type.

        :param backend: the optional backend to use (otherwise use default)
        :type backend: :class:`aiida.orm.implementation.Backend`

        :return: an object that can be used to access entities of this type
        :rtype: :class:`aiida.orm.Collection`
        """
        backend = backend or get_manager().get_backend()
        return cls.Collection.get_collection(cls, backend)

    @classmethod
    def get(cls, **kwargs):
        return cls.objects.get(**kwargs)  # pylint: disable=no-member

    @classmethod
    def from_backend_entity(cls, backend_entity):
        """
        Construct an entity from a backend entity instance

        :param backend_entity: the backend entity

        :return: an AiiDA entity instance
        """
        from .implementation.entities import BackendEntity

        type_check(backend_entity, BackendEntity)
        entity = cls.__new__(cls)
        entity.init_from_backend(backend_entity)
        call_with_super_check(entity.initialize)
        return entity

    def __init__(self, backend_entity):
        """
        :param backend_entity: the backend model supporting this entity
        :type backend_entity: :class:`aiida.orm.implementation.entities.BackendEntity`
        """
        self._backend_entity = backend_entity
        call_with_super_check(self.initialize)

    def init_from_backend(self, backend_entity):
        """
        :param backend_entity: the backend model supporting this entity
        :type backend_entity: :class:`aiida.orm.implementation.entities.BackendEntity`
        """
        self._backend_entity = backend_entity

    @super_check
    def initialize(self):
        """Initialize instance attributes.

        This will be called after the constructor is called or an entity is created from an existing backend entity.
        """

    @property
    def id(self):  # pylint: disable=invalid-name
        """Return the id for this entity.

        This identifier is guaranteed to be unique amongst entities of the same type for a single backend instance.

        :return: the entity's id
        """
        return self._backend_entity.id

    @property
    def pk(self):
        """Return the primary key for this entity.

        This identifier is guaranteed to be unique amongst entities of the same type for a single backend instance.

        :return: the entity's principal key
        """
        return self.id

    @property
    def uuid(self):
        """Return the UUID for this entity.

        This identifier is unique across all entities types and backend instances.

        :return: the entity uuid
        :rtype: :class:`uuid.UUID`
        """
        return self._backend_entity.uuid

    def store(self):
        """Store the entity."""
        self._backend_entity.store()
        return self

    @property
    def is_stored(self):
        """Return whether the entity is stored.

        :return: boolean, True if stored, False otherwise
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
