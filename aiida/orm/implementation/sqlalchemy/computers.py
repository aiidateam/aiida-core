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

from aiida.backends.sqlalchemy.models.computer import DbComputer
from aiida.common import exceptions
from aiida.orm.implementation.computers import BackendComputer, BackendComputerCollection

from . import entities, utils


class SqlaComputer(entities.SqlaModelEntity[DbComputer], BackendComputer):
    """SqlAlchemy implementation for `BackendComputer`."""

    # pylint: disable=too-many-public-methods

    MODEL_CLASS = DbComputer

    def __init__(self, backend, **kwargs):
        super().__init__(backend)
        self._aiida_model = utils.ModelWrapper(DbComputer(**kwargs), backend)

    @property
    def uuid(self):
        return str(self.aiida_model.uuid)

    @property
    def pk(self):
        return self.aiida_model.id

    @property
    def id(self):  # pylint: disable=invalid-name
        return self.aiida_model.id

    @property
    def is_stored(self):
        return self.aiida_model.id is not None

    def copy(self):
        """Create an unstored clone of an already stored `Computer`."""
        session = self.backend.get_session()

        if not self.is_stored:
            raise exceptions.InvalidOperation('You can copy a computer only after having stored it')

        dbcomputer = copy(self.aiida_model)
        make_transient(dbcomputer)
        session.add(dbcomputer)

        newobject = self.__class__.from_dbmodel(dbcomputer)  # pylint: disable=no-value-for-parameter

        return newobject

    def store(self):
        """Store the `Computer` instance."""
        try:
            self.aiida_model.save()
        except SQLAlchemyError:
            raise ValueError('Integrity error, probably the hostname already exists in the DB')

        return self

    @property
    def label(self):
        return self.aiida_model.label

    @property
    def description(self):
        return self.aiida_model.description

    @property
    def hostname(self):
        return self.aiida_model.hostname

    def get_metadata(self):
        return self.aiida_model._metadata  # pylint: disable=protected-access

    def set_metadata(self, metadata):
        self.aiida_model._metadata = metadata  # pylint: disable=protected-access

    def set_label(self, val):
        self.aiida_model.label = val

    def set_hostname(self, val):
        self.aiida_model.hostname = val

    def set_description(self, val):
        self.aiida_model.description = val

    def get_scheduler_type(self):
        return self.aiida_model.scheduler_type

    def set_scheduler_type(self, scheduler_type):
        self.aiida_model.scheduler_type = scheduler_type

    def get_transport_type(self):
        return self.aiida_model.transport_type

    def set_transport_type(self, transport_type):
        self.aiida_model.transport_type = transport_type


class SqlaComputerCollection(BackendComputerCollection):
    """Collection of `Computer` instances."""

    ENTITY_CLASS = SqlaComputer

    def list_names(self):
        session = self.backend.get_session()
        return session.query(DbComputer.label).all()

    def delete(self, pk):
        try:
            session = self.backend.get_session()
            row = session.get(DbComputer, pk)
            session.delete(row)
            session.commit()
        except SQLAlchemyError as exc:
            raise exceptions.InvalidOperation(
                'Unable to delete the requested computer: it is possible that there '
                'is at least one node using this computer (original message: {})'.format(exc)
            )
