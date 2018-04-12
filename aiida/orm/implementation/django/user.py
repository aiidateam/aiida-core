# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.backends.djsite.db.models import DbUser
from aiida.orm.user import AbstractUser, AbstractUserCollection
from aiida.orm.implementation.general.utils import get_db_columns
from aiida.utils.email import normalize_email
from aiida.common.utils import type_check


class DjangoUserCollection(AbstractUserCollection):
    def create(self, email):
        """
        Create a user with the provided email address

        :param email: An email address for the user
        :return: A new user object
        :rtype: :class:`aiida.orm.AbstractUser`
        """
        return DjangoUser(self, email=normalize_email(email))

    def _from_dbmodel(self, dbuser):
        return DjangoUser._from_dbmodel(self, dbuser)

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
            users.append(self._from_dbmodel(dbuser))
        return users


class DjangoUser(AbstractUser):
    @classmethod
    def _from_dbmodel(cls, backend, dbuser):
        """
        Create a DjangoUser from a dbmodel instance

        :param backend: The backend
        :type backend: :class:`DjangoUserCollection`
        :param dbuser: The dbuser instance
        :type dbuser: :class:`aiida.backends.djsite.db.models.DbUser`
        :return: A DjangoUser instance
        :rtype: :class:`DjangoUser`
        """
        type_check(dbuser, DbUser)
        user = cls.__new__(cls)
        super(DjangoUser, user).__init__(backend)
        user._dbuser = dbuser
        return user

    def __init__(self, backend, email):
        super(DjangoUser, self).__init__(backend)
        self._dbuser = DbUser(email=email)

    @staticmethod
    def get_db_columns():
        from aiida.backends.djsite.querybuilder_django.dummy_model import DbUser as DbU
        return get_db_columns(DbU)

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
        self._ensure_model_uptodate(fields=('email',))
        return self._dbuser.email

    @email.setter
    def email(self, val):
        self._dbuser.email = val
        self._flush(fields=('email',))

    def _set_password(self, val):
        self._dbuser.password = val
        self._flush(fields=('password',))

    def _get_password(self):
        self._ensure_model_uptodate(fields=('password',))
        return self._dbuser.password

    @property
    def first_name(self):
        self._ensure_model_uptodate(fields=('first_name',))
        return self._dbuser.first_name

    @first_name.setter
    def first_name(self, val):
        self._dbuser.first_name = val
        self._flush(fields=('first_name',))

    @property
    def last_name(self):
        self._ensure_model_uptodate(fields=('last_name',))
        return self._dbuser.last_name

    @last_name.setter
    def last_name(self, val):
        self._dbuser.last_name = val
        self._flush(fields=('last_name',))

    @property
    def institution(self):
        self._ensure_model_uptodate(fields=('institution',))
        return self._dbuser.institution

    @institution.setter
    def institution(self, val):
        self._dbuser.institution = val
        self._flush(fields=('institution',))

    @property
    def is_active(self):
        self._ensure_model_uptodate(fields=('is_active',))
        return self._dbuser.is_active

    @is_active.setter
    def is_active(self, val):
        self._dbuser.is_active = val
        self._flush(fields=('is_active',))

    @property
    def last_login(self):
        self._ensure_model_uptodate(fields=('last_login',))
        return self._dbuser.last_login

    @last_login.setter
    def last_login(self, val):
        self._dbuser.last_login = val
        self._flush(fields=('last_login',))

    @property
    def date_joined(self):
        self._ensure_model_uptodate(fields=('date_joined',))
        return self._dbuser.date_joined

    @date_joined.setter
    def date_joined(self, val):
        self._dbuser.date_joined = val
        self._flush(fields=('date_joined',))

    def _flush(self, fields=None):
        """ If the user is stored then save the current value """
        if self.is_stored:
            self._dbuser.save(update_fields=fields)

    def _ensure_model_uptodate(self, fields=None):
        if self.is_stored:
            # For now we have no choice but to reload the entire model.
            # Django 1.8 has support for refreshing an individual attribute, see:
            # https://docs.djangoproject.com/en/1.8/ref/models/instances/#refreshing-objects-from-database
            self._dbuser = DbUser.objects.get(pk=self.pk)
