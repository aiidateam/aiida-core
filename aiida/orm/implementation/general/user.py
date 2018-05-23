# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import logging
from abc import abstractmethod, abstractproperty, ABCMeta
from aiida.common.hashing import is_password_usable
from aiida.common.utils import abstractclassmethod


class AbstractUser(object):
    """
    An AiiDA ORM implementation of a user.
    """

    __metaclass__ = ABCMeta

    _logger = logging.getLogger(__name__)

    REQUIRED_FIELDS = ['first_name', 'last_name', 'institution']

    @abstractmethod
    def __init__(self, **kwargs):
        pass

    @abstractproperty
    def pk(self):
        pass

    @abstractproperty
    def id(self):
        pass

    @abstractmethod
    def save(self):
        pass

    @abstractmethod
    def force_save(self):
        pass

    @abstractproperty
    def email(self):
        pass

    @abstractmethod
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

    @abstractmethod
    def _get_password(self):
        pass

    @abstractmethod
    def _set_password(self):
        pass

    @abstractproperty
    def is_superuser(self):
        pass

    @abstractmethod
    @is_superuser.setter
    def is_superuser(self, val):
        pass

    @abstractproperty
    def first_name(self):
        pass

    @abstractmethod
    @first_name.setter
    def first_name(self, val):
        pass

    @abstractproperty
    def last_name(self):
        pass

    @abstractmethod
    @last_name.setter
    def last_name(self, val):
        pass

    @abstractproperty
    def institution(self):
        pass

    @abstractmethod
    @institution.setter
    def institution(self, val):
        pass

    @abstractproperty
    def is_staff(self):
        pass

    @abstractmethod
    @is_staff.setter
    def is_staff(self, val):
        pass

    @abstractproperty
    def is_active(self):
        pass

    @abstractmethod
    @is_active.setter
    def is_active(self, val):
        pass

    @abstractproperty
    def last_login(self):
        pass

    @abstractmethod
    @last_login.setter
    def last_login(self, val):
        pass

    @abstractproperty
    def date_joined(self):
        pass

    @abstractmethod
    @date_joined.setter
    def date_joined(self, val):
        pass

    def has_usable_password(self):
        return is_password_usable(self._get_password())

    @classmethod
    def get_all_users(cls):
        return cls.search_for_users()

    @abstractclassmethod
    def search_for_users(cls, **kwargs):
        """
        Search for a user the passed keys.

        :param kwargs: The keys to search for the user with.
        :return: A list of users matching the search criteria.
        """
        pass

    @staticmethod
    def get_schema():
        """
        Every node property contains:
            - display_name: display name of the property
            - help text: short help text of the property
            - is_foreign_key: is the property foreign key to other type of the node
            - type: type of the property. e.g. str, dict, int

        :return: get schema of the user
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


class Util(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def delete_user(self, pk):
        """
        Delete the user with the given pk.
        :param pk: The user pk.
        """
        pass

