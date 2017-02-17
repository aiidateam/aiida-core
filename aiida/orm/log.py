from abc import abstractmethod, abstractproperty, ABCMeta
from collections import namedtuple

ASCENDING = 1
DESCENDING = -1

OrderSpecifier = namedtuple("OrderSpecifier", ['field', 'direction'])


class Log(object):
    __metaclass__ = ABCMeta

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass


class LogEntry(object):
    __metaclass__ = ABCMeta

    @abstractproperty
    def id(self):
        pass

    @abstractproperty
    def time(self):
        """
        Get the time corresponding to the entry

        :return: The entry timestamp
        :rtype: :class:`datetime.datetime`
        """
        pass

    @abstractproperty
    def loggername(self):
        """
        The name of the logger that created this entry

        :return: The entry loggername
        :rtype: basestring
        """
        pass

        # TODO: Do the rest of these @sphuber

    @abstractmethod
    def save(self):
        pass
