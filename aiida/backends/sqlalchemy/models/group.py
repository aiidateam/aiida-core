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
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import backref, relationship
from sqlalchemy.schema import Column, Index, Table, UniqueConstraint
from sqlalchemy.types import DateTime, Integer, String, Text

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


class DbGroupNode(Base):
    """Database model to store group-to-nodes relations."""
    __tablename__ = table_groups_nodes.name
    __table__ = table_groups_nodes


class DbGroup(Base):
    """Database model to store groups of nodes.

    Users will typically identify and handle groups by using their ``label``
    (which, unlike the ``labels`` in other models, must be unique).
    Groups also have a ``type``, which serves to identify what plugin is being instanced,
    and the ``extras`` property for users to set any relevant information.
    """

    __tablename__ = 'db_dbgroup'

    id = Column(Integer, primary_key=True)  # pylint: disable=invalid-name

    uuid = Column(UUID(as_uuid=True), default=get_new_uuid, unique=True, nullable=False)
    label = Column(String(255), index=True, nullable=False)

    type_string = Column(String(255), default='', index=True, nullable=False)

    time = Column(DateTime(timezone=True), default=timezone.now, nullable=False)
    description = Column(Text, default='', nullable=False)

    extras = Column(JSONB, default=dict, nullable=False)

    user_id = Column(
        Integer, ForeignKey('db_dbuser.id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False
    )
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
