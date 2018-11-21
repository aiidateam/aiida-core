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
from sqlalchemy.orm import relationship, backref
from sqlalchemy.schema import Column, Table, UniqueConstraint, Index
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
    Column('dbgroup_id', Integer, ForeignKey('db_dbgroup.id', deferrable=True, initially="DEFERRED")),

    UniqueConstraint('dbgroup_id', 'dbnode_id', name='db_dbgroup_dbnodes_dbgroup_id_dbnode_id_key'),
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

    dbnodes = relationship('DbNode', secondary=table_groups_nodes, backref="dbgroups", lazy='dynamic')

    __table_args__ = (
        UniqueConstraint('name', 'type'),
    )

    Index('db_dbgroup_dbnodes_dbnode_id_idx', table_groups_nodes.c.dbnode_id)
    Index('db_dbgroup_dbnodes_dbgroup_id_idx', table_groups_nodes.c.dbgroup_id)

    @property
    def pk(self):
        return self.id

    def __str__(self):
        if self.type:
            return '<DbGroup [type: {}] "{}">'.format(self.type, self.name)

        return '<DbGroup [user-defined] "{}">'.format(self.name)

    def get_aiida_class(self):
        from aiida.orm.implementation.sqlalchemy.backend import SqlaBackend
        backend = SqlaBackend()
        return backend.groups.from_dbmodel(self)
