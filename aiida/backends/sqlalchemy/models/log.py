# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=import-error,no-name-in-module
"""Module to manage logs for the SQLA backend."""

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, backref
from sqlalchemy.schema import Column
from sqlalchemy.types import Integer, DateTime, String, Text

from aiida.backends.sqlalchemy.models.base import Base
from aiida.common import timezone
from aiida.common.utils import get_new_uuid


class DbLog(Base):
    """Class to store logs using SQLA backend."""
    __tablename__ = 'db_dblog'

    id = Column(Integer, primary_key=True)  # pylint: disable=invalid-name
    uuid = Column(UUID(as_uuid=True), default=get_new_uuid, unique=True)
    time = Column(DateTime(timezone=True), default=timezone.now)
    loggername = Column(String(255), index=True)
    levelname = Column(String(255), index=True)
    dbnode_id = Column(
        Integer, ForeignKey('db_dbnode.id', deferrable=True, initially='DEFERRED', ondelete='CASCADE'), nullable=False
    )
    message = Column(Text(), nullable=True)
    _metadata = Column('metadata', JSONB)

    dbnode = relationship('DbNode', backref=backref('dblogs', passive_deletes='all', cascade='merge'))

    def __init__(self, time, loggername, levelname, dbnode_id, **kwargs):
        """Setup initial value for the class attributes."""
        if 'uuid' in kwargs:
            self.uuid = kwargs['uuid']
        if 'message' in kwargs:
            self.message = kwargs['message']
        if 'metadata' in kwargs:
            self._metadata = kwargs['metadata'] or {}
        else:
            self._metadata = {}

        self.time = time
        self.loggername = loggername
        self.levelname = levelname
        self.dbnode_id = dbnode_id

    def __str__(self):
        return 'DbLog: {} for node {}: {}'.format(self.levelname, self.dbnode.id, self.message)
