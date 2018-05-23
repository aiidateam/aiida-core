# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.backends.sqlalchemy.models.authinfo import DbAuthInfo
from aiida.orm.authinfo import AuthInfoCollection, AuthInfo
from aiida.common import exceptions
from aiida.common.utils import type_check

from . import computer as computers
from . import user as users
from . import utils


class SqlaAuthInfoCollection(AuthInfoCollection):
    def create(self, computer, user):
        return SqlaAuthInfo(self, computer, user)

    def get(self, computer, user):
        """
        Return a SqlaAuthInfo given a computer and a user

        :param computer: A Computer or DbComputer instance
        :param user: A User or DbUser instance
        :return: a SqlaAuthInfo object associated to the given computer and User, if any
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

            return self._from_dbmodel(authinfo)
        except NoResultFound:
            raise exceptions.NotExistent(
                "The aiida user {} is not configured to use computer {}".format(
                    user.email, computer.name))
        except MultipleResultsFound:
            raise exceptions.ConfigurationError(
                "The aiida user {} is configured more than once to use "
                "computer {}! Only one configuration is allowed".format(
                    user.email, computer.name))

    def _from_dbmodel(self, dbmodel):
        return SqlaAuthInfo._from_dbmodel(self, dbmodel)


class SqlaAuthInfo(AuthInfo):
    """
    AuthInfo implementation for SQLAlchemy
    """

    @classmethod
    def _from_dbmodel(cls, backend, dbmodel):
        type_check(dbmodel, DbAuthInfo)
        authinfo = SqlaAuthInfo.__new__(cls)
        super(SqlaAuthInfo, authinfo).__init__(backend)
        authinfo._dbauthinfo = utils.ModelWrapper(dbmodel)
        return authinfo

    def __init__(self, backend, computer, user):
        """
        Construct an SqlaAuthInfo
        """
        from aiida.orm.computer import Computer

        super(SqlaAuthInfo, self).__init__(backend)

        type_check(user, users.SqlaUser)

        # Takes care of always getting a Computer instance from a DbComputer, Computer or string
        dbcomputer = Computer.get(computer).dbcomputer
        # user.email exists both for DbUser and User, so I'm robust w.r.t. the type of what I get
        dbuser = user.dbuser
        self._dbauthinfo = utils.ModelWrapper(
            DbAuthInfo(dbcomputer=dbcomputer, aiidauser=dbuser))

    @property
    def dbauthinfo(self):
        return self._dbauthinfo._model

    @property
    def is_stored(self):
        """
        Is it already stored or not?

        :return: Boolean
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
        return computers.Computer.get(self._dbauthinfo.dbcomputer)

    @property
    def user(self):
        return self._backend.users._from_dbmodel(self._dbauthinfo.aiidauser)

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

    def get_metadata(self):
        """
        Get the metadata dictionary from the DB

        :return: a dictionary
        """
        return self._dbauthinfo._metadata

    def set_metadata(self, metadata):
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
