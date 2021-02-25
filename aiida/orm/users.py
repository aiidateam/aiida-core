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

import warnings

from aiida.common import exceptions
from aiida.common.warnings import AiidaDeprecationWarning
from aiida.manage.manager import get_manager
from aiida.manage.configuration import get_profile

from . import entities

__all__ = ('User',)


class User(entities.Entity):
    """AiiDA User"""

    class Collection(entities.Collection):
        """The collection of users stored in a backend."""

        UNDEFINED = 'UNDEFINED'
        _default_user = None  # type: aiida.orm.User

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._default_user = self.UNDEFINED

        def get_or_create(self, email, **kwargs):
            """
            Get the existing user with a given email address or create an unstored one

            :param kwargs: The properties of the user to get or create
            :return: created, user object
            :rtype: bool, :class:`aiida.orm.User`
            """
            try:
                return False, self.get(email=email)
            except exceptions.NotExistent:
                return True, User(backend=self.backend, email=email, **kwargs)

        def get_default(self):
            """
            Get the current default user

            Note: Since the default user is required by many operations,
            once a user is found, the return value is cached.

            :return: The default user
            :rtype: :class:`aiida.orm.User`
            """
            if self._default_user is self.UNDEFINED:
                default_user_email = get_profile().default_user

                # Note: apparently, this is frequently the case in tests
                # if not default_user_email:
                #     raise ValueError(f'No default user specified for profile {get_profile()}.')

                try:
                    self._default_user = self.get(email=default_user_email)
                except (exceptions.MultipleObjectsError, exceptions.NotExistent):
                    self._default_user = None

            return self._default_user

        def get_or_create_default(self, email=None, **kwargs):
            """
            Get the default user or create an unstored one

            :param email: The email of the default user (required only, if the profile has no default user)
            :param kwargs: Remaining properties of the default user to get or create (optional)
            :return: created, user object
            :rtype: bool, :class:`aiida.orm.User`

            """
            if self._default_user is not self.UNDEFINED:
                if email and self._default_user.email != email:
                    raise ValueError(
                        f'Specified email {email} does not match default user email {self._default_user.email}.'
                    )
                return False, self._default_user

            current_profile = get_profile()
            email = email or current_profile.default_user
            if not email:
                raise ValueError(
                    f'Profile {current_profile} does not define a default user.' +
                    'Please specify email to create default user.'
                )
            if email != current_profile.default_user:
                raise ValueError(
                    f'Specified email {email} does not match default user email {current_profile.default_user} ' +
                    f'of profile {current_profile}.'
                )

            created, default_user = self.get_or_create(email=email, **kwargs)
            self._default_user = default_user
            return created, default_user

        def reset(self):
            """
            Reset internal caches (default user).
            """
            self._default_user = self.UNDEFINED

    REQUIRED_FIELDS = ['first_name', 'last_name', 'institution']

    def __init__(self, email, first_name='', last_name='', institution='', backend=None):
        """Create a new `User`."""
        # pylint: disable=too-many-arguments
        backend = backend or get_manager().get_backend()
        email = self.normalize_email(email)
        backend_entity = backend.users.create(email, first_name, last_name, institution)
        super().__init__(backend_entity)

    def __str__(self):
        return self.email

    @staticmethod
    def normalize_email(email):
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
    def email(self):
        return self._backend_entity.email

    @email.setter
    def email(self, email):
        self._backend_entity.email = email

    @property
    def first_name(self):
        return self._backend_entity.first_name

    @first_name.setter
    def first_name(self, first_name):
        self._backend_entity.first_name = first_name

    @property
    def last_name(self):
        return self._backend_entity.last_name

    @last_name.setter
    def last_name(self, last_name):
        self._backend_entity.last_name = last_name

    @property
    def institution(self):
        return self._backend_entity.institution

    @institution.setter
    def institution(self, institution):
        self._backend_entity.institution = institution

    def get_full_name(self):
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

    def get_short_name(self):
        """
        Return the user short name (typically, this returns the email)

        :return: The short name
        """
        return self.email

    @staticmethod
    def get_schema():
        """
        Every node property contains:

          - display_name: display name of the property
          - help text: short help text of the property
          - is_foreign_key: is the property foreign key to other type of the node
          - type: type of the property. e.g. str, dict, int

        :return: schema of the user

        .. deprecated:: 1.0.0

            Will be removed in `v2.0.0`.
            Use :meth:`~aiida.restapi.translator.base.BaseTranslator.get_projectable_properties` instead.

        """
        message = 'method is deprecated, use' \
            '`aiida.restapi.translator.base.BaseTranslator.get_projectable_properties` instead'
        warnings.warn(message, AiidaDeprecationWarning)  # pylint: disable=no-member

        return {
            'id': {
                'display_name': 'Id',
                'help_text': 'Id of the object',
                'is_foreign_key': False,
                'type': 'int'
            },
            'email': {
                'display_name': 'email',
                'help_text': 'e-mail of the user',
                'is_foreign_key': False,
                'type': 'str'
            },
            'first_name': {
                'display_name': 'First name',
                'help_text': 'First name of the user',
                'is_foreign_key': False,
                'type': 'str'
            },
            'institution': {
                'display_name': 'Institution',
                'help_text': 'Affiliation of the user',
                'is_foreign_key': False,
                'type': 'str'
            },
            'last_name': {
                'display_name': 'Last name',
                'help_text': 'Last name of the user',
                'is_foreign_key': False,
                'type': 'str'
            }
        }
