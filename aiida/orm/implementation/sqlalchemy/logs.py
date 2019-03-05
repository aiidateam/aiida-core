# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""SQLA Log and LogCollection module"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.backends.sqlalchemy import get_scoped_session
from aiida.backends.sqlalchemy.models import log as models
from aiida.common import exceptions

from .. import BackendLog, BackendLogCollection
from . import entities
from . import utils


class SqlaLog(entities.SqlaModelEntity[models.DbLog], BackendLog):
    """SQLA Log backend entity"""

    MODEL_CLASS = models.DbLog

    def __init__(self, backend, time, loggername, levelname, dbnode_id, message="", metadata=None):
        # pylint: disable=too-many-arguments
        super(SqlaLog, self).__init__(backend)
        self._dbmodel = utils.ModelWrapper(
            models.DbLog(
                time=time,
                loggername=loggername,
                levelname=levelname,
                dbnode_id=dbnode_id,
                message=message,
                metadata=metadata))

    @property
    def uuid(self):
        """
        Get the UUID of the log entry
        """
        return self._dbmodel.uuid

    @property
    def time(self):
        """
        Get the time corresponding to the entry
        """
        return self._dbmodel.time

    @property
    def loggername(self):
        """
        The name of the logger that created this entry
        """
        return self._dbmodel.loggername

    @property
    def levelname(self):
        """
        The name of the log level
        """
        return self._dbmodel.levelname

    @property
    def dbnode_id(self):
        """
        Get the id of the object that created the log entry
        """
        return self._dbmodel.dbnode_id

    @property
    def message(self):
        """
        Get the message corresponding to the entry
        """
        return self._dbmodel.message

    @property
    def metadata(self):
        """
        Get the metadata corresponding to the entry
        """
        return self._dbmodel._metadata  # pylint: disable=protected-access


class SqlaLogCollection(BackendLogCollection):
    """The SQLA collection for logs"""

    ENTITY_CLASS = SqlaLog

    def delete(self, log_id):
        """
        Remove a Log entry from the collection with the given id

        :param log_id: id of the log to delete
        """
        # pylint: disable=no-name-in-module,import-error
        from sqlalchemy.orm.exc import NoResultFound
        session = get_scoped_session()

        try:
            session.query(models.DbLog).filter_by(id=log_id).one().delete()
            session.commit()
        except NoResultFound:
            raise exceptions.NotExistent("Log with id '{}' not found".format(log_id))

    def delete_many(self, filters):
        """
        Delete all log entries in the table
        """
        if not filters:
            for entry in models.DbLog.query.all():
                entry.delete()
            get_scoped_session().commit()
        else:
            raise NotImplementedError('Only deleting all by passing an empty filter dictionary is currently supported')
