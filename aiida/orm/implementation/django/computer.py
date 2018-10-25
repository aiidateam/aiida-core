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
import collections
import six
from django.db import IntegrityError, transaction

from aiida.backends.djsite.db.models import DbComputer
from aiida.common.utils import type_check
from aiida.common.exceptions import (InvalidOperation, DbContentError)
from aiida.orm.implementation.computers import BackendComputerCollection, BackendComputer
from . import utils


class DjangoComputerCollection(BackendComputerCollection):
    def create(self, **attributes):
        return DjangoComputer(self.backend, attributes)

    def list_names(self):
        from aiida.backends.djsite.db.models import DbComputer
        return list(DbComputer.objects.filter().values_list('name', flat=True))

    def delete(self, id):
        """ Delete the computer with the given id """
        from django.db.models.deletion import ProtectedError
        try:
            DbComputer.objects.filter(pk=id).delete()
        except ProtectedError:
            raise InvalidOperation("Unable to delete the requested computer: there"
                                   "is at least one node using this computer")

    def from_dbmodel(self, computer):
        """
        Create a DjangoComputer from a DbComputer instance

        :param computer: The dbcomputer instance
        :type computer: :class:`aiida.backends.djsite.db.models.DbComputer`
        :return: The DjangoComputer instance
        :rtype: :class:`aiida.orm.implementation.django.computer.DjangoComputer`
        """
        return DjangoComputer.from_dbmodel(computer, self.backend)


class DjangoComputer(BackendComputer):
    @classmethod
    def from_dbmodel(cls, dbmodel, backend):
        """
        Create a DjangoUser from a dbmodel instance

        :param dbmodel: The dbmodel instance
        :type dbmodel: :class:`aiida.backends.djsite.db.models.DbComputer`
        :param backend: The backend
        :type backend: :class:`aiida.orm.implementation.django.backend.DjangoBackend`
        :return: A DjangoComputer instance
        :rtype: :class:`aiida.orm.implementation.django.computer.DjangoComputer`
        """
        type_check(dbmodel, DbComputer)
        computer = cls.__new__(cls)
        super(DjangoComputer, computer).__init__(backend)
        computer._dbcomputer = utils.ModelWrapper(dbmodel)
        return computer

    @property
    def uuid(self):
        return six.text_type(self._dbcomputer.uuid)

    @property
    def pk(self):
        return self._dbcomputer.pk

    @property
    def id(self):
        return self._dbcomputer.pk

    def __init__(self, backend, attributes):
        super(DjangoComputer, self).__init__(backend)
        self._dbcomputer = utils.ModelWrapper(DbComputer(**attributes))

    def set(self, **kwargs):
        for k, v in kwargs.items():
            try:
                method = getattr(self, 'set_{}'.format(k))
            except AttributeError:
                raise ValueError("Unable to set '{0}', no set_{0} method "
                                 "found".format(k))
            if not isinstance(method, collections.Callable):
                raise ValueError("Unable to set '{0}', set_{0} is not "
                                 "callable!".format(k))
            method(v)

    @property
    def is_stored(self):
        return self._dbcomputer.pk is not None

    def copy(self):
        from aiida.backends.djsite.db.models import DbComputer
        if not self.is_stored:
            raise InvalidOperation(
                "You can copy a computer only after having stored it")
        newdbcomputer = DbComputer.objects.get(pk=self.pk)
        newdbcomputer.pk = None

        newobject = self.__class__(dbcomputer=newdbcomputer)

        return newobject

    @property
    def dbcomputer(self):
        """
        Return the underlying DbComputer

        :return: Return the DbComputer
        :rtype: :class:`aiida.backends.djsite.db.models.DbComputer`
        """
        return self._dbcomputer._model

    def store(self):
        # As a first thing, I check if the data is valid
        sid = transaction.savepoint()
        try:
            # transactions are needed here for Postgresql:
            # https://docs.djangoproject.com/en/1.5/topics/db/transactions/#handling-exceptions-within-postgresql-transactions
            self._dbcomputer.save()
            transaction.savepoint_commit(sid)
        except IntegrityError:
            transaction.savepoint_rollback(sid)
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
        return json.loads(self._dbcomputer.metadata)

    def set_metadata(self, metadata_dict):
        # When setting, use the uncached _dbcomputer
        self._dbcomputer.metadata = json.dumps(metadata_dict)

    def get_transport_params(self):
        try:
            return json.loads(self._dbcomputer.transport_params)
        except ValueError:
            raise DbContentError(
                "Error while reading transport_params for computer {}".format(
                    self.hostname))

    def set_transport_params(self, val):
        # When setting, use the uncached _dbcomputer
        try:
            self._dbcomputer.transport_params = json.dumps(val)
        except ValueError:
            raise ValueError("The set of transport_params are not JSON-able")

    def get_name(self):
        return self._dbcomputer.name

    def set_name(self, val):
        # When setting, use the uncached _dbcomputer
        self._dbcomputer.name = val

    def get_hostname(self):
        return self._dbcomputer.hostname

    def set_hostname(self, val):
        # When setting, use the uncached _dbcomputer
        self._dbcomputer.hostname = val

    def get_description(self):
        return self._dbcomputer.description

    def set_description(self, val):
        # When setting, use the uncached _dbcomputer
        self._dbcomputer.description = val

    def is_enabled(self):
        return self._dbcomputer.enabled

    def set_enabled_state(self, enabled):
        """
        Set the enabled state.

        :param enabled: the new state
        """
        # When setting, use the uncached _dbcomputer
        self._dbcomputer.enabled = enabled

    def get_scheduler_type(self):
        return self._dbcomputer.scheduler_type

    def set_scheduler_type(self, val):
        # When setting, use the uncached _dbcomputer
        self._dbcomputer.scheduler_type = val

    def get_transport_type(self):
        return self._dbcomputer.transport_type

    def set_transport_type(self, val):
        # When setting, use the uncached _dbcomputer
        self._dbcomputer.transport_type = val
