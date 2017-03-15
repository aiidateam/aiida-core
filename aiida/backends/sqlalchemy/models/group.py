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
from sqlalchemy.orm import relationship, backref
from sqlalchemy.schema import Column, Table, UniqueConstraint
from sqlalchemy.types import Integer, String, Boolean, DateTime, Text

from sqlalchemy.dialects.postgresql import UUID

from aiida.utils import timezone
from aiida.backends.sqlalchemy.models.base import Base
from aiida.backends.sqlalchemy.models.utils import uuid_func



table_groups_nodes = Table(
    'db_dbgroup_dbnodes',
    Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('dbnode_id', Integer, ForeignKey('db_dbnode.id', deferrable=True, initially="DEFERRED")),
    Column('dbgroup_id', Integer, ForeignKey('db_dbgroup.id', deferrable=True, initially="DEFERRED"))
)

class DbGroup(Base):
    __tablename__ = "db_dbgroup"

    id = Column(Integer, primary_key=True)

    uuid = Column(UUID(as_uuid=True), default=uuid_func)
    name = Column(String(255), index=True)

    type = Column(String(255), default="", index=True)

    time = Column(DateTime(timezone=True), default=timezone.now)
    description = Column(Text, nullable=True)

    user_id = Column(Integer, ForeignKey('db_dbuser.id', ondelete='CASCADE', deferrable=True, initially="DEFERRED"))
    user = relationship('DbUser', backref=backref('dbgroups', cascade='merge'))

    dbnodes = relationship('DbNode', secondary=table_groups_nodes,
                           backref="dbgroups", lazy='dynamic')

    __table_args__ = (
        UniqueConstraint('name', 'type'),
    )

    def __str__(self):
        if self.type:
            return '<DbGroup [type: {}] "{}">'.format(self.type, self.name)
        else:
            return '<DbGroup [user-defined] "{}">'.format(self.name)

    def get_aiida_class(self):
        from aiida.orm.implementation.sqlalchemy.group import Group
        return Group(dbgroup=self)
