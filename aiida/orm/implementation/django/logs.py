# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The Django log and log collection module"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=import-error,no-name-in-module,fixme
from aiida.backends.djsite.db import models
from aiida.common import exceptions
from aiida.common import json

from . import entities
from .. import BackendLog, BackendLogCollection


class DjangoLog(entities.DjangoModelEntity[models.DbLog], BackendLog):
    """Django Log backend class"""

    MODEL_CLASS = models.DbLog

    def __init__(self, backend, time, loggername, levelname, dbnode_id, message="", metadata=None):
        # pylint: disable=too-many-arguments
        super(DjangoLog, self).__init__(backend)
        self._dbmodel = models.DbLog(
            time=time,
            loggername=loggername,
            levelname=levelname,
            dbnode_id=dbnode_id,
            message=message,
            metadata=json.dumps(metadata) if metadata else "{}")  # Make sure a json-serializable dict is created

    @property
    def uuid(self):
        """
        Get the uuid of the object that created the log entry
        """
        return self._dbmodel.uuid

    @property
    def time(self):
        """
        Get the time corresponding to the entry
        """
        return self._dbmodel.time

    @property
    def loggername(self):
        """
        The name of the logger that created this entry
        """
        return self._dbmodel.loggername

    @property
    def levelname(self):
        """
        The name of the log level
        """
        return self._dbmodel.levelname

    @property
    def dbnode_id(self):
        """
        Get the id of the object that created the log entry
        """
        return self._dbmodel.dbnode_id

    @property
    def message(self):
        """
        Get the message corresponding to the entry
        """
        return self._dbmodel.message

    @property
    def metadata(self):
        """
        Get the metadata corresponding to the entry
        """
        return json.loads(self._dbmodel.metadata)


class DjangoLogCollection(BackendLogCollection):
    """Django log collection"""

    ENTITY_CLASS = DjangoLog

    def delete(self, log_id):
        """
        Remove a Log entry from the collection with the given id

        :param log_id: id of the log to delete
        """
        # pylint: disable=no-name-in-module,import-error
        from django.core.exceptions import ObjectDoesNotExist
        assert log_id is not None
        try:
            models.DbLog.objects.get(id=log_id).delete()
        except ObjectDoesNotExist:
            raise exceptions.NotExistent("Log with id '{}' not found".format(log_id))

    def delete_many(self, filters):
        """
        Delete all log entries.
        Delete all log entries in the table if 'filters' is not defined.
        :param filters: Dictionary, where the keys can be: 'id' or 'node_id'.
        and the values may be a list. 'time' is not yet implemented.
        """
        if not filters:
            models.DbLog.objects.all().delete()
        else:
            raise NotImplementedError('Only deleting all by passing an empty filter dictionary is currently supported')
