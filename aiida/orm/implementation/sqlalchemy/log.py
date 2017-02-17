from aiida.orm.log import Log


class SqlaLog(Log):
    def create_entry(self, time, loggername, levelname, obj_name,
                     message="", obj_id=None, metadata=None):
        """
        Create a log entry.

        :param time: The time of creation for the entry
        :type time: :class:`datetime.datetime`
        :param loggername: The name of the logger that generated the entry
        :type loggername: :class:`basestring`
        :param levelname: The log level
        :type levelname: :class:`basestring`
        :param obj_name: The object name (if any) that emitted the entry
        :param message: The message to log
        :type message: :class:`basestring`
        :param obj_id: The object id that emitted the entry
        :param metadata: Any (optional) metadata, should be JSON
        :type metadata: :class:`basestring`
        :return: An object implementing the log entry interface
        :rtype: :class:`aiida.orm.log.LogEntry`
        """
        raise NotImplementedError()

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
