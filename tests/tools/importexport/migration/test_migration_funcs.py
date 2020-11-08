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
"""Test migrating all export archives included in `tests/static/export/migrate`."""
import zipfile

import pytest

from aiida import get_version
from aiida.tools.importexport.archive.migrations import MIGRATE_FUNCTIONS
from aiida.tools.importexport.archive.migrations.utils import verify_metadata_version
from aiida.tools.importexport.archive.common import CacheFolder
from tests.utils.archives import get_archive_file, read_json_files


@pytest.mark.parametrize(
    'migration_data',
    MIGRATE_FUNCTIONS.items(),
    ids=MIGRATE_FUNCTIONS.keys(),
)
def test_migrations(migration_data, tmp_path):
    """Test each migration method from the `aiida.tools.importexport.archive.migrations` module."""
    version_old, (version_new, migration_method) = migration_data

    filepath_archive_new = get_archive_file(f'export_v{version_new}_simple.aiida', filepath='export/migrate')

    metadata_new = read_json_files(filepath_archive_new, names=['metadata.json'])[0]
    verify_metadata_version(metadata_new, version=version_new)
    data_new = read_json_files(filepath_archive_new, names=['data.json'])[0]

    filepath_archive_old = get_archive_file(f'export_v{version_old}_simple.aiida', filepath='export/migrate')

    out_path = tmp_path / 'out.aiida'
    with zipfile.ZipFile(filepath_archive_old, 'r', allowZip64=True) as handle:
        handle.extractall(out_path)

    folder = CacheFolder(out_path)
    migration_method(folder)

    _, metadata_old = folder.load_json('metadata.json')
    _, data_old = folder.load_json('data.json')

    verify_metadata_version(metadata_old, version=version_new)

    # Remove AiiDA version, since this may change regardless of the migration function
    metadata_old.pop('aiida_version')
    metadata_new.pop('aiida_version')

    # Assert conversion message in `metadata.json` is correct and then remove it for later assertions
    metadata_new.pop('conversion_info')
    message = f'Converted from version {version_old} to {version_new} with AiiDA v{get_version()}'
    assert metadata_old.pop('conversion_info')[-1] == message, 'Conversion message after migration is wrong'

    assert metadata_old == metadata_new
    assert data_old == data_new
