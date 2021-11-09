# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the migration engine (Alembic) as well as for the AiiDA migrations for SQLAlchemy."""
from contextlib import contextmanager
from typing import Iterator

import pytest
from sqlalchemy.orm import Session

from aiida.backends.sqlalchemy.manager import SqlaBackendManager


class Migrator:
    """A class to yield from the ``perform_migrations`` fixture."""

    def __init__(self, backend, manager: SqlaBackendManager) -> None:
        self.backend = backend
        self._manager = manager

    def migrate_up(self, revision: str) -> None:
        """Migrate up to a given revision."""
        self._manager.migrate_up(revision)
        if revision != 'head':
            assert self._manager.get_schema_version_backend() == revision

    def migrate_down(self, revision: str) -> None:
        """Migrate down to a given revision."""
        self._manager.migrate_down(revision)
        assert self._manager.get_schema_version_backend() == revision

    def get_current_table(self, table_name):
        """
        Return a Model instantiated at the correct migration.
        Note that this is obtained by inspecting the database and not
        by looking into the models file.
        So, special methods possibly defined in the models files/classes are not present.

        For instance, you can do::

          DbGroup = self.get_current_table('db_dbgroup')

        :param table_name: the name of the table.
        """
        from alembic.migration import MigrationContext  # pylint: disable=import-error
        from sqlalchemy.ext.automap import automap_base  # pylint: disable=import-error,no-name-in-module

        with self.backend.get_session().bind.begin() as connection:
            context = MigrationContext.configure(connection)
            bind = context.bind

            base = automap_base()
            # reflect the tables
            base.prepare(autoload_with=bind.engine)

            return getattr(base.classes, table_name)

    @contextmanager
    def session(self) -> Iterator[Session]:
        """A context manager for a new session."""
        with self.backend.get_session().bind.begin() as connection:
            session = Session(connection.engine, future=True)
            try:
                yield session
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()


@pytest.fixture()
def perform_migrations(aiida_profile, backend, request):
    """A fixture to setup the database for migration tests"""
    # note downgrading to 1830c8430131 requires adding columns to `DbUser` and hangs if a user is present
    aiida_profile.reset_db(with_user=False)
    backend.get_session().commit()
    migrator = Migrator(backend, SqlaBackendManager())
    marker = request.node.get_closest_marker('migrate_down')
    if marker is not None:
        assert marker.args, 'No version given'
        migrator.migrate_down(marker.args[0])
    yield migrator
    # ensure that the database is migrated back up to the latest version, once finished
    migrator.migrate_up('head')
    aiida_profile.reset_db()
