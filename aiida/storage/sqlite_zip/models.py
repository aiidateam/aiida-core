# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""This module contains the SQLAlchemy models for the SQLite backend.

These models are intended to be identical to those of the `psql_dos` backend,
except for changes to the database specific types:

- UUID -> CHAR(32)
- DateTime -> TZDateTime
- JSONB -> JSON

Also, `varchar_pattern_ops` indexes are not possible in sqlite.
"""
from datetime import datetime
from typing import Optional

import pytz
import sqlalchemy as sa
from sqlalchemy import orm as sa_orm
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.dialects.sqlite import JSON

# we need to import all models, to ensure they are loaded on the SQLA Metadata
from aiida.storage.psql_dos.models import authinfo, base, comment, computer, group, log, node, user


class SqliteModel:
    """Represent a row in an sqlite database table"""

    def __repr__(self) -> str:
        """Return a representation of the row columns"""
        string = f'<{self.__class__.__name__}'
        for col in self.__table__.columns:  # type: ignore[attr-defined] # pylint: disable=no-member
            # don't include columns with potentially large values
            if isinstance(col.type, (JSON, sa.Text)):
                continue
            string += f' {col.name}={getattr(self, col.name)}'
        return string + '>'


class TZDateTime(sa.TypeDecorator):  # pylint: disable=abstract-method
    """A timezone naive UTC ``DateTime`` implementation for SQLite.

    see: https://docs.sqlalchemy.org/en/14/core/custom_types.html#store-timezone-aware-timestamps-as-timezone-naive-utc
    """
    impl = sa.DateTime
    cache_ok = True

    def process_bind_param(self, value: Optional[datetime], dialect):
        """Process before writing to database."""
        if value is None:
            return value
        if value.tzinfo is None:
            value = value.astimezone(pytz.utc)
        value = value.astimezone(pytz.utc).replace(tzinfo=None)
        return value

    def process_result_value(self, value: Optional[datetime], dialect):
        """Process when returning from database."""
        if value is None:
            return value
        if value.tzinfo is None:
            return value.replace(tzinfo=pytz.utc)
        return value.astimezone(pytz.utc)


SqliteBase = sa.orm.declarative_base(
    cls=SqliteModel, name='SqliteModel', metadata=sa.MetaData(naming_convention=dict(base.naming_convention))
)


def pg_to_sqlite(pg_table: sa.Table):
    """Convert a model intended for PostGreSQL to one compatible with SQLite"""
    new = pg_table.to_metadata(SqliteBase.metadata)
    for column in new.columns:
        if isinstance(column.type, UUID):
            column.type = sa.CHAR(32)
        elif isinstance(column.type, sa.DateTime):
            column.type = TZDateTime()
        elif isinstance(column.type, JSONB):
            column.type = JSON()
    return new


def create_orm_cls(klass: base.Base) -> SqliteBase:
    """Create an ORM class from an existing table in the declarative meta"""
    tbl = SqliteBase.metadata.tables[klass.__tablename__]
    return type(  # type: ignore[return-value]
        klass.__name__,
        (SqliteBase,),
        {
            '__tablename__': tbl.name,
            '__table__': tbl,
            **{col.name if col.name != 'metadata' else '_metadata': col for col in tbl.columns},
        },
    )


for table in base.Base.metadata.sorted_tables:
    pg_to_sqlite(table)

DbUser = create_orm_cls(user.DbUser)
DbComputer = create_orm_cls(computer.DbComputer)
DbAuthInfo = create_orm_cls(authinfo.DbAuthInfo)
DbGroup = create_orm_cls(group.DbGroup)
DbNode = create_orm_cls(node.DbNode)
DbGroupNodes = create_orm_cls(group.DbGroupNode)
DbComment = create_orm_cls(comment.DbComment)
DbLog = create_orm_cls(log.DbLog)
DbLink = create_orm_cls(node.DbLink)

# to-do This was the minimum for creating a graph, but really all relationships should be copied
DbNode.dbcomputer = sa_orm.relationship('DbComputer', backref='dbnodes')  # type: ignore[attr-defined]
DbGroup.dbnodes = sa_orm.relationship(  # type: ignore[attr-defined]
    'DbNode', secondary='db_dbgroup_dbnodes', backref='dbgroups', lazy='dynamic'
)
