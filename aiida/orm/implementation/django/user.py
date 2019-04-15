# -*- coding: utf-8 -*-

from aiida.orm.implementation.general.user import AbstractUser
from aiida.backends.djsite.db.models import DbUser
from aiida.utils.email import normalize_email

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0.1"
__authors__ = "The AiiDA team."


class User(AbstractUser):

    def __init__(self, **kwargs):
        # If no arguments are passed, then create a new DbUser
        if not kwargs:
            raise ValueError("User can not be instantiated without arguments")

        # If a DbUser is passed as argument. Just use it and
        # wrap it with a User object
        elif 'dbuser' in kwargs:
            # When a dbuser is passed as argument, then no other arguments
            # should be passed.
            if len(kwargs) > 1:
                raise ValueError("When a DbUser is passed as argument, no"
                                 "further arguments are accepted.")
            dbuser = kwargs.pop('dbuser')
            if not isinstance(dbuser, DbUser):
                raise ValueError("Expected a DbUser. Object of a different"
                                 "class was given as argument.")
            self._dbuser = dbuser

        # If the email of a users is given then create a new User object with
        # this email.
        elif 'email' in kwargs:
            # When a dbuser is passed as argument, then no other arguments
            # should be passed.
            if len(kwargs) > 1:
                raise ValueError("When an email is passed as argument, no"
                                 "further arguments are accepted.")
            email = normalize_email(kwargs.pop('email'))
            self._dbuser = DbUser(email=email)

        else:
            raise ValueError("Only dbuser & email are accepted as arguments")

    @property
    def pk(self):
        return self._dbuser.pk

    @property
    def id(self):
        return self._dbuser.pk

    @property
    def to_be_stored(self):
        return self._dbuser.pk is None

    def save(self):
        if not self.to_be_stored:
            self._dbuser.save()

    def force_save(self):
        self._dbuser.save()

    @property
    def email(self):
        return self._dbuser.email

    @email.setter
    def email(self, val):
        self._dbuser.email = val
        self.save()

    def _set_password(self, val):
        self._dbuser.password = val
        self.save()

    def _get_password(self):
        return self._dbuser.password

    @property
    def is_superuser(self):
        return self._dbuser.is_superuser

    @is_superuser.setter
    def is_superuser(self, val):
        self._dbuser.is_superuser = val
        self.save()

    @property
    def first_name(self):
        return self._dbuser.first_name

    @first_name.setter
    def first_name(self, val):
        self._dbuser.first_name = val
        self.save()

    @property
    def last_name(self):
        return self._dbuser.last_name

    @last_name.setter
    def last_name(self, val):
        self._dbuser.last_name = val
        self.save()

    @property
    def institution(self):
        return self._dbuser.institution

    @institution.setter
    def institution(self, val):
        self._dbuser.institution = val
        self.save()

    @property
    def is_staff(self):
        return self._dbuser.is_staff

    @is_staff.setter
    def is_staff(self, val):
        self._dbuser.is_staff = val
        self.save()

    @property
    def is_active(self):
        return self._dbuser.is_active

    @is_active.setter
    def is_active(self, val):
        self._dbuser.is_active = val
        self.save()

    @property
    def last_login(self):
        return self._dbuser.last_login

    @last_login.setter
    def last_login(self, val):
        self._dbuser.last_login = val
        self.save()

    @property
    def date_joined(self):
        return self._dbuser.date_joined

    @date_joined.setter
    def date_joined(self, val):
        self._dbuser.date_joined = val
        self.save()

    @classmethod
    def search_for_users(cls, **kwargs):

        id = kwargs.pop('id', None)
        if id is None:
            id = kwargs.pop('pk', None)
        email = kwargs.pop('email', None)

        # Constructing the default query
        import operator
        from django.db.models import Q
        query_list = []

        # If an id is specified then we add it to the query
        if id is not None:
            query_list.append(Q(pk=id))

        # If an email is specified then we add it to the query
        if email is not None:
            query_list.append(Q(email=email))

        if not query_list:
            dbusers = DbUser.objects.all()
        else:
            dbusers = DbUser.objects.filter(reduce(operator.and_, query_list))
        users = []
        for dbuser in dbusers:
            users.append(cls(dbuser=dbuser))
        return users
