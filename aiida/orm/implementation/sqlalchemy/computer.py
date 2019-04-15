# -*- coding: utf-8 -*-

import json

from copy import copy

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.session import make_transient
from sqlalchemy.orm.attributes import flag_modified

from aiida.backends.sqlalchemy.models.computer import DbComputer
from aiida.backends.sqlalchemy.models.authinfo import DbAuthInfo
from aiida.common.exceptions import (NotExistent, ConfigurationError,
                                     InvalidOperation, DbContentError)
from aiida.orm.implementation.general.computer import AbstractComputer


__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__authors__ = "The AiiDA team."
__version__ = "0.6.0.1"

class Computer(AbstractComputer):

    @property
    def uuid(self):
        return self._dbcomputer.uuid

    @property
    def pk(self):
        return self._dbcomputer.id

    def __init__(self, **kwargs):
        uuid = kwargs.pop('uuid', None)

        if uuid is not None:
            if kwargs:
                raise ValueError("If you pass a uuid, you cannot pass any "
                                 "further parameter")

            dbcomputer = DbComputer.query.filter_by(uuid=uuid).first()
            if not dbcomputer:
                raise NotExistent("No entry with UUID={} found".format(uuid))

            self._dbcomputer = dbcomputer

        else:
            if 'dbcomputer' in kwargs:
                dbcomputer = kwargs.pop('dbcomputer')
                if not (isinstance(dbcomputer, DbComputer)):
                    raise TypeError("dbcomputer must be of type DbComputer")
                self._dbcomputer = dbcomputer

                if kwargs:
                    raise ValueError("If you pass a dbcomputer parameter, "
                                     "you cannot pass any further parameter")
            else:
                self._dbcomputer = DbComputer()

            # Set all remaining parameters, stop if unknown
            self.set(**kwargs)

    def set(self, **kwargs):
        for key, val in kwargs.iteritems():
            if hasattr(self._dbcomputer, key):
                setattr(self._dbcomputer, key, val)
            else:
                self._dbcomputer._metadata[key] = val

        flag_modified(self._dbcomputer, "_metadata")


    @classmethod
    def list_names(cls):
        return list(DbComputer.objects.filter().values_list('name', flat=True))

    @property
    def full_text_info(self):
        ret_lines = []
        ret_lines.append("Computer name:     {}".format(self.name))
        ret_lines.append(" * PK:             {}".format(self.id))
        ret_lines.append(" * UUID:           {}".format(self.uuid))
        ret_lines.append(" * Description:    {}".format(self.description))
        ret_lines.append(" * Hostname:       {}".format(self.hostname))
        ret_lines.append(" * Enabled:        {}".format("True" if self.is_enabled() else "False"))
        ret_lines.append(" * Transport type: {}".format(self.get_transport_type()))
        ret_lines.append(" * Scheduler type: {}".format(self.get_scheduler_type()))
        ret_lines.append(" * Work directory: {}".format(self.get_workdir()))
        ret_lines.append(" * mpirun command: {}".format(" ".join(
            self.get_mpirun_command())))
        def_cpus_machine = self.get_default_mpiprocs_per_machine()

        if def_cpus_machine is not None:
            ret_lines.append(" * Default number of cpus per machine: {}".format(
                def_cpus_machine))

        ret_lines.append(" * Used by:        {} nodes".format(
            len(self.dbcomputer.dbnodes.all())))

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
    def to_be_stored(self):
        return self._dbcomputer.id is None

    @classmethod
    def get(cls, computer):
        return cls(dbcomputer=DbComputer.get_dbcomputer(computer))

    def copy(self):
        if self.to_be_stored:
            raise InvalidOperation("You can copy a computer only after having stored it")

        newdbcomputer = copy(self.dbcomputer)
        make_transient(newdbcomputer)
        session.add(newdbcomputer)

        newobject = self.__class__(newdbcomputer)

        return newobject

    @property
    def dbcomputer(self):
        return self._dbcomputer

    def store(self):
        self.validate()

        try:
            self.dbcomputer.save(commit=True)
        except SQLAlchemyError as e:
            raise ValueError("Integrity error, probably the hostname already exists in the DB")

        return self

    @property
    def name(self):
        return self.dbcomputer.name

    @property
    def description(self):
        return self.dbcomputer.description

    @property
    def hostname(self):
        return self.dbcomputer.hostname

    def _get_metadata(self):
        return self.dbcomputer._metadata

    def _set_metadata(self, metadata_dict):
        self.dbcomputer._metadata = metadata_dict
        flag_modified(self.dbcomputer, "_metadata")
        if not self.to_be_stored:
            self.dbcomputer.save()

    def get_transport_params(self):
        try:
            return json.loads(self.dbcomputer.transport_params)
        except ValueError:
            raise DbContentError(
                "Error while reading transport_params for computer {}".format(
                    self.hostname))

    def set_transport_params(self, val):
        # if self.to_be_stored:
        try:
            self.dbcomputer.transport_params = json.dumps(val)
        except ValueError:
            raise ValueError("The set of transport_params are not JSON-able")
        if not self.to_be_stored:
            self.dbcomputer.save()

        #        else:
        #            raise ModificationNotAllowed("Cannot set a property after having stored the entry")

    def get_workdir(self):
        try:
            return self.dbcomputer.get_workdir()
        except ConfigurationError:
            # This happens the first time: I provide a reasonable default value
            return "/scratch/{username}/aiida_run/"

    def set_workdir(self, val):
        pass
        # if self.to_be_stored:
        metadata = self._get_metadata()
        metadata['workdir'] = val
        self._set_metadata(metadata)
        #else:
        #    raise ModificationNotAllowed("Cannot set a property after having stored the entry")

    def get_name(self):
        return self.dbcomputer.name

    def set_name(self, val):
        self.dbcomputer.name = val
        if not self.to_be_stored:
            self.dbcomputer.save()

    def get_hostname(self):
        return self.dbcomputer.hostname

    def set_hostname(self, val):
        self.dbcomputer.hostname = val
        if not self.to_be_stored:
            self.dbcomputer.save()

    def get_description(self):
        return self.dbcomputer.description

    def set_description(self, val):
        self.dbcomputer.description = val
        if not self.to_be_stored:
            self.dbcomputer.save()

    def is_enabled(self):
        return self.dbcomputer.enabled

    def get_dbauthinfo(self, user):
        info = DbAuthInfo.query.filter_by(dbcomputer=self.dbcomputer,
                                          aiidauser=user.first())
        if not info:
            raise NotExistent("The user '{}' is not configured for "
                              "computer '{}'".format(
                                  user.email, self.name))
        return info

    def is_user_configured(self, user):
        try:
            self.get_dbauthinfo(user)
            return True
        except NotExistent:
            return False

    def is_user_enabled(self, user):
        try:
            dbauthinfo = self.get_dbauthinfo(user)
            return dbauthinfo.enabled
        except NotExistent:
            # Return False if the user is not configured (in a sense,
            # it is disabled for that user)
            return False

    def set_enabled_state(self, enabled):
        self.dbcomputer.enabled = enabled
        if not self.to_be_stored:
            self.dbcomputer.save()

    def get_scheduler_type(self):
        return self.dbcomputer.scheduler_type

    def set_scheduler_type(self, val):

        self.dbcomputer.scheduler_type = val
        if not self.to_be_stored:
            self.dbcomputer.save()

    def get_transport_type(self):
        return self.dbcomputer.transport_type

    def set_transport_type(self, val):
        self.dbcomputer.transport_type = val
        if not self.to_be_stored:
            self.dbcomputer.save()
