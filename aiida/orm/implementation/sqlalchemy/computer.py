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
import json
from copy import copy
import six
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.session import make_transient
from sqlalchemy.orm.attributes import flag_modified

from aiida.common.utils import type_check
from aiida.backends.sqlalchemy.models.computer import DbComputer
from aiida.common.exceptions import InvalidOperation
from aiida.orm.implementation.computers import BackendComputerCollection, BackendComputer
from . import utils


class SqlaComputerCollection(BackendComputerCollection):
    def create(self, **attributes):
        return SqlaComputer(self.backend, attributes)

    def list_names(cls):
        from aiida.backends.sqlalchemy import get_scoped_session
        session = get_scoped_session()
        return session.query(DbComputer.name).all()

    def delete(self, id):
        import aiida.backends.sqlalchemy
        try:
            session = aiida.backends.sqlalchemy.get_scoped_session()
            session.query(DbComputer).get(id).delete()
            session.commit()
        except SQLAlchemyError as exc:
            raise InvalidOperation("Unable to delete the requested computer: it is possible that there "
                                   "is at least one node using this computer (original message: {})".format(exc))

    def from_dbmodel(self, computer):
        """
        Construct a SqlaComputer instance from the corresponding database entry

        :param computer: The DbComputer instance
        :return: The Computer instance
        :rtype: :class:`aiida.orm.implementation.sqlalchemy.computer.SqlaComputer`
        """
        return SqlaComputer.from_dbmodel(computer, self.backend)


class SqlaComputer(BackendComputer):
    @classmethod
    def from_dbmodel(cls, dbmodel, backend):
        type_check(dbmodel, DbComputer)
        computer = SqlaComputer.__new__(cls)
        super(SqlaComputer, computer).__init__(backend)
        computer._dbcomputer = utils.ModelWrapper(dbmodel)
        return computer

    @property
    def uuid(self):
        return six.text_type(self._dbcomputer.uuid)

    @property
    def pk(self):
        return self._dbcomputer.id

    @property
    def id(self):
        return self._dbcomputer.id

    def __init__(self, backend, attributes):
        super(SqlaComputer, self).__init__(backend)
        self._dbcomputer = utils.ModelWrapper(DbComputer(**attributes))

    def set(self, **kwargs):

        is_modified = False

        for key, val in kwargs.items():
            if hasattr(self._dbcomputer, key):
                setattr(self._dbcomputer, key, val)
            else:
                self._dbcomputer._metadata[key] = val
                is_modified = True

        if is_modified:
            flag_modified(self._dbcomputer, "_metadata")

    @property
    def is_stored(self):
        return self._dbcomputer.id is not None

    def copy(self):
        from aiida.backends.sqlalchemy import get_scoped_session
        session = get_scoped_session()

        if not self.is_stored:
            raise InvalidOperation("You can copy a computer only after having stored it")

        newdbcomputer = copy(self._dbcomputer)
        make_transient(newdbcomputer)
        session.add(newdbcomputer)

        newobject = self.__class__(dbcomputer=newdbcomputer)

        return newobject

    @property
    def dbcomputer(self):
        return self._dbcomputer._model

    def store(self):
        try:
            self._dbcomputer.save()
        except SQLAlchemyError:
            raise ValueError(
                "Integrity error, probably the hostname already exists in the"
                " DB")

        return self

    @property
    def name(self):
        return self._dbcomputer.name

    @property
    def description(self):
        return self._dbcomputer.description

    @property
    def hostname(self):
        return self._dbcomputer.hostname

    def get_metadata(self):
        return self._dbcomputer._metadata

    def set_metadata(self, metadata_dict):
        self._dbcomputer._metadata = metadata_dict
        flag_modified(self._dbcomputer, "_metadata")

    def get_transport_params(self):
        """
        Return transport params stored in dbcomputer instance
        """
        return self._dbcomputer.transport_params

    def set_transport_params(self, val):
        try:
            json.dumps(val)  # Check if json compatible
            self._dbcomputer.transport_params = val
        except ValueError:
            raise ValueError("The set of transport_params are not JSON-able")

    def get_name(self):
        return self._dbcomputer.name

    def set_name(self, val):
        self._dbcomputer.name = val

    def get_hostname(self):
        return self._dbcomputer.hostname

    def set_hostname(self, val):
        self._dbcomputer.hostname = val

    def get_description(self):
        return self._dbcomputer.description

    def set_description(self, val):
        self._dbcomputer.description = val

    def is_enabled(self):
        return self._dbcomputer.enabled

    def set_enabled_state(self, enabled):
        self._dbcomputer.enabled = enabled

    def get_scheduler_type(self):
        return self._dbcomputer.scheduler_type

    def set_scheduler_type(self, scheduler_type):

        self._dbcomputer.scheduler_type = scheduler_type

    def get_transport_type(self):
        return self._dbcomputer.transport_type

    def set_transport_type(self, val):
        self._dbcomputer.transport_type = val
