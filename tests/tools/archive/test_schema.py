###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test the schema of the sqlite file within the archive."""

from contextlib import suppress

import pytest
import yaml
from archive_path import extract_file_in_zip
from sqlalchemy import String, inspect
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.engine import Inspector

from aiida import get_profile
from aiida.storage.psql_dos.utils import create_sqlalchemy_engine
from aiida.storage.sqlite_zip import models, utils
from aiida.storage.sqlite_zip.migrator import get_schema_version_head, migrate
from tests.utils.archives import get_archive_file


@pytest.mark.requires_psql
def test_psql_sync_init(tmp_path):
    """Test the schema is in-sync with the ``psql_dos`` backend, when initialising a new archive."""
    # note, directly using the global profile's engine here left connections open
    with create_sqlalchemy_engine(get_profile().storage_config).connect() as conn:
        psql_insp = inspect(conn)

        engine = utils.create_sqla_engine(tmp_path / 'archive.sqlite')
        models.SqliteBase.metadata.create_all(engine)
        sqlite_insp = inspect(engine)

        diffs = diff_schemas(psql_insp, sqlite_insp)
        if diffs:
            raise AssertionError(f'Schema is not in-sync with the psql backend:\n{yaml.safe_dump(diffs)}')


@pytest.mark.requires_psql
def test_psql_sync_migrate(tmp_path):
    """Test the schema is in-sync with the ``psql_dos`` backend, when migrating an old archive to the latest version."""
    # note, directly using the global profile's engine here left connections open
    with create_sqlalchemy_engine(get_profile().storage_config).connect() as conn:
        psql_insp = inspect(conn)

        # migrate an old archive
        filepath_archive = get_archive_file('export_0.4_simple.aiida', 'export/migrate')
        migrate(filepath_archive, tmp_path / 'archive.aiida', get_schema_version_head())

        # extract the database
        with tmp_path.joinpath('archive.sqlite').open('wb') as handle:
            extract_file_in_zip(tmp_path / 'archive.aiida', 'db.sqlite3', handle)

        engine = utils.create_sqla_engine(tmp_path / 'archive.sqlite')
        sqlite_insp = inspect(engine)

        diffs = diff_schemas(psql_insp, sqlite_insp)
        if diffs:
            raise AssertionError(f'Schema is not in-sync with the psql backend:\n{yaml.safe_dump(diffs)}')


def diff_schemas(psql_insp: Inspector, sqlite_insp: Inspector):
    """Compare the reflected schemas of the two databases."""
    diffs: dict = {}

    for table_name in sqlite_insp.get_table_names():
        if not table_name.startswith('db_') or table_name == 'db_dbsetting':
            continue  # not an aiida table
        if table_name not in psql_insp.get_table_names():
            diffs[table_name] = 'additional'
    for table_name in psql_insp.get_table_names():
        if not table_name.startswith('db_') or table_name == 'db_dbsetting':
            continue  # not an aiida table
        if table_name not in sqlite_insp.get_table_names():
            diffs[table_name] = 'missing'
            continue
        psql_columns = {col['name']: col for col in psql_insp.get_columns(table_name)}
        sqlite_columns = {col['name']: col for col in sqlite_insp.get_columns(table_name)}
        for column_name in psql_columns:
            # check existence
            if column_name not in sqlite_columns:
                diffs.setdefault(table_name, {})[column_name] = 'missing'
                continue
            # check type
            psql_type = psql_columns[column_name]['type']
            sqlite_type = sqlite_columns[column_name]['type']

            # standardise types
            # Since sqlalchemy v2.0 the ``UUID.as_generic()`` for PostgreSQL is converted to ``CHAR(32)`` which causes
            # a discrepancy between the field for sqlite which is defined as ``VARCHAR(32)``. Therefore ``UUID`` is
            # converted to string manually before calling ``.as_generic()``.
            if isinstance(psql_type, UUID):
                psql_type = String(length=32)

            with suppress(NotImplementedError):
                psql_type = psql_type.as_generic()
            with suppress(NotImplementedError):
                sqlite_type = sqlite_type.as_generic()

            if not isinstance(sqlite_type, type(psql_type)):
                diffs.setdefault(table_name, {}).setdefault(column_name, {})['type'] = f'{sqlite_type} != {psql_type}'
            elif isinstance(psql_type, String):
                if psql_type.length != sqlite_type.length:  # type: ignore[attr-defined]
                    string = f'{sqlite_type.length} != {psql_type.length}'  # type: ignore[attr-defined]
                    diffs.setdefault(table_name, {}).setdefault(column_name, {})['length'] = string
            # check nullability
            psql_nullable = psql_columns[column_name]['nullable']
            sqlite_nullable = sqlite_columns[column_name]['nullable']
            if psql_nullable != sqlite_nullable:
                diffs.setdefault(table_name, {}).setdefault(column_name, {})['nullable'] = (
                    f'{sqlite_nullable} != {psql_nullable}'
                )

        # compare unique constraints
        psql_uq_constraints = [c['name'] for c in psql_insp.get_unique_constraints(table_name)]
        sqlite_uq_constraints = [c['name'] for c in sqlite_insp.get_unique_constraints(table_name)]
        for uq_constraint in psql_uq_constraints:
            if uq_constraint not in sqlite_uq_constraints:
                diffs.setdefault(table_name, {}).setdefault('uq_constraints', {})[uq_constraint] = 'missing'
        for uq_constraint in sqlite_uq_constraints:
            if uq_constraint not in psql_uq_constraints:
                diffs.setdefault(table_name, {}).setdefault('uq_constraints', {})[uq_constraint] = 'additional'

        # compare foreign key constraints
        psql_fk_constraints = [c['name'] for c in psql_insp.get_foreign_keys(table_name)]
        sqlite_fk_constraints = [c['name'] for c in sqlite_insp.get_foreign_keys(table_name)]
        for fk_constraint in psql_fk_constraints:
            if fk_constraint not in sqlite_fk_constraints:
                diffs.setdefault(table_name, {}).setdefault('fk_constraints', {})[fk_constraint] = 'missing'
        for fk_constraint in sqlite_fk_constraints:
            if fk_constraint not in psql_fk_constraints:
                diffs.setdefault(table_name, {}).setdefault('fk_constraints', {})[fk_constraint] = 'additional'

        # compare indexes (discarding any postgresql specific ones, e.g. varchar_pattern_ops)
        psql_indexes = [
            idx['name']
            for idx in psql_insp.get_indexes(table_name)
            if not idx['unique'] and not (idx['name'] is not None and idx['name'].startswith('ix_pat_'))
        ]
        sqlite_indexes = [idx['name'] for idx in sqlite_insp.get_indexes(table_name) if not idx['unique']]
        for index in psql_indexes:
            if index not in sqlite_indexes:
                diffs.setdefault(table_name, {}).setdefault('indexes', {})[index] = 'missing'
        for index in sqlite_indexes:
            if index not in psql_indexes:
                diffs.setdefault(table_name, {}).setdefault('indexes', {})[index] = 'additional'

    return diffs
