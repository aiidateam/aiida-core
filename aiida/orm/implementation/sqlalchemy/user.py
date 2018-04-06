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
from aiida.backends.sqlalchemy import get_scoped_session
from aiida.common.lang import override
from aiida.orm.implementation.general.user import AbstractUser, Util as UserUtil


class User(AbstractUser):
    @classmethod
    def from_dbmodel(cls, dbuser):
        if not isinstance(dbuser, DbUser):
            raise ValueError("Expected a DbUser. Object of a different"
                             "class was given as argument.")

        user = cls.__new__(cls)
        user._dbuser = dbuser
        return user

    def __init__(self, email):
        super(User, self).__init__()
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
    def to_be_stored(self):
        return self._dbuser.id is None

    def save(self):
        if not self.to_be_stored:
            self._dbuser.save()

    def force_save(self):
        self._dbuser.save()

    @property
    def email(self):
        self._ensure_model_uptodate(attribute_names=['email'])
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
        self._ensure_model_uptodate(attribute_names=['is_superuser'])
        return self._dbuser.is_superuser

    @is_superuser.setter
    def is_superuser(self, val):
        self._dbuser.is_superuser = val
        self.save()

    @property
    def first_name(self):
        self._ensure_model_uptodate(attribute_names=['first_name'])
        return self._dbuser.first_name

    @first_name.setter
    def first_name(self, val):
        self._dbuser.first_name = val
        self.save()

    @property
    def last_name(self):
        self._ensure_model_uptodate(attribute_names=['last_name'])
        return self._dbuser.last_name

    @last_name.setter
    def last_name(self, val):
        self._dbuser.last_name = val
        self.save()

    @property
    def institution(self):
        self._ensure_model_uptodate(attribute_names=['institution'])
        return self._dbuser.institution

    @institution.setter
    def institution(self, val):
        self._dbuser.institution = val
        self.save()

    @property
    def is_staff(self):
        self._ensure_model_uptodate(attribute_names=['is_staff'])
        return self._dbuser.is_staff

    @is_staff.setter
    def is_staff(self, val):
        self._dbuser.is_staff = val
        self.save()

    @property
    def is_active(self):
        self._ensure_model_uptodate(attribute_names=['is_active'])
        return self._dbuser.is_active

    @is_active.setter
    def is_active(self, val):
        self._dbuser.is_active = val
        self.save()

    @property
    def last_login(self):
        self._ensure_model_uptodate(attribute_names=['last_login'])
        return self._dbuser.last_login

    @last_login.setter
    def last_login(self, val):
        self._dbuser.last_login = val
        self.save()

    @property
    def date_joined(self):
        self._ensure_model_uptodate(attribute_names=['date_joined'])
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
            users.append(User.from_dbmodel(dbuser))
        return users

    def _ensure_model_uptodate(self, attribute_names=None):
        if not self.to_be_stored:
            self._dbuser.session.expire(self._dbuser, attribute_names=attribute_names)


class Util(UserUtil):
    @override
    def delete_user(self, pk):
        """
        Delete the user with the given pk.
        :param pk: The user pk.
        """
        DbUser.query.filter_by(id=pk).delete()


def _get_db_user(user):
    """
    Take an AiiDA User and return the SQLA dbuser model if compatible, otherwise
    raise TypeError

    :param user: The AiiDA user object
    :return: The SQLA dbuser model
    """
    import aiida.orm as orm

    if not isinstance(user, orm.User):
        raise TypeError("Expecting User, got '{}'".format(type(user)))
    backend_user = user._impl

    if not isinstance(backend_user, User):
        raise TypeError("Expected SQLA user, got '{}'".format(user))

    return backend_user._dbuser
