# -*- coding: utf-8 -*-

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.schema import Column, Table, UniqueConstraint
from sqlalchemy.types import Integer, String, Boolean, DateTime, Text

from sqlalchemy.dialects.postgresql import UUID

from aiida.utils import timezone
from aiida.backends.sqlalchemy.models.base import Base
from aiida.backends.sqlalchemy.models.utils import uuid_func


table_groups_nodes = Table(
    'db_dbnode_groups',
    Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('db_dbnode_id', Integer, ForeignKey('db_dbnode.id')),
    Column('db_dbgroup_id', Integer, ForeignKey('db_dbuser.id'))
)

class DbGroup(Base):
    __tablename__ = "db_dbgroup"

    id = Column(Integer, primary_key=True)

    uuid = Column(UUID, default=uuid_func)
    name = Column(String(255), index=True)

    type = Column(String(255), default="", index=True)

    time = Column(DateTime(timezone=True), default=timezone.now)
    description = Column(Text, nullable=True)

    user_id = Column(Integer, ForeignKey('db_dbuser.id', ondelete='CASCADE'))
    user = relationship('DbUser', backref='dbgroups')

    __table_args__ = (
        UniqueConstraint('name', 'type'),
    )

    def __str__(self):
        if self.type:
            return '<DbGroup [type: {}] "{}">'.format(self.type, self.name)
        else:
            return '<DbGroup [user-defined] "{}">'.format(self.name)
