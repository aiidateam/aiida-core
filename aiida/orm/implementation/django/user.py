# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from __future__ import absolute_import
from functools import reduce

from aiida.backends.djsite.db.models import DbUser
from aiida.orm.user import User, UserCollection
from aiida.utils.email import normalize_email
from aiida.common.utils import type_check
from . import utils


class DjangoUserCollection(UserCollection):

    def create(self, email, first_name='', last_name='', institution=''):
        """
        Create a user with the provided email address

        :return: A new user object
        :rtype: :class:`aiida.orm.User`
        """
        return DjangoUser(self.backend,
                          email=normalize_email(email),
                          first_name=first_name,
                          last_name=last_name,
                          institution=institution)

    def find(self, email=None, id=None):
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
            users.append(self.from_dbmodel(dbuser))
        return users

    def from_dbmodel(self, dbmodel):
        return DjangoUser.from_dbmodel(dbmodel, self.backend)


class DjangoUser(User):

    @classmethod
    def from_dbmodel(cls, dbmodel, backend):
        """
        Create a DjangoUser from a dbmodel instance

        :param backend: The backend
        :type backend: :class:`DjangoUserCollection`
        :param dbmodel: The dbmodel instance
        :type dbmodel: :class:`aiida.backends.djsite.db.models.DbUser`
        :return: A DjangoUser instance
        :rtype: :class:`DjangoUser`
        """
        type_check(dbmodel, DbUser)
        user = cls.__new__(cls)
        super(DjangoUser, user).__init__(backend)
        user._dbuser = utils.ModelWrapper(dbmodel)
        return user

    def __init__(self, backend, email, first_name, last_name, institution):
        super(DjangoUser, self).__init__(backend)
        self._dbuser = utils.ModelWrapper(DbUser(
            email=email,
            first_name=first_name,
            last_name=last_name,
            institution=institution))

    @property
    def dbuser(self):
        # We have to get the underlying model here rather than just the wrapper
        return self._dbuser._model

    @property
    def pk(self):
        return self._dbuser.pk

    @property
    def id(self):
        return self._dbuser.pk

    def __int__(self):
        # Needed to pass this object to raw django queries
        return self.id

    @property
    def is_stored(self):
        return self._dbuser.pk is not None

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
