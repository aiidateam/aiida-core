###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for :mod:`aiida.storage.utils`."""

import typing as t
from collections.abc import Generator
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from aiida.storage.utils import IN_CLAUSE_BATCH_SIZE_FLOOR, _create_smarter_in_clause, _max_batches

# Type alias for the fixture's yielded value
SqliteSessionFixture = tuple[Session, sa.Column[int]]


@pytest.fixture
def sqlite_session() -> Generator[SqliteSessionFixture, None, None]:
    """In-memory SQLite session with a simple integer table."""
    engine: sa.Engine = sa.create_engine(url='sqlite://')
    metadata: sa.MetaData = sa.MetaData()
    table: sa.Table = sa.Table(
        'items',
        metadata,
        sa.Column(name='id', type_=sa.Integer, primary_key=True),
    )
    metadata.create_all(bind=engine)
    with Session(bind=engine) as session:
        yield session, table.c.id


@pytest.mark.parametrize(
    'n_values',
    [pytest.param(2, id='unbatched'), pytest.param(5, id='batched')],
)
def test_unsupported_dialect_is_reported_the_same_on_both_paths(monkeypatch: pytest.MonkeyPatch, n_values: int) -> None:
    """A dialect with no implementation registered names itself and the supported backends.

    The batched path reaches ``_max_batches`` before ``_build_select_stmt``, so both have to say it.
    """
    monkeypatch.setattr('aiida.storage.utils.IN_CLAUSE_BATCH_SIZE_FLOOR', 2)

    class UnregisteredDialect:
        pass

    session = SimpleNamespace(bind=SimpleNamespace(dialect=UnregisteredDialect()))
    table: sa.Table = sa.Table('items', sa.MetaData(), sa.Column(name='id', type_=sa.Integer, primary_key=True))

    with pytest.raises(NotImplementedError, match=r'UnregisteredDialect.*only supports PostgreSQL and SQLite'):
        _create_smarter_in_clause(session=session, column=table.c.id, values=list(range(n_values)))


def test_session_without_a_bind_is_reported() -> None:
    """A session with no engine cannot be dispatched on, and says so rather than raising AttributeError."""
    table: sa.Table = sa.Table('items', sa.MetaData(), sa.Column(name='id', type_=sa.Integer, primary_key=True))

    with pytest.raises(RuntimeError, match='not bound to an engine'):
        _create_smarter_in_clause(session=SimpleNamespace(bind=None), column=table.c.id, values=[1, 2])


def test_sqlite_uses_json_each(sqlite_session: SqliteSessionFixture) -> None:
    """SQLite: generates ``id IN (SELECT CAST(value AS INTEGER) FROM json_each(?))``."""
    session: Session
    column: sa.Column[int]
    session, column = sqlite_session

    in_clause: ColumnElement[bool] = _create_smarter_in_clause(session=session, column=column, values=[1, 2])
    sql: str = str(in_clause.compile(bind=session.bind))

    assert 'json_each' in sql
    assert 'IN (SELECT' in sql


def test_sqlite_batches_large_lists(sqlite_session: SqliteSessionFixture) -> None:
    """SQLite: a list past the batch size renders as ``OR``'d ``IN`` clauses, one per batch."""
    session: Session
    column: sa.Column[int]
    session, column = sqlite_session

    values: list[int] = list(range(IN_CLAUSE_BATCH_SIZE_FLOOR + 1))
    in_clause: ColumnElement[bool] = _create_smarter_in_clause(session=session, column=column, values=values)
    sql: str = str(in_clause.compile(bind=session.bind))

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
    monkeypatch.setattr('aiida.storage.utils.IN_CLAUSE_BATCH_SIZE_FLOOR', 2)

    engine: sa.Engine = sa.create_engine(url='sqlite://')
    metadata: sa.MetaData = sa.MetaData()
    table: sa.Table = sa.Table(
        'items',
        metadata,
        sa.Column(name='id', type_=sa.Integer, primary_key=True),
        sa.Column(name='ctime', type_=sa.DateTime(timezone=True)),
    )
    metadata.create_all(bind=engine)

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


def test_sqlite_batches_grow_rather_than_exceed_the_or_limit(
    sqlite_session: SqliteSessionFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A list needing more batches than SQLite can OR together grows them instead of adding more.

    997 is one past the 996 terms a default ``SQLITE_MAX_EXPR_DEPTH`` of 1000 allows, so an
    unbatched-out clause is rejected by SQLite itself. The value is hardcoded rather than read
    from ``_max_batches``, so that mis-registering a dialect's limit fails here too.
    """
    monkeypatch.setattr('aiida.storage.utils.IN_CLAUSE_BATCH_SIZE_FLOOR', 1)
    session: Session
    column: sa.Column[int]
    session, column = sqlite_session

    over_the_limit: int = 997
    in_clause: ColumnElement[bool] = _create_smarter_in_clause(
        session=session, column=column, values=list(range(over_the_limit))
    )

    n_clauses: int = str(in_clause.compile(bind=session.bind)).count('IN (SELECT')
    assert 1 < n_clauses < over_the_limit

    # Rows for every value, so a grown batch that drops some of them shows up in the result and not
    # merely in the term count. SQLite also rejects an OR chain past its depth limit, so this has to
    # execute at all for the growth to be what saved it.
    session.execute(column.table.insert(), [{'id': value} for value in range(over_the_limit)])
    session.commit()
    matched = session.execute(sa.select(column).where(in_clause)).scalars().all()

    assert matched == list(range(over_the_limit))


def test_sqlite_in_clause_datetime_values() -> None:
    """SQLite: datetime values are serialized using the column bind processor."""
    engine: sa.Engine = sa.create_engine(url='sqlite://')
    metadata: sa.MetaData = sa.MetaData()
    table: sa.Table = sa.Table(
        'items',
        metadata,
        sa.Column(name='id', type_=sa.Integer, primary_key=True),
        sa.Column(name='ctime', type_=sa.DateTime(timezone=True)),
    )
    metadata.create_all(bind=engine)

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
@pytest.mark.usefixtures('aiida_profile_clean')
def test_psql_uses_unnest() -> None:
    """PostgreSQL: generates ``id IN (SELECT unnest(ARRAY[...]::integer[]))``."""
    from aiida.manage import get_manager
    from aiida.storage.psql_dos.backend import PsqlDosBackend
    from aiida.storage.psql_dos.models.node import DbNode

    storage: PsqlDosBackend = t.cast(PsqlDosBackend, get_manager().get_profile_storage())
    session: Session = storage.get_session()
    in_clause: ColumnElement[bool] = _create_smarter_in_clause(session=session, column=DbNode.id, values=[1, 2])
    sql: str = str(in_clause.compile(bind=session.bind))

    assert 'unnest' in sql
    assert 'IN (SELECT' in sql


@pytest.mark.requires_psql
@pytest.mark.usefixtures('aiida_profile_clean')
def test_psql_batch_limit_matches_the_wire_protocol() -> None:
    """``_max_batches`` for PostgreSQL has to equal what the driver will actually send.

    Each batch costs one bind parameter, so the limit is only right if a statement with that many
    is accepted and one more is refused. Checked against a flat ``IN`` list, since expression
    nesting hits the stack depth limit first.
    """
    from aiida.manage import get_manager
    from aiida.storage.psql_dos.backend import PsqlDosBackend

    storage: PsqlDosBackend = t.cast(PsqlDosBackend, get_manager().get_profile_storage())
    session: Session = storage.get_session()
    limit: int = _max_batches(session.bind.dialect)

    def send(n_params: int) -> None:
        placeholders = ', '.join([f':p{i}' for i in range(n_params)])
        statement = sa.text(f'SELECT 1 WHERE -1 IN ({placeholders})')
        session.execute(statement, {f'p{i}': i for i in range(n_params)})

    send(limit)
    with pytest.raises(sa.exc.DBAPIError):
        send(limit + 1)
    session.rollback()


@pytest.mark.requires_psql
@pytest.mark.usefixtures('aiida_profile_clean')
def test_psql_batches_grow_rather_than_exceed_the_batch_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    """The growth is dialect-independent, so PostgreSQL takes it too, with its own limit."""
    from aiida.manage import get_manager
    from aiida.storage.psql_dos.backend import PsqlDosBackend
    from aiida.storage.psql_dos.models.node import DbNode
    from tests.utils.nodes import create_int_nodes

    monkeypatch.setattr('aiida.storage.utils.IN_CLAUSE_BATCH_SIZE_FLOOR', 2)
    monkeypatch.setattr('aiida.storage.utils._max_batches', lambda dialect: 3)

    storage: PsqlDosBackend = t.cast(PsqlDosBackend, get_manager().get_profile_storage())
    session: Session = storage.get_session()
    pks: list[int] = create_int_nodes(10)
    in_clause: ColumnElement[bool] = _create_smarter_in_clause(session=session, column=DbNode.id, values=pks)

    # Ten values capped at three batches is four per batch, so three terms rather than five.
    assert str(in_clause.compile(bind=session.bind)).count('UNION ALL') == 2

    # Executed, so that a clause of the right shape which drops a batch still fails here.
    matched = session.execute(sa.select(DbNode.id).where(in_clause)).scalars().all()
    assert sorted(matched) == sorted(pks)


@pytest.mark.requires_psql
@pytest.mark.usefixtures('aiida_profile_clean')
def test_psql_batches_large_lists() -> None:
    """PostgreSQL: a list past the batch size renders as one ``IN`` over a ``UNION ALL`` of the batches."""
    from aiida.manage import get_manager
    from aiida.storage.psql_dos.backend import PsqlDosBackend
    from aiida.storage.psql_dos.models.node import DbNode

    storage: PsqlDosBackend = t.cast(PsqlDosBackend, get_manager().get_profile_storage())
    session: Session = storage.get_session()
    values: list[int] = list(range(IN_CLAUSE_BATCH_SIZE_FLOOR + 1))
    in_clause: ColumnElement[bool] = _create_smarter_in_clause(session=session, column=DbNode.id, values=values)
    sql: str = str(in_clause.compile(bind=session.bind))

    assert sql.count('IN (SELECT') == 1
    assert sql.count('UNION ALL') == 1
