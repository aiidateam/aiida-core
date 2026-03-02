###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""SQLAlchemy utilities shared across storage backends."""

from __future__ import annotations

import json
from functools import singledispatch
from typing import TYPE_CHECKING, Any

from sqlalchemy import cast as sql_cast
from sqlalchemy import func as sa_func
from sqlalchemy import or_, select, type_coerce
from sqlalchemy.dialects.postgresql.base import PGDialect
from sqlalchemy.dialects.sqlite.base import SQLiteDialect
from sqlalchemy.sql.elements import ColumnElement

from aiida.common.utils import batch_iter

if TYPE_CHECKING:
    from sqlalchemy import Function, Select, TableValuedAlias
    from sqlalchemy.orm.session import Session
    from sqlalchemy.sql.elements import KeyedColumnElement


@singledispatch
def _in_clause_select(dialect, coltype: Any, values) -> 'Select[Any]':
    """Return a SELECT subquery over ``values`` appropriate for the given dialect.

    Dispatches to the dialect-specific implementation via :func:`singledispatch`.
    """
    msg = f'Unsupported database dialect: {type(dialect).__name__}. AiiDA only supports PostgreSQL and SQLite.'
    raise NotImplementedError(msg)


@_in_clause_select.register(PGDialect)
def _postgresql_in_clause_select(dialect, coltype: Any, values) -> 'Select[Any]':
    """PostgreSQL: ``SELECT unnest(:array)`` — passes the entire list as 1 parameter."""
    from sqlalchemy.dialects.postgresql import ARRAY

    unnest_expr: Function[Any] = sa_func.unnest(type_coerce(expression=values, type_=ARRAY(item_type=coltype)))
    return select(unnest_expr)


@_in_clause_select.register(SQLiteDialect)
def _sqlite_in_clause_select(dialect, coltype: Any, values) -> 'Select[Any]':
    """SQLite: ``SELECT CAST(value AS coltype) FROM json_each(:json)`` — passes the list as 1 parameter."""
    json_each_table: TableValuedAlias = sa_func.json_each(json.dumps(list(values))).table_valued('value')
    value_col: KeyedColumnElement = json_each_table.c.value
    return select(sql_cast(expression=value_col, type_=coltype)).select_from(json_each_table)


def _create_smarter_in_clause(session: 'Session', column, values) -> 'ColumnElement[bool]':
    """Return an IN condition using database-specific functions to avoid parameter limits.

    Uses ``unnest()`` (PostgreSQL) or ``json_each()`` (SQLite) to pass large lists as a single
    parameter instead of N parameters, avoiding database parameter limits.

    For very large lists (>500k items), automatically batches into multiple OR'd conditions
    to balance query performance with memory usage and database load.

    .. note::
        The 500k batch threshold is chosen to balance several factors:

        - **Parameter limits**: Each batch uses 1 parameter. With SQLite's minimum limit of 999
          parameters, this allows up to ~500M items (999 x 500k). PostgreSQL's limit of ~65k
          parameters allows up to ~33B items (65,535 x 500k).
        - **Memory constraints**: In practice, Python memory becomes the bottleneck before
          database limits. A list of 500M items would require 4-20GB RAM before even reaching
          the database.
        - **Database performance**: Modern databases handle 500k-item arrays/JSON easily on
          typical workstations and servers.

    For example, small list (50k items)::

        WHERE column IN (SELECT unnest(:array))  -- 1 parameter

    Large list (1.5M items)::

        WHERE (
            column IN (SELECT unnest(:array_1))  -- First 500k
            OR column IN (SELECT unnest(:array_2))  -- Second 500k
            OR column IN (SELECT unnest(:array_3))  -- Remaining 500k
        )

    :param session: the SQLAlchemy session, used to detect the database dialect.
    :param column: the SQLAlchemy column to filter on.
    :param values: the list of values to match against.
    """
    assert session.bind is not None
    dialect = session.bind.dialect
    coltype: Any = column.type

    batch_threshold = 500_000

    if len(values) > batch_threshold:
        # For very large lists, batch to avoid memory/performance issues
        # Create individual IN clauses for each batch and combine with OR
        batch_in_clauses = [
            column.in_(_in_clause_select(dialect, coltype, batch).scalar_subquery())
            for _, batch in batch_iter(values, batch_threshold)
        ]
        return or_(*batch_in_clauses)

    subq = _in_clause_select(dialect, coltype, values).scalar_subquery()
    return column.in_(subq)
