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
from aiida.common.utils import classproperty, type_check

from . import backends

__all__ = ('Entity', 'Collection')


class Collection(object):
    """Container class that represents the collection of objects of a particular type."""

    def __init__(self, backend, entity_class):
        # assert issubclass(entity_class, Entity), "Must provide an entity type"
        self._backend = backend
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

        return self.__class__(backend, self._entity_type)

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
        query.append(self._entity_type, project='*')
        return query

    def get(self, **kwargs):
        """
        Get a collection entry using keyword parameter filters

        :param kwargs: the filters identifying the object to get
        :return: the entry
        """
        query = self.query()
        query.add_filter(self.entity_type, kwargs)
        res = [_[0] for _ in query.all()]
        if not res:
            raise exceptions.NotExistent("No {} with filter '{}' found".format(self.entity_type.__name__, kwargs))
        if len(res) > 1:
            raise exceptions.MultipleObjectsError("Multiple {}s found with the same id '{}'".format(
                self.entity_type.__name__, id))

        return res[0]

    def find(self, **filters):
        """
        Find entries matching the given filters

        :param filters: the keyword value pair filters to match
        :return: a list of resulting matches
        :rtype: list
        """
        query = self.query()
        query.add_filter(self.entity_type, filters)
        res = [_[0] for _ in query.all()]
        if not res:
            raise exceptions.NotExistent("No {} with filter '{}' found".format(self.entity_type.__name__, filters))
        if len(res) > 1:
            raise exceptions.MultipleObjectsError("Multiple {}s found with the same id '{}'".format(
                self.entity_type.__name__, id))

        return res

    def all(self):
        """
        Get all entities in this collection

        :return: A collection of users matching the criteria
        """
        return [_[0] for _ in self.query().all()]


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
        computer = cls.__new__(cls)
        computer.init_from_backend(backend_entity)
        return computer

    def __init__(self, backend_entity):
        """
        :param backend_entity: the backend model supporting this entity
        :type backend_entity: :class:`aiida.orm.implementation.BackendEntity`
        """
        self._backend_entity = backend_entity

    def init_from_backend(self, backend_entity):
        """
        :param backend_entity: the backend model supporting this entity
        :type backend_entity: :class:`aiida.orm.implementation.BackendEntity`
        """
        self._backend_entity = backend_entity

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
