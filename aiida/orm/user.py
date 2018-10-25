# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Module for the ORM user classes yo
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import abc

import six

from aiida.common.hashing import is_password_usable
from aiida.common import exceptions
from .backends import CollectionEntry
from . import entities

__all__ = ['User', 'UserCollection']


@six.add_metaclass(abc.ABCMeta)
class UserCollection(entities.Collection):
    """
    The collection of users stored in a backend
    """

    @abc.abstractmethod
    def create(self, email, first_name='', last_name='', institution=''):
        """
        Create a user with the provided email address

        :param email: An email address for the user
        :param first_name: The users first name
        :type first_name: str
        :param last_name: The users last name
        :type last_name: str
        :institution: The users instution
        :type institution: str
        :return: A new user object
        :rtype: :class:`User`
        """
        pass

    def find(self, email=None, id=None):
        """
        Final all users matching the given criteria

        :param email: An email address to search for
        :return: A collection of users matching the criteria
        """
        # pylint: disable=no-self-use, invalid-name, redefined-builtin
        from .querybuilder import QueryBuilder

        qb = QueryBuilder()

        filters = {}
        if id is not None:
            filters['id'] = {'==': id}
        if email is not None:
            filters['email'] = {'==': email}

        qb.append(User, filters=filters)
        res = [_[0] for _ in qb.all()]
        if res is None:
            return []

        return res

    def get(self, email):
        """
        Get a user using the email address
        :param email: The user's email address
        :return: The corresponding user object
        :raises: :class:`aiida.common.exceptions.MultipleObjectsError`, :class:`aiida.common.exceptions.NotExistent`
        """
        results = self.find(email=email)
        if not results:
            raise exceptions.NotExistent()
        else:
            if len(results) > 1:
                raise exceptions.MultipleObjectsError()
            else:
                return results[0]

    def get_or_create(self, email):
        """
        Get the existing user with a given email address or create an unstored one
        :param email: The user's email address
        :return: The corresponding user object
        :raises: :class:`aiida.common.exceptions.MultipleObjectsError`, :class:`aiida.common.exceptions.NotExistent`
        """
        try:
            return False, self.get(email)
        except exceptions.NotExistent:
            return True, self.create(email)

    def get_automatic_user(self):
        """
        Get the current automatic (default) user
        :return: The automatic user
        """
        from aiida.common.utils import get_configured_user_email

        email = get_configured_user_email()
        if not email:
            return None

        try:
            return self.get(email)
        except (exceptions.MultipleObjectsError, exceptions.NotExistent):
            return None

    def all(self):
        """
        Get all users

        :return: A collection of users matching the criteria
        """
        # pylint: disable=no-self-use
        from .querybuilder import QueryBuilder

        query = QueryBuilder()
        query.append(User)
        return [_[0] for _ in query.all()]


@six.add_metaclass(abc.ABCMeta)
class User(CollectionEntry):
    """
    This is the base class for User information in AiiDA.  An implementing
    backend needs to provide a concrete version.
    """
    # pylint: disable=invalid-name

    REQUIRED_FIELDS = ['first_name', 'last_name', 'institution']

    def __str__(self):
        return self.email

    @abc.abstractproperty
    def pk(self):
        pass

    @abc.abstractproperty
    def id(self):
        pass

    @abc.abstractproperty
    def is_stored(self):
        """
        Is the user stored

        :return: True if stored, False otherwise
        :rtype: bool
        """
        pass

    @abc.abstractmethod
    def store(self):
        pass

    @abc.abstractproperty
    def email(self):
        pass

    @abc.abstractmethod
    @email.setter
    def email(self, val):
        pass

    @property
    def password(self):
        return self._get_password()

    @password.setter
    def password(self, val):
        from aiida.common.hashing import create_unusable_pass, pwd_context

        if val is None:
            pass_hash = create_unusable_pass()
        else:
            pass_hash = pwd_context.encrypt(val)

        self._set_password(pass_hash)

    def verify_password(self, password):
        from aiida.common.hashing import pwd_context

        return pwd_context.verify(password, self.password)

    @abc.abstractmethod
    def _get_password(self):
        pass

    @abc.abstractmethod
    def _set_password(self, new_pass):
        pass

    @abc.abstractproperty
    def first_name(self):
        pass

    @abc.abstractmethod
    @first_name.setter
    def first_name(self, val):
        pass

    @abc.abstractproperty
    def last_name(self):
        pass

    @abc.abstractmethod
    @last_name.setter
    def last_name(self, val):
        pass

    @abc.abstractproperty
    def institution(self):
        pass

    @abc.abstractmethod
    @institution.setter
    def institution(self, val):
        pass

    @abc.abstractproperty
    def is_active(self):
        pass

    @abc.abstractmethod
    @is_active.setter
    def is_active(self, val):
        pass

    @abc.abstractproperty
    def last_login(self):
        pass

    @abc.abstractmethod
    @last_login.setter
    def last_login(self, val):
        pass

    @abc.abstractproperty
    def date_joined(self):
        pass

    @abc.abstractmethod
    @date_joined.setter
    def date_joined(self, val):
        pass

    def has_usable_password(self):
        return is_password_usable(self._get_password())

    def get_full_name(self):
        """
        Return the user full name

        :return: the user full name
        """
        if self.first_name and self.last_name:
            return "{} {} ({})".format(self.first_name, self.last_name, self.email)
        elif self.first_name:
            return "{} ({})".format(self.first_name, self.email)
        elif self.last_name:
            return "{} ({})".format(self.last_name, self.email)

        return "{}".format(self.email)

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
