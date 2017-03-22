# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import json
import collections

from django.db import IntegrityError, transaction
from django.core.exceptions import ObjectDoesNotExist

from aiida.backends.djsite.db.models import DbComputer
from aiida.common.lang import override
from aiida.orm.implementation.general.computer import AbstractComputer, Util as ComputerUtil
from aiida.common.exceptions import (NotExistent, ConfigurationError,
                                     InvalidOperation, DbContentError)
from aiida.orm.implementation.django.utils import get_db_columns



class Computer(AbstractComputer):
    @property
    def uuid(self):
        return unicode(self._dbcomputer.uuid)

    @property
    def pk(self):
        return self._dbcomputer.pk

    @property
    def id(self):
        return self._dbcomputer.pk

    def __init__(self, **kwargs):
        super(Computer, self).__init__()

        uuid = kwargs.pop('uuid', None)
        if uuid is not None:
            if kwargs:
                raise ValueError("If you pass a uuid, you cannot pass any "
                                 "further parameter")
            try:
                dbcomputer = DbComputer.objects.get(uuid=uuid)
            except ObjectDoesNotExist:
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
        for k, v in kwargs.iteritems():
            try:
                method = getattr(self, 'set_{}'.format(k))
            except AttributeError:
                raise ValueError("Unable to set '{0}', no set_{0} method "
                                 "found".format(k))
            if not isinstance(method, collections.Callable):
                raise ValueError("Unable to set '{0}', set_{0} is not "
                                 "callable!".format(k))
            method(v)


    @staticmethod
    def get_db_columns():
        from aiida.backends.djsite.db.models import DbComputer
        return get_db_columns(DbComputer)

    @classmethod
    def list_names(cls):
        from aiida.backends.djsite.db.models import DbComputer
        return list(DbComputer.objects.filter().values_list('name', flat=True))

    @property
    def full_text_info(self):
        ret_lines = []
        ret_lines.append("Computer name:     {}".format(self.name))
        ret_lines.append(" * PK:             {}".format(self.pk))
        ret_lines.append(" * UUID:           {}".format(self.uuid))
        ret_lines.append(" * Description:    {}".format(self.description))
        ret_lines.append(" * Hostname:       {}".format(self.hostname))
        ret_lines.append(" * Enabled:        {}".format(
            "True" if self.is_enabled() else "False"))
        ret_lines.append(
            " * Transport type: {}".format(self.get_transport_type()))
        ret_lines.append(
            " * Scheduler type: {}".format(self.get_scheduler_type()))
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
        return (self._dbcomputer.pk is None)

    @classmethod
    def get(cls, computer):
        from aiida.backends.djsite.db.models import DbComputer
        return cls(dbcomputer=DbComputer.get_dbcomputer(computer))

    def copy(self):
        from aiida.backends.djsite.db.models import DbComputer
        if self.to_be_stored:
            raise InvalidOperation(
                "You can copy a computer only after having stored it")
        newdbcomputer = DbComputer.objects.get(pk=self.dbcomputer.pk)
        newdbcomputer.pk = None

        newobject = self.__class__(newdbcomputer)

        return newobject

    @property
    def dbcomputer(self):
        return self._dbcomputer

    def store(self):
        # if self.to_be_stored:

        # As a first thing, I check if the data is valid
        self.validate()
        try:
            # transactions are needed here for Postgresql:
            # https://docs.djangoproject.com/en/1.5/topics/db/transactions/#handling-exceptions-within-postgresql-transactions
            sid = transaction.savepoint()
            self.dbcomputer.save()
            transaction.savepoint_commit(sid)
        except IntegrityError:
            transaction.savepoint_rollback(sid)
            raise ValueError(
                "Integrity error, probably the hostname already exists in the"
                " DB")

        # This is useful because in this way I can do
        # c = Computer().store()
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
        return json.loads(self.dbcomputer.metadata)

    def _set_metadata(self, metadata_dict):
        # if not self.to_be_stored:
        #            raise ModificationNotAllowed("Cannot set a property after having stored the entry")
        self.dbcomputer.metadata = json.dumps(metadata_dict)
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

    def get_workdir(self):
        try:
            return self.dbcomputer.get_workdir()
        except ConfigurationError:
            # This happens the first time: I provide a reasonable default value
            return "/scratch/{username}/aiida_run/"

    def set_workdir(self, val):
        # if self.to_be_stored:
        metadata = self._get_metadata()
        metadata['workdir'] = val
        self._set_metadata(metadata)
        # else:
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

    def get_calculations_on_computer(self):
        from aiida.backends.djsite.db.models import DbNode
        return DbNode.objects.filter(dbcomputer__name=self.name,
                                     type__startswith='calculation')

    def is_enabled(self):
        return self.dbcomputer.enabled

    def get_dbauthinfo(self, user):
        from aiida.backends.djsite.db.models import DbAuthInfo
        try:
            return DbAuthInfo.objects.get(dbcomputer=self.dbcomputer,
                                          aiidauser=user)
        except ObjectDoesNotExist:
            raise NotExistent("The user '{}' is not configured for "
                              "computer '{}'".format(
                user.email, self.name))

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


class Util(ComputerUtil):
    @override
    def delete_computer(self, pk):
        """
        Delete the computer with the given pk.
        :param pk: The computer pk.
        """
        from django.db.models.deletion import ProtectedError
        try:
            DbComputer.objects.filter(pk=pk).delete()
        except ProtectedError:
            raise InvalidOperation("Unable to delete the requested computer: there"
                                   "is at least one node using this computer")
