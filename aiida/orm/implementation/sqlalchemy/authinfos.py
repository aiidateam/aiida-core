# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for the SqlAlchemy backend implementation of the `AuthInfo` ORM class."""

from aiida.backends.sqlalchemy import get_scoped_session
from aiida.backends.sqlalchemy.models.authinfo import DbAuthInfo
from aiida.common import exceptions
from aiida.common.lang import type_check

from ..authinfos import BackendAuthInfo, BackendAuthInfoCollection
from . import entities
from . import utils


class SqlaAuthInfo(entities.SqlaModelEntity[DbAuthInfo], BackendAuthInfo):
    """SqlAlchemy backend implementation for the `AuthInfo` ORM class."""

    MODEL_CLASS = DbAuthInfo

    def __init__(self, backend, computer, user):
        """Construct a new instance.

        :param computer: a :class:`aiida.orm.implementation.computers.BackendComputer` instance
        :param user: a :class:`aiida.orm.implementation.users.BackendUser` instance
        :return: an :class:`aiida.orm.implementation.authinfos.BackendAuthInfo` instance
        """
        from . import computers
        from . import users
        super().__init__(backend)
        type_check(user, users.SqlaUser)
        type_check(computer, computers.SqlaComputer)
        self._dbmodel = utils.ModelWrapper(DbAuthInfo(dbcomputer=computer.dbmodel, aiidauser=user.dbmodel))

    @property
    def id(self):  # pylint: disable=invalid-name
        return self._dbmodel.id

    @property
    def is_stored(self):
        """Return whether the entity is stored.

        :return: True if stored, False otherwise
        :rtype: bool
        """
        return self._dbmodel.is_saved()

    @property
    def enabled(self):
        """Return whether this instance is enabled.

        :return: boolean, True if enabled, False otherwise
        """
        return self._dbmodel.enabled

    @enabled.setter
    def enabled(self, enabled):
        """Set the enabled state

        :param enabled: boolean, True to enable the instance, False to disable it
        """
        self._dbmodel.enabled = enabled

    @property
    def computer(self):
        """Return the computer associated with this instance.

        :return: :class:`aiida.orm.implementation.computers.BackendComputer`
        """
        return self.backend.computers.from_dbmodel(self._dbmodel.dbcomputer)

    @property
    def user(self):
        """Return the user associated with this instance.

        :return: :class:`aiida.orm.implementation.users.BackendUser`
        """
        return self._backend.users.from_dbmodel(self._dbmodel.aiidauser)

    def get_auth_params(self):
        """Return the dictionary of authentication parameters

        :return: a dictionary with authentication parameters
        """
        return self._dbmodel.auth_params

    def set_auth_params(self, auth_params):
        """Set the dictionary of authentication parameters

        :param auth_params: a dictionary with authentication parameters
        """
        self._dbmodel.auth_params = auth_params

    def get_metadata(self):
        """Return the dictionary of metadata

        :return: a dictionary with metadata
        """
        return self._dbmodel._metadata  # pylint: disable=protected-access

    def set_metadata(self, metadata):
        """Set the dictionary of metadata

        :param metadata: a dictionary with metadata
        """
        self._dbmodel._metadata = metadata  # pylint: disable=protected-access


class SqlaAuthInfoCollection(BackendAuthInfoCollection):
    """The collection of SqlAlchemy backend `AuthInfo` entries."""

    ENTITY_CLASS = SqlaAuthInfo

    def delete(self, pk):
        """Delete an entry from the collection.

        :param pk: the pk of the entry to delete
        """
        # pylint: disable=import-error,no-name-in-module
        from sqlalchemy.orm.exc import NoResultFound

        session = get_scoped_session()

        try:
            session.query(DbAuthInfo).filter_by(id=pk).one().delete()
            session.commit()
        except NoResultFound:
            raise exceptions.NotExistent(f'AuthInfo<{pk}> does not exist')

    def get(self, computer, user):
        """Return an entry from the collection that is configured for the given computer and user

        :param computer: a :class:`aiida.orm.implementation.computers.BackendComputer` instance
        :param user: a :class:`aiida.orm.implementation.users.BackendUser` instance
        :return: :class:`aiida.orm.implementation.authinfos.BackendAuthInfo`
        :raise aiida.common.exceptions.NotExistent: if no entry exists for the computer/user pair
        :raise aiida.common.exceptions.MultipleObjectsError: if multiple entries exist for the computer/user pair
        """
        # pylint: disable=import-error,no-name-in-module
        from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

        session = get_scoped_session()

        try:
            authinfo = session.query(DbAuthInfo).filter_by(dbcomputer_id=computer.id, aiidauser_id=user.id).one()
        except NoResultFound:
            raise exceptions.NotExistent(f'User<{user.email}> has no configuration for Computer<{computer.name}>')
        except MultipleResultsFound:
            raise exceptions.MultipleObjectsError(
                f'User<{user.email}> has multiple configurations for Computer<{computer.name}>'
            )
        else:
            return self.from_dbmodel(authinfo)
