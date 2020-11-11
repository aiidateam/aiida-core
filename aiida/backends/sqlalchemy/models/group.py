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
"""Module to manage computers for the SQLA backend."""

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.schema import Column, Table, UniqueConstraint, Index
from sqlalchemy.types import Integer, String, DateTime, Text

from sqlalchemy.dialects.postgresql import UUID, JSONB

from aiida.common import timezone
from aiida.common.utils import get_new_uuid

from .base import Base

table_groups_nodes = Table(  # pylint: disable=invalid-name
    'db_dbgroup_dbnodes',
    Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('dbnode_id', Integer, ForeignKey('db_dbnode.id', deferrable=True, initially='DEFERRED')),
    Column('dbgroup_id', Integer, ForeignKey('db_dbgroup.id', deferrable=True, initially='DEFERRED')),
    UniqueConstraint('dbgroup_id', 'dbnode_id', name='db_dbgroup_dbnodes_dbgroup_id_dbnode_id_key'),
)


class DbGroup(Base):
    """Class to store groups using SQLA backend."""

    __tablename__ = 'db_dbgroup'

    id = Column(Integer, primary_key=True)  # pylint: disable=invalid-name

    uuid = Column(UUID(as_uuid=True), default=get_new_uuid, unique=True)
    label = Column(String(255), index=True)

    type_string = Column(String(255), default='', index=True)

    time = Column(DateTime(timezone=True), default=timezone.now)
    description = Column(Text, nullable=True)

    extras = Column(JSONB, default=dict, nullable=False)

    user_id = Column(Integer, ForeignKey('db_dbuser.id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'))
    user = relationship('DbUser', backref=backref('dbgroups', cascade='merge'))

    dbnodes = relationship('DbNode', secondary=table_groups_nodes, backref='dbgroups', lazy='dynamic')

    __table_args__ = (UniqueConstraint('label', 'type_string'),)

    Index('db_dbgroup_dbnodes_dbnode_id_idx', table_groups_nodes.c.dbnode_id)
    Index('db_dbgroup_dbnodes_dbgroup_id_idx', table_groups_nodes.c.dbgroup_id)

    @property
    def pk(self):
        return self.id

    def __str__(self):
        return f'<DbGroup [type: {self.type_string}] "{self.label}">'
