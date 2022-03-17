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
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import backref, relationship
from sqlalchemy.schema import Column
from sqlalchemy.sql.schema import ForeignKey, Index
from sqlalchemy.types import DateTime, Integer, String, Text

from aiida.common import timezone
from aiida.common.utils import get_new_uuid
from aiida.storage.psql_dos.models.base import Base


class DbLog(Base):
    """Database model to data for :py:class:`aiida.orm.Log`, corresponding to :py:class:`aiida.orm.ProcessNode`."""
    __tablename__ = 'db_dblog'

    id = Column(Integer, primary_key=True)  # pylint: disable=invalid-name
    uuid = Column(UUID(as_uuid=True), default=get_new_uuid, nullable=False, unique=True)
    time = Column(DateTime(timezone=True), default=timezone.now, nullable=False)
    loggername = Column(String(255), nullable=False, index=True, doc='What process recorded the message')
    levelname = Column(String(50), nullable=False, index=True, doc='How critical the message is')
    dbnode_id = Column(
        Integer,
        ForeignKey('db_dbnode.id', deferrable=True, initially='DEFERRED', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    message = Column(Text(), default='', nullable=False)
    _metadata = Column('metadata', JSONB, default=dict, nullable=False)

    dbnode = relationship('DbNode', backref=backref('dblogs', passive_deletes='all', cascade='merge'))

    __table_args__ = (
        Index(
            'ix_pat_db_dblog_loggername',
            loggername,
            postgresql_using='btree',
            postgresql_ops={'loggername': 'varchar_pattern_ops'}
        ),
        Index(
            'ix_pat_db_dblog_levelname',
            levelname,
            postgresql_using='btree',
            postgresql_ops={'levelname': 'varchar_pattern_ops'}
        ),
    )

    def __str__(self):
        return f'DbLog: {self.levelname} for node {self.dbnode.id}: {self.message}'
