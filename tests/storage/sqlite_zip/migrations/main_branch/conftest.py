###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Fixtures for testing the ``main`` branch archive data migrations."""

from pathlib import Path

import pytest
from sqlalchemy import insert, text

from aiida.common.utils import get_new_uuid
from aiida.storage.sqlite_zip.migrations import v1_db_schema as v1_schema
from aiida.storage.sqlite_zip.migrator import _migration_context
from aiida.storage.sqlite_zip.utils import create_sqla_engine


@pytest.fixture
def null_content_database(tmp_path: Path) -> Path:
    """Create a ``main_0000`` archive database containing ``NULL`` values.

    This reproduces the state produced by the legacy conversion
    (:mod:`aiida.storage.sqlite_zip.migrations.legacy_to_main`), which creates
    the database from the nullable ``v1`` schema and stamps it as ``main_0000``:
    rows may contain ``NULL`` values and orphaned references that the
    ``main_0000a`` and ``main_0000b`` migrations have to clean up.

    Note that the rows are inserted with Core inserts and explicit ``None``
    values, mirroring the legacy conversion: going through the ORM would apply
    the Python-side column defaults instead of storing ``NULL``. The ``JSON``
    columns additionally need a raw ``SQL`` pass: SQLAlchemy serialises a ``None``
    for a ``JSON`` column to the ``'null'`` string instead of a real ``SQL NULL``
    (which is also why the migration matches them with ``IS NULL``).
    """
    database_path = tmp_path / 'database.sqlite'
    engine = create_sqla_engine(database_path)
    v1_schema.ArchiveV1Base.metadata.create_all(engine)

    with engine.begin() as connection:
        connection.execute(
            insert(v1_schema.DbUser.__table__),
            [{'id': 1, 'email': 'test@aiida.net', 'first_name': None, 'last_name': None, 'institution': None}],
        )
        connection.execute(
            insert(v1_schema.DbComputer.__table__),
            [
                {
                    'id': 1,
                    'uuid': get_new_uuid(),
                    'label': 'test',
                    'hostname': None,
                    'description': None,
                    'scheduler_type': None,
                    'transport_type': None,
                    'metadata': None,
                }
            ],
        )
        connection.execute(
            insert(v1_schema.DbNode.__table__),
            [
                {
                    'id': 1,
                    'uuid': get_new_uuid(),
                    'node_type': 'node.process.calculation.CalculationNode.',
                    'user_id': 1,
                    'label': None,
                    'description': None,
                    'ctime': None,
                    'mtime': None,
                    'attributes': {},
                    'extras': {},
                    'repository_metadata': {},
                }
            ],
        )
        connection.execute(
            insert(v1_schema.DbGroup.__table__),
            [
                {
                    'id': 1,
                    'uuid': get_new_uuid(),
                    'label': 'test',
                    'type_string': None,
                    'time': None,
                    'description': None,
                    'user_id': 1,
                    'extras': {},
                }
            ],
        )
        connection.execute(
            insert(v1_schema.DbAuthInfo.__table__),
            [
                # Valid row with ``NULL`` values to be replaced.
                {'aiidauser_id': 1, 'dbcomputer_id': 1, 'enabled': None, 'auth_params': None, 'metadata': None},
                # Orphaned rows left behind by deleted users/computers, to be removed.
                {'aiidauser_id': None, 'dbcomputer_id': 1, 'enabled': None, 'auth_params': None, 'metadata': None},
                {'aiidauser_id': 1, 'dbcomputer_id': None, 'enabled': None, 'auth_params': None, 'metadata': None},
            ],
        )
        connection.execute(
            insert(v1_schema.DbComment.__table__),
            [
                # Valid row with ``NULL`` values to be replaced.
                {'uuid': get_new_uuid(), 'dbnode_id': 1, 'user_id': 1, 'content': None, 'ctime': None, 'mtime': None},
                # Orphaned row left behind by a deleted node/user, to be removed.
                {
                    'uuid': get_new_uuid(),
                    'dbnode_id': None,
                    'user_id': None,
                    'content': None,
                    'ctime': None,
                    'mtime': None,
                },
            ],
        )
        connection.execute(
            insert(v1_schema.DbLog.__table__),
            [
                {
                    'uuid': get_new_uuid(),
                    'dbnode_id': 1,
                    'time': None,
                    'loggername': None,
                    'levelname': None,
                    'message': None,
                    'metadata': None,
                }
            ],
        )

    with engine.begin() as connection:
        for table, columns in {
            'db_dbauthinfo': ['auth_params', 'metadata'],
            'db_dbcomputer': ['metadata'],
            'db_dblog': ['metadata'],
        }.items():
            for column in columns:
                connection.execute(text(f'UPDATE {table} SET {column} = NULL'))

    with _migration_context(database_path) as context:
        assert context.script is not None
        assert context.connection is not None
        context.stamp(context.script, 'main_0000')
        context.connection.commit()

    return database_path
