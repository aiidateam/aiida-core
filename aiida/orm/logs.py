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
from datetime import datetime
import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Type

from aiida.common import timezone
from aiida.common.lang import classproperty
from aiida.manage import get_manager

from . import entities

if TYPE_CHECKING:
    from aiida.orm import Node
    from aiida.orm.implementation import BackendLog, StorageBackend
    from aiida.orm.querybuilder import FilterType, OrderByType

__all__ = ('Log', 'OrderSpecifier', 'ASCENDING', 'DESCENDING')

ASCENDING = 'asc'
DESCENDING = 'desc'


def OrderSpecifier(field, direction):  # pylint: disable=invalid-name
    return {field: direction}


class LogCollection(entities.Collection['Log']):
    """
    This class represents the collection of logs and can be used to create
    and retrieve logs.
    """

    @staticmethod
    def _entity_base_cls() -> Type['Log']:
        return Log

    def create_entry_from_record(self, record: logging.LogRecord) -> Optional['Log']:
        """Helper function to create a log entry from a record created as by the python logging library

        :param record: The record created by the logging module
        :return: A stored log instance
        """
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
            metadata=metadata,
            backend=self.backend
        )

    def get_logs_for(self, entity: 'Node', order_by: Optional['OrderByType'] = None) -> List['Log']:
        """Get all the log messages for a given node and optionally sort

        :param entity: the entity to get logs for
        :param order_by: a list of (key, direction) pairs specifying the sort order

        :return: the list of log entries
        """
        from . import nodes

        if not isinstance(entity, nodes.Node):
            raise Exception('Only node logs are stored')

        return self.find({'dbnode_id': entity.pk}, order_by=order_by)

    def delete(self, pk: int) -> None:
        """Remove a Log entry from the collection with the given id

        :param pk: id of the Log to delete

        :raises `~aiida.common.exceptions.NotExistent`: if Log with ID ``pk`` is not found
        """
        return self._backend.logs.delete(pk)

    def delete_all(self) -> None:
        """Delete all Logs in the collection

        :raises `~aiida.common.exceptions.IntegrityError`: if all Logs could not be deleted
        """
        return self._backend.logs.delete_all()

    def delete_many(self, filters: 'FilterType') -> List[int]:
        """Delete Logs based on ``filters``

        :param filters: filters to pass to the QueryBuilder
        :return: (former) ``PK`` s of deleted Logs

        :raises TypeError: if ``filters`` is not a `dict`
        :raises `~aiida.common.exceptions.ValidationError`: if ``filters`` is empty
        """
        return self._backend.logs.delete_many(filters)


class Log(entities.Entity['BackendLog', LogCollection]):
    """
    An AiiDA Log entity.  Corresponds to a logged message against a particular AiiDA node.
    """

    _CLS_COLLECTION = LogCollection

    def __init__(
        self,
        time: datetime,
        loggername: str,
        levelname: str,
        dbnode_id: int,
        message: str = '',
        metadata: Optional[Dict[str, Any]] = None,
        backend: Optional['StorageBackend'] = None
    ):  # pylint: disable=too-many-arguments
        """Construct a new log

        :param time: time
        :param loggername: name of logger
        :param levelname: name of log level
        :param dbnode_id: id of database node
        :param message: log message
        :param metadata: metadata
        :param backend: database backend
        """
        from aiida.common import exceptions

        if metadata is not None and not isinstance(metadata, dict):
            raise TypeError('metadata must be a dict')

        if not loggername or not levelname:
            raise exceptions.ValidationError('The loggername and levelname cannot be empty')

        backend = backend or get_manager().get_profile_storage()
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
    def uuid(self) -> str:
        """Return the UUID for this log.

        This identifier is unique across all entities types and backend instances.

        :return: the entity uuid
        """
        return self._backend_entity.uuid

    @property
    def time(self) -> datetime:
        """
        Get the time corresponding to the entry

        :return: The entry timestamp
        """
        return self._backend_entity.time

    @property
    def loggername(self) -> str:
        """
        The name of the logger that created this entry

        :return: The entry loggername
        """
        return self._backend_entity.loggername

    @property
    def levelname(self) -> str:
        """
        The name of the log level

        :return: The entry log level name
        """
        return self._backend_entity.levelname

    @property
    def dbnode_id(self) -> int:
        """
        Get the id of the object that created the log entry

        :return: The id of the object that created the log entry
        """
        return self._backend_entity.dbnode_id

    @property
    def message(self) -> str:
        """
        Get the message corresponding to the entry

        :return: The entry message
        """
        return self._backend_entity.message

    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Get the metadata corresponding to the entry

        :return: The entry metadata
        """
        return self._backend_entity.metadata
