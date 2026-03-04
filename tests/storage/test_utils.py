###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for :mod:`aiida.storage.utils`."""

from collections.abc import Generator
from typing import cast

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from aiida.storage.utils import IN_CLAUSE_BATCH_SIZE, _create_smarter_in_clause

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
    """SQLite: lists > 500k are split into OR'd batches."""
    session: Session
    column: sa.Column[int]
    session, column = sqlite_session

    values: list[int] = list(range(IN_CLAUSE_BATCH_SIZE + 1))
    in_clause: ColumnElement[bool] = _create_smarter_in_clause(session=session, column=column, values=values)
    sql: str = str(in_clause.compile(bind=session.bind))

    assert sql.count('IN (SELECT') == 2
    assert ' OR ' in sql


@pytest.mark.requires_psql
@pytest.mark.usefixtures('aiida_profile_clean')
def test_psql_uses_unnest() -> None:
    """PostgreSQL: generates ``id IN (SELECT unnest(ARRAY[...]::integer[]))``."""
    from aiida.manage import get_manager
    from aiida.storage.psql_dos.backend import PsqlDosBackend
    from aiida.storage.psql_dos.models.node import DbNode

    storage: PsqlDosBackend = cast(PsqlDosBackend, get_manager().get_profile_storage())
    session: Session = storage.get_session()
    in_clause: ColumnElement[bool] = _create_smarter_in_clause(session=session, column=DbNode.id, values=[1, 2])
    sql: str = str(in_clause.compile(bind=session.bind))

    assert 'unnest' in sql
    assert 'IN (SELECT' in sql


@pytest.mark.requires_psql
@pytest.mark.usefixtures('aiida_profile_clean')
def test_psql_batches_large_lists() -> None:
    """PostgreSQL: lists > 500k are split into OR'd batches."""
    from aiida.manage import get_manager
    from aiida.storage.psql_dos.backend import PsqlDosBackend
    from aiida.storage.psql_dos.models.node import DbNode

    storage: PsqlDosBackend = cast(PsqlDosBackend, get_manager().get_profile_storage())
    session: Session = storage.get_session()
    values: list[int] = list(range(IN_CLAUSE_BATCH_SIZE + 1))
    in_clause: ColumnElement[bool] = _create_smarter_in_clause(session=session, column=DbNode.id, values=values)
    sql: str = str(in_clause.compile(bind=session.bind))

    assert sql.count('IN (SELECT') == 2
    assert ' OR ' in sql
