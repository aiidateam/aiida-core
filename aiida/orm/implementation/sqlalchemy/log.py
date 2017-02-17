from aiida.orm.log import Log, LogEntry
from aiida.backends.sqlalchemy.models import DbLog


class SqlaLog(Log):
    def create_entry(self, time, logger_name, log_level, obj_name,
                     message="", obj_id=None, metadata=None):
        """
        Create a log entry.

        :param time: The time of creation for the entry
        :type time: :class:`datetime.datetime`
        :param logger_name: The name of the logger that generated the entry
        :type logger_name: :class:`basestring`
        :param log_level: The log level
        :type log_level: :class:`basestring`
        :param obj_name: The object name (if any) that emitted the entry
        :param message: The message to log
        :type message: :class:`basestring`
        :param obj_id: The object id that emitted the entry
        :param metadata: Any (optional) metadata, should be JSON
        :type metadata: :class:`dict`
        :return: An object implementing the log entry interface
        :rtype: :class:`aiida.orm.log.LogEntry`
        """
        return DbLog(
            loggername=logger_name, levelname=log_level, objname=obj_name,
            objpk=obj_id, message=message, metadata=metadata)

    def find(self, filter_by=None, order_by=None, limit=None):
        """
        Find all entries in the Log collection that confirm to the filter and
        optionally sort and/or apply a limit.

        :param filter_by: A dictionary of key value pairs where the entries have
            to match all the criteria (i.e. an AND operation)
        :type filter_by: :class:`dict`
        :param order_by: A list of tuples of type :class:`OrderSpecifier`
        :type order_by: list
        :param limit: The number of entries to retrieve
        :return: An iterable of the matching entries
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
        return self._model.pk

    @property
    def time(self):
        return self._model.time

    @property
    def metadata(self):
        return self._model.metadata

    @property
    def obj_id(self):
        return self._model.objpk

    @property
    def obj_name(self):
        return self._model.objname

    @property
    def logger_name(self):
        return self._model.loggername

    @property
    def log_level(self):
        return self._model.levelname

    def store(self):
        from aiida.backends.sqlalchemy import session
        session.add(self)
        session.commit()
