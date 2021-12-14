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
from sqlalchemy.sql.schema import Index, UniqueConstraint
from sqlalchemy.types import DateTime, Integer, String, Text

from aiida.backends.sqlalchemy.models.base import Base
from aiida.common import timezone
from aiida.common.utils import get_new_uuid


class DbLog(Base):
    """Database model to store log levels and messages relating to a process node."""
    __tablename__ = 'db_dblog'

    id = Column(Integer, primary_key=True)  # pylint: disable=invalid-name
    uuid = Column(UUID(as_uuid=True), default=get_new_uuid, nullable=False)
    time = Column(DateTime(timezone=True), default=timezone.now, nullable=False)
    loggername = Column(String(255), nullable=False, doc='What process recorded the message')
    levelname = Column(String(50), nullable=False, doc='How critical the message is')
    dbnode_id = Column(
        Integer, ForeignKey('db_dbnode.id', deferrable=True, initially='DEFERRED', ondelete='CASCADE'), nullable=False
    )
    message = Column(Text(), default='', nullable=False)
    _metadata = Column('metadata', JSONB, default=dict, nullable=False)

    dbnode = relationship('DbNode', backref=backref('dblogs', passive_deletes='all', cascade='merge'))

    __table_args__ = (
        # index/constrain names mirror django's auto-generated ones
        UniqueConstraint(uuid, name='db_dblog_uuid_9cf77df3_uniq'),
        Index('db_dblog_loggername_00b5ba16', loggername),
        Index('db_dblog_levelname_ad5dc346', levelname),
        Index('db_dblog_dbnode_id_da34b732', dbnode_id),
        Index(
            'db_dblog_loggername_00b5ba16_like',
            loggername,
            postgresql_using='btree',
            postgresql_ops={'data': 'varchar_pattern_ops'}
        ),
        Index(
            'db_dblog_levelname_ad5dc346_like',
            levelname,
            postgresql_using='btree',
            postgresql_ops={'data': 'varchar_pattern_ops'}
        ),
    )

    def __str__(self):
        return f'DbLog: {self.levelname} for node {self.dbnode.id}: {self.message}'

    def __init__(self, *args, **kwargs):
        """Construct new instance making sure the `_metadata` column is initialized to empty dict if `None`."""
        super().__init__(*args, **kwargs)
        self._metadata = kwargs.pop('metadata', {}) or {}
