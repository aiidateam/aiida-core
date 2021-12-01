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
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import backref, relationship
from sqlalchemy.schema import Column
from sqlalchemy.types import DateTime, Integer, String, Text

from aiida.backends.sqlalchemy.models.base import Base
from aiida.common import timezone
from aiida.common.utils import get_new_uuid


class DbLog(Base):
    """Database model to store log levels and messages relating to a process node."""
    __tablename__ = 'db_dblog'

    id = Column(Integer, primary_key=True)  # pylint: disable=invalid-name
    uuid = Column(UUID(as_uuid=True), default=get_new_uuid, unique=True)
    time = Column(DateTime(timezone=True), default=timezone.now)
    loggername = Column(String(255), index=True, doc='What process recorded the message')
    levelname = Column(String(255), index=True, doc='How critical the message is')
    dbnode_id = Column(
        Integer, ForeignKey('db_dbnode.id', deferrable=True, initially='DEFERRED', ondelete='CASCADE'), nullable=False
    )
    message = Column(Text(), nullable=True)
    _metadata = Column('metadata', JSONB)

    dbnode = relationship('DbNode', backref=backref('dblogs', passive_deletes='all', cascade='merge'))

    def __str__(self):
        return f'DbLog: {self.levelname} for node {self.dbnode.id}: {self.message}'

    def __init__(self, *args, **kwargs):
        """Construct new instance making sure the `_metadata` column is initialized to empty dict if `None`."""
        super().__init__(*args, **kwargs)
        self._metadata = kwargs.pop('metadata', {}) or {}
