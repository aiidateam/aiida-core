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

from aiida.common.exceptions import StorageMigrationError
from aiida.storage.sqlite_zip.migrator import migrate
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
