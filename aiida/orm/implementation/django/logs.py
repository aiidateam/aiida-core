# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The Django log and log collection module"""
# pylint: disable=import-error,no-name-in-module

from django.core.exceptions import ObjectDoesNotExist

from aiida.backends.djsite.db import models
from aiida.common import exceptions

from . import entities
from .. import BackendLog, BackendLogCollection


class DjangoLog(entities.DjangoModelEntity[models.DbLog], BackendLog):
    """Django Log backend class"""

    MODEL_CLASS = models.DbLog

    def __init__(self, backend, time, loggername, levelname, dbnode_id, message='', metadata=None):
        # pylint: disable=too-many-arguments
        super().__init__(backend)
        self._dbmodel = models.DbLog(
            time=time,
            loggername=loggername,
            levelname=levelname,
            dbnode_id=dbnode_id,
            message=message,
            metadata=metadata or {}
        )

    @property
    def uuid(self):
        """
        Get the string representation of the uuid of the object that created the log entry
        """
        return str(self._dbmodel.uuid)

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
        return self._dbmodel.metadata


class DjangoLogCollection(BackendLogCollection):
    """Django log collection"""

    ENTITY_CLASS = DjangoLog

    def delete(self, log_id):
        """
        Remove a Log entry from the collection with the given id

        :param log_id: id of the Log to delete
        :type log_id: int

        :raises TypeError: if ``log_id`` is not an `int`
        :raises `~aiida.common.exceptions.NotExistent`: if Log with ID ``log_id`` is not found
        """
        if not isinstance(log_id, int):
            raise TypeError('log_id must be an int')

        try:
            models.DbLog.objects.get(id=log_id).delete()
        except ObjectDoesNotExist:
            raise exceptions.NotExistent("Log with id '{}' not found".format(log_id))

    def delete_all(self):
        """
        Delete all Log entries.

        :raises `~aiida.common.exceptions.IntegrityError`: if all Logs could not be deleted
        """
        from django.db import transaction
        try:
            with transaction.atomic():
                models.DbLog.objects.all().delete()
        except Exception as exc:
            raise exceptions.IntegrityError('Could not delete all Logs. Full exception: {}'.format(exc))

    def delete_many(self, filters):
        """
        Delete Logs based on ``filters``

        :param filters: similar to QueryBuilder filter
        :type filters: dict

        :return: (former) ``PK`` s of deleted Logs
        :rtype: list

        :raises TypeError: if ``filters`` is not a `dict`
        :raises `~aiida.common.exceptions.ValidationError`: if ``filters`` is empty
        """
        from aiida.orm import Log, QueryBuilder

        # Checks
        if not isinstance(filters, dict):
            raise TypeError('filters must be a dictionary')
        if not filters:
            raise exceptions.ValidationError('filters must not be empty')

        # Apply filter and delete found entities
        builder = QueryBuilder().append(Log, filters=filters, project='id').all()
        entities_to_delete = [_[0] for _ in builder]
        for entity in entities_to_delete:
            self.delete(entity)

        # Return list of deleted entities' (former) PKs for checking
        return entities_to_delete
