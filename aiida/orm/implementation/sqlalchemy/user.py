# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from aiida.backends.sqlalchemy.models.user import DbUser
from aiida.common.utils import type_check
from aiida.orm.implementation import users

from . import utils


class SqlaUserCollection(users.BackendUserCollection):

    def create(self, email, first_name='', last_name='', institution=''):
        """
        Create a user with the provided email address

        :return: A new user object
        :rtype: :class:`aiida.orm.User`
        """
        return SqlaUser(self.backend, email, first_name, last_name, institution)

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
            users.append(self.from_dbmodel(dbuser))
        return users

    def from_dbmodel(self, dbmodel):
        return SqlaUser.from_dbmodel(dbmodel, self.backend)


class SqlaUser(users.BackendUser):

    @classmethod
    def from_dbmodel(cls, dbmodel, backend):
        type_check(dbmodel, DbUser)
        user = cls.__new__(cls)
        super(SqlaUser, user).__init__(backend)
        user._dbuser = utils.ModelWrapper(dbmodel)
        return user

    def __init__(self, backend, email, first_name, last_name, institution):
        super(SqlaUser, self).__init__(backend)
        self._dbuser = utils.ModelWrapper(DbUser(
            email=email,
            first_name=first_name,
            last_name=last_name,
            institution=institution))

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
    def email(self, email):
        self._dbuser.email = email

    def set_password(self, val):
        self._dbuser.password = val

    def get_password(self):
        return self._dbuser.password

    @property
    def first_name(self):
        return self._dbuser.first_name

    @first_name.setter
    def first_name(self, first_name):
        self._dbuser.first_name = first_name

    @property
    def last_name(self):
        return self._dbuser.last_name

    @last_name.setter
    def last_name(self, last_name):
        self._dbuser.last_name = last_name

    @property
    def institution(self):
        return self._dbuser.institution

    @institution.setter
    def institution(self, institution):
        self._dbuser.institution = institution

    @property
    def is_active(self):
        return self._dbuser.is_active

    @is_active.setter
    def is_active(self, active):
        self._dbuser.is_active = active

    @property
    def last_login(self):
        return self._dbuser.last_login

    @last_login.setter
    def last_login(self, last_login):
        self._dbuser.last_login = last_login

    @property
    def date_joined(self):
        return self._dbuser.date_joined

    @date_joined.setter
    def date_joined(self, date_joined):
        self._dbuser.date_joined = date_joined
