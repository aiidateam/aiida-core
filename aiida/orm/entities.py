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
import abc
import copy
from enum import Enum
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Dict, Generic, List, Optional, Protocol, Type, TypeVar, cast

from plumpy.base.utils import call_with_super_check, super_check

from aiida.common import exceptions
from aiida.common.lang import classproperty, type_check
from aiida.manage import get_manager

if TYPE_CHECKING:
    from aiida.orm.implementation import BackendEntity, StorageBackend
    from aiida.orm.querybuilder import FilterType, OrderByType, QueryBuilder

__all__ = ('Entity', 'Collection', 'EntityAttributesMixin', 'EntityExtrasMixin', 'EntityTypes')

CollectionType = TypeVar('CollectionType', bound='Collection')
EntityType = TypeVar('EntityType', bound='Entity')
BackendEntityType = TypeVar('BackendEntityType', bound='BackendEntity')

_NO_DEFAULT: Any = tuple()


class EntityTypes(Enum):
    """Enum for referring to ORM entities in a backend-agnostic manner."""
    AUTHINFO = 'authinfo'
    COMMENT = 'comment'
    COMPUTER = 'computer'
    GROUP = 'group'
    LOG = 'log'
    NODE = 'node'
    USER = 'user'
    LINK = 'link'
    GROUP_NODE = 'group_node'


class Collection(abc.ABC, Generic[EntityType]):
    """Container class that represents the collection of objects of a particular entity type."""

    @staticmethod
    @abc.abstractmethod
    def _entity_base_cls() -> Type[EntityType]:
        """The allowed entity class or subclasses thereof."""

    @classmethod
    @lru_cache(maxsize=100)
    def get_cached(cls, entity_class: Type[EntityType], backend: 'StorageBackend'):
        """Get the cached collection instance for the given entity class and backend.

        :param backend: the backend instance to get the collection for
        """
        from aiida.orm.implementation import StorageBackend
        type_check(backend, StorageBackend)
        return cls(entity_class, backend=backend)

    def __init__(self, entity_class: Type[EntityType], backend: Optional['StorageBackend'] = None) -> None:
        """ Construct a new entity collection.

        :param entity_class: the entity type e.g. User, Computer, etc
        :param backend: the backend instance to get the collection for, or use the default
        """
        from aiida.orm.implementation import StorageBackend
        type_check(backend, StorageBackend, allow_none=True)
        assert issubclass(entity_class, self._entity_base_cls())
        self._backend = backend or get_manager().get_profile_storage()
        self._entity_type = entity_class

    def __call__(self: CollectionType, backend: 'StorageBackend') -> CollectionType:
        """Get or create a cached collection using a new backend."""
        if backend is self._backend:
            return self
        return self.get_cached(self.entity_type, backend=backend)  # type: ignore

    @property
    def entity_type(self) -> Type[EntityType]:
        """The entity type for this instance."""
        return self._entity_type

    @property
    def backend(self) -> 'StorageBackend':
        """Return the backend."""
        return self._backend

    def query(
        self,
        filters: Optional['FilterType'] = None,
        order_by: Optional['OrderByType'] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> 'QueryBuilder':
        """Get a query builder for the objects of this collection.

        :param filters: the keyword value pair filters to match
        :param order_by: a list of (key, direction) pairs specifying the sort order
        :param limit: the maximum number of results to return
        :param offset: number of initial results to be skipped
        """
        from . import querybuilder

        filters = filters or {}
        order_by = {self.entity_type: order_by} if order_by else {}

        query = querybuilder.QueryBuilder(backend=self._backend, limit=limit, offset=offset)
        query.append(self.entity_type, project='*', filters=filters)
        query.order_by([order_by])
        return query

    def get(self, **filters: Any) -> EntityType:
        """Get a single collection entry that matches the filter criteria.

        :param filters: the filters identifying the object to get

        :return: the entry
        """
        res = self.query(filters=filters)
        return res.one()[0]

    def find(
        self,
        filters: Optional['FilterType'] = None,
        order_by: Optional['OrderByType'] = None,
        limit: Optional[int] = None
    ) -> List[EntityType]:
        """Find collection entries matching the filter criteria.

        :param filters: the keyword value pair filters to match
        :param order_by: a list of (key, direction) pairs specifying the sort order
        :param limit: the maximum number of results to return

        :return: a list of resulting matches
        """
        query = self.query(filters=filters, order_by=order_by, limit=limit)
        return cast(List[EntityType], query.all(flat=True))

    def all(self) -> List[EntityType]:
        """Get all entities in this collection.

        :return: A list of all entities
        """
        return cast(List[EntityType], self.query().all(flat=True))  # pylint: disable=no-member

    def count(self, filters: Optional['FilterType'] = None) -> int:
        """Count entities in this collection according to criteria.

        :param filters: the keyword value pair filters to match

        :return: The number of entities found using the supplied criteria
        """
        return self.query(filters=filters).count()


class Entity(abc.ABC, Generic[BackendEntityType]):
    """An AiiDA entity"""

    @classproperty
    @abc.abstractmethod
    def objects(cls: EntityType) -> Collection[EntityType]:  # pylint: disable=no-self-argument,disable=no-self-use
        """Get a collection for objects of this type, with the default backend.

        :return: an object that can be used to access entities of this type
        """

    @classmethod
    def get(cls, **kwargs):
        return cls.objects.get(**kwargs)  # pylint: disable=no-member

    @classmethod
    def from_backend_entity(cls: Type[EntityType], backend_entity: BackendEntityType) -> EntityType:
        """
        Construct an entity from a backend entity instance

        :param backend_entity: the backend entity

        :return: an AiiDA entity instance
        """
        from .implementation.entities import BackendEntity

        type_check(backend_entity, BackendEntity)
        entity = cls.__new__(cls)
        entity._backend_entity = backend_entity
        call_with_super_check(entity.initialize)
        return entity

    def __init__(self, backend_entity: BackendEntityType) -> None:
        """
        :param backend_entity: the backend model supporting this entity
        """
        self._backend_entity = backend_entity
        call_with_super_check(self.initialize)

    @super_check
    def initialize(self) -> None:
        """Initialize instance attributes.

        This will be called after the constructor is called or an entity is created from an existing backend entity.
        """

    @property
    def id(self) -> int:  # pylint: disable=invalid-name
        """Return the id for this entity.

        This identifier is guaranteed to be unique amongst entities of the same type for a single backend instance.

        :return: the entity's id
        """
        return self._backend_entity.id

    @property
    def pk(self) -> int:
        """Return the primary key for this entity.

        This identifier is guaranteed to be unique amongst entities of the same type for a single backend instance.

        :return: the entity's principal key
        """
        return self.id

    def store(self: EntityType) -> EntityType:
        """Store the entity."""
        self._backend_entity.store()
        return self

    @property
    def is_stored(self) -> bool:
        """Return whether the entity is stored."""
        return self._backend_entity.is_stored

    @property
    def backend(self) -> 'StorageBackend':
        """Get the backend for this entity"""
        return self._backend_entity.backend

    @property
    def backend_entity(self) -> BackendEntityType:
        """Get the implementing class for this object"""
        return self._backend_entity


class EntityProtocol(Protocol):
    """Protocol for attributes required by Entity mixins."""

    @property
    def backend_entity(self) -> 'BackendEntity':
        ...

    @property
    def is_stored(self) -> bool:
        ...


class EntityAttributesMixin:
    """Mixin class that adds all methods for the attributes column to an entity."""

    @property
    def attributes(self: EntityProtocol) -> Dict[str, Any]:
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

    def get_attribute(self: EntityProtocol, key: str, default=_NO_DEFAULT) -> Any:
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

    def get_attribute_many(self: EntityProtocol, keys: List[str]) -> List[Any]:
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

    def set_attribute(self: EntityProtocol, key: str, value: Any) -> None:
        """Set an attribute to the given value.

        :param key: name of the attribute
        :param value: value of the attribute
        :raise aiida.common.ValidationError: if the key is invalid, i.e. contains periods
        :raise aiida.common.ModificationNotAllowed: if the entity is stored
        """
        if self.is_stored:
            raise exceptions.ModificationNotAllowed('the attributes of a stored entity are immutable')

        self.backend_entity.set_attribute(key, value)

    def set_attribute_many(self: EntityProtocol, attributes: Dict[str, Any]) -> None:
        """Set multiple attributes.

        .. note:: This will override any existing attributes that are present in the new dictionary.

        :param attributes: a dictionary with the attributes to set
        :raise aiida.common.ValidationError: if any of the keys are invalid, i.e. contain periods
        :raise aiida.common.ModificationNotAllowed: if the entity is stored
        """
        if self.is_stored:
            raise exceptions.ModificationNotAllowed('the attributes of a stored entity are immutable')

        self.backend_entity.set_attribute_many(attributes)

    def reset_attributes(self: EntityProtocol, attributes: Dict[str, Any]) -> None:
        """Reset the attributes.

        .. note:: This will completely clear any existing attributes and replace them with the new dictionary.

        :param attributes: a dictionary with the attributes to set
        :raise aiida.common.ValidationError: if any of the keys are invalid, i.e. contain periods
        :raise aiida.common.ModificationNotAllowed: if the entity is stored
        """
        if self.is_stored:
            raise exceptions.ModificationNotAllowed('the attributes of a stored entity are immutable')

        self.backend_entity.reset_attributes(attributes)

    def delete_attribute(self: EntityProtocol, key: str) -> None:
        """Delete an attribute.

        :param key: name of the attribute
        :raises AttributeError: if the attribute does not exist
        :raise aiida.common.ModificationNotAllowed: if the entity is stored
        """
        if self.is_stored:
            raise exceptions.ModificationNotAllowed('the attributes of a stored entity are immutable')

        self.backend_entity.delete_attribute(key)

    def delete_attribute_many(self: EntityProtocol, keys: List[str]) -> None:
        """Delete multiple attributes.

        :param keys: names of the attributes to delete
        :raises AttributeError: if at least one of the attribute does not exist
        :raise aiida.common.ModificationNotAllowed: if the entity is stored
        """
        if self.is_stored:
            raise exceptions.ModificationNotAllowed('the attributes of a stored entity are immutable')

        self.backend_entity.delete_attribute_many(keys)

    def clear_attributes(self: EntityProtocol) -> None:
        """Delete all attributes."""
        if self.is_stored:
            raise exceptions.ModificationNotAllowed('the attributes of a stored entity are immutable')

        self.backend_entity.clear_attributes()

    def attributes_items(self: EntityProtocol):
        """Return an iterator over the attributes.

        :return: an iterator with attribute key value pairs
        """
        return self.backend_entity.attributes_items()

    def attributes_keys(self: EntityProtocol):
        """Return an iterator over the attribute keys.

        :return: an iterator with attribute keys
        """
        return self.backend_entity.attributes_keys()


class EntityExtrasMixin:
    """Mixin class that adds all methods for the extras column to an entity."""

    @property
    def extras(self: EntityProtocol) -> Dict[str, Any]:
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

    def get_extra(self: EntityProtocol, key: str, default: Any = _NO_DEFAULT) -> Any:
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

    def get_extra_many(self: EntityProtocol, keys: List[str]) -> List[Any]:
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

    def set_extra(self: EntityProtocol, key: str, value: Any) -> None:
        """Set an extra to the given value.

        :param key: name of the extra
        :param value: value of the extra
        :raise aiida.common.ValidationError: if the key is invalid, i.e. contains periods
        """
        self.backend_entity.set_extra(key, value)

    def set_extra_many(self: EntityProtocol, extras: Dict[str, Any]) -> None:
        """Set multiple extras.

        .. note:: This will override any existing extras that are present in the new dictionary.

        :param extras: a dictionary with the extras to set
        :raise aiida.common.ValidationError: if any of the keys are invalid, i.e. contain periods
        """
        self.backend_entity.set_extra_many(extras)

    def reset_extras(self: EntityProtocol, extras: Dict[str, Any]) -> None:
        """Reset the extras.

        .. note:: This will completely clear any existing extras and replace them with the new dictionary.

        :param extras: a dictionary with the extras to set
        :raise aiida.common.ValidationError: if any of the keys are invalid, i.e. contain periods
        """
        self.backend_entity.reset_extras(extras)

    def delete_extra(self: EntityProtocol, key: str) -> None:
        """Delete an extra.

        :param key: name of the extra
        :raises AttributeError: if the extra does not exist
        """
        self.backend_entity.delete_extra(key)

    def delete_extra_many(self: EntityProtocol, keys: List[str]) -> None:
        """Delete multiple extras.

        :param keys: names of the extras to delete
        :raises AttributeError: if at least one of the extra does not exist
        """
        self.backend_entity.delete_extra_many(keys)

    def clear_extras(self: EntityProtocol) -> None:
        """Delete all extras."""
        self.backend_entity.clear_extras()

    def extras_items(self: EntityProtocol):
        """Return an iterator over the extras.

        :return: an iterator with extra key value pairs
        """
        return self.backend_entity.extras_items()

    def extras_keys(self: EntityProtocol):
        """Return an iterator over the extra keys.

        :return: an iterator with extra keys
        """
        return self.backend_entity.extras_keys()
