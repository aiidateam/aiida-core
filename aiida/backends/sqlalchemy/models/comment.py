# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Column
from sqlalchemy.types import Integer, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID

from aiida.utils import timezone
from aiida.backends.sqlalchemy.models.base import Base
from aiida.backends.sqlalchemy.models.utils import uuid_func


class DbComment(Base):
    __tablename__ = "db_dbcomment"

    id = Column(Integer, primary_key=True)

    uuid = Column(UUID(as_uuid=True), default=uuid_func)
    dbnode_id = Column(
            Integer,
            ForeignKey(
                'db_dbnode.id', ondelete="CASCADE",
                deferrable=True, initially="DEFERRED"
            )
        )

    ctime = Column(DateTime(timezone=True), default=timezone.now)
    mtime = Column(DateTime(timezone=True), default=timezone.now)

    user_id = Column(
            Integer,
            ForeignKey(
                'db_dbuser.id', ondelete="CASCADE",
                deferrable=True, initially="DEFERRED"
            )
        )
    content = Column(Text, nullable=True)

    dbnode = relationship('DbNode', backref='dbcomments')
    user = relationship("DbUser")

    def __str__(self):
        return "DbComment for [{} {}] on {}".format(
            self.dbnode.get_simple_name(),
            self.dbnode.id, timezone.localtime(self.ctime).strftime("%Y-%m-%d")
        )
