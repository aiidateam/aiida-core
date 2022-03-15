# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""SqlAlchemy implementations for the `Computer` entity and collection."""

from copy import copy

# pylint: disable=import-error,no-name-in-module
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.session import make_transient

from aiida.common import exceptions
from aiida.orm.implementation.computers import BackendComputer, BackendComputerCollection
from aiida.storage.psql_dos.models.computer import DbComputer

from . import entities, utils


class SqlaComputer(entities.SqlaModelEntity[DbComputer], BackendComputer):
    """SqlAlchemy implementation for `BackendComputer`."""

    # pylint: disable=too-many-public-methods

    MODEL_CLASS = DbComputer

    def __init__(self, backend, **kwargs):
        super().__init__(backend)
        self._model = utils.ModelWrapper(self.MODEL_CLASS(**kwargs), backend)

    @property
    def uuid(self):
        return str(self.model.uuid)

    @property
    def pk(self):
        return self.model.id

    @property
    def id(self):  # pylint: disable=invalid-name
        return self.model.id

    @property
    def is_stored(self):
        return self.model.id is not None

    def copy(self):
        """Create an unstored clone of an already stored `Computer`."""
        session = self.backend.get_session()

        if not self.is_stored:
            raise exceptions.InvalidOperation('You can copy a computer only after having stored it')

        dbcomputer = copy(self.model)
        make_transient(dbcomputer)
        session.add(dbcomputer)

        newobject = self.__class__.from_dbmodel(dbcomputer, self.backend)

        return newobject

    def store(self):
        """Store the `Computer` instance."""
        try:
            self.model.save()
        except SQLAlchemyError:
            raise ValueError('Integrity error, probably the hostname already exists in the DB')

        return self

    @property
    def label(self):
        return self.model.label

    @property
    def description(self):
        return self.model.description

    @property
    def hostname(self):
        return self.model.hostname

    def get_metadata(self):
        return self.model._metadata  # pylint: disable=protected-access

    def set_metadata(self, metadata):
        self.model._metadata = metadata  # pylint: disable=protected-access

    def set_label(self, val):
        self.model.label = val

    def set_hostname(self, val):
        self.model.hostname = val

    def set_description(self, val):
        self.model.description = val

    def get_scheduler_type(self):
        return self.model.scheduler_type

    def set_scheduler_type(self, scheduler_type):
        self.model.scheduler_type = scheduler_type

    def get_transport_type(self):
        return self.model.transport_type

    def set_transport_type(self, transport_type):
        self.model.transport_type = transport_type


class SqlaComputerCollection(BackendComputerCollection):
    """Collection of `Computer` instances."""

    ENTITY_CLASS = SqlaComputer

    def list_names(self):
        session = self.backend.get_session()
        return session.query(self.ENTITY_CLASS.MODEL_CLASS.label).all()

    def delete(self, pk):
        try:
            session = self.backend.get_session()
            row = session.get(self.ENTITY_CLASS.MODEL_CLASS, pk)
            session.delete(row)
            session.commit()
        except SQLAlchemyError as exc:
            raise exceptions.InvalidOperation(
                'Unable to delete the requested computer: it is possible that there '
                'is at least one node using this computer (original message: {})'.format(exc)
            )
