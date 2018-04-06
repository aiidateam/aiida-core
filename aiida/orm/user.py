# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.orm.utils import BackendDelegateWithDefault
from aiida.common.hashing import is_password_usable
from aiida.utils.email import normalize_email

from . import querybuilder

__all__ = ['User', 'Util', 'get_automatic_user']


class User(object):
    REQUIRED_FIELDS = ['first_name', 'last_name', 'institution']

    @classmethod
    def load(cls, impl):
        obj = cls.__new__(cls)
        obj._impl = impl
        return obj

    def __init__(self, email):
        import aiida.orm.implementation as backend
        email = normalize_email(email)
        self._impl = backend.User(email=email)

    @property
    def pk(self):
        return self._impl.pk

    @property
    def id(self):
        return self.pk

    def save(self):
        return self._impl.save()

    def force_save(self):
        return self._impl.force_save()

    @property
    def email(self):
        return self._impl.email

    @email.setter
    def email(self, val):
        self._impl.email = val

    @property
    def password(self):
        return self._impl._get_password()

    @password.setter
    def password(self, val):
        from aiida.common.hashing import create_unusable_pass, pwd_context

        if val is None:
            pass_hash = create_unusable_pass()
        else:
            pass_hash = pwd_context.encrypt(val)

        self._impl._set_password(pass_hash)

    @property
    def is_superuser(self):
        return self._impl.is_superuser

    @is_superuser.setter
    def is_superuser(self, val):
        self._impl.is_superuser = val

    @property
    def first_name(self):
        return self._impl.first_name

    @first_name.setter
    def first_name(self, val):
        self._impl.first_name = val

    @property
    def last_name(self):
        return self._impl.last_name

    @last_name.setter
    def last_name(self, val):
        self._impl.last_name = val

    @property
    def institution(self):
        return self._impl.institution

    @institution.setter
    def institution(self, val):
        self._impl.institution = val

    @property
    def is_staff(self):
        return self._impl.is_staff

    @is_staff.setter
    def is_staff(self, val):
        self._impl.is_staff = val

    @property
    def is_active(self):
        return self._impl.is_active

    @is_active.setter
    def is_active(self, val):
        self._impl.is_active = val

    @property
    def last_login(self):
        return self._impl.last_login

    @last_login.setter
    def last_login(self, val):
        self._impl.last_login = val

    @property
    def date_joined(self):
        return self._impl.date_joined

    @date_joined.setter
    def date_joined(self, val):
        self._impl.date_joined = val

    def has_usable_password(self):
        return is_password_usable(self.password)

    @classmethod
    def get_all_users(cls):
        return cls.search_for_users()

    @classmethod
    def search_for_users(cls, **kwargs):
        """
        Search for a user the passed keys.

        :param kwargs: The keys to search for the user with.
        :return: A list of users matching the search criteria.
        """
        from aiida.orm.implementation import User as BackendUser
        return [User.load(delegate) for delegate in BackendUser.search_for_users(**kwargs)]


class Util(BackendDelegateWithDefault):
    @classmethod
    def create_default(cls):
        # Fall back to Django
        from aiida.orm.implementation.django.user import Util as UserUtil
        return Util(UserUtil())

    def delete_user(self, pk):
        return self._backend.delete_user(pk)


def get_automatic_user():
    import aiida.orm.implementation as backend
    from aiida.common.utils import get_configured_user_email

    email = get_configured_user_email()
    if not email:
        return None

    qb = querybuilder.QueryBuilder()
    qb.append(User, filters={'email': {'==': email}})
    result = qb.first()
    if result:
        return result[0]
    else:
        return None
