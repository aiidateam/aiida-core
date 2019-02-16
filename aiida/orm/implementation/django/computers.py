# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Django implementations for the `Computer` entity and collection."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import six

# pylint: disable=import-error,no-name-in-module
from django.db import IntegrityError, transaction

from aiida.backends.djsite.db import models
from aiida.common import exceptions, json

from ..computers import BackendComputerCollection, BackendComputer
from . import entities
from . import utils


class DjangoComputer(entities.DjangoModelEntity[models.DbComputer], BackendComputer):
    """Django implementation for `BackendComputer`."""

    # pylint: disable=too-many-public-methods

    MODEL_CLASS = models.DbComputer

    def __init__(self, backend, **kwargs):
        """Construct a new `DjangoComputer` instance."""
        super(DjangoComputer, self).__init__(backend)
        self._dbmodel = utils.ModelWrapper(models.DbComputer(**kwargs))

    @property
    def uuid(self):
        return six.text_type(self._dbmodel.uuid)

    def copy(self):
        """Create an unstored clone of an already stored `Computer`."""
        if not self.is_stored:
            raise exceptions.InvalidOperation('You can copy a computer only after having stored it')
        dbomputer = models.DbComputer.objects.get(pk=self.pk)
        dbomputer.pk = None

        newobject = self.__class__.from_dbmodel(dbomputer)

        return newobject

    def store(self):
        """Store the `Computer` instance."""
        # As a first thing, I check if the data is valid
        sid = transaction.savepoint()
        try:
            # transactions are needed here for Postgresql:
            # https://docs.djangoproject.com/en/1.5/topics/db/transactions/#handling-exceptions-within-postgresql-transactions
            self._dbmodel.save()
            transaction.savepoint_commit(sid)
        except IntegrityError:
            transaction.savepoint_rollback(sid)
            raise ValueError('Integrity error, probably the hostname already exists in the database')

        return self

    @property
    def is_stored(self):
        return self._dbmodel.id is not None

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
        return json.loads(self._dbmodel.metadata)

    def set_metadata(self, metadata_dict):
        self._dbmodel.metadata = json.dumps(metadata_dict)

    def get_transport_params(self):
        try:
            return json.loads(self._dbmodel.transport_params)
        except ValueError:
            raise exceptions.DbContentError('Error while reading transport params for Computer<{}>'.format(
                self.hostname))

    def set_transport_params(self, val):
        try:
            self._dbmodel.transport_params = json.dumps(val)
        except ValueError:
            raise ValueError('The set of transport_params are not JSON-able')

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
        """Set the enabled state.

        :param enabled: the new state
        """
        self._dbmodel.enabled = enabled

    def get_scheduler_type(self):
        return self._dbmodel.scheduler_type

    def set_scheduler_type(self, scheduler_type):
        self._dbmodel.scheduler_type = scheduler_type

    def get_transport_type(self):
        return self._dbmodel.transport_type

    def set_transport_type(self, transport_type):
        self._dbmodel.transport_type = transport_type


class DjangoComputerCollection(BackendComputerCollection):
    """Collection of `Computer` instances."""

    ENTITY_CLASS = DjangoComputer

    @staticmethod
    def list_names():
        return list(models.DbComputer.objects.filter().values_list('name', flat=True))

    def delete(self, pk):
        """Delete the computer with the given pk."""
        from django.db.models.deletion import ProtectedError
        try:
            models.DbComputer.objects.filter(pk=pk).delete()
        except ProtectedError:
            raise exceptions.InvalidOperation("Unable to delete the requested computer: there"
                                              "is at least one node using this computer")
