# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from __future__ import absolute_import
import json
from copy import copy
import six
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.session import make_transient
from sqlalchemy.orm.attributes import flag_modified

from aiida.common.utils import type_check
from aiida.orm.computer import Computer, ComputerCollection
from aiida.backends.sqlalchemy.models.computer import DbComputer
from aiida.common.exceptions import (ConfigurationError, InvalidOperation)
from aiida.common.lang import override
from . import utils


class SqlaComputerCollection(ComputerCollection):
    def create(self, name, hostname, description='', transport_type='', scheduler_type='', workdir=None,
               enabled_state=True):
        return SqlaComputer(self.backend, name=name, hostname=hostname, description=description,
                            transport_type=transport_type, scheduler_type=scheduler_type, workdir=workdir,
                            enabled=enabled_state)

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


class SqlaComputer(Computer):
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

    def __init__(self, backend, name, hostname, description='', transport_type='', scheduler_type='', workdir=None,
                 enabled=True):
        super(Computer, self).__init__(backend)
        self._dbcomputer = utils.ModelWrapper(DbComputer(
            name=name,
            hostname=hostname,
            description=description,
            transport_type=transport_type,
            scheduler_type=scheduler_type,
            enabled=enabled
        ))
        if workdir:
            self.set_workdir(workdir)

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
    def full_text_info(self):
        ret_lines = []
        ret_lines.append("Computer name:     {}".format(self.name))
        ret_lines.append(" * PK:             {}".format(self.pk))
        ret_lines.append(" * UUID:           {}".format(self.uuid))
        ret_lines.append(" * Description:    {}".format(self.description))
        ret_lines.append(" * Hostname:       {}".format(self.hostname))
        ret_lines.append(" * Enabled:        {}".format("True" if self.is_enabled() else "False"))
        ret_lines.append(" * Transport type: {}".format(self.get_transport_type()))
        ret_lines.append(" * Scheduler type: {}".format(self.get_scheduler_type()))
        ret_lines.append(" * Work directory: {}".format(self.get_workdir()))
        ret_lines.append(" * Shebang:        {}".format(self.get_shebang()))
        ret_lines.append(" * mpirun command: {}".format(" ".join(
            self.get_mpirun_command())))
        def_cpus_machine = self.get_default_mpiprocs_per_machine()

        if def_cpus_machine is not None:
            ret_lines.append(" * Default number of cpus per machine: {}".format(
                def_cpus_machine))
        ret_lines.append(" * Used by:        {} nodes".format(
            len(self._dbcomputer.dbnodes)))

        ret_lines.append(" * prepend text:")

        if self.get_prepend_text().strip():
            for l in self.get_prepend_text().split('\n'):
                ret_lines.append("   {}".format(l))
        else:
            ret_lines.append("   # No prepend text.")

        ret_lines.append(" * append text:")

        if self.get_append_text().strip():
            for l in self.get_append_text().split('\n'):
                ret_lines.append("   {}".format(l))
        else:
            ret_lines.append("   # No append text.")

        return "\n".join(ret_lines)

    @property
    def is_stored(self):
        return self._dbcomputer.id is not None

    @override
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
        self.validate()

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

    def _get_metadata(self):
        return self._dbcomputer._metadata

    def _set_metadata(self, metadata_dict):
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

    def get_workdir(self):
        try:
            return self._dbcomputer.get_workdir()
        except ConfigurationError:
            # This happens the first time: I provide a reasonable default value
            return "/scratch/{username}/aiida_run/"

    def set_workdir(self, val):
        pass
        metadata = self._get_metadata()
        metadata['workdir'] = val
        self._set_metadata(metadata)

    def get_shebang(self):
        try:
            return self._dbcomputer.get_shebang()
        except ConfigurationError:
            # This happens the first time: I provide a reasonable default value
            return "#!/bin/bash"

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

    def get_calculations_on_computer(self):
        from aiida.backends.sqlalchemy.models.node import DbNode
        return DbNode.query.filter(
            DbNode.dbcomputer_id == self._dbcomputer.id,
            DbNode.type.like("calculation%")).all()

    def is_enabled(self):
        return self._dbcomputer.enabled

    def set_enabled_state(self, enabled):
        self._dbcomputer.enabled = enabled

    def get_scheduler_type(self):
        return self._dbcomputer.scheduler_type

    def set_scheduler_type(self, val):

        self._dbcomputer.scheduler_type = val

    def get_transport_type(self):
        return self._dbcomputer.transport_type

    def set_transport_type(self, val):
        self._dbcomputer.transport_type = val
