###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for :mod:`aiida.storage.utils`."""

import sys
import typing as t
from collections.abc import Generator
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from aiida.storage.utils import (
    MIN_IN_CLAUSE_BATCH_SIZE,
    _create_smarter_in_clause,
    _in_clause_strategy,
    _PsqlInClauseStrategy,
    _sqlite_max_expr_depth,
    _SqliteInClauseStrategy,
)

SEEDED_ROWS = 10


class InClauseSession(t.NamedTuple):
    """A session and the column to filter on."""

    session: Session
    column: t.Any


class SeededSession(t.NamedTuple):
    """A session, the column to filter on, and the ids seeded into it."""

    session: Session
    column: t.Any
    ids: list[int]


def lower_max_batches(monkeypatch: pytest.MonkeyPatch, limit: int) -> None:
    """Lower every dialect's batch limit, so a branch bounded by it is reached with few values."""
    for strategy_class in (_PsqlInClauseStrategy, _SqliteInClauseStrategy):
        monkeypatch.setattr(strategy_class, 'max_batches', staticmethod(lambda limit=limit: limit))


def make_sqlite_table(*extra_columns: sa.Column) -> tuple[sa.Engine, sa.Table]:
    """Return an in-memory engine and a created ``items`` table with an integer ``id`` and any extras."""
    engine: sa.Engine = sa.create_engine(url='sqlite://')
    metadata: sa.MetaData = sa.MetaData()
    table: sa.Table = sa.Table(
        'items', metadata, sa.Column(name='id', type_=sa.Integer, primary_key=True), *extra_columns
    )
    metadata.create_all(bind=engine)
    return engine, table


@pytest.fixture
def sqlite_session() -> Generator[InClauseSession, None, None]:
    """In-memory SQLite session with a simple integer table."""
    engine: sa.Engine
    table: sa.Table
    engine, table = make_sqlite_table()
    with Session(bind=engine) as session:
        yield InClauseSession(session=session, column=table.c.id)


@pytest.fixture
def psql_session(aiida_profile_clean) -> InClauseSession:
    """Session on the profile's PostgreSQL storage, filtering on ``DbNode.id``."""
    from aiida.manage import get_manager
    from aiida.storage.psql_dos.models.node import DbNode

    return InClauseSession(session=get_manager().get_profile_storage().get_session(), column=DbNode.id)


@pytest.fixture(
    params=[
        pytest.param('sqlite', id='sqlite'),
        pytest.param('psql', id='psql', marks=pytest.mark.requires_psql),
    ]
)
def seeded_session(request: pytest.FixtureRequest) -> Generator[SeededSession, None, None]:
    """Session over a table holding ``SEEDED_ROWS`` integer ids, on the requested backend."""
    if request.param == 'psql':
        from tests.utils.nodes import create_int_nodes

        psql: InClauseSession = request.getfixturevalue('psql_session')
        yield SeededSession(session=psql.session, column=psql.column, ids=create_int_nodes(SEEDED_ROWS))
        return

    engine: sa.Engine
    table: sa.Table
    engine, table = make_sqlite_table()
    ids: list[int] = list(range(1, SEEDED_ROWS + 1))
    with Session(bind=engine) as session:
        session.execute(table.insert(), [{'id': identifier} for identifier in ids])
        session.commit()
        yield SeededSession(session=session, column=table.c.id, ids=ids)


def test_unsupported_dialect_is_reported() -> None:
    """A dialect with no strategy registered names itself and the supported backends."""

    class UnregisteredDialect:
        pass

    session = SimpleNamespace(bind=SimpleNamespace(dialect=UnregisteredDialect()))
    table: sa.Table = sa.Table('items', sa.MetaData(), sa.Column(name='id', type_=sa.Integer, primary_key=True))

    with pytest.raises(NotImplementedError, match=r'UnregisteredDialect.*only supports PostgreSQL and SQLite'):
        _create_smarter_in_clause(session=session, column=table.c.id, values=[1, 2])


def test_batches_grow_rather_than_exceed_the_limit(
    seeded_session: SeededSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A list needing more batches than the dialect can combine grows them instead of adding more.

    Nothing here is dialect-specific but the limit itself, so both backends run the same assertions.
    Each batch travels as one bind parameter on either dialect, which is what counts the batches
    without depending on the shape they are combined in.
    """
    monkeypatch.setattr('aiida.storage.utils.MIN_IN_CLAUSE_BATCH_SIZE', 2)
    lower_max_batches(monkeypatch, 3)

    seeded: SeededSession = seeded_session
    in_clause: ColumnElement[bool] = _create_smarter_in_clause(
        session=seeded.session, column=seeded.column, values=seeded.ids
    )

    # Ten values capped at three batches is four per batch, so three batches rather than five.
    assert len(in_clause.compile(bind=seeded.session.bind).params) == 3

    # Executed, so that a clause of the right shape which drops a batch still fails here.
    matched = seeded.session.execute(sa.select(seeded.column).where(in_clause)).scalars().all()
    assert sorted(matched) == sorted(seeded.ids)


def test_sqlite_uses_json_each(sqlite_session: InClauseSession) -> None:
    """SQLite: generates ``id IN (SELECT CAST(value AS INTEGER) FROM json_each(?))``."""
    in_clause: ColumnElement[bool] = _create_smarter_in_clause(
        session=sqlite_session.session, column=sqlite_session.column, values=[1, 2]
    )
    sql: str = str(in_clause.compile(bind=sqlite_session.session.bind))

    assert 'json_each' in sql
    assert 'IN (SELECT' in sql


def test_sqlite_batches_large_lists(sqlite_session: InClauseSession) -> None:
    """SQLite: a list past the batch size renders as ``OR``'d ``IN`` clauses, one per batch."""
    values: list[int] = list(range(MIN_IN_CLAUSE_BATCH_SIZE + 1))
    in_clause: ColumnElement[bool] = _create_smarter_in_clause(
        session=sqlite_session.session, column=sqlite_session.column, values=values
    )
    sql: str = str(in_clause.compile(bind=sqlite_session.session.bind))

    assert sql.count('IN (SELECT') == 2
    assert ' OR ' in sql


@pytest.mark.parametrize(
    'column_name, matching_ids',
    [
        pytest.param('id', [1, 3, 5, 7, 9], id='integer'),
        pytest.param('ctime', [2, 4, 6, 8, 10], id='datetime'),
    ],
)
def test_sqlite_batched_in_clause_matches_every_batch(
    monkeypatch: pytest.MonkeyPatch, column_name: str, matching_ids: list[int]
) -> None:
    """Every batch contributes to the match, for both raw and bind-processed values.

    The batch threshold is lowered so the batching branch runs on a handful of values instead of 500k.
    """
    monkeypatch.setattr('aiida.storage.utils.MIN_IN_CLAUSE_BATCH_SIZE', 2)

    engine: sa.Engine
    table: sa.Table
    engine, table = make_sqlite_table(sa.Column(name='ctime', type_=sa.DateTime(timezone=True)))

    rows = [
        {'id': identifier, 'ctime': datetime(2026, 1, identifier, tzinfo=timezone.utc)} for identifier in range(1, 11)
    ]

    with Session(bind=engine) as session:
        session.execute(table.insert(), rows)
        session.commit()

        column = table.c[column_name]
        values = [row[column_name] for row in rows if row['id'] in matching_ids]
        in_clause: ColumnElement[bool] = _create_smarter_in_clause(session=session, column=column, values=values)
        sql: str = str(in_clause.compile(bind=engine))
        result = session.execute(sa.select(table.c.id).where(in_clause)).scalars().all()

    # Five values at a batch size of two is three batches, hence three IN clauses.
    assert sql.count('IN (SELECT') == 3
    assert result == matching_ids


def test_sqlite_batch_limit_matches_the_expression_depth(
    sqlite_session: InClauseSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``max_batches`` for SQLite has to equal the longest OR chain the build actually accepts.

    Each batch costs one term of the chain, and ``SQLITE_MAX_EXPR_DEPTH`` bounds it. That bound is
    build-dependent, so the expected number is read rather than written out, and what pins it is
    SQLite: a chain of that many terms has to execute and one more has to be refused.
    """
    limit: int = _in_clause_strategy(sqlite_session.session.bind.dialect).max_batches()

    # One value per batch, and no cap on their number, so the term count is the value count.
    monkeypatch.setattr('aiida.storage.utils.MIN_IN_CLAUSE_BATCH_SIZE', 1)
    lower_max_batches(monkeypatch, 10**9)

    def send(n_terms: int) -> None:
        in_clause: ColumnElement[bool] = _create_smarter_in_clause(
            session=sqlite_session.session, column=sqlite_session.column, values=list(range(n_terms))
        )
        assert str(in_clause.compile(bind=sqlite_session.session.bind)).count('IN (SELECT') == n_terms
        sqlite_session.session.execute(sa.select(sqlite_session.column).where(in_clause)).all()

    send(limit)
    with pytest.raises(sa.exc.OperationalError, match='Expression tree is too large'):
        send(limit + 1)
    sqlite_session.session.rollback()


def test_sqlite_expr_depth_falls_back_where_the_driver_cannot_report_it(monkeypatch: pytest.MonkeyPatch) -> None:
    """Python 3.10 has no ``sqlite3.Connection.getlimit``, so the common build value is assumed.

    Exercised explicitly because the interpreter running the suite may well have ``getlimit``, leaving
    the branch that every 3.10 job takes unverified. A sentinel stands in for the default.
    """
    sentinel: int = 4242
    _sqlite_max_expr_depth.cache_clear()
    monkeypatch.setattr('aiida.storage.utils._SQLITE_DEFAULT_EXPR_DEPTH', sentinel)
    monkeypatch.setattr(sys, 'version_info', (3, 10, 18, 'final', 0))
    try:
        assert _sqlite_max_expr_depth() == sentinel
    finally:
        _sqlite_max_expr_depth.cache_clear()


@pytest.mark.parametrize(
    'depth, expected',
    [
        pytest.param(0, sys.maxsize, id='zero-is-unlimited'),
        pytest.param(1, 1, id='below-the-overhead'),
        pytest.param(4, 1, id='exactly-the-overhead'),
        pytest.param(5, 1, id='one-above-the-overhead'),
        pytest.param(1000, 996, id='common-build'),
    ],
)
def test_sqlite_max_batches_stays_usable_at_degenerate_depths(
    sqlite_session: InClauseSession, monkeypatch: pytest.MonkeyPatch, depth: int, expected: int
) -> None:
    """A depth at or below the chain overhead still yields a usable batch count.

    Subtracting the overhead outright gave 0 at a depth of 4, and the batch-size division then raised
    ``ZeroDivisionError``. SQLite also reads a depth of 0 as unbounded rather than as a tiny limit.
    """
    monkeypatch.setattr('aiida.storage.utils._sqlite_max_expr_depth', lambda: depth)
    monkeypatch.setattr('aiida.storage.utils.MIN_IN_CLAUSE_BATCH_SIZE', 2)

    strategy = _in_clause_strategy(sqlite_session.session.bind.dialect)
    assert strategy.max_batches() == expected

    # The batch-size division reads max_batches, so it has to survive the degenerate value too.
    in_clause: ColumnElement[bool] = _create_smarter_in_clause(
        session=sqlite_session.session, column=sqlite_session.column, values=[1, 2, 3]
    )
    assert sqlite_session.session.execute(sa.select(sqlite_session.column).where(in_clause)).scalars().all() == []


def test_sqlite_in_clause_datetime_values() -> None:
    """SQLite: datetime values are serialized using the column bind processor."""
    engine: sa.Engine
    table: sa.Table
    engine, table = make_sqlite_table(sa.Column(name='ctime', type_=sa.DateTime(timezone=True)))

    timestamp = datetime(2026, 7, 23, 12, 0, 0, 123456, tzinfo=timezone.utc)
    with Session(bind=engine) as session:
        session.execute(table.insert().values(id=1, ctime=timestamp))
        session.execute(table.insert().values(id=2, ctime=datetime(2026, 7, 24, tzinfo=timezone.utc)))
        session.commit()

        in_clause: ColumnElement[bool] = _create_smarter_in_clause(
            session=session, column=table.c.ctime, values=[timestamp]
        )
        result = session.execute(sa.select(table.c.id).where(in_clause)).scalars().all()

    assert result == [1]


@pytest.mark.requires_psql
def test_psql_uses_unnest(psql_session: InClauseSession) -> None:
    """PostgreSQL: generates ``id IN (SELECT unnest(ARRAY[...]::integer[]))``."""
    in_clause: ColumnElement[bool] = _create_smarter_in_clause(
        session=psql_session.session, column=psql_session.column, values=[1, 2]
    )
    sql: str = str(in_clause.compile(bind=psql_session.session.bind))

    assert 'unnest' in sql
    assert 'IN (SELECT' in sql


@pytest.mark.requires_psql
def test_psql_batch_limit_matches_the_wire_protocol(psql_session: InClauseSession) -> None:
    """``max_batches`` for PostgreSQL has to equal what the driver will actually send.

    Each batch costs one bind parameter, so the limit is only right if a statement with that many
    is accepted and one more is refused. Checked against a flat ``IN`` list, since expression
    nesting hits the stack depth limit first.
    """
    limit: int = _in_clause_strategy(psql_session.session.bind.dialect).max_batches()

    def send(n_params: int) -> None:
        placeholders = ', '.join([f':p{i}' for i in range(n_params)])
        statement = sa.text(f'SELECT 1 WHERE -1 IN ({placeholders})')
        psql_session.session.execute(statement, {f'p{i}': i for i in range(n_params)})

    send(limit)
    with pytest.raises(sa.exc.DBAPIError):
        send(limit + 1)
    psql_session.session.rollback()


@pytest.mark.requires_psql
def test_psql_batches_large_lists(psql_session: InClauseSession) -> None:
    """PostgreSQL: a list past the batch size renders as one ``IN`` over a ``UNION ALL`` of the batches."""
    values: list[int] = list(range(MIN_IN_CLAUSE_BATCH_SIZE + 1))
    in_clause: ColumnElement[bool] = _create_smarter_in_clause(
        session=psql_session.session, column=psql_session.column, values=values
    )
    sql: str = str(in_clause.compile(bind=psql_session.session.bind))

    assert sql.count('IN (SELECT') == 1
    assert sql.count('UNION ALL') == 1
