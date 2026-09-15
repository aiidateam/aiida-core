###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for orm logging abstract classes"""

from __future__ import annotations

import logging
import typing as t
from datetime import datetime

import pydantic as pdt

from aiida.common import timezone
from aiida.manage import get_manager
from aiida.orm import entities, nodes
from aiida.orm.decorators import column
from aiida.orm.models.adapters import EntityPkAdapter, StrUuidAdapter

if t.TYPE_CHECKING:
    from aiida.orm import Node
    from aiida.orm.implementation import StorageBackend
    from aiida.orm.implementation.logs import BackendLog
    from aiida.orm.querybuilder import FilterType, OrderByType

__all__ = ('ASCENDING', 'DESCENDING', 'Log', 'OrderSpecifier')

ASCENDING = 'asc'
DESCENDING = 'desc'


def OrderSpecifier(field, direction):  # noqa: N802
    return {field: direction}


class LogCollection(entities.EntityCollection['Log']):
    """This class represents the collection of logs and can be used to create
    and retrieve logs.
    """

    collection_type: t.ClassVar[str] = 'logs'

    def create_entry_from_record(self, record: logging.LogRecord) -> Log | None:
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
            backend=self.backend,
        )

    def get_logs_for(self, entity: Node, order_by: OrderByType | None = None) -> list[Log]:
        """Get all the log messages for a given node and optionally sort

        :param entity: the entity to get logs for
        :param order_by: a list of (key, direction) pairs specifying the sort order

        :return: the list of log entries
        """
        from aiida.orm import nodes

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

    def delete_many(self, filters: FilterType) -> list[int]:
        """Delete Logs based on ``filters``

        :param filters: filters to pass to the QueryBuilder
        :return: (former) ``PK`` s of deleted Logs

        :raises TypeError: if ``filters`` is not a `dict`
        :raises `~aiida.common.exceptions.ValidationError`: if ``filters`` is empty
        """
        return self._backend.logs.delete_many(filters)

    @staticmethod
    def _entity_base_cls() -> type[Log]:
        return Log


class Log(entities.Entity['BackendLog', LogCollection]):
    """ORM representation of an AiiDA log entry attached to a node."""

    identity_field = 'uuid'

    _CLS_COLLECTION = LogCollection

    def __init__(
        self,
        time: datetime,
        loggername: str,
        levelname: str,
        dbnode_id: int | None = None,
        message: str = '',
        metadata: dict[str, t.Any] | None = None,
        backend: StorageBackend | None = None,
        node: Node | None = None,
    ):
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

        dbnode_id = dbnode_id or (node.pk if node is not None else None)
        if dbnode_id is None:
            raise exceptions.ValidationError('Either dbnode_id or node must be provided to create a Log entry')

        backend = backend or get_manager().get_profile_storage()
        model = backend.logs.create(
            time=time,
            loggername=loggername,
            levelname=levelname,
            dbnode_id=dbnode_id,
            message=message,
            metadata=metadata,
        )
        super().__init__(model)

        self.store()  # Logs are immutable and automatically stored

    @column(
        readonly=True,
        model_adapter=StrUuidAdapter(),
    )
    def uuid(self) -> str:
        """The UUID for this log."""
        return self._backend_entity.uuid

    @column(readonly=True)
    def time(self) -> datetime:
        """The creation time of the log entry."""
        return self._backend_entity.time

    @column
    def loggername(self) -> str:
        """The name of the logger that created this entry."""
        return self._backend_entity.loggername

    @loggername.setter
    def loggername(self, value: str) -> None:
        self._backend_entity.loggername = value

    @column
    def levelname(self) -> str:
        """The name of the log level."""
        return self._backend_entity.levelname

    @levelname.setter
    def levelname(self, value: str) -> None:
        self._backend_entity.levelname = value

    @column(model_adapter=EntityPkAdapter(nodes.Node))
    def node(self) -> Node:
        """The node associated to the log entry."""
        from aiida.orm.utils.loaders import load_node

        return load_node(self.dbnode_id)

    @node.setter
    def node(self, value: Node | int) -> None:
        if isinstance(value, int):
            self._backend_entity.dbnode_id = value
        else:
            self._backend_entity.dbnode_id = value.pk

    @column
    def message(self) -> str:
        """The message corresponding to the entry."""
        return self._backend_entity.message

    @message.setter
    def message(self, value: str) -> None:
        self._backend_entity.message = value

    @column(model_field_info=pdt.fields.FieldInfo(default_factory=dict))
    def metadata(self) -> dict[str, t.Any]:
        """The metadata corresponding to the entry."""
        return self._backend_entity.metadata

    @metadata.setter
    def metadata(self, value: dict[str, t.Any]) -> None:
        self._backend_entity.metadata = value

    @property
    def dbnode_id(self) -> int:
        """The id of the node that created the log entry"""
        return self._backend_entity.dbnode_id
