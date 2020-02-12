# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for orm logging abstract classes"""

from aiida.common import timezone
from aiida.manage.manager import get_manager
from . import entities

__all__ = ('Log', 'OrderSpecifier', 'ASCENDING', 'DESCENDING')

ASCENDING = 'asc'
DESCENDING = 'desc'


def OrderSpecifier(field, direction):  # pylint: disable=invalid-name
    return {field: direction}


class Log(entities.Entity):
    """
    An AiiDA Log entity.  Corresponds to a logged message against a particular AiiDA node.
    """

    class Collection(entities.Collection):
        """
        This class represents the collection of logs and can be used to create
        and retrieve logs.
        """

        @staticmethod
        def create_entry_from_record(record):
            """
            Helper function to create a log entry from a record created as by the python logging library

            :param record: The record created by the logging module
            :type record: :class:`logging.record`

            :return: An object implementing the log entry interface
            :rtype: :class:`aiida.orm.logs.Log`
            """
            from datetime import datetime

            dbnode_id = record.__dict__.get('dbnode_id', None)

            # Do not store if dbnode_id is not set
            if dbnode_id is None:
                return None

            metadata = dict(record.__dict__)

            # If an `exc_info` is present, the log message was an exception, so format the full traceback
            try:
                import traceback
                exc_info = metadata.pop('exc_info')
                message = ''.join(traceback.format_exception(*exc_info))
            except (TypeError, KeyError):
                message = record.getMessage()

            # Stringify the content of `args` if they exist in the metadata to ensure serializability
            for key in ['args']:
                if key in metadata:
                    metadata[key] = str(metadata[key])

            return Log(
                time=timezone.make_aware(datetime.fromtimestamp(record.created)),
                loggername=record.name,
                levelname=record.levelname,
                dbnode_id=dbnode_id,
                message=message,
                metadata=metadata
            )

        def get_logs_for(self, entity, order_by=None):
            """
            Get all the log messages for a given entity and optionally sort

            :param entity: the entity to get logs for
            :type entity: :class:`aiida.orm.Entity`

            :param order_by: a list of (key, direction) pairs specifying the sort order
            :type order_by: list

            :return: the list of log entries
            :rtype: list
            """
            from . import nodes

            if not isinstance(entity, nodes.Node):
                raise Exception('Only node logs are stored')

            return self.find({'dbnode_id': entity.pk}, order_by=order_by)

        def delete(self, log_id):
            """
            Remove a Log entry from the collection with the given id

            :param log_id: id of the Log to delete
            :type log_id: int

            :raises TypeError: if ``log_id`` is not an `int`
            :raises `~aiida.common.exceptions.NotExistent`: if Log with ID ``log_id`` is not found
            """
            self._backend.logs.delete(log_id)

        def delete_all(self):
            """
            Delete all Logs in the collection

            :raises `~aiida.common.exceptions.IntegrityError`: if all Logs could not be deleted
            """
            self._backend.logs.delete_all()

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
            self._backend.logs.delete_many(filters)

    def __init__(self, time, loggername, levelname, dbnode_id, message='', metadata=None, backend=None):  # pylint: disable=too-many-arguments
        """Construct a new log

        :param time: time
        :type time: :class:`!datetime.datetime`

        :param loggername: name of logger
        :type loggername: basestring

        :param levelname: name of log level
        :type levelname: basestring

        :param dbnode_id: id of database node
        :type dbnode_id: int

        :param message: log message
        :type message: basestring

        :param metadata: metadata
        :type metadata: dict

        :param backend: database backend
        :type backend: :class:`aiida.orm.implementation.Backend`


        """
        from aiida.common import exceptions

        if metadata is not None and not isinstance(metadata, dict):
            raise TypeError('metadata must be a dict')

        if not loggername or not levelname:
            raise exceptions.ValidationError('The loggername and levelname cannot be empty')

        backend = backend or get_manager().get_backend()
        model = backend.logs.create(
            time=time,
            loggername=loggername,
            levelname=levelname,
            dbnode_id=dbnode_id,
            message=message,
            metadata=metadata
        )
        super().__init__(model)
        self.store()  # Logs are immutable and automatically stored

    @property
    def time(self):
        """
        Get the time corresponding to the entry

        :return: The entry timestamp
        :rtype: :class:`!datetime.datetime`
        """
        return self._backend_entity.time

    @property
    def loggername(self):
        """
        The name of the logger that created this entry

        :return: The entry loggername
        :rtype: basestring
        """
        return self._backend_entity.loggername

    @property
    def levelname(self):
        """
        The name of the log level

        :return: The entry log level name
        :rtype: basestring
        """
        return self._backend_entity.levelname

    @property
    def dbnode_id(self):
        """
        Get the id of the object that created the log entry

        :return: The id of the object that created the log entry
        :rtype: int
        """
        return self._backend_entity.dbnode_id

    @property
    def message(self):
        """
        Get the message corresponding to the entry

        :return: The entry message
        :rtype: basestring
        """
        return self._backend_entity.message

    @property
    def metadata(self):
        """
        Get the metadata corresponding to the entry

        :return: The entry metadata
        :rtype: dict
        """
        return self._backend_entity.metadata
