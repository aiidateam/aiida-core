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
from aiida.backends.testbase import AiidaTestCase
from aiida.tools.importexport.migration.utils import verify_metadata_version
from tests.utils.archives import get_json_files


class ArchiveMigrationTest(AiidaTestCase):
    """Base class to write specific tests for a particular export archive migration."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.external_archive = {'filepath': 'archives', 'external_module': 'aiida-export-migration-tests'}
        cls.core_archive = {'filepath': 'export/migrate'}
        cls.maxDiff = None  # pylint: disable=invalid-name

    def migrate(self, filename_archive, version_old, version_new, migration_method):
        """Migrate one of the archives from `aiida-export-migration-tests`.

        :param filename_archive: the relative file name of the archive
        :param version_old: version of the archive
        :param version_new: version to migrate to
        :param migration_method: the migration method that should convert between version_old and version_new
        :return: the migrated metadata and data as a tuple
        """
        metadata, data = get_json_files(filename_archive, **self.external_archive)
        verify_metadata_version(metadata, version=version_old)

        migration_method(metadata, data)
        verify_metadata_version(metadata, version=version_new)

        return metadata, data
