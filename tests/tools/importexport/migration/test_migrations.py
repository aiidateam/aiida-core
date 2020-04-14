# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=redefined-outer-name
"""Test the export archive migrations on the archives included in `tests/fixtures/export/migrate`."""
import copy
import pytest

from aiida import get_version
from aiida.tools.importexport.common import Archive
from aiida.tools.importexport.migration.v01_to_v02 import migrate_v1_to_v2
from aiida.tools.importexport.migration.v02_to_v03 import migrate_v2_to_v3
from aiida.tools.importexport.migration.v03_to_v04 import migrate_v3_to_v4
from aiida.tools.importexport.migration.v04_to_v05 import migrate_v4_to_v5
from aiida.tools.importexport.migration.v05_to_v06 import migrate_v5_to_v6
from aiida.tools.importexport.migration.v06_to_v07 import migrate_v6_to_v7
from aiida.tools.importexport.migration.v07_to_v08 import migrate_v7_to_v8
from aiida.tools.importexport.migration.utils import verify_metadata_version
from tests.utils.archives import get_json_files, get_archive_file


@pytest.fixture
def migration_data(request):
    """For a given tuple of two subsequent versions and corresponding migration method, return metadata and data."""
    version_old, version_new, migration_method = request.param

    filepath_archive = 'export_v{}_simple.aiida'.format(version_new)
    metadata_new, data_new = get_json_files(filepath_archive, filepath='export/migrate')
    verify_metadata_version(metadata_new, version=version_new)

    filepath_archive = get_archive_file('export_v{}_simple.aiida'.format(version_old), filepath='export/migrate')

    with Archive(filepath_archive) as archive:
        metadata_old = copy.deepcopy(archive.meta_data)
        data_old = copy.deepcopy(archive.data)

        migration_method(metadata_old, data_old, archive.folder)
        verify_metadata_version(metadata_old, version=version_new)

    yield version_old, version_new, metadata_old, metadata_new, data_old, data_new


@pytest.mark.parametrize(
    'migration_data',
    (('0.1', '0.2', migrate_v1_to_v2), ('0.2', '0.3', migrate_v2_to_v3), ('0.3', '0.4', migrate_v3_to_v4),
     ('0.4', '0.5', migrate_v4_to_v5), ('0.5', '0.6', migrate_v5_to_v6), ('0.6', '0.7', migrate_v6_to_v7),
     ('0.7', '0.8', migrate_v7_to_v8)),
    indirect=True
)
def test_migrations(migration_data):
    """Test each migration method from the `aiida.tools.importexport.migration` module."""
    version_old, version_new, metadata_old, metadata_new, data_old, data_new = migration_data

    # Remove AiiDA version, since this may change regardless of the migration function
    metadata_old.pop('aiida_version')
    metadata_new.pop('aiida_version')

    # Assert conversion message in `metadata.json` is correct and then remove it for later assertions
    metadata_new.pop('conversion_info')
    message = 'Converted from version {} to {} with AiiDA v{}'.format(version_old, version_new, get_version())
    assert metadata_old.pop('conversion_info')[-1] == message, 'Conversion message after migration is wrong'

    assert metadata_old == metadata_new
    assert data_old == data_new
