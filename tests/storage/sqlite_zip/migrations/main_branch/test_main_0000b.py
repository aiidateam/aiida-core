###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test ``main_0000b_non_nullable.py``."""

from pathlib import Path

import pytest
from alembic.command import upgrade
from sqlalchemy import insert, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from aiida.storage.sqlite_zip.migrations import v1_db_schema as v1_schema
from aiida.storage.sqlite_zip.migrator import _alembic_connect, _migration_context
from aiida.storage.sqlite_zip.utils import create_sqla_engine


def test_migration(null_content_database: Path):
    """Test the migration cleans the data and makes the columns non-nullable."""
    with _alembic_connect(null_content_database, enforce_foreign_keys=False) as config:
        upgrade(config, 'main_0000b')

    with _migration_context(null_content_database) as context:
        assert context.get_current_revision() == 'main_0000b'

    engine = create_sqla_engine(null_content_database)

    # The data migration from ``main_0000a`` runs first as part of the chain.
    with Session(engine) as session:
        assert session.query(v1_schema.DbAuthInfo).count() == 1
        assert session.query(v1_schema.DbComment).count() == 1
        assert session.query(v1_schema.DbUser).one().first_name == ''

    for table, names in {
        'db_dbauthinfo': ['aiidauser_id', 'dbcomputer_id', 'metadata', 'auth_params', 'enabled'],
        'db_dbcomment': ['dbnode_id', 'user_id', 'content', 'ctime', 'mtime'],
        'db_dbcomputer': ['description', 'hostname', 'metadata', 'scheduler_type', 'transport_type'],
        'db_dbgroup': ['description', 'time', 'type_string'],
        'db_dblog': ['levelname', 'loggername', 'message', 'time', 'metadata'],
        'db_dbnode': ['ctime', 'description', 'label', 'mtime'],
        'db_dbuser': ['first_name', 'last_name', 'institution'],
    }.items():
        table_columns = {column['name']: column for column in inspect(engine).get_columns(table)}
        for name in names:
            assert table_columns[name]['nullable'] is False, f'{table}.{name} should be non-nullable'

    # Inserting a ``NULL`` value now violates the constraints.
    with engine.begin() as connection:
        with pytest.raises(IntegrityError):
            connection.execute(insert(v1_schema.DbUser.__table__).values(email='null@aiida.net', first_name=None))
