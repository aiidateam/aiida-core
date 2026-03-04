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
import math
import typing as t
from collections.abc import Sequence
from functools import singledispatch

from sqlalchemy import Select, select, type_coerce, union_all
from sqlalchemy import func as sa_func
from sqlalchemy.dialects.postgresql.base import PGDialect
from sqlalchemy.dialects.sqlite.base import SQLiteDialect
from sqlalchemy.engine import Dialect
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.elements import BinaryExpression, ColumnElement
from sqlalchemy.types import TypeEngine

from aiida.common.utils import batch_iter

if t.TYPE_CHECKING:
    from sqlalchemy.orm.session import Session


# NOTE: How many values a single unnest() (PostgreSQL) or json_each() (SQLite) call is meant to carry, and the
# threshold above which a list is batched at all. 500k balances memory usage with query performance. Batches are
# combined with UNION ALL, and grow past this size only where MAX_COMPOUND_SELECT_TERMS would otherwise be exceeded.
DEFAULT_IN_CLAUSE_BATCH_SIZE: t.Final[int] = 500_000

# NOTE: Caps how many batches a UNION ALL may have. SQLite refuses a compound SELECT with more terms than
# SQLITE_MAX_COMPOUND_SELECT, whose default is 500; beyond that the batches grow instead. PostgreSQL has no
# equivalent limit, so capping both dialects costs nothing and saves a dialect branch here.
MAX_COMPOUND_SELECT_TERMS: t.Final[int] = 500

T = t.TypeVar('T')


@singledispatch
def _build_select_stmt(dialect: Dialect, coltype: TypeEngine[T], values: Sequence[T]) -> Select[tuple[T]]:
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
def _build_select_stmt_psql(dialect: PGDialect, coltype: TypeEngine[T], values: Sequence[T]) -> Select[tuple[T]]:
    """PostgreSQL: ``SELECT unnest(:array)`` — passes the entire list as 1 parameter."""
    from sqlalchemy.dialects.postgresql import ARRAY

    unnest_expr = sa_func.unnest(type_coerce(expression=values, type_=ARRAY(item_type=coltype)))
    return select(unnest_expr)


@_build_select_stmt.register
def _build_select_stmt_sqlite(dialect: SQLiteDialect, coltype: TypeEngine[T], values: Sequence[T]) -> Select[tuple[T]]:
    """SQLite: ``SELECT value FROM json_each(:json)`` — passes the list as 1 parameter.

    Values are serialized through the column's bind processor so their JSON representation matches
    how they are stored; SQLite then applies the column's comparison affinity to evaluate the ``IN``.
    """
    processor = coltype.dialect_impl(dialect).bind_processor(dialect)

    def process(value: T) -> t.Any:
        return processor(value) if processor is not None and value is not None else value

    json_each_table = sa_func.json_each(json.dumps([process(value) for value in values])).table_valued('value')
    return select(json_each_table.c.value).select_from(json_each_table)


def _create_smarter_in_clause(
    session: Session, column: ColumnElement[T] | InstrumentedAttribute[T], values: Sequence[T]
) -> BinaryExpression[bool]:
    """Return an IN condition using database-specific functions to avoid parameter limits.

    Uses ``unnest()`` (PostgreSQL) or ``json_each()`` (SQLite) to pass large lists as a single
    parameter instead of N parameters, avoiding database parameter limits.

    For very large lists (>500k items), automatically batches into multiple subqueries
    combined with UNION ALL to balance query performance with memory usage and database load.

    .. note::
        The 500k batch threshold is chosen to balance several factors:

        - **Parameter limits**: Each batch uses 1 parameter and contributes one term to the
          ``UNION ALL``. Beyond 500 batches the batch grows instead, so the term count stays
          within ``SQLITE_MAX_COMPOUND_SELECT`` and the ceiling becomes the payload size of a
          single batch: ~64B items for SQLite under ``SQLITE_MAX_LENGTH``.
        - **Memory constraints**: In practice, Python memory becomes the bottleneck before
          database limits. A list of 500M items would require 4-20GB RAM before even reaching
          the database.
        - **Database performance**: Modern databases handle 500k-item arrays/JSON easily on
          typical workstations and servers.

    For example, small list (50k items)::

        WHERE column IN (SELECT unnest(:array))  -- 1 parameter

    Large list (1.5M items)::

        WHERE column IN (
            SELECT unnest(:array_1)  -- First 500k
            UNION ALL SELECT unnest(:array_2)  -- Second 500k
            UNION ALL SELECT unnest(:array_3)  -- Remaining 500k
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
    coltype: TypeEngine[T] = column.type

    if len(values) > DEFAULT_IN_CLAUSE_BATCH_SIZE:
        # PostgreSQL plans one IN over a single derived set as an index-driven nested loop,
        # where OR'd IN subqueries become hashed subplans behind a sequential scan.
        # SQLite caps how many terms that compound SELECT may have, and each batch is one of
        # them, so past MAX_COMPOUND_SELECT_TERMS the batches grow in size instead of in number.
        n_batches: int = min(MAX_COMPOUND_SELECT_TERMS, math.ceil(len(values) / DEFAULT_IN_CLAUSE_BATCH_SIZE))
        batch_size: int = math.ceil(len(values) / n_batches)
        batch_selects = [_build_select_stmt(dialect, coltype, batch) for _, batch in batch_iter(values, batch_size)]
        return column.in_(union_all(*batch_selects).scalar_subquery())

    subq = _build_select_stmt(dialect, coltype, values).scalar_subquery()
    return column.in_(subq)
