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

import contextlib
import json
import sqlite3
import sys
import typing as t
from collections.abc import Sequence
from functools import cache, singledispatch

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


# NOTE: The smallest number of values one payload carries. Larger lists are split into batches of this size,
# which grow past it only where the dialect cannot combine that many.
MIN_IN_CLAUSE_BATCH_SIZE: t.Final[int] = 500_000

# An OR chain of the subqueries SQLAlchemy renders parses four levels deeper than its term count, measured
# over SQLITE_MAX_EXPR_DEPTH 20 to 10000 on SQLite 3.45 to 3.53, across uv, Ubuntu and conda-forge builds.
# The fourth level is the ``AS anon_N`` alias, so the figure tracks SQLAlchemy's rendering as much as SQLite;
# a query nesting the chain further has less room. A wrong figure on another build turns
# ``test_sqlite_batch_limit_matches_the_expression_depth`` red.
_SQLITE_OR_CHAIN_DEPTH_OVERHEAD: t.Final[int] = 4

# SQLITE_MAX_EXPR_DEPTH as CPython and Ubuntu build it, for where the driver cannot report the build's own.
_SQLITE_DEFAULT_EXPR_DEPTH: t.Final[int] = 1000

T = t.TypeVar('T')


@cache
def _sqlite_max_expr_depth() -> int:
    """Return ``SQLITE_MAX_EXPR_DEPTH`` for the sqlite3 build in this process.

    The limit is a compile-time constant every new connection starts from, so one throwaway connection
    answers for all of them. It varies by build, 1000 on CPython's own and Ubuntu's against 10000 on
    conda-forge's, and ``getlimit`` arrived in Python 3.11, below which the common value is assumed.
    """
    if sys.version_info < (3, 11):  # sqlite3.Connection.getlimit
        return _SQLITE_DEFAULT_EXPR_DEPTH
    with contextlib.closing(sqlite3.connect(':memory:')) as connection:
        return connection.getlimit(sqlite3.SQLITE_LIMIT_EXPR_DEPTH)


class _PsqlInClauseStrategy:
    """PostgreSQL: ``unnest()`` batches joined by ``UNION ALL`` under one ``IN``.

    Carries no dialect, since the list travels as one bound array and psycopg converts it.
    """

    @staticmethod
    def max_batches() -> int:
        """Each batch is one bind parameter, and the v3 wire protocol counts those in an int16."""
        return 65_535

    @staticmethod
    def build_select(coltype: TypeEngine[T], values: Sequence[T]) -> Select[tuple[T]]:
        """``SELECT unnest(:array)``, which passes the entire list as 1 parameter."""
        from sqlalchemy.dialects.postgresql import ARRAY

        unnest_expr = sa_func.unnest(type_coerce(expression=values, type_=ARRAY(item_type=coltype)))
        return select(unnest_expr)

    @staticmethod
    def combine(
        column: ColumnElement[T] | InstrumentedAttribute[T], batch_selects: Sequence[Select[tuple[T]]]
    ) -> ColumnElement[bool]:
        """One ``IN`` over a ``UNION ALL`` of the batches.

        A single derived set is planned as an index-driven nested loop, where ``OR``'d ``IN`` subqueries
        become hashed subplans behind a sequential scan of the outer table.
        """
        return column.in_(union_all(*batch_selects).scalar_subquery())


class _SqliteInClauseStrategy:
    """SQLite: ``json_each()`` batches ``OR``'d together.

    Carries a dialect because it serializes the values itself, ahead of the driver, so it has to
    reproduce the bind processing the driver would otherwise have done.
    """

    # Held rather than taken from the session: the bind processors it selects are the same either way,
    # and a dialect instance caches the type implementations it is asked for.
    _DIALECT: t.ClassVar[SQLiteDialect] = SQLiteDialect()

    @staticmethod
    def max_batches() -> int:
        """Each batch is one term of the OR chain, which ``SQLITE_MAX_EXPR_DEPTH`` bounds.

        SQLite reads a limit of 0 as no depth checking at all. A limit below the chain's own overhead
        still leaves room for a single batch, which is one ``IN`` and no chain.
        """
        depth: int = _sqlite_max_expr_depth()
        if depth == 0:
            return sys.maxsize
        return max(1, depth - _SQLITE_OR_CHAIN_DEPTH_OVERHEAD)

    @classmethod
    def build_select(cls, coltype: TypeEngine[T], values: Sequence[T]) -> Select[tuple[T]]:
        """``SELECT value FROM json_each(:json)``, which passes the list as 1 parameter.

        Values are serialized through the column's bind processor so their JSON representation matches
        how they are stored; SQLite then applies the column's comparison affinity to evaluate the ``IN``.
        """
        processor = coltype.dialect_impl(cls._DIALECT).bind_processor(cls._DIALECT)

        def process(value: T) -> t.Any:
            return processor(value) if processor is not None and value is not None else value

        json_each_table = sa_func.json_each(json.dumps([process(value) for value in values])).table_valued('value')
        return select(json_each_table.c.value).select_from(json_each_table)

    @staticmethod
    def combine(
        column: ColumnElement[T] | InstrumentedAttribute[T], batch_selects: Sequence[Select[tuple[T]]]
    ) -> ColumnElement[bool]:
        """One ``IN`` per batch, ``OR``'d together.

        SQLite plans this as a ``MULTI-INDEX OR`` and keeps the index lookups, so PostgreSQL's compound
        ``SELECT`` buys it nothing: the two measure within noise of each other. Both shapes are bounded, this
        one higher, since ``SQLITE_MAX_COMPOUND_SELECT`` fixes a ``UNION ALL`` at 500 terms.
        """
        return or_(*(column.in_(batch_select.scalar_subquery()) for batch_select in batch_selects))


# The two implementations above, which have to agree on all three members: the SELECT that unpacks one
# batch, the shape that joins several of them, and how many of those the dialect accepts in one clause.
_InClauseStrategy: t.TypeAlias = type[_PsqlInClauseStrategy] | type[_SqliteInClauseStrategy]


@singledispatch
def _in_clause_strategy(dialect: Dialect) -> _InClauseStrategy:
    """Return the IN-clause strategy registered for the given dialect.

    :param dialect: The SQLAlchemy dialect (e.g., PostgreSQL, SQLite).
    :return: The strategy carrying that dialect's select shape, combine shape and batch limit.
    :raises NotImplementedError: If no strategy is registered for the dialect.
    """
    msg = f'Unsupported database dialect: {type(dialect).__name__}. AiiDA only supports PostgreSQL and SQLite.'
    raise NotImplementedError(msg)


@_in_clause_strategy.register
def _in_clause_strategy_psql(dialect: PGDialect) -> _InClauseStrategy:
    return _PsqlInClauseStrategy


@_in_clause_strategy.register
def _in_clause_strategy_sqlite(dialect: SQLiteDialect) -> _InClauseStrategy:
    return _SqliteInClauseStrategy


def _create_smarter_in_clause(
    session: Session, column: ColumnElement[T] | InstrumentedAttribute[T], values: Sequence[T]
) -> ColumnElement[bool]:
    """Return an IN condition using database-specific functions to avoid parameter limits.

    Uses ``unnest()`` (PostgreSQL) or ``json_each()`` (SQLite) to pass large lists as a single
    parameter instead of N parameters, avoiding database parameter limits.

    A list within :data:`MIN_IN_CLAUSE_BATCH_SIZE` becomes a single subquery. Past it the list is
    split, and the strategy's ``combine`` joins one subquery per batch.

    :param session: The SQLAlchemy session, used to detect the database dialect.
    :param column: The SQLAlchemy column to filter on.
    :param values: The sequence of values to match against.
    :return: A SQLAlchemy expression representing the IN clause.
    :raises RuntimeError: If the session is not bound to an engine.
    :raises NotImplementedError: If the session's dialect is neither PostgreSQL nor SQLite.
    """
    if session.bind is None:
        msg = 'Session is not bound to an engine; cannot determine database dialect.'
        raise RuntimeError(msg)
    strategy: _InClauseStrategy = _in_clause_strategy(session.bind.dialect)
    coltype: TypeEngine[T] = column.type

    if len(values) > MIN_IN_CLAUSE_BATCH_SIZE:
        # Stays at MIN_IN_CLAUSE_BATCH_SIZE until the batches would outnumber what the dialect can combine.
        batch_size: int = max(MIN_IN_CLAUSE_BATCH_SIZE, -(-len(values) // strategy.max_batches()))
        batch_selects: list[Select[tuple[T]]] = [
            strategy.build_select(coltype=coltype, values=batch) for _, batch in batch_iter(values, batch_size)
        ]
        return strategy.combine(column=column, batch_selects=batch_selects)

    subq = strategy.build_select(coltype=coltype, values=values).scalar_subquery()
    return column.in_(subq)
