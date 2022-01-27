# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""This is the sqlite DB schema, coresponding to the 34a831f4286d main DB revision.

For normal operation of the archive,
we auto-generate the schema from the models in ``aiida.backends.sqlalchemy.models``.
However, when migrating an archive from the old format, we require a fixed revision of the schema.

The only difference between the PostGreSQL schema and SQLite one,
is the replacement of ``JSONB`` with ``JSON``, and ``UUID`` with ``CHAR(36)``.
"""
from sqlalchemy import ForeignKey, orm
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.schema import Column, Index, UniqueConstraint
from sqlalchemy.types import CHAR, Boolean, DateTime, Integer, String, Text

ArchiveV1Base = orm.declarative_base()


class DbAuthInfo(ArchiveV1Base):
    """Class that keeps the authernification data."""

    __tablename__ = 'db_dbauthinfo'
    __table_args__ = (UniqueConstraint('aiidauser_id', 'dbcomputer_id'),)

    id = Column(Integer, primary_key=True)  # pylint: disable=invalid-name
    aiidauser_id = Column(
        Integer, ForeignKey('db_dbuser.id', ondelete='CASCADE', deferrable=True, initially='DEFERRED')
    )
    dbcomputer_id = Column(
        Integer, ForeignKey('db_dbcomputer.id', ondelete='CASCADE', deferrable=True, initially='DEFERRED')
    )
    _metadata = Column('metadata', JSON)
    auth_params = Column(JSON)
    enabled = Column(Boolean, default=True)


class DbComment(ArchiveV1Base):
    """Class to store comments."""

    __tablename__ = 'db_dbcomment'

    id = Column(Integer, primary_key=True)  # pylint: disable=invalid-name
    uuid = Column(CHAR(36), unique=True)
    dbnode_id = Column(Integer, ForeignKey('db_dbnode.id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'))
    ctime = Column(DateTime(timezone=True))
    mtime = Column(DateTime(timezone=True))
    user_id = Column(Integer, ForeignKey('db_dbuser.id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'))
    content = Column(Text, nullable=True)


class DbComputer(ArchiveV1Base):
    """Class to store computers."""
    __tablename__ = 'db_dbcomputer'

    id = Column(Integer, primary_key=True)  # pylint: disable=invalid-name
    uuid = Column(CHAR(36), unique=True)
    label = Column(String(255), unique=True, nullable=False)
    hostname = Column(String(255))
    description = Column(Text, nullable=True)
    scheduler_type = Column(String(255))
    transport_type = Column(String(255))
    _metadata = Column('metadata', JSON)


class DbGroupNodes(ArchiveV1Base):
    """Class to store join table for group -> nodes."""

    __tablename__ = 'db_dbgroup_dbnodes'
    __table_args__ = (UniqueConstraint('dbgroup_id', 'dbnode_id', name='db_dbgroup_dbnodes_dbgroup_id_dbnode_id_key'),)

    id = Column(Integer, primary_key=True)  # pylint: disable=invalid-name
    dbnode_id = Column(Integer, ForeignKey('db_dbnode.id', deferrable=True, initially='DEFERRED'))
    dbgroup_id = Column(Integer, ForeignKey('db_dbgroup.id', deferrable=True, initially='DEFERRED'))


class DbGroup(ArchiveV1Base):
    """Class to store groups."""

    __tablename__ = 'db_dbgroup'
    __table_args__ = (UniqueConstraint('label', 'type_string'),)

    id = Column(Integer, primary_key=True)  # pylint: disable=invalid-name
    uuid = Column(CHAR(36), unique=True)
    label = Column(String(255), index=True)
    type_string = Column(String(255), default='', index=True)
    time = Column(DateTime(timezone=True))
    description = Column(Text, nullable=True)
    extras = Column(JSON, default=dict, nullable=False)
    user_id = Column(Integer, ForeignKey('db_dbuser.id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'))

    Index('db_dbgroup_dbnodes_dbnode_id_idx', DbGroupNodes.dbnode_id)
    Index('db_dbgroup_dbnodes_dbgroup_id_idx', DbGroupNodes.dbgroup_id)


class DbLog(ArchiveV1Base):
    """Class to store logs."""

    __tablename__ = 'db_dblog'

    id = Column(Integer, primary_key=True)  # pylint: disable=invalid-name
    uuid = Column(CHAR(36), unique=True)
    time = Column(DateTime(timezone=True))
    loggername = Column(String(255), index=True)
    levelname = Column(String(255), index=True)
    dbnode_id = Column(
        Integer, ForeignKey('db_dbnode.id', deferrable=True, initially='DEFERRED', ondelete='CASCADE'), nullable=False
    )
    message = Column(Text(), nullable=True)
    _metadata = Column('metadata', JSON)


class DbNode(ArchiveV1Base):
    """Class to store nodes."""

    __tablename__ = 'db_dbnode'

    id = Column(Integer, primary_key=True)  # pylint: disable=invalid-name
    uuid = Column(CHAR(36), unique=True)
    node_type = Column(String(255), index=True)
    process_type = Column(String(255), index=True)
    label = Column(String(255), index=True, nullable=True, default='')
    description = Column(Text(), nullable=True, default='')
    ctime = Column(DateTime(timezone=True))
    mtime = Column(DateTime(timezone=True))
    attributes = Column(JSON)
    extras = Column(JSON)
    repository_metadata = Column(JSON, nullable=False, default=dict, server_default='{}')
    dbcomputer_id = Column(
        Integer,
        ForeignKey('db_dbcomputer.id', deferrable=True, initially='DEFERRED', ondelete='RESTRICT'),
        nullable=True
    )
    user_id = Column(
        Integer, ForeignKey('db_dbuser.id', deferrable=True, initially='DEFERRED', ondelete='restrict'), nullable=False
    )


class DbLink(ArchiveV1Base):
    """Class to store links between nodes."""

    __tablename__ = 'db_dblink'

    id = Column(Integer, primary_key=True)  # pylint: disable=invalid-name
    input_id = Column(Integer, ForeignKey('db_dbnode.id', deferrable=True, initially='DEFERRED'), index=True)
    output_id = Column(
        Integer, ForeignKey('db_dbnode.id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), index=True
    )
    label = Column(String(255), index=True, nullable=False)
    type = Column(String(255), index=True)


class DbUser(ArchiveV1Base):
    """Class to store users."""

    __tablename__ = 'db_dbuser'

    id = Column(Integer, primary_key=True)  # pylint: disable=invalid-name
    email = Column(String(254), unique=True, index=True)
    first_name = Column(String(254), nullable=True)
    last_name = Column(String(254), nullable=True)
    institution = Column(String(254), nullable=True)
