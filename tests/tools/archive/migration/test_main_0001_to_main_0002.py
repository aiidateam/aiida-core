###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test archive migration from ``main_0001`` to ``main_0002``, which drops the legacy ``Code`` plugin."""

from aiida import orm
from aiida.storage.sqlite_zip.migrator import migrate
from aiida.tools.archive.implementations.sqlite_zip.main import ArchiveFormatSqlZip
from tests.utils.archives import get_archive_file


def test_migrate_legacy_code(tmp_path):
    """Test that a legacy ``Code`` node in an archive is rewritten to an ``InstalledCode``.

    ``export_main_0001_simple.aiida`` contains a single remote legacy code, i.e. one with ``is_local=False``.
    """
    filepath_archive = get_archive_file('export_main_0001_simple.aiida', filepath='export/migrate')
    filepath_migrated = tmp_path / 'archive.aiida'

    migrate(filepath_archive, filepath_migrated, 'main_0002')

    with ArchiveFormatSqlZip().open(filepath_migrated, 'r') as archive:
        query = orm.QueryBuilder(backend=archive.get_backend()).append(orm.InstalledCode, project=['attributes'])
        (attributes,) = query.all(flat=True)

    assert attributes['filepath_executable'] == ('/ssoft/quantum-espresso/5.1.1/RH6/intel-15.0.0/x86_E5v2/intel/pw.x')
    assert 'is_local' not in attributes
    assert 'remote_exec_path' not in attributes
    # Attributes that the modern code plugins store under the same key are left untouched.
    assert attributes['input_plugin'] == 'quantumespresso.pw'
    assert attributes['prepend_text'] == 'module load quantum-espresso/5.1.1/intel-15.0.0'
