# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.orm.log import Log, LogEntry
from aiida.orm.log import OrderSpecifier, ASCENDING, DESCENDING
from aiida.backends.sqlalchemy import get_scoped_session
session = get_scoped_session()
from aiida.backends.sqlalchemy.models.log import DbLog
from aiida.utils import timezone


class SqlaLog(Log):
    def create_entry(self, time, loggername, levelname, objname,
                     objpk=None, message="", metadata=None):
        """
        Create a log entry.
        """
        if objpk is None or objname is None:
            return None

        entry = SqlaLogEntry(
            DbLog(
                time=time,
                loggername=loggername,
                levelname=levelname,
                objname=objname,
                objpk=objpk,
                message=message,
                metadata=metadata
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

        # Map the LogEntry property names to DbLog field names
        for key, value in filter_by.iteritems():
            filters[key] = value

        columns = {}
        for column in DbLog.__table__.columns:
            columns[column.key] = column

        if not order_by:
            order_by = []

        for column in order_by:
            if column.field in columns:
                if column.direction == ASCENDING:
                    order.append(columns[column.field].asc())
                else:
                    order.append(columns[column.field].desc())

        if filters:
            entries = session.query(DbLog).filter_by(**filters).order_by(*order).limit(limit)
        else:
            entries = session.query(DbLog).order_by(*order).limit(limit)

        return [SqlaLogEntry(entry) for entry in entries]

    def delete_many(self, filter):
        """
        Delete all log entries in the table
        """
        if not filter:
            for entry in DbLog.query.all():
                entry.delete()
            session.commit()
        else:
            raise NotImplemented(
                "Only deleting all by passing an empty filer dictionary is "
                "currently supported")


class SqlaLogEntry(LogEntry):
    def __init__(self, model):
        """
        :param model: :class:`aiida.backends.sqlalchemy.models.log.DbLog`
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
        return self._model._metadata

    def save(self):
        """
        Persist the log entry to the database
        """
        session.add(self._model)
        session.commit()
