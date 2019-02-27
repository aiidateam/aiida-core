# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""SqlAlchemy implementations for the AuthInfo entity and collection."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=import-error,no-name-in-module
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from aiida.backends.sqlalchemy import get_scoped_session
from aiida.backends.sqlalchemy.models.authinfo import DbAuthInfo
from aiida.common import exceptions
from aiida.common.lang import type_check
from aiida.orm.implementation.authinfos import BackendAuthInfo, BackendAuthInfoCollection

from . import entities
from . import utils


class SqlaAuthInfo(entities.SqlaModelEntity[DbAuthInfo], BackendAuthInfo):
    """AuthInfo implementation for SQLAlchemy."""

    MODEL_CLASS = DbAuthInfo

    def __init__(self, backend, computer, user):
        """
        Construct an SqlaAuthInfo

        :param computer: a Computer instance
        :param user: a User instance
        :return: an AuthInfo object associated with the given computer and user
        """
        from . import computers
        from . import users
        super(SqlaAuthInfo, self).__init__(backend)
        type_check(user, users.SqlaUser)
        type_check(computer, computers.SqlaComputer)
        self._dbmodel = utils.ModelWrapper(DbAuthInfo(dbcomputer=computer.dbmodel, aiidauser=user.dbmodel))

    @property
    def dbauthinfo(self):
        return self._dbmodel._model  # pylint: disable=protected-access

    @property
    def is_stored(self):
        """
        Return whether the AuthInfo is stored

        :return: True if stored, False otherwise
        """
        return self._dbmodel.is_saved()

    @property
    def id(self):
        return self._dbmodel.id

    @property
    def enabled(self):
        return self._dbmodel.enabled

    @enabled.setter
    def enabled(self, enabled):
        self._dbmodel.enabled = enabled

    @property
    def computer(self):
        return self._backend.computers.from_dbmodel(self._dbmodel.dbcomputer)

    @property
    def user(self):
        return self._backend.users.from_dbmodel(self._dbmodel.aiidauser)

    def get_auth_params(self):
        """
        Get the auth_params dictionary from the DB

        :return: a dictionary
        """
        return self._dbmodel.auth_params

    def set_auth_params(self, auth_params):
        """
        Replace the auth_params dictionary in the DB with the provided dictionary
        """
        # Raises ValueError if data is not JSON-serializable
        self._dbmodel.auth_params = auth_params

    def get_metadata(self):
        """
        Get the metadata dictionary from the DB

        :return: a dictionary
        """
        return self._dbmodel._metadata  # pylint: disable=protected-access

    def set_metadata(self, metadata):
        """
        Replace the metadata dictionary in the DB with the provided dictionary
        """
        # Raises ValueError if data is not JSON-serializable
        self._dbmodel._metadata = metadata  # pylint: disable=protected-access


class SqlaAuthInfoCollection(BackendAuthInfoCollection):
    """Collection of AuthInfo instances."""

    ENTITY_CLASS = SqlaAuthInfo

    def get(self, computer, user):
        """
        Return a SqlaAuthInfo given a computer and a user

        :param computer: a Computer instance
        :param user: a User instance
        :return: an AuthInfo object associated with the given computer and user
        :raise aiida.common.NotExistent: if the user is not configured to use computer
        :raise sqlalchemy.orm.exc.MultipleResultsFound: if the user is configured
             more than once to use the computer! Should never happen
        """
        session = get_scoped_session()

        try:
            authinfo = session.query(DbAuthInfo).filter_by(
                dbcomputer_id=computer.id,
                aiidauser_id=user.id,
            ).one()

            return self.from_dbmodel(authinfo)
        except NoResultFound:
            raise exceptions.NotExistent('The aiida user {} is not configured to use computer {}'.format(
                user.email, computer.name))
        except MultipleResultsFound:
            raise exceptions.ConfigurationError('The aiida user {} is configured more than once to use '
                                                'computer {}! Only one configuration is allowed'.format(
                                                    user.email, computer.name))

    def delete(self, authinfo_id):
        session = get_scoped_session()
        try:
            session.query(DbAuthInfo).filter_by(id=authinfo_id).one().delete()
            session.commit()
        except NoResultFound:
            raise exceptions.NotExistent("AuthInfo with id '{}' not found".format(authinfo_id))
