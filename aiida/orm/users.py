# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for the ORM user class."""
from typing import TYPE_CHECKING, Optional, Tuple, Type

from aiida.common import exceptions
from aiida.common.lang import classproperty
from aiida.manage import get_manager

from . import entities

if TYPE_CHECKING:
    from aiida.orm.implementation import BackendUser, StorageBackend

__all__ = ('User',)


class UserCollection(entities.Collection['User']):
    """The collection of users stored in a backend."""

    @staticmethod
    def _entity_base_cls() -> Type['User']:
        return User

    def __init__(self, entity_class: Type['User'], backend: Optional['StorageBackend'] = None) -> None:
        super().__init__(entity_class=entity_class, backend=backend)
        self._default_user: Optional[User] = None

    def get_or_create(self, email: str, **kwargs) -> Tuple[bool, 'User']:
        """Get the existing user with a given email address or create an unstored one

        :param kwargs: The properties of the user to get or create
        :return: The corresponding user object
        :raises: :class:`aiida.common.exceptions.MultipleObjectsError`,
            :class:`aiida.common.exceptions.NotExistent`
        """
        try:
            return False, self.get(email=email)
        except exceptions.NotExistent:
            return True, User(backend=self.backend, email=email, **kwargs)

    def get_default(self) -> Optional['User']:
        """Get the current default user"""
        if self._default_user is None:
            email = self.backend.profile.default_user_email
            if not email:
                self._default_user = None

            try:
                self._default_user = self.get(email=email)
            except (exceptions.MultipleObjectsError, exceptions.NotExistent):
                self._default_user = None

        return self._default_user

    def reset(self) -> None:
        """
        Reset internal caches (default user).
        """
        self._default_user = None


class User(entities.Entity['BackendUser']):
    """AiiDA User"""

    Collection = UserCollection

    @classproperty
    def objects(cls: Type['User']) -> UserCollection:  # type: ignore[misc] # pylint: disable=no-self-argument
        return UserCollection.get_cached(cls, get_manager().get_profile_storage())

    def __init__(
        self,
        email: str,
        first_name: str = '',
        last_name: str = '',
        institution: str = '',
        backend: Optional['StorageBackend'] = None
    ):
        """Create a new `User`."""
        # pylint: disable=too-many-arguments
        backend = backend or get_manager().get_profile_storage()
        email = self.normalize_email(email)
        backend_entity = backend.users.create(email, first_name, last_name, institution)
        super().__init__(backend_entity)

    def __str__(self) -> str:
        return self.email

    @staticmethod
    def normalize_email(email: str) -> str:
        """Normalize the address by lowercasing the domain part of the email address (taken from Django)."""
        email = email or ''
        try:
            email_name, domain_part = email.strip().rsplit('@', 1)
        except ValueError:
            pass
        else:
            email = '@'.join([email_name, domain_part.lower()])
        return email

    @property
    def email(self) -> str:
        return self._backend_entity.email

    @email.setter
    def email(self, email: str) -> None:
        self._backend_entity.email = email

    @property
    def first_name(self) -> str:
        return self._backend_entity.first_name

    @first_name.setter
    def first_name(self, first_name: str) -> None:
        self._backend_entity.first_name = first_name

    @property
    def last_name(self) -> str:
        return self._backend_entity.last_name

    @last_name.setter
    def last_name(self, last_name: str) -> None:
        self._backend_entity.last_name = last_name

    @property
    def institution(self) -> str:
        return self._backend_entity.institution

    @institution.setter
    def institution(self, institution: str) -> None:
        self._backend_entity.institution = institution

    def get_full_name(self) -> str:
        """
        Return the user full name

        :return: the user full name
        """
        if self.first_name and self.last_name:
            full_name = f'{self.first_name} {self.last_name} ({self.email})'
        elif self.first_name:
            full_name = f'{self.first_name} ({self.email})'
        elif self.last_name:
            full_name = f'{self.last_name} ({self.email})'
        else:
            full_name = f'{self.email}'

        return full_name

    def get_short_name(self) -> str:
        """
        Return the user short name (typically, this returns the email)

        :return: The short name
        """
        return self.email

    @property
    def uuid(self) -> None:
        """
        For now users do not have UUIDs so always return None
        """
        return None
