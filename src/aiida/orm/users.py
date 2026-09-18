###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for the ORM user class."""

from __future__ import annotations

import typing as t

import pydantic as pdt

from aiida.common import exceptions
from aiida.manage import get_manager
from aiida.orm import entities
from aiida.orm.decorators import column

if t.TYPE_CHECKING:
    from aiida.orm.implementation import StorageBackend
    from aiida.orm.implementation.users import BackendUser

__all__ = ('User',)


class UserCollection(entities.EntityCollection['User']):
    """The collection of users stored in a backend."""

    collection_type: t.ClassVar[str] = 'users'

    def get_or_create(self, email: str, **kwargs) -> tuple[bool, User]:
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

    def get_default(self) -> User | None:
        """Get the current default user"""
        return self.backend.default_user

    def get_one_by_identifier(self, identifier: object) -> User:
        """Get a single user by its identifier.

        :param identifier: the primary key or email of the user to get
        :return: the user instance
        """
        if isinstance(identifier, int):
            return self.get(pk=identifier)
        if isinstance(identifier, str):
            return self.get(email=identifier)
        raise TypeError('Identifier must be an int or str')

    @staticmethod
    def _entity_base_cls() -> type[User]:
        return User


class User(entities.Entity['BackendUser', UserCollection]):
    """ORM representation of an AiiDA user."""

    _CLS_COLLECTION = UserCollection

    def __init__(
        self,
        email: str,
        first_name: str = '',
        last_name: str = '',
        institution: str = '',
        backend: StorageBackend | None = None,
    ):
        """Create a new `User`."""
        backend = backend or get_manager().get_profile_storage()
        email = self.normalize_email(email)
        backend_entity = backend.users.create(
            email=email,
            first_name=first_name,
            last_name=last_name,
            institution=institution,
        )
        super().__init__(backend_entity)

    def __str__(self) -> str:
        return self.email

    def __eq__(self, other) -> bool:
        if not isinstance(other, User):
            return False

        return self.email == other.email

    @column
    def email(self) -> str:
        """The email of the user."""
        return self._backend_entity.email

    @email.setter
    def email(self, email: str) -> None:
        self._backend_entity.email = email

    @column(model_field_info=pdt.fields.FieldInfo(default=''))
    def first_name(self) -> str:
        """The first name of the user."""
        return self._backend_entity.first_name

    @first_name.setter
    def first_name(self, first_name: str) -> None:
        self._backend_entity.first_name = first_name

    @column(model_field_info=pdt.fields.FieldInfo(default=''))
    def last_name(self) -> str:
        """The last name of the user."""
        return self._backend_entity.last_name

    @last_name.setter
    def last_name(self, last_name: str) -> None:
        self._backend_entity.last_name = last_name

    @column(model_field_info=pdt.fields.FieldInfo(default=''))
    def institution(self) -> str:
        """The institution of the user."""
        return self._backend_entity.institution

    @institution.setter
    def institution(self, institution: str) -> None:
        self._backend_entity.institution = institution

    @property
    def uuid(self) -> None:
        """For now users do not have UUIDs so always return None"""
        return None

    @property
    def is_default(self) -> bool:
        """Return whether the user is the default user."""
        default_user = self.collection.get_default()
        return default_user is not None and self.pk == default_user.pk

    @property
    def full_name(self) -> str:
        """Return the user full name"""
        if self.first_name and self.last_name:
            full_name = f'{self.first_name} {self.last_name} ({self.email})'
        elif self.first_name:
            full_name = f'{self.first_name} ({self.email})'
        elif self.last_name:
            full_name = f'{self.last_name} ({self.email})'
        else:
            full_name = f'{self.email}'

        return full_name

    @property
    def short_name(self) -> str:
        """Return the user short name (typically, this returns the email)"""
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
            email = f'{email_name}@{domain_part.lower()}'
        return email
