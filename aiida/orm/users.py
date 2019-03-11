# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for the ORM user class."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.common.hashing import is_password_usable
from aiida.common import exceptions
from aiida.manage.manager import get_manager

from . import entities

__all__ = ('User',)


class User(entities.Entity):
    """AiiDA User"""

    class Collection(entities.Collection):
        """
            The collection of users stored in a backend
            """
        UNDEFINED = 'UNDEFINED'
        _default_user = None  # type: aiida.orm.User

        def __init__(self, *args, **kwargs):
            super(User.Collection, self).__init__(*args, **kwargs)
            self._default_user = self.UNDEFINED

        def get_or_create(self, **kwargs):
            """
                Get the existing user with a given email address or create an unstored one

                :param kwargs: The properties of the user to get or create
                :return: The corresponding user object
                :rtype: :class:`aiida.orm.User`
                :raises: :class:`aiida.common.exceptions.MultipleObjectsError`,
                    :class:`aiida.common.exceptions.NotExistent`
                """
            try:
                return False, self.get(**kwargs)
            except exceptions.NotExistent:
                return True, User(backend=self.backend, **kwargs)

        def get_default(self):
            """
            Get the current default user

            :return: The default user
            :rtype: :class:`aiida.orm.User`
            """
            if self._default_user is self.UNDEFINED:
                email = get_manager().get_profile().default_user_email
                if not email:
                    self._default_user = None

                try:
                    self._default_user = self.get(email=email)
                except (exceptions.MultipleObjectsError, exceptions.NotExistent):
                    self._default_user = None

            return self._default_user

    REQUIRED_FIELDS = ['first_name', 'last_name', 'institution']

    def __init__(self, email, first_name='', last_name='', institution='', backend=None):
        backend = backend or get_manager().get_backend()
        email = self.normalize_email(email)
        backend_entity = backend.users.create(email, first_name, last_name, institution)
        super(User, self).__init__(backend_entity)

    def __str__(self):
        return self.email

    @staticmethod
    def normalize_email(email):
        """
        Normalize the address by lowercasing the domain part of the email
        address.

        Taken from Django.
        """
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
    def password(self):
        return self._backend_entity.get_password()

    @password.setter
    def password(self, val):
        from aiida.common.hashing import create_unusable_pass, pwd_context

        if val is None:
            pass_hash = create_unusable_pass()
        else:
            pass_hash = pwd_context.encrypt(val)

        self._backend_entity.set_password(pass_hash)

    def verify_password(self, password):
        from aiida.common.hashing import pwd_context

        return pwd_context.verify(password, self.password)

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

    @property
    def is_active(self):
        return self._backend_entity.is_active

    @is_active.setter
    def is_active(self, active):
        self._backend_entity.is_active = active

    @property
    def last_login(self):
        return self._backend_entity.last_login

    @last_login.setter
    def last_login(self, last_login):
        self._backend_entity.last_login = last_login

    @property
    def date_joined(self):
        return self._backend_entity.date_joined

    @date_joined.setter
    def date_joined(self, date_joined):
        self._backend_entity.date_joined = date_joined

    def has_usable_password(self):
        return is_password_usable(self.password)

    def get_full_name(self):
        """
        Return the user full name

        :return: the user full name
        """
        if self.first_name and self.last_name:
            full_name = "{} {} ({})".format(self.first_name, self.last_name, self.email)
        elif self.first_name:
            full_name = "{} ({})".format(self.first_name, self.email)
        elif self.last_name:
            full_name = "{} ({})".format(self.last_name, self.email)
        else:
            full_name = "{}".format(self.email)

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
        """
        return {
            "date_joined": {
                "display_name": "User since",
                "help_text": "Date and time of registration",
                "is_foreign_key": False,
                "type": "datetime.datetime"
            },
            "email": {
                "display_name": "email",
                "help_text": "e-mail of the user",
                "is_foreign_key": False,
                "type": "str"
            },
            "first_name": {
                "display_name": "First name",
                "help_text": "First name of the user",
                "is_foreign_key": False,
                "type": "str"
            },
            "id": {
                "display_name": "Id",
                "help_text": "Id of the object",
                "is_foreign_key": False,
                "type": "int"
            },
            "institution": {
                "display_name": "Institution",
                "help_text": "Affiliation of the user",
                "is_foreign_key": False,
                "type": "str"
            },
            "is_active": {
                "display_name": "Active",
                "help_text": "True(False) if the user is active(not)",
                "is_foreign_key": False,
                "type": "bool"
            },
            "last_login": {
                "display_name": "Last login",
                "help_text": "Date and time of the last login",
                "is_foreign_key": False,
                "type": "datetime.datetime"
            },
            "last_name": {
                "display_name": "Last name",
                "help_text": "Last name of the user",
                "is_foreign_key": False,
                "type": "str"
            }
        }
