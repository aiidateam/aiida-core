# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The Django log and log collection module"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.backends.djsite.db import models
import aiida.common.json as json
from . import entities
from .. import BackendLog, BackendLogCollection


class DjangoLog(entities.DjangoModelEntity[models.DbLog], BackendLog):
    """Django log class"""

    MODEL_CLASS = models.DbLog

    def __init__(self, backend, time, loggername, levelname, objname, objpk=None, message="", metadata=None):
        # pylint: disable=too-many-arguments
        super(DjangoLog, self).__init__(backend)
        self._dbmodel = models.DbLog(
            time=time,
            loggername=loggername,
            levelname=levelname,
            objname=objname,
            objpk=objpk,
            message=message,
            metadata=json.dumps(metadata))

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
    def objpk(self):
        """
        Get the id of the object that created the log entry
        """
        return self._dbmodel.objpk

    @property
    def objname(self):
        """
        Get the name of the object that created the log entry
        """
        return self._dbmodel.objname

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
        return json.loads(self._dbmodel.metadata)


class DjangoLogCollection(BackendLogCollection):
    """Django log collection"""

    ENTITY_CLASS = DjangoLog

    def delete_many(self, filters):
        """
        Delete all log entries in the table
        """
        if not filters:
            models.DbLog.objects.all().delete()
        else:
            raise NotImplementedError("Only deleting all by passing an empty filer dictionary is "
                                      "currently supported")
