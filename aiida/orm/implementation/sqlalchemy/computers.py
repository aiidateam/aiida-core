# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""SqlAlchemy implementations for the `Computer` entity and collection."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from copy import copy
import six

# pylint: disable=import-error,no-name-in-module
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.session import make_transient

from aiida.backends.sqlalchemy import get_scoped_session
from aiida.backends.sqlalchemy.models.computer import DbComputer
from aiida.common import exceptions, json
from aiida.orm.implementation.computers import BackendComputerCollection, BackendComputer

from . import utils
from . import entities


class SqlaComputer(entities.SqlaModelEntity[DbComputer], BackendComputer):
    """SqlAlchemy implementation for `BackendComputer`."""

    # pylint: disable=too-many-public-methods

    MODEL_CLASS = DbComputer

    def __init__(self, backend, **kwargs):
        super(SqlaComputer, self).__init__(backend)
        self._dbmodel = utils.ModelWrapper(DbComputer(**kwargs))

    @property
    def uuid(self):
        return six.text_type(self._dbmodel.uuid)

    @property
    def pk(self):
        return self._dbmodel.id

    @property
    def id(self):  # pylint: disable=invalid-name
        return self._dbmodel.id

    @property
    def is_stored(self):
        return self._dbmodel.id is not None

    def copy(self):
        """Create an unstored clone of an already stored `Computer`."""
        session = get_scoped_session()

        if not self.is_stored:
            raise exceptions.InvalidOperation("You can copy a computer only after having stored it")

        dbcomputer = copy(self._dbmodel)
        make_transient(dbcomputer)
        session.add(dbcomputer)

        newobject = self.__class__.from_dbmodel(dbcomputer)

        return newobject

    def store(self):
        """Store the `Computer` instance."""
        try:
            self._dbmodel.save()
        except SQLAlchemyError:
            raise ValueError("Integrity error, probably the hostname already exists in the" " DB")

        return self

    @property
    def name(self):
        return self._dbmodel.name

    @property
    def description(self):
        return self._dbmodel.description

    @property
    def hostname(self):
        return self._dbmodel.hostname

    def get_metadata(self):
        return self._dbmodel._metadata  # pylint: disable=protected-access

    def set_metadata(self, metadata_dict):
        self._dbmodel._metadata = metadata_dict  # pylint: disable=protected-access

    def get_transport_params(self):
        """
        Return transport params stored in dbcomputer instance
        """
        return self._dbmodel.transport_params

    def set_transport_params(self, val):
        try:
            json.dumps(val)  # Check if json compatible
            self._dbmodel.transport_params = val
        except ValueError:
            raise ValueError("The set of transport_params are not JSON-able")

    def get_name(self):
        return self._dbmodel.name

    def set_name(self, val):
        self._dbmodel.name = val

    def get_hostname(self):
        return self._dbmodel.hostname

    def set_hostname(self, val):
        self._dbmodel.hostname = val

    def get_description(self):
        return self._dbmodel.description

    def set_description(self, val):
        self._dbmodel.description = val

    def is_enabled(self):
        return self._dbmodel.enabled

    def set_enabled_state(self, enabled):
        self._dbmodel.enabled = enabled

    def get_scheduler_type(self):
        return self._dbmodel.scheduler_type

    def set_scheduler_type(self, scheduler_type):
        self._dbmodel.scheduler_type = scheduler_type

    def get_transport_type(self):
        return self._dbmodel.transport_type

    def set_transport_type(self, transport_type):
        self._dbmodel.transport_type = transport_type


class SqlaComputerCollection(BackendComputerCollection):
    """Collection of `Computer` instances."""

    ENTITY_CLASS = SqlaComputer

    @staticmethod
    def list_names():
        session = get_scoped_session()
        return session.query(DbComputer.name).all()

    def delete(self, pk):
        try:
            session = get_scoped_session()
            session.query(DbComputer).get(pk).delete()
            session.commit()
        except SQLAlchemyError as exc:
            raise exceptions.InvalidOperation(
                "Unable to delete the requested computer: it is possible that there "
                "is at least one node using this computer (original message: {})".format(exc))
