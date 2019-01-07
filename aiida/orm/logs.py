# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for orm logging abstract classes"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.common import timezone
from aiida.manage import get_manager
from . import entities
from . import node

__all__ = ('Log',)

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

            objpk = record.__dict__.get('objpk', None)
            objname = record.__dict__.get('objname', None)

            # Do not store if objpk and objname are not set
            if objpk is None or objname is None:
                return None

            metadata = dict(record.__dict__)
            # Get rid of the exc info because this is usually not serializable
            metadata['exc_info'] = None
            return Log(
                time=timezone.make_aware(datetime.fromtimestamp(record.created)),
                loggername=record.name,
                levelname=record.levelname,
                objname=objname,
                objpk=objpk,
                message=record.getMessage(),
                metadata=metadata)

        def get_logs_for(self, entity, order_by=None):
            """
            Get all the log messages for a given entity and optionally sort

            :param entity: the entity to get logs for
            :type entity: :class:`aiida.orm.Entity`
            :param order_by: the optional sort order
            :return: the list of log entries
            :rtype: list
            """
            if isinstance(entity, node.Node):
                if entity._plugin_type_string:  # pylint: disable=protected-access
                    objname = "node." + entity._plugin_type_string  # pylint: disable=protected-access
                else:
                    objname = "node"
            else:
                objname = entity.__class__.__module__ + "." + entity.__class__.__name__
            objpk = entity.pk
            filters = {'objpk': objpk, 'objname': objname}
            return self.find(filters, order_by=order_by)

        def delete(self, log_id):
            """
            Remove a Log entry from the collection with the given id

            :param log_id: id of the log to delete
            """
            self._backend.logs.delete(log_id)

        def delete_many(self, filters):
            """
            Delete all the log entries matching the given filters
            """
            self._backend.logs.delete_many(filters)

    def __init__(self, time, loggername, levelname, objname, objpk=None, message='', metadata=None, backend=None):  # pylint: disable=too-many-arguments
        """Construct a new computer"""
        backend = backend or get_manager().get_backend()
        model = backend.logs.create(
            time=time,
            loggername=loggername,
            levelname=levelname,
            objname=objname,
            objpk=objpk,
            message=message,
            metadata=metadata)
        super(Log, self).__init__(model)
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
    def objpk(self):
        """
        Get the id of the object that created the log entry

        :return: The entry timestamp
        :rtype: int
        """
        return self._backend_entity.objpk

    @property
    def objname(self):
        """
        Get the name of the object that created the log entry

        :return: The entry object name
        :rtype: basestring
        """
        return self._backend_entity.objname

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
        :rtype: :class:`!json.json`
        """
        return self._backend_entity.metadata
