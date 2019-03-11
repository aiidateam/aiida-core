# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, backref
from sqlalchemy.schema import Column
from sqlalchemy.types import Integer, DateTime, String, Text

from aiida.backends.sqlalchemy.models.base import Base
from aiida.common import timezone
from aiida.common.utils import get_new_uuid


class DbLog(Base):

    __tablename__ = 'db_dblog'

    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True), default=get_new_uuid, unique=True)
    time = Column(DateTime(timezone=True), default=timezone.now)
    loggername = Column(String(255), index=True)
    levelname = Column(String(255), index=True)
    dbnode_id = Column(
        Integer,
        ForeignKey('db_dbnode.id', deferrable=True, initially='DEFERRED', ondelete='CASCADE'),
        nullable=False
    )
    message = Column(Text(), nullable=True)
    _metadata = Column('metadata', JSONB)

    dbnode = relationship('DbNode', backref=backref('dblogs', passive_deletes='all', cascade='merge'))

    def __init__(self, time, loggername, levelname, dbnode_id, uuid=None, message=None, metadata=None):
        if uuid is not None:
            self.uuid = uuid

        self.time = time
        self.loggername = loggername
        self.levelname = levelname
        self.dbnode_id = dbnode_id
        self.message = message
        self._metadata = metadata or {}

    def __str__(self):
        return 'DbLog: {} for node {}: {}'.format(self.levelname, self.dbnode.id, self.message)
