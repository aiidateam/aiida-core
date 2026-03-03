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
from typing import TYPE_CHECKING, Any, Sequence

from sqlalchemy import Select, or_, select, type_coerce
from sqlalchemy import cast as sql_cast
from sqlalchemy import func as sa_func
from sqlalchemy.dialects.postgresql.base import PGDialect
from sqlalchemy.dialects.sqlite.base import SQLiteDialect
from sqlalchemy.engine import Dialect
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.types import TypeEngine

from aiida.common.utils import batch_iter

if TYPE_CHECKING:
    from sqlalchemy.orm.session import Session


# NOTE: Controls how many values are passed to a single unnest() (PostgreSQL) or json_each() (SQLite) call.
# For very large lists, multiple batches are combined with OR. 500k balances memory usage with query performance.
IN_CLAUSE_BATCH_SIZE: int = 500_000


@singledispatch
def _build_select_stmt(dialect: Dialect, coltype: TypeEngine[Any], values: Sequence[Any]) -> Select[Any]:
    """Return a SELECT statement over ``values`` appropriate for the given dialect.

    Dispatches to the dialect-specific implementation via :func:`singledispatch`.

    :param dialect: The SQLAlchemy dialect (e.g., PostgreSQL, SQLite).
    :param coltype: The SQLAlchemy type of the column being filtered.
    :param values: The sequence of values to match against.
    :return: A SELECT statement that can be used as a subquery.
    """
    msg = f'Unsupported database dialect: {type(dialect).__name__}. AiiDA only supports PostgreSQL and SQLite.'
    raise NotImplementedError(msg)


@_build_select_stmt.register
def _build_select_stmt_psql(dialect: PGDialect, coltype: TypeEngine[Any], values: Sequence[Any]) -> Select[Any]:
    """PostgreSQL: ``SELECT unnest(:array)`` — passes the entire list as 1 parameter."""
    from sqlalchemy.dialects.postgresql import ARRAY

    unnest_expr = sa_func.unnest(type_coerce(expression=values, type_=ARRAY(item_type=coltype)))
    return select(unnest_expr)


@_build_select_stmt.register
def _build_select_stmt_sqlite(dialect: SQLiteDialect, coltype: TypeEngine[Any], values: Sequence[Any]) -> Select[Any]:
    """SQLite: ``SELECT CAST(value AS coltype) FROM json_each(:json)`` — passes the list as 1 parameter."""
    json_each_table = sa_func.json_each(json.dumps(list(values))).table_valued('value')
    value_col = json_each_table.c.value
    return select(sql_cast(expression=value_col, type_=coltype)).select_from(json_each_table)


def _create_smarter_in_clause(
    session: 'Session', column: ColumnElement[Any], values: Sequence[Any]
) -> ColumnElement[bool]:
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

    :param session: The SQLAlchemy session, used to detect the database dialect.
    :param column: The SQLAlchemy column to filter on.
    :param values: The sequence of values to match against.
    :return: A SQLAlchemy expression representing the IN clause.
    """
    if session.bind is None:
        msg = 'Session is not bound to an engine; cannot determine database dialect.'
        raise RuntimeError(msg)
    dialect: Dialect = session.bind.dialect
    coltype: TypeEngine[Any] = column.type

    if len(values) > IN_CLAUSE_BATCH_SIZE:
        # For very large lists, batch to avoid memory/performance issues
        # Create individual IN clauses for each batch and combine with OR
        batch_in_clauses = [
            column.in_(_build_select_stmt(dialect, coltype, batch).scalar_subquery())
            for _, batch in batch_iter(values, IN_CLAUSE_BATCH_SIZE)
        ]
        return or_(*batch_in_clauses)

    subq = _build_select_stmt(dialect, coltype, values).scalar_subquery()
    return column.in_(subq)
