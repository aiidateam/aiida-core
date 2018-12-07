# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""SQLA user"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from aiida.backends.sqlalchemy.models.user import DbUser
from aiida.orm.implementation.users import BackendUser, BackendUserCollection
from . import entities
from . import utils

__all__ = ('SqlaUserCollection', 'SqlaUser')


class SqlaUserCollection(BackendUserCollection):
    """Collection of SQLA Users"""

    def create(self, email, first_name='', last_name='', institution=''):
        """
        Create a user with the provided email address

        :return: A new user object
        :rtype: :class:`aiida.orm.User`
        """
        return SqlaUser(self.backend, email, first_name, last_name, institution)

    def find(self, email=None, id=None):  # pylint: disable=redefined-builtin, invalid-name
        """
        Find a user in matching the given criteria

        :param email: the email address
        :param id: the id
        :return: the matching user
        :rtype: :class:`aiida.orm.implementation.sqlalchemy.users.SqlaUser`
        """

        # Constructing the default query
        dbuser_query = DbUser.query

        # If an id is specified then we add it to the query
        if id is not None:
            dbuser_query = dbuser_query.filter_by(id=id)

        # If an email is specified then we add it to the query
        if email is not None:
            dbuser_query = dbuser_query.filter_by(email=email)

        dbusers = dbuser_query.all()
        found_users = []
        for dbuser in dbusers:
            found_users.append(self.from_dbmodel(dbuser))
        return found_users

    def from_dbmodel(self, dbmodel):
        return SqlaUser.from_dbmodel(dbmodel, self.backend)


class SqlaUser(entities.SqlaModelEntity[DbUser], BackendUser):
    """SQLA user"""

    MODEL_CLASS = DbUser

    def __init__(self, backend, email, first_name, last_name, institution):
        super(SqlaUser, self).__init__(backend)
        self._dbmodel = utils.ModelWrapper(
            DbUser(email=email, first_name=first_name, last_name=last_name, institution=institution))

    @property
    def email(self):
        return self._dbmodel.email

    @email.setter
    def email(self, email):
        self._dbmodel.email = email

    def set_password(self, new_pass):
        self._dbmodel.password = new_pass

    def get_password(self):
        return self._dbmodel.password

    @property
    def first_name(self):
        return self._dbmodel.first_name

    @first_name.setter
    def first_name(self, first_name):
        self._dbmodel.first_name = first_name

    @property
    def last_name(self):
        return self._dbmodel.last_name

    @last_name.setter
    def last_name(self, last_name):
        self._dbmodel.last_name = last_name

    @property
    def institution(self):
        return self._dbmodel.institution

    @institution.setter
    def institution(self, institution):
        self._dbmodel.institution = institution

    @property
    def is_active(self):
        return self._dbmodel.is_active

    @is_active.setter
    def is_active(self, active):
        self._dbmodel.is_active = active

    @property
    def last_login(self):
        return self._dbmodel.last_login

    @last_login.setter
    def last_login(self, last_login):
        self._dbmodel.last_login = last_login

    @property
    def date_joined(self):
        return self._dbmodel.date_joined

    @date_joined.setter
    def date_joined(self, date_joined):
        self._dbmodel.date_joined = date_joined
