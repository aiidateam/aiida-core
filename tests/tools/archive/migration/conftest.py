###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module with tests for export archive migrations."""

import pytest

from aiida.storage.sqlite_zip.migrations.utils import verify_metadata_version
from tests.utils.archives import get_archive_file, read_json_files


@pytest.fixture()
def core_archive():
    """Return parameters for the core archive."""
    return {'filepath': 'export/migrate'}


@pytest.fixture()
def external_archive() -> dict:
    """Return parameters for the external archive."""
    return {'filepath': 'archives', 'external_module': 'aiida-export-migration-tests'}


@pytest.fixture()
def migrate_from_func():
    """Create migrate function."""

    def _migrate(filename_archive, version_old, version_new, migration_method, archive_kwargs=None):
        """Migrate one of the archives from `aiida-export-migration-tests`.

        :param filename_archive: the relative file name of the archive
        :param version_old: version of the archive
        :param version_new: version to migrate to
        :param migration_method: the migration method that should convert between version_old and version_new
        :return: the migrated metadata and data as a tuple

        """
        archive_path = get_archive_file(
            filename_archive,
            **(archive_kwargs or {'filepath': 'archives', 'external_module': 'aiida-export-migration-tests'}),
        )
        metadata, data = read_json_files(archive_path)
        verify_metadata_version(metadata, version=version_old)
        migration_method(metadata, data)
        verify_metadata_version(metadata, version=version_new)

        return metadata, data

    return _migrate
