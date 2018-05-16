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
from aiida.orm.user import User, UserCollection
from aiida.utils.email import normalize_email

from . import utils


class SqlaUserCollection(UserCollection):
    def create(self, email):
        """
        Create a user with the provided email address

        :param email: An email address for the user
        :return: A new user object
        :rtype: :class:`aiida.orm.User`
        """
        return SqlaUser(self, normalize_email(email))

    def _from_dbmodel(self, dbuser):
        return SqlaUser._from_dbmodel(self, dbuser)

    def find(self, email=None, id=None):
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
            users.append(self._from_dbmodel(dbuser))
        return users


class SqlaUser(User):
    @classmethod
    def _from_dbmodel(cls, backend, dbuser):
        if not isinstance(dbuser, DbUser):
            raise ValueError("Expected a DbUser. Object of a different"
                             "class was given as argument.")

        user = cls.__new__(cls)
        super(SqlaUser, user).__init__(backend)
        user._dbuser = utils.ModelWrapper(dbuser)
        return user

    def __init__(self, backend, email):
        super(SqlaUser, self).__init__(backend)
        self._dbuser = utils.ModelWrapper(DbUser(email=email))

    @property
    def dbuser(self):
        return self._dbuser._model

    @property
    def pk(self):
        return self._dbuser.id

    @property
    def id(self):
        return self._dbuser.id

    @property
    def is_stored(self):
        return self._dbuser.id is not None

    def store(self):
        self._dbuser.save()

    @property
    def email(self):
        return self._dbuser.email

    @email.setter
    def email(self, val):
        self._dbuser.email = val

    def _set_password(self, val):
        self._dbuser.password = val

    def _get_password(self):
        return self._dbuser.password

    @property
    def first_name(self):
        return self._dbuser.first_name

    @first_name.setter
    def first_name(self, val):
        self._dbuser.first_name = val

    @property
    def last_name(self):
        return self._dbuser.last_name

    @last_name.setter
    def last_name(self, val):
        self._dbuser.last_name = val

    @property
    def institution(self):
        return self._dbuser.institution

    @institution.setter
    def institution(self, val):
        self._dbuser.institution = val

    @property
    def is_active(self):
        return self._dbuser.is_active

    @is_active.setter
    def is_active(self, val):
        self._dbuser.is_active = val

    @property
    def last_login(self):
        return self._dbuser.last_login

    @last_login.setter
    def last_login(self, val):
        self._dbuser.last_login = val

    @property
    def date_joined(self):
        return self._dbuser.date_joined

    @date_joined.setter
    def date_joined(self, val):
        self._dbuser.date_joined = val
