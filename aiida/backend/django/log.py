import json
from aiida.backend.log import Log, LogEntry
from aiida.backends.djsite.db.models import DbLog


class DjangoLog(Log):

    def __init__(self):
        self._property_map = {
            'id'          : 'pk',
            'time'        : 'time',
            'logger_name' : 'loggername',
            'log_level'   : 'levelname',
            'obj_id'      : 'objpk',
            'obj_name'    : 'objname',
            'message'     : 'message',
            'metadata'    : 'metadata',
        }

    def map_property_name(self, property_name):
        """
        LogEntry property names do not necessarily match the field names
        used in the database model and have to be mapped internally
        """
        try:
            return self._property_map[property_name]
        except KeyError:
            raise KeyError

    def create_entry(self, time, logger_name, log_level, obj_name,
                     message="", obj_id=None, metadata=None):
        """
        Create a log entry.
        """
        return DjangoLogEntry(
            DbLog(
                loggername=logger_name,
                levelname=log_level,
                objname=obj_name,
                objpk=obj_id,
                message=message,
                metadata=json.dumps(metadata)
            )
        )

    def get(self, filter_by={}, order_by=[], limit=None):
        """
        Find all entries in the Log collection that confirm to the filter and
        optionally sort and/or apply a limit.
        """
        order   = []
        filters = {}

        # Map the LogEntry property names to DbLog field names
        for key, value in filter_by.iteritems():
            filters[self.map_property_name(key)] = value

        for column in order_by:
            order.append(self.map_property_name(column.field))

        if filters:
            entries = DbLog.objects.filter(**filters).order_by(*order)[:limit]
        else:
            entries = DbLog.objects.filter().order_by(*order)[:limit]

        return [DjangoLogEntry(entry) for entry in entries]


class DjangoLogEntry(LogEntry):
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
    def logger_name(self):
        """
        The name of the logger that created this entry
        """
        return self._model.loggername

    @property
    def log_level(self):
        """
        The name of the log level
        """
        return self._model.levelname

    @property
    def obj_id(self):
        """
        Get the id of the object that created the log entry
        """
        return self._model.objpk

    @property
    def obj_name(self):
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

    def persist(self):
        """
        Persist the log entry to the database
        """
        return self._model.save()