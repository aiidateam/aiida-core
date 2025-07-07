###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test archive file migration from export version 0.8 to 0.9"""

from aiida.storage.sqlite_zip.migrations.legacy.v08_to_v09 import migrate_v8_to_v9, migration_dbgroup_type_string


def test_migrate_external(migrate_from_func):
    """Test the migration on the test archive provided by the external test package."""
    _, data = migrate_from_func('export_v0.8_manual.aiida', '0.8', '0.9', migrate_v8_to_v9)

    for attributes in data.get('export_data', {}).get('Group', {}).values():
        assert attributes['type_string'] in [
            'core',
            'core.upf',
            'core.import',
            'core.auto',
        ], f'encountered illegal type string `{attributes["type_string"]}`'


def test_migration_dbgroup_type_string():
    """Test the `migration_dbgroup_type_string` function directly."""
    data = {
        'export_data': {
            'Group': {
                '50': {
                    'type_string': 'user',
                },
                '51': {
                    'type_string': 'data.upf',
                },
                '52': {
                    'type_string': 'auto.import',
                },
                '53': {
                    'type_string': 'auto.run',
                },
            }
        }
    }

    migration_dbgroup_type_string(data)

    assert data == {
        'export_data': {
            'Group': {
                '50': {
                    'type_string': 'core',
                },
                '51': {
                    'type_string': 'core.upf',
                },
                '52': {
                    'type_string': 'core.import',
                },
                '53': {
                    'type_string': 'core.auto',
                },
            }
        }
    }
