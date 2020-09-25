# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Classes and methods for backend non-specific entities"""
import abc
import typing

from aiida.orm.implementation.utils import clean_value, validate_attribute_extra_key

__all__ = (
    'BackendEntity', 'BackendCollection', 'EntityType', 'BackendEntityAttributesMixin', 'BackendEntityExtrasMixin'
)

EntityType = typing.TypeVar('EntityType')  # pylint: disable=invalid-name


class BackendEntity(abc.ABC):
    """An first-class entity in the backend"""

    def __init__(self, backend):
        self._backend = backend
        self._dbmodel = None

    @property
    def backend(self):
        """Return the backend this entity belongs to

        :return: the backend instance
        """
        return self._backend

    @property
    def dbmodel(self):
        return self._dbmodel

    @abc.abstractproperty
    def id(self):  # pylint: disable=invalid-name
        """Return the id for this entity.

        This is unique only amongst entities of this type for a particular backend.

        :return: the entity id
        """

    @property
    def pk(self):
        """Return the id for this entity.

        This is unique only amongst entities of this type for a particular backend.

        :return: the entity id
        """
        return self.id

    @abc.abstractmethod
    def store(self):
        """Store this entity in the backend.

        Whether it is possible to call store more than once is delegated to the object itself
        """

    @abc.abstractproperty
    def is_stored(self):
        """Return whether the entity is stored.

        :return: True if stored, False otherwise
        :rtype: bool
        """

    def _flush_if_stored(self, fields):
        if self._dbmodel.is_saved():
            self._dbmodel._flush(fields)  # pylint: disable=protected-access


class BackendCollection(typing.Generic[EntityType]):
    """Container class that represents a collection of entries of a particular backend entity."""

    ENTITY_CLASS = None  # type: EntityType

    def __init__(self, backend):
        """
        :param backend: the backend this collection belongs to
        :type backend: :class:`aiida.orm.implementation.Backend`
        """
        assert issubclass(self.ENTITY_CLASS, BackendEntity), 'Must set the ENTRY_CLASS class variable to an entity type'
        self._backend = backend

    def from_dbmodel(self, dbmodel):
        """
        Create an entity from the backend dbmodel

        :param dbmodel: the dbmodel to create the entity from
        :return: the entity instance
        """
        return self.ENTITY_CLASS.from_dbmodel(dbmodel, self.backend)

    @property
    def backend(self):
        """
        Return the backend.

        :rtype: :class:`aiida.orm.implementation.Backend`
        """
        return self._backend

    def create(self, **kwargs):
        """
        Create new a entry and set the attributes to those specified in the keyword arguments

        :return: the newly created entry of type ENTITY_CLASS
        """
        return self.ENTITY_CLASS(backend=self._backend, **kwargs)  # pylint: disable=not-callable


class BackendEntityAttributesMixin(abc.ABC):
    """Mixin class that adds all methods for the attributes column to a backend entity"""

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
        return self._dbmodel.attributes

    def get_attribute(self, key):
        """Return the value of an attribute.

        .. warning:: While the entity is unstored, this will return a reference of the attribute on the database model,
            meaning that changes on the returned value (if they are mutable themselves, e.g. a list or dictionary) will
            automatically be reflected on the database model as well. As soon as the entity is stored, the returned
            attribute will be a deep copy and mutations of the database attributes will have to go through the
            appropriate set methods.

        :param key: name of the attribute
        :return: the value of the attribute
        :raises AttributeError: if the attribute does not exist
        """
        try:
            return self._dbmodel.attributes[key]
        except KeyError as exception:
            raise AttributeError(f'attribute `{exception}` does not exist') from exception

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
        try:
            return [self.get_attribute(key) for key in keys]
        except KeyError as exception:
            raise AttributeError(f'attribute `{exception}` does not exist') from exception

    def set_attribute(self, key, value):
        """Set an attribute to the given value.

        :param key: name of the attribute
        :param value: value of the attribute
        """
        validate_attribute_extra_key(key)

        if self.is_stored:
            value = clean_value(value)

        self._dbmodel.attributes[key] = value
        self._flush_if_stored({'attributes'})

    def set_attribute_many(self, attributes):
        """Set multiple attributes.

        .. note:: This will override any existing attributes that are present in the new dictionary.

        :param attributes: a dictionary with the attributes to set
        """
        for key in attributes:
            validate_attribute_extra_key(key)

        if self.is_stored:
            attributes = {key: clean_value(value) for key, value in attributes.items()}

        for key, value in attributes.items():
            # We need to use `self.dbmodel` without the underscore, because otherwise the second iteration will refetch
            # what is in the database and we lose the initial changes.
            self.dbmodel.attributes[key] = value
        self._flush_if_stored({'attributes'})

    def reset_attributes(self, attributes):
        """Reset the attributes.

        .. note:: This will completely clear any existing attributes and replace them with the new dictionary.

        :param attributes: a dictionary with the attributes to set
        """
        for key in attributes:
            validate_attribute_extra_key(key)

        if self.is_stored:
            attributes = clean_value(attributes)

        self.dbmodel.attributes = attributes
        self._flush_if_stored({'attributes'})

    def delete_attribute(self, key):
        """Delete an attribute.

        :param key: name of the attribute
        :raises AttributeError: if the attribute does not exist
        """
        try:
            self._dbmodel.attributes.pop(key)
        except KeyError as exception:
            raise AttributeError(f'attribute `{exception}` does not exist') from exception
        else:
            self._flush_if_stored({'attributes'})

    def delete_attribute_many(self, keys):
        """Delete multiple attributes.

        :param keys: names of the attributes to delete
        :raises AttributeError: if at least one of the attribute does not exist
        """
        non_existing_keys = [key for key in keys if key not in self._dbmodel.attributes]

        if non_existing_keys:
            raise AttributeError(f"attributes `{', '.join(non_existing_keys)}` do not exist")

        for key in keys:
            self.dbmodel.attributes.pop(key)

        self._flush_if_stored({'attributes'})

    def clear_attributes(self):
        """Delete all attributes."""
        self._dbmodel.attributes = {}
        self._flush_if_stored({'attributes'})

    def attributes_items(self):
        """Return an iterator over the attributes.

        :return: an iterator with attribute key value pairs
        """
        for key, value in self._dbmodel.attributes.items():
            yield key, value

    def attributes_keys(self):
        """Return an iterator over the attribute keys.

        :return: an iterator with attribute keys
        """
        for key in self._dbmodel.attributes.keys():
            yield key

    @abc.abstractproperty
    def is_stored(self):
        """Return whether the entity is stored.

        :return: True if stored, False otherwise
        :rtype: bool
        """

    @abc.abstractmethod
    def _flush_if_stored(self, fields):
        """Flush the fields"""


class BackendEntityExtrasMixin(abc.ABC):
    """Mixin class that adds all methods for the extras column to a backend entity"""

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
        return self._dbmodel.extras

    def get_extra(self, key):
        """Return the value of an extra.

        .. warning:: While the entity is unstored, this will return a reference of the extra on the database model,
            meaning that changes on the returned value (if they are mutable themselves, e.g. a list or dictionary) will
            automatically be reflected on the database model as well. As soon as the entity is stored, the returned
            extra will be a deep copy and mutations of the database extras will have to go through the appropriate set
            methods.

        :param key: name of the extra
        :return: the value of the extra
        :raises AttributeError: if the extra does not exist
        """
        try:
            return self._dbmodel.extras[key]
        except KeyError as exception:
            raise AttributeError(f'extra `{exception}` does not exist') from exception

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
        return [self.get_extra(key) for key in keys]

    def set_extra(self, key, value):
        """Set an extra to the given value.

        :param key: name of the extra
        :param value: value of the extra
        """
        validate_attribute_extra_key(key)

        if self.is_stored:
            value = clean_value(value)

        self._dbmodel.extras[key] = value
        self._flush_if_stored({'extras'})

    def set_extra_many(self, extras):
        """Set multiple extras.

        .. note:: This will override any existing extras that are present in the new dictionary.

        :param extras: a dictionary with the extras to set
        """
        for key in extras:
            validate_attribute_extra_key(key)

        if self.is_stored:
            extras = {key: clean_value(value) for key, value in extras.items()}

        for key, value in extras.items():
            self.dbmodel.extras[key] = value

        self._flush_if_stored({'extras'})

    def reset_extras(self, extras):
        """Reset the extras.

        .. note:: This will completely clear any existing extras and replace them with the new dictionary.

        :param extras: a dictionary with the extras to set
        """
        for key in extras:
            validate_attribute_extra_key(key)

        if self.is_stored:
            extras = clean_value(extras)

        self.dbmodel.extras = extras
        self._flush_if_stored({'extras'})

    def delete_extra(self, key):
        """Delete an extra.

        :param key: name of the extra
        :raises AttributeError: if the extra does not exist
        """
        try:
            self._dbmodel.extras.pop(key)
        except KeyError as exception:
            raise AttributeError(f'extra `{exception}` does not exist') from exception
        else:
            self._flush_if_stored({'extras'})

    def delete_extra_many(self, keys):
        """Delete multiple extras.

        :param keys: names of the extras to delete
        :raises AttributeError: if at least one of the extra does not exist
        """
        non_existing_keys = [key for key in keys if key not in self._dbmodel.extras]

        if non_existing_keys:
            raise AttributeError(f"extras `{', '.join(non_existing_keys)}` do not exist")

        for key in keys:
            self.dbmodel.extras.pop(key)

        self._flush_if_stored({'extras'})

    def clear_extras(self):
        """Delete all extras."""
        self._dbmodel.extras = {}
        self._flush_if_stored({'extras'})

    def extras_items(self):
        """Return an iterator over the extras.

        :return: an iterator with extra key value pairs
        """
        for key, value in self._dbmodel.extras.items():
            yield key, value

    def extras_keys(self):
        """Return an iterator over the extra keys.

        :return: an iterator with extra keys
        """
        for key in self._dbmodel.extras.keys():
            yield key

    @abc.abstractproperty
    def is_stored(self):
        """Return whether the entity is stored.

        :return: True if stored, False otherwise
        :rtype: bool
        """

    @abc.abstractmethod
    def _flush_if_stored(self, fields):
        """Flush the fields"""
