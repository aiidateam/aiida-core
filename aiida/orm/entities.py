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
import abc
import copy

from plumpy.base.utils import super_check, call_with_super_check

from aiida.common import datastructures, exceptions
from aiida.common.lang import classproperty, type_check
from aiida.manage.manager import get_manager

__all__ = ('Entity', 'Collection', 'EntityAttributesMixin', 'EntityExtrasMixin')

EntityType = typing.TypeVar('EntityType')  # pylint: disable=invalid-name

_NO_DEFAULT = tuple()


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


class EntityAttributesMixin(abc.ABC):
    """Mixin class that adds all methods for the attributes column to an entity."""

    @property
    def attributes(self):
        """Return the complete attributes dictionary.

        .. warning:: While the entity is unstored, this will return references of the attributes on the database model,
            meaning that changes on the returned values (if they are mutable themselves, e.g. a list or dictionary) will
            automatically be reflected on the database model as well. As soon as the entity is stored, the returned
            attributes will be a deep copy and mutations of the database attributes will have to go through the
            appropriate set methods. Therefore, once stored, retrieving a deep copy can be a heavy operation. If you
            only need the keys or some values, use the iterators `attributes_keys` and `attributes_items`, or the
            getters `get_attribute` and `get_attribute_many` instead.

        :return: the attributes as a dictionary
        """
        attributes = self.backend_entity.attributes

        if self.is_stored:
            attributes = copy.deepcopy(attributes)

        return attributes

    def get_attribute(self, key, default=_NO_DEFAULT):
        """Return the value of an attribute.

        .. warning:: While the entity is unstored, this will return a reference of the attribute on the database model,
            meaning that changes on the returned value (if they are mutable themselves, e.g. a list or dictionary) will
            automatically be reflected on the database model as well. As soon as the entity is stored, the returned
            attribute will be a deep copy and mutations of the database attributes will have to go through the
            appropriate set methods.

        :param key: name of the attribute
        :param default: return this value instead of raising if the attribute does not exist
        :return: the value of the attribute
        :raises AttributeError: if the attribute does not exist and no default is specified
        """
        try:
            attribute = self.backend_entity.get_attribute(key)
        except AttributeError:
            if default is _NO_DEFAULT:
                raise
            attribute = default

        if self.is_stored:
            attribute = copy.deepcopy(attribute)

        return attribute

    def get_attribute_many(self, keys):
        """Return the values of multiple attributes.

        .. warning:: While the entity is unstored, this will return references of the attributes on the database model,
            meaning that changes on the returned values (if they are mutable themselves, e.g. a list or dictionary) will
            automatically be reflected on the database model as well. As soon as the entity is stored, the returned
            attributes will be a deep copy and mutations of the database attributes will have to go through the
            appropriate set methods. Therefore, once stored, retrieving a deep copy can be a heavy operation. If you
            only need the keys or some values, use the iterators `attributes_keys` and `attributes_items`, or the
            getters `get_attribute` and `get_attribute_many` instead.

        :param keys: a list of attribute names
        :return: a list of attribute values
        :raises AttributeError: if at least one attribute does not exist
        """
        attributes = self.backend_entity.get_attribute_many(keys)

        if self.is_stored:
            attributes = copy.deepcopy(attributes)

        return attributes

    def set_attribute(self, key, value):
        """Set an attribute to the given value.

        :param key: name of the attribute
        :param value: value of the attribute
        :raise aiida.common.ValidationError: if the key is invalid, i.e. contains periods
        :raise aiida.common.ModificationNotAllowed: if the entity is stored
        """
        if self.is_stored:
            raise exceptions.ModificationNotAllowed('the attributes of a stored entity are immutable')

        self.backend_entity.set_attribute(key, value)

    def set_attribute_many(self, attributes):
        """Set multiple attributes.

        .. note:: This will override any existing attributes that are present in the new dictionary.

        :param attributes: a dictionary with the attributes to set
        :raise aiida.common.ValidationError: if any of the keys are invalid, i.e. contain periods
        :raise aiida.common.ModificationNotAllowed: if the entity is stored
        """
        if self.is_stored:
            raise exceptions.ModificationNotAllowed('the attributes of a stored entity are immutable')

        self.backend_entity.set_attribute_many(attributes)

    def reset_attributes(self, attributes):
        """Reset the attributes.

        .. note:: This will completely clear any existing attributes and replace them with the new dictionary.

        :param attributes: a dictionary with the attributes to set
        :raise aiida.common.ValidationError: if any of the keys are invalid, i.e. contain periods
        :raise aiida.common.ModificationNotAllowed: if the entity is stored
        """
        if self.is_stored:
            raise exceptions.ModificationNotAllowed('the attributes of a stored entity are immutable')

        self.backend_entity.reset_attributes(attributes)

    def delete_attribute(self, key):
        """Delete an attribute.

        :param key: name of the attribute
        :raises AttributeError: if the attribute does not exist
        :raise aiida.common.ModificationNotAllowed: if the entity is stored
        """
        if self.is_stored:
            raise exceptions.ModificationNotAllowed('the attributes of a stored entity are immutable')

        self.backend_entity.delete_attribute(key)

    def delete_attribute_many(self, keys):
        """Delete multiple attributes.

        :param keys: names of the attributes to delete
        :raises AttributeError: if at least one of the attribute does not exist
        :raise aiida.common.ModificationNotAllowed: if the entity is stored
        """
        if self.is_stored:
            raise exceptions.ModificationNotAllowed('the attributes of a stored entity are immutable')

        self.backend_entity.delete_attribute_many(keys)

    def clear_attributes(self):
        """Delete all attributes."""
        if self.is_stored:
            raise exceptions.ModificationNotAllowed('the attributes of a stored entity are immutable')

        self.backend_entity.clear_attributes()

    def attributes_items(self):
        """Return an iterator over the attributes.

        :return: an iterator with attribute key value pairs
        """
        return self.backend_entity.attributes_items()

    def attributes_keys(self):
        """Return an iterator over the attribute keys.

        :return: an iterator with attribute keys
        """
        return self.backend_entity.attributes_keys()


class EntityExtrasMixin(abc.ABC):
    """Mixin class that adds all methods for the extras column to an entity."""

    @property
    def extras(self):
        """Return the complete extras dictionary.

        .. warning:: While the entity is unstored, this will return references of the extras on the database model,
            meaning that changes on the returned values (if they are mutable themselves, e.g. a list or dictionary) will
            automatically be reflected on the database model as well. As soon as the entity is stored, the returned
            extras will be a deep copy and mutations of the database extras will have to go through the appropriate set
            methods. Therefore, once stored, retrieving a deep copy can be a heavy operation. If you only need the keys
            or some values, use the iterators `extras_keys` and `extras_items`, or the getters `get_extra` and
            `get_extra_many` instead.

        :return: the extras as a dictionary
        """
        extras = self.backend_entity.extras

        if self.is_stored:
            extras = copy.deepcopy(extras)

        return extras

    def get_extra(self, key, default=_NO_DEFAULT):
        """Return the value of an extra.

        .. warning:: While the entity is unstored, this will return a reference of the extra on the database model,
            meaning that changes on the returned value (if they are mutable themselves, e.g. a list or dictionary) will
            automatically be reflected on the database model as well. As soon as the entity is stored, the returned
            extra will be a deep copy and mutations of the database extras will have to go through the appropriate set
            methods.

        :param key: name of the extra
        :param default: return this value instead of raising if the attribute does not exist
        :return: the value of the extra
        :raises AttributeError: if the extra does not exist and no default is specified
        """
        try:
            extra = self.backend_entity.get_extra(key)
        except AttributeError:
            if default is _NO_DEFAULT:
                raise
            extra = default

        if self.is_stored:
            extra = copy.deepcopy(extra)

        return extra

    def get_extra_many(self, keys):
        """Return the values of multiple extras.

        .. warning:: While the entity is unstored, this will return references of the extras on the database model,
            meaning that changes on the returned values (if they are mutable themselves, e.g. a list or dictionary) will
            automatically be reflected on the database model as well. As soon as the entity is stored, the returned
            extras will be a deep copy and mutations of the database extras will have to go through the appropriate set
            methods. Therefore, once stored, retrieving a deep copy can be a heavy operation. If you only need the keys
            or some values, use the iterators `extras_keys` and `extras_items`, or the getters `get_extra` and
            `get_extra_many` instead.

        :param keys: a list of extra names
        :return: a list of extra values
        :raises AttributeError: if at least one extra does not exist
        """
        extras = self.backend_entity.get_extra_many(keys)

        if self.is_stored:
            extras = copy.deepcopy(extras)

        return extras

    def set_extra(self, key, value):
        """Set an extra to the given value.

        :param key: name of the extra
        :param value: value of the extra
        :raise aiida.common.ValidationError: if the key is invalid, i.e. contains periods
        """
        self.backend_entity.set_extra(key, value)

    def set_extra_many(self, extras):
        """Set multiple extras.

        .. note:: This will override any existing extras that are present in the new dictionary.

        :param extras: a dictionary with the extras to set
        :raise aiida.common.ValidationError: if any of the keys are invalid, i.e. contain periods
        """
        self.backend_entity.set_extra_many(extras)

    def reset_extras(self, extras):
        """Reset the extras.

        .. note:: This will completely clear any existing extras and replace them with the new dictionary.

        :param extras: a dictionary with the extras to set
        :raise aiida.common.ValidationError: if any of the keys are invalid, i.e. contain periods
        """
        self.backend_entity.reset_extras(extras)

    def delete_extra(self, key):
        """Delete an extra.

        :param key: name of the extra
        :raises AttributeError: if the extra does not exist
        """
        self.backend_entity.delete_extra(key)

    def delete_extra_many(self, keys):
        """Delete multiple extras.

        :param keys: names of the extras to delete
        :raises AttributeError: if at least one of the extra does not exist
        """
        self.backend_entity.delete_extra_many(keys)

    def clear_extras(self):
        """Delete all extras."""
        self.backend_entity.clear_extras()

    def extras_items(self):
        """Return an iterator over the extras.

        :return: an iterator with extra key value pairs
        """
        return self.backend_entity.extras_items()

    def extras_keys(self):
        """Return an iterator over the extra keys.

        :return: an iterator with extra keys
        """
        return self.backend_entity.extras_keys()
