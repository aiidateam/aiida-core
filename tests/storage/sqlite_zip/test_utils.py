###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""SQLite physical transaction boundaries under sqlite3's legacy transaction control."""

import sqlite3
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from aiida.storage.sqlite_zip.utils import create_sqla_engine, sqlite_transaction


@pytest.mark.parametrize('already_open', [True, False])
def test_sqlite_transaction(tmp_path: Path, already_open: bool) -> None:
    """Begin only at explicit boundaries and tolerate an already-physical transaction."""
    engine = create_sqla_engine(path=tmp_path / 'database.sqlite')
    session = Session(engine)
    try:
        session.execute(text('SELECT 1'))
        driver = session.connection().connection.driver_connection
        assert isinstance(driver, sqlite3.Connection)
        assert not driver.in_transaction, 'Ordinary reads keep their existing legacy behavior'
        if already_open:
            _ = session.connection().exec_driver_sql('BEGIN')
        with sqlite_transaction(session=session):
            with sqlite_transaction(session=session):
                assert driver.in_transaction
            assert driver.in_transaction
        if already_open:
            assert driver.in_transaction
            session.rollback()
        else:
            assert not driver.in_transaction
    finally:
        session.close()
        engine.dispose()


def test_sqlite_transaction_releases_new_root_on_body_failure(tmp_path: Path) -> None:
    """A body failure rolls back a physical root started here and releases the writer lock."""
    engine = create_sqla_engine(path=tmp_path / 'database.sqlite')
    session = Session(engine)
    try:
        session.execute(text('SELECT 1'))
        driver = session.connection().connection.driver_connection
        assert isinstance(driver, sqlite3.Connection)
        with pytest.raises(RuntimeError, match='body failed'):
            with sqlite_transaction(session=session):
                _ = session.connection().exec_driver_sql('CREATE TABLE probe (id INTEGER PRIMARY KEY)')
                raise RuntimeError('body failed')
        assert not driver.in_transaction
    finally:
        session.close()
        engine.dispose()
