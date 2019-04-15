# -*- coding: utf-8 -*-

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Column
from sqlalchemy.types import Integer, DateTime, Text

from aiida.utils import timezone
from aiida.backends.sqlalchemy.models.base import Base

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__authors__ = "The AiiDA team."
__version__ = "0.6.0.1"

class DbComment(Base):
    __tablename__ = "db_dbcomment"

    id = Column(Integer, primary_key=True)

    dbnode_id = Column(Integer, ForeignKey('db_dbnode.id', ondelete="CASCADE", deferrable=True, initially="DEFERRED"))
    dbnode = relationship('DbNode', backref='dbcomments')

    ctime = Column(DateTime(timezone=True), default=timezone.now)
    mtime = Column(DateTime(timezone=True), default=timezone.now)

    user_id = Column(Integer, ForeignKey('db_dbuser.id', ondelete="CASCADE", deferrable=True, initially="DEFERRED"))
    user = relationship("DbUser")

    content = Column(Text, nullable=True)

    def __str__(self):
        return "DbComment for [{} {}] on {}".format(
            self.dbnode.get_simple_name(),
            self.dbnode.id, timezone.localtime(self.ctime).strftime("%Y-%m-%d")
        )
