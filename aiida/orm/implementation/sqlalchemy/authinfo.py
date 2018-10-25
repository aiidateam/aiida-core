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
from aiida.backends.sqlalchemy.models.authinfo import DbAuthInfo
from aiida.common import exceptions
from aiida.common.utils import type_check
from aiida.orm.authinfo import AuthInfoCollection, AuthInfo

from . import computer as computers
from . import user as users
from . import utils


class SqlaAuthInfoCollection(AuthInfoCollection):

    def create(self, computer, user):
        return SqlaAuthInfo(self.backend, computer, user)

    def get(self, computer, user):
        """
        Return a SqlaAuthInfo given a computer and a user

        :param computer: a Computer instance
        :param user: a User instance
        :return: an AuthInfo object associated with the given computer and user
        :raise NotExistent: if the user is not configured to use computer
        :raise sqlalchemy.orm.exc.MultipleResultsFound: if the user is configured
             more than once to use the computer! Should never happen
        """
        from aiida.backends.sqlalchemy.models.authinfo import DbAuthInfo
        from aiida.backends.sqlalchemy import get_scoped_session
        session = get_scoped_session()
        from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

        try:
            authinfo = session.query(DbAuthInfo).filter_by(
                dbcomputer_id=computer.id,
                aiidauser_id=user.id,
            ).one()

            return self.from_dbmodel(authinfo)
        except NoResultFound:
            raise exceptions.NotExistent(
                "The aiida user {} is not configured to use computer {}".format(
                    user.email, computer.name))
        except MultipleResultsFound:
            raise exceptions.ConfigurationError(
                "The aiida user {} is configured more than once to use "
                "computer {}! Only one configuration is allowed".format(
                    user.email, computer.name))

    def remove(self, authinfo_id):
        from sqlalchemy.orm.exc import NoResultFound
        from aiida.backends.sqlalchemy import get_scoped_session

        session = get_scoped_session()
        try:
            session.query(DbAuthInfo).filter_by(id=authinfo_id).delete()
            session.commit()
        except NoResultFound:
            raise exceptions.NotExistent("AuthInfo with id '{}' not found".format(authinfo_id))

    def from_dbmodel(self, dbmodel):
        return SqlaAuthInfo.from_dbmodel(dbmodel, self.backend)


class SqlaAuthInfo(AuthInfo):
    """AuthInfo implementation for SQLAlchemy."""

    @classmethod
    def from_dbmodel(cls, dbmodel, backend):
        type_check(dbmodel, DbAuthInfo)
        authinfo = SqlaAuthInfo.__new__(cls)
        super(SqlaAuthInfo, authinfo).__init__(backend)
        authinfo._dbauthinfo = utils.ModelWrapper(dbmodel)
        return authinfo

    def __init__(self, backend, computer, user):
        """
        Construct an SqlaAuthInfo

        :param computer: a Computer instance
        :param user: a User instance
        :return: an AuthInfo object associated with the given computer and user
        """
        super(SqlaAuthInfo, self).__init__(backend)
        type_check(user, users.SqlaUser)
        backend_computer = computer.backend_entity
        type_check(backend_computer, computers.SqlaComputer)
        self._dbauthinfo = utils.ModelWrapper(DbAuthInfo(dbcomputer=backend_computer.dbcomputer, aiidauser=user.dbuser))

    @property
    def dbauthinfo(self):
        return self._dbauthinfo._model

    @property
    def is_stored(self):
        """
        Return whether the AuthInfo is stored

        :return: True if stored, False otherwise
        """
        return self._dbauthinfo.is_saved()

    @property
    def id(self):
        return self._dbauthinfo.id

    @property
    def enabled(self):
        return self._dbauthinfo.enabled

    @enabled.setter
    def enabled(self, value):
        self._dbauthinfo.enabled = value

    @property
    def computer(self):
        return self._backend.computers.from_dbmodel(self._dbauthinfo.dbcomputer)

    @property
    def user(self):
        return self._backend.users.from_dbmodel(self._dbauthinfo.aiidauser)

    def get_auth_params(self):
        """
        Get the auth_params dictionary from the DB

        :return: a dictionary
        """
        return self._dbauthinfo.auth_params

    def set_auth_params(self, auth_params):
        """
        Replace the auth_params dictionary in the DB with the provided dictionary
        """
        # Raises ValueError if data is not JSON-serializable
        self._dbauthinfo.auth_params = auth_params

    def _get_metadata(self):
        """
        Get the metadata dictionary from the DB

        :return: a dictionary
        """
        return self._dbauthinfo._metadata

    def _set_metadata(self, metadata):
        """
        Replace the metadata dictionary in the DB with the provided dictionary
        """
        # Raises ValueError if data is not JSON-serializable
        self._dbauthinfo._metadata = metadata

    def store(self):
        """
        Store the AuthInfo (possibly updating values if changed)

        :return: the AuthInfo instance
        """
        self._dbauthinfo.save()
        return self
