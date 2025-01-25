###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for the SqlAlchemy backend implementation of the `AuthInfo` ORM class."""

from aiida.common import exceptions
from aiida.common.lang import type_check
from aiida.orm.implementation.authinfos import BackendAuthInfo, BackendAuthInfoCollection
from aiida.storage.psql_dos.models.authinfo import DbAuthInfo

from . import computers, entities, users, utils


class SqlaAuthInfo(entities.SqlaModelEntity[DbAuthInfo], BackendAuthInfo):
    """SqlAlchemy backend implementation for the `AuthInfo` ORM class."""

    MODEL_CLASS = DbAuthInfo
    USER_CLASS = users.SqlaUser
    COMPUTER_CLASS = computers.SqlaComputer

    def __init__(self, backend, computer, user, enabled, auth_params, metadata):
        """Construct a new instance.

        :param computer: a :class:`aiida.orm.implementation.computers.BackendComputer` instance
        :param user: a :class:`aiida.orm.implementation.users.BackendUser` instance
        :return: an :class:`aiida.orm.implementation.authinfos.BackendAuthInfo` instance
        """
        super().__init__(backend)
        type_check(user, self.USER_CLASS)
        type_check(computer, self.COMPUTER_CLASS)
        self._model = utils.ModelWrapper(
            self.MODEL_CLASS(
                dbcomputer=computer.bare_model,
                aiidauser=user.bare_model,
                enabled=enabled,
                auth_params=auth_params,
                metadata=metadata,
            ),
            backend,
        )

    @property
    def id(self):
        return self.model.id

    @property
    def is_stored(self) -> bool:
        """Return whether the entity is stored.

        :return: True if stored, False otherwise
        """
        return self.model.is_saved()

    @property
    def enabled(self) -> bool:
        """Return whether this instance is enabled.

        :return: boolean, True if enabled, False otherwise
        """
        return self.model.enabled

    @enabled.setter
    def enabled(self, enabled):
        """Set the enabled state

        :param enabled: boolean, True to enable the instance, False to disable it
        """
        self.model.enabled = enabled

    @property
    def computer(self):
        """Return the computer associated with this instance.

        :return: :class:`aiida.orm.implementation.computers.BackendComputer`
        """
        return self.backend.computers.ENTITY_CLASS.from_dbmodel(self.model.dbcomputer, self.backend)

    @property
    def user(self):
        """Return the user associated with this instance.

        :return: :class:`aiida.orm.implementation.users.BackendUser`
        """
        return self.backend.users.ENTITY_CLASS.from_dbmodel(self.model.aiidauser, self.backend)

    def get_auth_params(self):
        """Return the dictionary of authentication parameters

        :return: a dictionary with authentication parameters
        """
        return self.model.auth_params

    def set_auth_params(self, auth_params):
        """Set the dictionary of authentication parameters

        :param auth_params: a dictionary with authentication parameters
        """
        self.model.auth_params = auth_params

    def get_metadata(self):
        """Return the dictionary of metadata

        :return: a dictionary with metadata
        """
        return self.model._metadata

    def set_metadata(self, metadata):
        """Set the dictionary of metadata

        :param metadata: a dictionary with metadata
        """
        self.model._metadata = metadata


class SqlaAuthInfoCollection(BackendAuthInfoCollection):
    """The collection of SqlAlchemy backend `AuthInfo` entries."""

    ENTITY_CLASS = SqlaAuthInfo

    def delete(self, pk):
        """Delete an entry from the collection.

        :param pk: the pk of the entry to delete
        """
        from sqlalchemy.orm.exc import NoResultFound

        session = self.backend.get_session()

        try:
            row = session.query(self.ENTITY_CLASS.MODEL_CLASS).filter_by(id=pk).one()
            session.delete(row)
            session.commit()
        except NoResultFound:
            raise exceptions.NotExistent(f'AuthInfo<{pk}> does not exist')
