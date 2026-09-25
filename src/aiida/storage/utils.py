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

from sqlalchemy import Select, or_, select, type_coerce, union_all
from sqlalchemy import func as sa_func
from sqlalchemy.dialects.postgresql.base import PGDialect
from sqlalchemy.dialects.sqlite.base import SQLiteDialect
from sqlalchemy.engine import Dialect
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.types import TypeEngine

from aiida.common.utils import batch_iter

if t.TYPE_CHECKING:
    from sqlalchemy.orm.session import Session


# NOTE: The smallest number of values one unnest() (PostgreSQL) or json_each() (SQLite) payload carries, which
# is what bounds a single bind parameter. Larger lists are split into batches of
# this size, combined per dialect by `_combine_batches`, and `_max_batches` grows them past it where a dialect
# cannot combine that many. 500k balances memory usage with query performance.
IN_CLAUSE_BATCH_SIZE_FLOOR: t.Final[int] = 500_000

T = t.TypeVar('T')


@singledispatch
def _build_select_stmt(dialect: Dialect, coltype: TypeEngine[T], values: Sequence[T]) -> Select[tuple[T]]:
    """Return a SELECT statement over ``values`` appropriate for the given dialect.

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


@singledispatch
def _combine_batches(
    dialect: Dialect, column: ColumnElement[T] | InstrumentedAttribute[T], batch_selects: Sequence[Select[tuple[T]]]
) -> ColumnElement[bool]:
    """Return one IN condition over several batch SELECTs, in the shape the dialect's planner handles best.

    An unsupported dialect is rejected by :func:`_build_select_stmt`, which runs first, so this
    fallback is reached only by a backend that registers a select builder and no combinator.

    :param dialect: The SQLAlchemy dialect (e.g., PostgreSQL, SQLite).
    :param column: The SQLAlchemy column to filter on.
    :param batch_selects: One SELECT per batch, as built by :func:`_build_select_stmt`.
    :return: A SQLAlchemy expression matching ``column`` against the union of all batches.
    """
    msg = f'No IN-clause batch combinator is registered for {type(dialect).__name__}.'
    raise NotImplementedError(msg)


@_combine_batches.register
def _combine_batches_psql(
    dialect: PGDialect, column: ColumnElement[T] | InstrumentedAttribute[T], batch_selects: Sequence[Select[tuple[T]]]
) -> ColumnElement[bool]:
    """PostgreSQL: one ``IN`` over a ``UNION ALL`` of the batches.

    A single derived set is planned as an index-driven nested loop, where OR'd IN subqueries
    become hashed subplans behind a sequential scan of the outer table. For 1.5M items::

        WHERE column IN (
            SELECT unnest(:array_1)  -- First 500k
            UNION ALL SELECT unnest(:array_2)  -- Second 500k
            UNION ALL SELECT unnest(:array_3)  -- Remaining 500k
        )
    """
    return column.in_(union_all(*batch_selects).scalar_subquery())


@_combine_batches.register
def _combine_batches_sqlite(
    dialect: SQLiteDialect,
    column: ColumnElement[T] | InstrumentedAttribute[T],
    batch_selects: Sequence[Select[tuple[T]]],
) -> ColumnElement[bool]:
    """SQLite: one ``IN`` per batch, ``OR``'d together.

    SQLite plans this as a MULTI-INDEX OR and keeps the index lookups, so PostgreSQL's compound
    SELECT buys it nothing: the two measure within noise of each other. Both shapes are bounded, this one
    higher: an OR chain is bounded by ``SQLITE_MAX_EXPR_DEPTH``, four short of its value and so
    996 batches on a default build, against the 500 that ``SQLITE_MAX_COMPOUND_SELECT`` fixes for
    a ``UNION ALL``. For 1.5M items::

        WHERE (
            column IN (SELECT value FROM json_each(:json_1))  -- First 500k
            OR column IN (SELECT value FROM json_each(:json_2))  -- Second 500k
            OR column IN (SELECT value FROM json_each(:json_3))  -- Remaining 500k
        )
    """
    return or_(*(column.in_(batch_select.scalar_subquery()) for batch_select in batch_selects))


@singledispatch
def _max_batches(dialect: Dialect) -> int:
    """Return how many batches the dialect can combine into one clause.

    Reached before :func:`_build_select_stmt` on the batching path, so an unsupported dialect has
    to fail here with the same message it would give on the unbatched one.

    :param dialect: The SQLAlchemy dialect (e.g., PostgreSQL, SQLite).
    :return: The largest number of batches :func:`_combine_batches` can join for this dialect.
    """
    msg = f'Unsupported database dialect: {type(dialect).__name__}. AiiDA only supports PostgreSQL and SQLite.'
    raise NotImplementedError(msg)


@_max_batches.register
def _max_batches_psql(dialect: PGDialect) -> int:
    """Each batch is one bind parameter, and the v3 wire protocol counts those in an int16."""
    return 65_535


@_max_batches.register
def _max_batches_sqlite(dialect: SQLiteDialect) -> int:
    """Each batch is one term of the OR chain, which ``SQLITE_MAX_EXPR_DEPTH`` bounds.

    That limit reads 1000 on every build tested: uv-installed CPython 3.10 through 3.14 and Ubuntu
    24.04's own, over SQLite 3.45 to 3.53. This clause shape reaches 996 terms within it. Hardcoded
    because the limit cannot be read before Python 3.11; a build that lowers it fails earlier anyway.
    """
    return 996


def _create_smarter_in_clause(
    session: Session, column: ColumnElement[T] | InstrumentedAttribute[T], values: Sequence[T]
) -> ColumnElement[bool]:
    """Return an IN condition using database-specific functions to avoid parameter limits.

    Uses ``unnest()`` (PostgreSQL) or ``json_each()`` (SQLite) to pass large lists as a single
    parameter instead of N parameters, avoiding database parameter limits.

    For very large lists (>500k items), automatically batches into multiple subqueries, which
    :func:`_combine_batches` joins in the shape the dialect's planner handles best.

    .. note::
        The 500k batch size is chosen to balance several factors:

        - **Payload size**: A batch travels as one bind parameter, which SQLite caps via
          ``SQLITE_MAX_LENGTH`` at ~128M items. Batching keeps each payload far under that, and
          holds SQLite's ``json.dumps`` to one batch at a time. It costs memory on PostgreSQL
          instead, where an unbatched array is passed through without a copy.
        - **Batch count**: Each batch costs a bind parameter on PostgreSQL and a term of the OR
          chain on SQLite, both capped. Past ~498M items on SQLite and ~33B on PostgreSQL the
          batches grow instead of multiplying, so neither bound is reached by a list that fits in
          memory.
        - **Database performance**: Modern databases handle 500k-item arrays/JSON easily on
          typical workstations and servers.

    A list within the batch size becomes a single subquery, on PostgreSQL::

        WHERE column IN (SELECT unnest(:array))  -- 1 parameter

    Past it, :func:`_combine_batches` joins one subquery per batch.

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

    if len(values) > IN_CLAUSE_BATCH_SIZE_FLOOR:
        # Stays at IN_CLAUSE_BATCH_SIZE_FLOOR until the batches would outnumber what the dialect can combine.
        batch_size = max(IN_CLAUSE_BATCH_SIZE_FLOOR, math.ceil(len(values) / _max_batches(dialect)))
        batch_selects: list[Select[tuple[T]]] = [
            _build_select_stmt(dialect, coltype, batch) for _, batch in batch_iter(values, batch_size)
        ]
        return _combine_batches(dialect, column, batch_selects)

    subq = _build_select_stmt(dialect, coltype, values).scalar_subquery()
    return column.in_(subq)
