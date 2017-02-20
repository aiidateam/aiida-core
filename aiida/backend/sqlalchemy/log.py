from aiida.backend.log import Log, LogEntry
from aiida.backends.sqlalchemy.models import DbLog


class SqlaLog(Log):
    def create_entry(self, time, loggername, levelname, objname,
                     objpk=None, message="", metadata=None):
        """
        Create a log entry.
        """
        return SqlaLogEntry(
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

    def create_entry_from_record(self, record):
        """
        Create a log entry from a record created by the python logging
        """
        from datetime import datetime

        return SqlaLogEntry(
            DbLog(
                time=datetime.fromtimestamp(record.created),
                loggername=record.name,
                levelname=record.levelname,
                objname=record.objname,
                objpk=record.objpk,
                message=record.message,
                metadata=record.__dict__
            )
        )

    def find(self, filter_by=None, order_by=None, limit=None):
        """
        Find all entries in the Log collection that confirm to the filter and
        optionally sort and/or apply a limit.
        """
        raise NotImplementedError()


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
        from aiida.backends.sqlalchemy import session
        session.add(self)
        session.commit()
