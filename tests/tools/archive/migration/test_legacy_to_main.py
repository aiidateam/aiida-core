###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test archive file migration from legacy format (JSON) to main format (SQLite)."""

import pytest
from archive_path import extract_file_in_zip
from sqlalchemy import inspect

from aiida.common.exceptions import StorageMigrationError
from aiida.storage.sqlite_zip.migrator import get_schema_version_head, migrate
from aiida.storage.sqlite_zip.utils import DB_FILENAME, create_sqla_engine
from tests.utils.archives import get_archive_file


def test_dangling_links(tmp_path):
    """Test that links with node UUIDs that are not in the archive are correctly handled."""
    filepath_archive = get_archive_file('0.10_dangling_link.aiida', 'export/migrate')
    with pytest.raises(StorageMigrationError, match='Database contains link with unknown input node'):
        migrate(filepath_archive, tmp_path / 'archive.aiida', 'main_0001')


def test_missing_nodes_in_groups(tmp_path, caplog):
    """Test that groups with listed node UUIDs that are not in the archive are correctly handled."""
    filepath_archive = get_archive_file('0.10_unknown_nodes_in_group.aiida', 'export/migrate')
    migrate(filepath_archive, tmp_path / 'archive.aiida', 'main_0001')
    assert 'Dropped unknown nodes in groups' in caplog.text, caplog.text


def test_fields_with_null_values(tmp_path):
    """Test that fields with null values are correctly handled."""
    filepath_archive = get_archive_file('0.10_null_fields.aiida', 'export/migrate')
    migrate(filepath_archive, tmp_path / 'archive.aiida', 'main_0001')


def test_legacy_to_main_versioned_node_schema(tmp_path):
    """Test versioned-node columns are added only by their archive schema migration."""
    filepath_archive = get_archive_file('0.10_null_fields.aiida', 'export/migrate')

    archive_main_0001 = tmp_path / 'archive-main-0001.aiida'
    migrate(filepath_archive, archive_main_0001, 'main_0001')

    database_main_0001 = tmp_path / 'archive-main-0001.sqlite'
    with database_main_0001.open('wb') as handle:
        extract_file_in_zip(archive_main_0001, DB_FILENAME, handle)

    with create_sqla_engine(database_main_0001).connect() as connection:
        inspector = inspect(connection)
        columns = {column['name']: column for column in inspector.get_columns('db_dbnode')}
        unique_constraints = {constraint['name'] for constraint in inspector.get_unique_constraints('db_dbnode')}

    assert 'lineage_uuid' not in columns
    assert 'version' not in columns
    assert 'uq_dbnode_lineage_version' not in unique_constraints

    archive_head = tmp_path / 'archive-head.aiida'
    migrate(filepath_archive, archive_head, get_schema_version_head())

    database_head = tmp_path / 'archive-head.sqlite'
    with database_head.open('wb') as handle:
        extract_file_in_zip(archive_head, DB_FILENAME, handle)

    with create_sqla_engine(database_head).connect() as connection:
        inspector = inspect(connection)
        columns = {column['name']: column for column in inspector.get_columns('db_dbnode')}
        unique_constraints = {constraint['name'] for constraint in inspector.get_unique_constraints('db_dbnode')}

    assert columns['lineage_uuid']['nullable']
    assert not columns['version']['nullable']
    assert 'uq_dbnode_lineage_version' in unique_constraints
