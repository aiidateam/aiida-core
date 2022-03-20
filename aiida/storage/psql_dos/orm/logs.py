# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""SQLA Log and LogCollection module"""
# pylint: disable=import-error,no-name-in-module

from sqlalchemy.orm.exc import NoResultFound

from aiida.common import exceptions
from aiida.orm.implementation import BackendLog, BackendLogCollection
from aiida.storage.psql_dos.models import log as models

from . import entities, utils


class SqlaLog(entities.SqlaModelEntity[models.DbLog], BackendLog):
    """SQLA Log backend entity"""

    MODEL_CLASS = models.DbLog

    def __init__(self, backend, time, loggername, levelname, dbnode_id, message='', metadata=None):
        # pylint: disable=too-many-arguments
        super().__init__(backend)
        self._model = utils.ModelWrapper(
            self.MODEL_CLASS(
                time=time,
                loggername=loggername,
                levelname=levelname,
                dbnode_id=dbnode_id,
                message=message,
                metadata=metadata
            ), backend
        )

    @property
    def uuid(self):
        """
        Get the string representation of the UUID of the log entry
        """
        return str(self.model.uuid)

    @property
    def time(self):
        """
        Get the time corresponding to the entry
        """
        return self.model.time

    @property
    def loggername(self):
        """
        The name of the logger that created this entry
        """
        return self.model.loggername

    @property
    def levelname(self):
        """
        The name of the log level
        """
        return self.model.levelname

    @property
    def dbnode_id(self):
        """
        Get the id of the object that created the log entry
        """
        return self.model.dbnode_id

    @property
    def message(self):
        """
        Get the message corresponding to the entry
        """
        return self.model.message

    @property
    def metadata(self):
        """
        Get the metadata corresponding to the entry
        """
        return self.model._metadata  # pylint: disable=protected-access


class SqlaLogCollection(BackendLogCollection):
    """The SQLA collection for logs"""

    ENTITY_CLASS = SqlaLog

    def delete(self, log_id):
        """
        Remove a Log entry from the collection with the given id

        :param log_id: id of the Log to delete
        :type log_id: int

        :raises TypeError: if ``log_id`` is not an `int`
        :raises `~aiida.common.exceptions.NotExistent`: if Log with ID ``log_id`` is not found
        """
        if not isinstance(log_id, int):
            raise TypeError('log_id must be an int')

        session = self.backend.get_session()

        try:
            row = session.query(self.ENTITY_CLASS.MODEL_CLASS).filter_by(id=log_id).one()
            session.delete(row)
            session.commit()
        except NoResultFound:
            session.rollback()
            raise exceptions.NotExistent(f"Log with id '{log_id}' not found")

    def delete_all(self):
        """
        Delete all Log entries.

        :raises `~aiida.common.exceptions.IntegrityError`: if all Logs could not be deleted
        """
        session = self.backend.get_session()

        try:
            session.query(self.ENTITY_CLASS.MODEL_CLASS).delete()
            session.commit()
        except Exception as exc:
            session.rollback()
            raise exceptions.IntegrityError(f'Could not delete all Logs. Full exception: {exc}')

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
        from aiida.orm import Log, QueryBuilder

        # Checks
        if not isinstance(filters, dict):
            raise TypeError('filters must be a dictionary')
        if not filters:
            raise exceptions.ValidationError('filter must not be empty')

        # Apply filter and delete found entities
        builder = QueryBuilder(backend=self.backend).append(Log, filters=filters, project='id')
        entities_to_delete = builder.all(flat=True)
        for entity in entities_to_delete:
            self.delete(entity)

        # Return list of deleted entities' (former) PKs for checking
        return entities_to_delete
