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
from datetime import datetime, timezone
import functools
from typing import Any, Optional, Set, Tuple

import sqlalchemy as sa
from sqlalchemy import ColumnDefault
from sqlalchemy import orm as sa_orm
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.dialects.sqlite import JSON

from aiida.orm.entities import EntityTypes
# we need to import all models, to ensure they are loaded on the SQLA Metadata
from aiida.storage.psql_dos.models import authinfo, base, comment, computer, group, log, node, user


class SqliteModel:
    """Represent a row in an sqlite database table"""

    def __repr__(self) -> str:
        """Return a representation of the row columns"""
        string = f'<{self.__class__.__name__}'
        for col in self.__table__.columns:  # type: ignore[attr-defined] # pylint: disable=no-member
            col_name = col.name
            if col_name == 'metadata':
                col_name = '_metadata'
            val = f'{getattr(self, col_name)!r}'
            if len(val) > 10:  # truncate long values
                val = val[:10] + '...'
            string += f' {col_name}={val},'
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
            value = value.astimezone(timezone.utc)
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
        return value

    def process_result_value(self, value: Optional[datetime], dialect):
        """Process when returning from database."""
        if value is None:
            return value
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


SqliteBase = sa.orm.declarative_base(
    cls=SqliteModel, name='SqliteModel', metadata=sa.MetaData(naming_convention=dict(base.naming_convention))
)
sa.event.listen(SqliteBase, 'init', base.instant_defaults_listener, propagate=True)


def pg_to_sqlite(pg_table: sa.Table):
    """Convert a model intended for PostGreSQL to one compatible with SQLite"""
    new = pg_table.to_metadata(SqliteBase.metadata)
    for column in new.columns:
        if isinstance(column.type, UUID):
            column.type = sa.String(32)
        elif isinstance(column.type, sa.DateTime):
            column.type = TZDateTime()
        elif isinstance(column.type, JSONB):
            column.type = JSON()
            column.default = ColumnDefault(dict)
    # remove any postgresql specific indexes, e.g. varchar_pattern_ops
    new.indexes.difference_update([idx for idx in new.indexes if idx.dialect_kwargs])
    return new


def create_orm_cls(klass: base.Base) -> SqliteBase:
    """Create an ORM class from an existing table in the declarative meta"""
    tbl = SqliteBase.metadata.tables[klass.__tablename__]
    return type(  # type: ignore[return-value]
        klass.__name__,
        (SqliteBase,),
        {
            '__doc__': klass.__doc__,
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

# to-do ideally these relationships should be auto-generated in `create_orm_cls`, but this proved difficult
DbAuthInfo.aiidauser = sa_orm.relationship(  # type: ignore[attr-defined]
    'DbUser', backref=sa_orm.backref('authinfos', passive_deletes=True, cascade='all, delete')
)
DbAuthInfo.dbcomputer = sa_orm.relationship(  # type: ignore[attr-defined]
    'DbComputer', backref=sa_orm.backref('authinfos', passive_deletes=True, cascade='all, delete')
)
DbComment.dbnode = sa_orm.relationship('DbNode', backref='dbcomments')  # type: ignore[attr-defined]
DbComment.user = sa_orm.relationship('DbUser')  # type: ignore[attr-defined]
DbGroup.user = sa_orm.relationship(  # type: ignore[attr-defined]
    'DbUser', backref=sa_orm.backref('dbgroups', cascade='merge')
)
DbGroup.dbnodes = sa_orm.relationship(  # type: ignore[attr-defined]
    'DbNode', secondary='db_dbgroup_dbnodes', backref='dbgroups', lazy='dynamic'
)
DbLog.dbnode = sa_orm.relationship(  # type: ignore[attr-defined]
    'DbNode', backref=sa_orm.backref('dblogs', passive_deletes='all', cascade='merge')
)
DbNode.dbcomputer = sa_orm.relationship(  # type: ignore[attr-defined]
    'DbComputer', backref=sa_orm.backref('dbnodes', passive_deletes='all', cascade='merge')
)
DbNode.user = sa_orm.relationship('DbUser', backref=sa_orm.backref(  # type: ignore[attr-defined]
    'dbnodes',
    passive_deletes='all',
    cascade='merge',
))


@functools.lru_cache(maxsize=10)
def get_model_from_entity(entity_type: EntityTypes) -> Tuple[Any, Set[str]]:
    """Return the Sqlalchemy model and column names corresponding to the given entity."""
    model = {
        EntityTypes.USER: DbUser,
        EntityTypes.AUTHINFO: DbAuthInfo,
        EntityTypes.GROUP: DbGroup,
        EntityTypes.NODE: DbNode,
        EntityTypes.COMMENT: DbComment,
        EntityTypes.COMPUTER: DbComputer,
        EntityTypes.LOG: DbLog,
        EntityTypes.LINK: DbLink,
        EntityTypes.GROUP_NODE: DbGroupNodes
    }[entity_type]
    mapper = sa.inspect(model).mapper
    column_names = {col.name for col in mapper.c.values()}
    return model, column_names
