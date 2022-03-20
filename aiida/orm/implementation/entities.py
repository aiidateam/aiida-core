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
from typing import TYPE_CHECKING, Any, ClassVar, Dict, Generic, Iterable, List, Tuple, Type, TypeVar

if TYPE_CHECKING:
    from aiida.orm.implementation import StorageBackend

__all__ = ('BackendEntity', 'BackendCollection', 'EntityType', 'BackendEntityExtrasMixin')

EntityType = TypeVar('EntityType', bound='BackendEntity')  # pylint: disable=invalid-name


class BackendEntity(abc.ABC):
    """An first-class entity in the backend"""

    def __init__(self, backend: 'StorageBackend', **kwargs: Any):  # pylint: disable=unused-argument
        self._backend = backend

    @property
    def backend(self) -> 'StorageBackend':
        """Return the backend this entity belongs to

        :return: the backend instance
        """
        return self._backend

    @property
    @abc.abstractmethod
    def id(self) -> int:  # pylint: disable=invalid-name
        """Return the id for this entity.

        This is unique only amongst entities of this type for a particular backend.

        :return: the entity id
        """

    @property
    def pk(self) -> int:
        """Return the id for this entity.

        This is unique only amongst entities of this type for a particular backend.

        :return: the entity id
        """
        return self.id

    @abc.abstractmethod
    def store(self: EntityType) -> EntityType:
        """Store this entity in the backend.

        Whether it is possible to call store more than once is delegated to the object itself
        """

    @property
    @abc.abstractmethod
    def is_stored(self) -> bool:
        """Return whether the entity is stored.

        :return: True if stored, False otherwise
        """


class BackendCollection(Generic[EntityType]):
    """Container class that represents a collection of entries of a particular backend entity."""

    ENTITY_CLASS: ClassVar[Type[EntityType]]  # type: ignore[misc]

    def __init__(self, backend: 'StorageBackend'):
        """
        :param backend: the backend this collection belongs to
        """
        assert issubclass(self.ENTITY_CLASS, BackendEntity), 'Must set the ENTRY_CLASS class variable to an entity type'
        self._backend = backend

    @property
    def backend(self) -> 'StorageBackend':
        """Return the backend."""
        return self._backend

    def create(self, **kwargs: Any) -> EntityType:
        """
        Create new a entry and set the attributes to those specified in the keyword arguments

        :return: the newly created entry of type ENTITY_CLASS
        """
        return self.ENTITY_CLASS(backend=self._backend, **kwargs)


class BackendEntityExtrasMixin(abc.ABC):
    """Mixin class that adds all abstract methods for the extras column to a backend entity"""

    @property
    @abc.abstractmethod
    def extras(self) -> Dict[str, Any]:
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

    @abc.abstractmethod
    def get_extra(self, key: str) -> Any:
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

    def get_extra_many(self, keys: Iterable[str]) -> List[Any]:
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

    @abc.abstractmethod
    def set_extra(self, key: str, value: Any) -> None:
        """Set an extra to the given value.

        :param key: name of the extra
        :param value: value of the extra
        """

    def set_extra_many(self, extras: Dict[str, Any]) -> None:
        """Set multiple extras.

        .. note:: This will override any existing extras that are present in the new dictionary.

        :param extras: a dictionary with the extras to set
        """
        for key, value in extras.items():
            self.set_extra(key, value)

    @abc.abstractmethod
    def reset_extras(self, extras: Dict[str, Any]) -> None:
        """Reset the extras.

        .. note:: This will completely clear any existing extras and replace them with the new dictionary.

        :param extras: a dictionary with the extras to set
        """

    @abc.abstractmethod
    def delete_extra(self, key: str) -> None:
        """Delete an extra.

        :param key: name of the extra
        :raises AttributeError: if the extra does not exist
        """

    def delete_extra_many(self, keys: Iterable[str]) -> None:
        """Delete multiple extras.

        :param keys: names of the extras to delete
        :raises AttributeError: if at least one of the extra does not exist
        """
        for key in keys:
            self.delete_extra(key)

    @abc.abstractmethod
    def clear_extras(self) -> None:
        """Delete all extras."""

    @abc.abstractmethod
    def extras_items(self) -> Iterable[Tuple[str, Any]]:
        """Return an iterator over the extras key/value pairs."""

    @abc.abstractmethod
    def extras_keys(self) -> Iterable[str]:
        """Return an iterator over the extra keys."""
