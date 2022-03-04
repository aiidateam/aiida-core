# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""This is the sqlite DB schema, coresponding to the `main_0000` revision of the `sqlite_zip` backend,
see: `versions/main_0000_initial.py`

For normal operation of the archive,
we auto-generate the schema from the models in ``aiida.storage.psql_dos.models``.
However, when migrating an archive from the old format, we require a fixed revision of the schema.

The only difference between the PostGreSQL schema and SQLite one,
is the replacement of ``JSONB`` with ``JSON``, and ``UUID`` with ``CHAR(32)``.
"""
from sqlalchemy import ForeignKey, MetaData, orm
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.schema import Column, UniqueConstraint
from sqlalchemy.types import CHAR, Boolean, DateTime, Integer, String, Text

from aiida.common import timezone
from aiida.common.utils import get_new_uuid

# see https://alembic.sqlalchemy.org/en/latest/naming.html
naming_convention = (
    ('pk', '%(table_name)s_pkey'),
    ('ix', 'ix_%(table_name)s_%(column_0_N_label)s'),
    ('uq', 'uq_%(table_name)s_%(column_0_N_name)s'),
    ('ck', 'ck_%(table_name)s_%(constraint_name)s'),
    ('fk', 'fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s'),
)

ArchiveV1Base = orm.declarative_base(metadata=MetaData(naming_convention=dict(naming_convention)))


class DbAuthInfo(ArchiveV1Base):
    """Class that keeps the authentication data."""

    __tablename__ = 'db_dbauthinfo'
    __table_args__ = (UniqueConstraint('aiidauser_id', 'dbcomputer_id'),)

    id = Column(Integer, primary_key=True)  # pylint: disable=invalid-name
    aiidauser_id = Column(
        Integer,
        ForeignKey('db_dbuser.id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'),
        nullable=True,
        index=True
    )
    dbcomputer_id = Column(
        Integer,
        ForeignKey('db_dbcomputer.id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'),
        nullable=True,
        index=True
    )
    _metadata = Column('metadata', JSON, default=dict, nullable=True)
    auth_params = Column(JSON, default=dict, nullable=True)
    enabled = Column(Boolean, default=True, nullable=True)


class DbComment(ArchiveV1Base):
    """Class to store comments."""

    __tablename__ = 'db_dbcomment'

    id = Column(Integer, primary_key=True)  # pylint: disable=invalid-name
    uuid = Column(CHAR(32), default=get_new_uuid, nullable=False, unique=True)
    dbnode_id = Column(
        Integer,
        ForeignKey('db_dbnode.id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'),
        nullable=True,
        index=True
    )
    ctime = Column(DateTime(timezone=True), default=timezone.now, nullable=True)
    mtime = Column(DateTime(timezone=True), default=timezone.now, nullable=True)
    user_id = Column(
        Integer,
        ForeignKey('db_dbuser.id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'),
        nullable=True,
        index=True
    )
    content = Column(Text, default='', nullable=True)


class DbComputer(ArchiveV1Base):
    """Class to store computers."""
    __tablename__ = 'db_dbcomputer'

    id = Column(Integer, primary_key=True)  # pylint: disable=invalid-name
    uuid = Column(CHAR(32), default=get_new_uuid, nullable=False, unique=True)
    label = Column(String(255), unique=True, nullable=False)
    hostname = Column(String(255), default='', nullable=True)
    description = Column(Text, default='', nullable=True)
    scheduler_type = Column(String(255), default='', nullable=True)
    transport_type = Column(String(255), default='', nullable=True)
    _metadata = Column('metadata', JSON, default=dict, nullable=True)


class DbGroupNodes(ArchiveV1Base):
    """Class to store join table for group -> nodes."""

    __tablename__ = 'db_dbgroup_dbnodes'
    __table_args__ = (UniqueConstraint('dbgroup_id', 'dbnode_id'),)

    id = Column(Integer, primary_key=True)  # pylint: disable=invalid-name
    dbnode_id = Column(
        Integer, ForeignKey('db_dbnode.id', deferrable=True, initially='DEFERRED'), nullable=False, index=True
    )
    dbgroup_id = Column(
        Integer, ForeignKey('db_dbgroup.id', deferrable=True, initially='DEFERRED'), nullable=False, index=True
    )


class DbGroup(ArchiveV1Base):
    """Class to store groups."""

    __tablename__ = 'db_dbgroup'
    __table_args__ = (UniqueConstraint('label', 'type_string'),)

    id = Column(Integer, primary_key=True)  # pylint: disable=invalid-name
    uuid = Column(CHAR(32), default=get_new_uuid, nullable=False, unique=True)
    label = Column(String(255), nullable=False, index=True)
    type_string = Column(String(255), default='', nullable=True, index=True)
    time = Column(DateTime(timezone=True), default=timezone.now, nullable=True)
    description = Column(Text, default='', nullable=True)
    extras = Column(JSON, default=dict, nullable=False)
    user_id = Column(
        Integer,
        ForeignKey('db_dbuser.id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'),
        nullable=False,
        index=True
    )


class DbLog(ArchiveV1Base):
    """Class to store logs."""

    __tablename__ = 'db_dblog'

    id = Column(Integer, primary_key=True)  # pylint: disable=invalid-name
    uuid = Column(CHAR(32), default=get_new_uuid, nullable=False, unique=True)
    time = Column(DateTime(timezone=True), default=timezone.now, nullable=True)
    loggername = Column(String(255), default='', nullable=True, index=True)
    levelname = Column(String(50), default='', nullable=True, index=True)
    dbnode_id = Column(
        Integer,
        ForeignKey('db_dbnode.id', deferrable=True, initially='DEFERRED', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    message = Column(Text(), default='', nullable=True)
    _metadata = Column('metadata', JSON, default=dict, nullable=True)


class DbNode(ArchiveV1Base):
    """Class to store nodes."""

    __tablename__ = 'db_dbnode'

    id = Column(Integer, primary_key=True)  # pylint: disable=invalid-name
    uuid = Column(CHAR(32), default=get_new_uuid, nullable=False, unique=True)
    node_type = Column(String(255), default='', nullable=False, index=True)
    process_type = Column(String(255), index=True)
    label = Column(String(255), default='', index=True, nullable=True)
    description = Column(Text(), default='', nullable=True)
    ctime = Column(DateTime(timezone=True), default=timezone.now, nullable=True, index=True)
    mtime = Column(DateTime(timezone=True), default=timezone.now, nullable=True, index=True)
    attributes = Column(JSON)
    extras = Column(JSON)
    repository_metadata = Column(JSON, nullable=False, default=dict, server_default='{}')
    dbcomputer_id = Column(
        Integer,
        ForeignKey('db_dbcomputer.id', deferrable=True, initially='DEFERRED', ondelete='RESTRICT'),
        nullable=True,
        index=True
    )
    user_id = Column(
        Integer,
        ForeignKey('db_dbuser.id', deferrable=True, initially='DEFERRED', ondelete='restrict'),
        nullable=False,
        index=True
    )


class DbLink(ArchiveV1Base):
    """Class to store links between nodes."""

    __tablename__ = 'db_dblink'

    id = Column(Integer, primary_key=True)  # pylint: disable=invalid-name
    input_id = Column(
        Integer, ForeignKey('db_dbnode.id', deferrable=True, initially='DEFERRED'), nullable=False, index=True
    )
    output_id = Column(
        Integer,
        ForeignKey('db_dbnode.id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'),
        nullable=False,
        index=True
    )
    label = Column(String(255), default='', nullable=False, index=True)
    type = Column(String(255), nullable=False, index=True)


class DbUser(ArchiveV1Base):
    """Class to store users."""

    __tablename__ = 'db_dbuser'

    id = Column(Integer, primary_key=True)  # pylint: disable=invalid-name
    email = Column(String(254), nullable=False, unique=True)
    first_name = Column(String(254), default='', nullable=True)
    last_name = Column(String(254), default='', nullable=True)
    institution = Column(String(254), default='', nullable=True)
