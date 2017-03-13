from aiida.orm.log import Log, LogEntry
from aiida.orm.log import OrderSpecifier, ASCENDING, DESCENDING
from aiida.backends.sqlalchemy import session
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
        entry.persist()

        return entry


    def create_entry_from_record(self, record):
        """
        Create a log entry from a record created by the python logging
        """
        from datetime import datetime

        objpk   = record.__dict__.get('objpk', None)
        objname = record.__dict__.get('objname', None)

        # Do not store if objpk and objname are not set
        if objpk is None or objname is None:
            return None

        entry = SqlaLogEntry(
            DbLog(
                time=timezone.make_aware(datetime.fromtimestamp(record.created)),
                loggername=record.name,
                levelname=record.levelname,
                objname=objname,
                objpk=objpk,
                message=record.getMessage(),
                metadata=record.__dict__
            )
        )
        entry.persist()

        return entry


    def find(self, filter_by=None, order_by=None, limit=None):
        """
        Find all entries in the Log collection that confirm to the filter and
        optionally sort and/or apply a limit.
        """
        order   = []
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


    def delete_all(self):
        """
        Delete all log entries in the table
        """
        for entry in DbLog.query.all():
            entry.delete()
        session.commit()



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

    def persist(self):
        """
        Persist the log entry to the database
        """
        session.add(self._model)
        session.commit()
