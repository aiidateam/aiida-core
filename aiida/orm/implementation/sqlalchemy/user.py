# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.backends.sqlalchemy.models.user import DbUser
from aiida.common.lang import override
from aiida.orm.implementation.general.user import AbstractUser, Util as UserUtil
from aiida.utils.email import normalize_email



class User(AbstractUser):

    def __init__(self, **kwargs):
        super(User, self).__init__()

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

    @staticmethod
    def get_db_columns():
        from aiida.orm.implementation.sqlalchemy.utils import get_db_columns
        return get_db_columns(DbUser)

    @property
    def pk(self):
        return self._dbuser.id

    @property
    def id(self):
        return self._dbuser.id

    @property
    def to_be_stored(self):
        return self._dbuser.id is None

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
        if not self.to_be_stored:
            self._dbuser.save()

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
        dbuser_query = DbUser.query

        # If an id is specified then we add it to the query
        if id is not None:
            dbuser_query = dbuser_query.filter_by(id=id)

        # If an email is specified then we add it to the query
        if email is not None:
            dbuser_query = dbuser_query.filter_by(email=email)

        dbusers = dbuser_query.all()
        users = []
        for dbuser in dbusers:
            users.append(cls(dbuser=dbuser))
        return users


class Util(UserUtil):
    @override
    def delete_user(self, pk):
        """
        Delete the user with the given pk.
        :param pk: The user pk.
        """
        DbUser.query.filter_by(id=pk).delete()