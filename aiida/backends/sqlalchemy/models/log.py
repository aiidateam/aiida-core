# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import json

from sqlalchemy.schema import Column
from sqlalchemy.types import Integer, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from aiida.utils import timezone
from aiida.backends.sqlalchemy.models.base import Base
from aiida.common.exceptions import ValidationError



class DbLog(Base):
    __tablename__ = "db_dblog"

    id = Column(Integer, primary_key=True)

    time = Column(DateTime(timezone=True), default=timezone.now)
    loggername = Column(String(255), index=True)
    levelname = Column(String(255), index=True)

    objname = Column(String(255), index=True)
    objpk = Column(Integer, index=True, nullable=True)

    message = Column(Text(), nullable=True)
    _metadata = Column('metadata', JSONB)

    def __init__(self, loggername="", levelname="", objname="", objpk=None,
                 message=None, metadata=None):

        if not loggername or not levelname:
            raise ValidationError(
                "The loggername and levelname can't be empty")

        self.loggername = loggername
        self.levelname = levelname
        self.objname = objname
        self.objpk = objpk
        self.message = message
        self._metadata = metadata or {}


    def __str__(self):
        return "DbComment for [{} {}] on {}".format(
            self.dbnode.get_simple_name(),
            self.dbnode.id, timezone.localtime(self.ctime).strftime("%Y-%m-%d")
        )

    @classmethod
    def add_from_logrecord(cls, record):
        """
        Add a new entry from a LogRecord (from the standard python
        logging facility). No exceptions are managed here.
        """

        objpk = record.__dict__.get('objpk', None)
        objname = record.__dict__.get('objname', None)

        # Filter: Do not store in DB if no objpk and objname is given
        if objpk is None or objname is None:
            return

        new_entry = cls(loggername=record.name,
                        levelname=record.levelname,
                        objname=objname,
                        objpk=objpk,
                        message=record.getMessage(),
                        metadata=record.__dict__)
        new_entry.save()
