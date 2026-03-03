###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for :mod:`aiida.storage.utils`."""

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session

from aiida.storage.utils import IN_CLAUSE_BATCH_SIZE, _create_smarter_in_clause


@pytest.fixture
def sqlite_session():
    """In-memory SQLite session with a simple integer table."""
    engine = sa.create_engine('sqlite://')
    metadata = sa.MetaData()
    table = sa.Table('items', metadata, sa.Column('id', sa.Integer, primary_key=True))
    metadata.create_all(engine)
    with Session(engine) as session:
        yield session, table.c.id


def test_sqlite_uses_json_each(sqlite_session):
    """SQLite: generates ``id IN (SELECT CAST(value AS INTEGER) FROM json_each(?))``."""
    session, column = sqlite_session
    in_clause = _create_smarter_in_clause(session=session, column=column, values=[1, 2])
    sql = str(in_clause.compile(session.bind))
    assert 'json_each' in sql
    assert 'IN (SELECT' in sql


def test_sqlite_batches_large_lists(sqlite_session):
    """SQLite: lists > 500k are split into OR'd batches."""
    session, column = sqlite_session
    values = list(range(IN_CLAUSE_BATCH_SIZE + 1))
    in_clause = _create_smarter_in_clause(session=session, column=column, values=values)
    sql = str(in_clause.compile(session.bind))
    assert sql.count('IN (SELECT') == 2
    assert ' OR ' in sql


@pytest.mark.requires_psql
@pytest.mark.usefixtures('aiida_profile_clean')
def test_psql_uses_unnest():
    """PostgreSQL: generates ``id IN (SELECT unnest(ARRAY[...]::integer[]))``."""
    from aiida.manage import get_manager
    from aiida.storage.psql_dos.models.node import DbNode

    session = get_manager().get_profile_storage().get_session()
    in_clause = _create_smarter_in_clause(session=session, column=DbNode.id, values=[1, 2])
    sql = str(in_clause.compile(session.bind))
    assert 'unnest' in sql
    assert 'IN (SELECT' in sql


@pytest.mark.requires_psql
@pytest.mark.usefixtures('aiida_profile_clean')
def test_psql_batches_large_lists():
    """PostgreSQL: lists > 500k are split into OR'd batches."""
    from aiida.manage import get_manager
    from aiida.storage.psql_dos.models.node import DbNode

    session = get_manager().get_profile_storage().get_session()
    values = list(range(IN_CLAUSE_BATCH_SIZE + 1))
    in_clause = _create_smarter_in_clause(session=session, column=DbNode.id, values=values)
    sql = str(in_clause.compile(session.bind))
    assert sql.count('IN (SELECT') == 2
    assert ' OR ' in sql
