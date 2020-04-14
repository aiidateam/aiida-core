# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test export file migration from export version 0.8 to 0.9"""
from aiida.tools.importexport.migration.v08_to_v09 import migrate_v8_to_v9, migration_dbgroup_type_string

from . import ArchiveMigrationTest


class TestMigrate(ArchiveMigrationTest):
    """Tests specific for this archive migration."""

    def test_migrate_external(self):
        """Test the migration on the test archive provided by the external test package."""
        _, data = self.migrate('export_v0.8_manual.aiida', '0.8', '0.9', migrate_v8_to_v9)

        for attributes in data.get('export_data', {}).get('Group', {}).values():
            if attributes['type_string'] not in ['core', 'core.upf', 'core.import', 'core.auto']:
                raise AssertionError('encountered illegal type string `{}`'.format(attributes['type_string']))

    def test_migration_dbgroup_type_string(self):
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
                    }
                }
            }
        }

        migration_dbgroup_type_string(data)

        self.assertEqual(
            data, {
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
                        }
                    }
                }
            }
        )
