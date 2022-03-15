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
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import backref, relationship
from sqlalchemy.schema import Column, ForeignKey, Index, UniqueConstraint
from sqlalchemy.types import DateTime, Integer, String, Text

from aiida.common import timezone
from aiida.common.utils import get_new_uuid

from .base import Base


class DbGroupNode(Base):
    """Database model to store group-to-nodes relations."""
    __tablename__ = 'db_dbgroup_dbnodes'

    id = Column(Integer, primary_key=True)
    dbnode_id = Column(
        Integer, ForeignKey('db_dbnode.id', deferrable=True, initially='DEFERRED'), nullable=False, index=True
    )
    dbgroup_id = Column(
        Integer, ForeignKey('db_dbgroup.id', deferrable=True, initially='DEFERRED'), nullable=False, index=True
    )

    __table_args__ = (UniqueConstraint('dbgroup_id', 'dbnode_id'),)


table_groups_nodes = DbGroupNode.__table__


class DbGroup(Base):
    """Database model to store :py:class:`aiida.orm.Group` data.

    A group may contain many different nodes, but also each node can be included in different groups.

    Users will typically identify and handle groups by using their ``label``
    (which, unlike the ``labels`` in other models, must be unique).
    Groups also have a ``type``, which serves to identify what plugin is being instanced,
    and the ``extras`` property for users to set any relevant information.
    """

    __tablename__ = 'db_dbgroup'

    id = Column(Integer, primary_key=True)  # pylint: disable=invalid-name
    uuid = Column(UUID(as_uuid=True), default=get_new_uuid, nullable=False, unique=True)
    label = Column(String(255), nullable=False, index=True)
    type_string = Column(String(255), default='', nullable=False, index=True)
    time = Column(DateTime(timezone=True), default=timezone.now, nullable=False)
    description = Column(Text, default='', nullable=False)
    extras = Column(JSONB, default=dict, nullable=False)
    user_id = Column(
        Integer,
        ForeignKey('db_dbuser.id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'),
        nullable=False,
        index=True
    )

    user = relationship('DbUser', backref=backref('dbgroups', cascade='merge'))
    dbnodes = relationship('DbNode', secondary=table_groups_nodes, backref='dbgroups', lazy='dynamic')

    __table_args__ = (
        UniqueConstraint('label', 'type_string'),
        Index(
            'ix_pat_db_dbgroup_label', label, postgresql_using='btree', postgresql_ops={'label': 'varchar_pattern_ops'}
        ),
        Index(
            'ix_pat_db_dbgroup_type_string',
            type_string,
            postgresql_using='btree',
            postgresql_ops={'type_string': 'varchar_pattern_ops'}
        ),
    )

    @property
    def pk(self):
        return self.id

    def __str__(self):
        return f'<DbGroup [type: {self.type_string}] "{self.label}">'
