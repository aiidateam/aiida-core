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

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from aiida.storage.utils import DEFAULT_IN_CLAUSE_BATCH_SIZE, MAX_COMPOUND_SELECT_TERMS, _create_smarter_in_clause

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
    """SQLite: lists > 500k are split into batches combined with ``UNION ALL`` under a single ``IN``."""
    session: Session
    column: sa.Column[int]
    session, column = sqlite_session

    values: list[int] = list(range(DEFAULT_IN_CLAUSE_BATCH_SIZE + 1))
    in_clause: ColumnElement[bool] = _create_smarter_in_clause(session=session, column=column, values=values)
    sql: str = str(in_clause.compile(bind=session.bind))

    assert sql.count('IN (SELECT') == 1
    assert sql.count('UNION ALL') == 1


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
    """Every batch of a ``UNION ALL`` clause contributes to the match, for both raw and processed values.

    The batch threshold is lowered so the batching branch runs on a handful of values instead of 500k.
    """
    monkeypatch.setattr('aiida.storage.utils.DEFAULT_IN_CLAUSE_BATCH_SIZE', 2)

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

    # Five values at a batch size of two is three batches, joined by two UNION ALL terms.
    assert sql.count('UNION ALL') == 2
    assert result == matching_ids


def test_sqlite_batching_stays_within_the_compound_select_limit(
    sqlite_session: SqliteSessionFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Past 500 batches the batch grows, since SQLite refuses a compound SELECT with more terms."""
    monkeypatch.setattr('aiida.storage.utils.DEFAULT_IN_CLAUSE_BATCH_SIZE', 1)
    session: Session
    column: sa.Column[int]
    session, column = sqlite_session

    values: list[int] = list(range(2 * MAX_COMPOUND_SELECT_TERMS))
    in_clause: ColumnElement[bool] = _create_smarter_in_clause(session=session, column=column, values=values)

    terms: int = str(in_clause.compile(bind=session.bind)).count('UNION ALL') + 1
    assert terms == MAX_COMPOUND_SELECT_TERMS

    # A compound SELECT over the limit is rejected by SQLite itself, so this also has to execute.
    assert session.execute(sa.select(column).where(in_clause)).scalars().all() == []


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
def test_psql_batches_large_lists() -> None:
    """PostgreSQL: lists > 500k are split into batches combined with ``UNION ALL`` under a single ``IN``."""
    from aiida.manage import get_manager
    from aiida.storage.psql_dos.backend import PsqlDosBackend
    from aiida.storage.psql_dos.models.node import DbNode

    storage: PsqlDosBackend = t.cast(PsqlDosBackend, get_manager().get_profile_storage())
    session: Session = storage.get_session()
    values: list[int] = list(range(DEFAULT_IN_CLAUSE_BATCH_SIZE + 1))
    in_clause: ColumnElement[bool] = _create_smarter_in_clause(session=session, column=DbNode.id, values=values)
    sql: str = str(in_clause.compile(bind=session.bind))

    assert sql.count('IN (SELECT') == 1
    assert sql.count('UNION ALL') == 1
