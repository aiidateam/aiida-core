# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module with tests for export archive migrations."""
import tarfile
import zipfile

from archive_path import TarPath, ZipPath
import pytest

from aiida.tools.importexport.archive import CacheFolder
from aiida.tools.importexport.archive.migrations.utils import verify_metadata_version
from tests.utils.archives import get_archive_file


@pytest.fixture()
def core_archive():
    """Return parameters for the core archive."""
    return {'filepath': 'export/migrate'}


@pytest.fixture()
def external_archive() -> dict:
    """Return parameters for the external archive."""
    return {'filepath': 'archives', 'external_module': 'aiida-export-migration-tests'}


@pytest.fixture()
def migrate_from_func(tmp_path):
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
            **(archive_kwargs or {
                'filepath': 'archives',
                'external_module': 'aiida-export-migration-tests'
            })
        )
        out_path = tmp_path / 'out.aiida'

        if zipfile.is_zipfile(archive_path):
            ZipPath(archive_path).extract_tree(out_path)
        elif tarfile.is_tarfile(archive_path):
            TarPath(archive_path).extract_tree(out_path)
        else:
            raise ValueError('invalid file format, expected either a zip archive or gzipped tarball')

        folder = CacheFolder(out_path)
        _, old_metadata = folder.load_json('metadata.json')
        verify_metadata_version(old_metadata, version=version_old)

        migration_method(folder)

        _, metadata = folder.load_json('metadata.json')
        verify_metadata_version(metadata, version=version_new)

        _, data = folder.load_json('data.json')

        return metadata, data

    return _migrate
