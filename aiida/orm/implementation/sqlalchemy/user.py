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
from aiida.orm.user import AbstractUser, AbstractUserCollection
from aiida.utils.email import normalize_email


class SqlaUserCollection(AbstractUserCollection):
    def create(self, email):
        """
        Create a user with the provided email address

        :param email: An email address for the user
        :return: A new user object
        :rtype: :class:`aiida.orm.AbstractUser`
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


class SqlaUser(AbstractUser):
    @classmethod
    def _from_dbmodel(cls, backend, dbuser):
        if not isinstance(dbuser, DbUser):
            raise ValueError("Expected a DbUser. Object of a different"
                             "class was given as argument.")

        user = cls.__new__(cls)
        super(SqlaUser, user).__init__(backend)
        user._dbuser = dbuser
        return user

    def __init__(self, backend, email):
        super(SqlaUser, self).__init__(backend)
        self._dbuser = DbUser(email=email)

    @staticmethod
    def get_db_columns():
        from aiida.orm.implementation.general.utils import get_db_columns
        return get_db_columns(DbUser)

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
        self._dbuser.session.commit()

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
            # We can't selectively update certain fields only so just
            # restore the whole thing
            self.store()

    def _ensure_model_uptodate(self, fields=None):
        if self.is_stored:
            self._dbuser.session.expire(self._dbuser, attribute_names=fields)
