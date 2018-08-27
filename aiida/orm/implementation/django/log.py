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
from aiida.orm.log import LogCollection, Log
from aiida.orm.log import ASCENDING
from aiida.backends.djsite.db.models import DbLog


class DjangoLogCollection(LogCollection):

    def create_entry(self, time, loggername, levelname, objname, objpk=None, message="", metadata=None):
        """
        Create a log entry if and only if objpk and objname are set
        """
        if objpk is None or objname is None:
            return None

        entry = DjangoLog(
            DbLog(
                time=time,
                loggername=loggername,
                levelname=levelname,
                objname=objname,
                objpk=objpk,
                message=message,
                metadata=json.dumps(metadata)
            )
        )
        entry.save()

        return entry

    def find(self, filter_by=None, order_by=None, limit=None):
        """
        Find all entries in the Log collection that confirm to the filter and
        optionally sort and/or apply a limit.
        """
        order = []
        filters = {}

        if not filter_by:
            filter_by = {}

        # Map the Log property names to DbLog field names
        for key, value in filter_by.items():
            filters[key] = value

        if not order_by:
            order_by = []

        for column in order_by:
            if column.direction == ASCENDING:
                order.append(column.field)
            else:
                order.append('-' + column.field)

        if filters:
            entries = DbLog.objects.filter(**filters).order_by(*order)[:limit]
        else:
            entries = DbLog.objects.filter().order_by(*order)[:limit]

        return [DjangoLog(entry) for entry in entries]

    def delete_many(self, filter):
        """
        Delete all log entries in the table
        """
        if not filter:
            DbLog.objects.all().delete()
        else:
            raise NotImplementedError(
                "Only deleting all by passing an empty filer dictionary is "
                "currently supported")


class DjangoLog(Log):

    def __init__(self, model):
        """
        :param model: :class:`aiida.backends.djsite.db.models.DbLog`
        """
        self._model = model

    @property
    def id(self):
        """
        Get the primary key of the entry
        """
        return self._model.pk

    @property
    def time(self):
        """
        Get the time corresponding to the entry
        """
        return self._model.time

    @property
    def loggername(self):
        """
        The name of the logger that created this entry
        """
        return self._model.loggername

    @property
    def levelname(self):
        """
        The name of the log level
        """
        return self._model.levelname

    @property
    def objpk(self):
        """
        Get the id of the object that created the log entry
        """
        return self._model.objpk

    @property
    def objname(self):
        """
        Get the name of the object that created the log entry
        """
        return self._model.objname

    @property
    def message(self):
        """
        Get the message corresponding to the entry
        """
        return self._model.message

    @property
    def metadata(self):
        """
        Get the metadata corresponding to the entry
        """
        return json.loads(self._model.metadata)

    def save(self):
        """
        Persist the log entry to the database
        """
        return self._model.save()
