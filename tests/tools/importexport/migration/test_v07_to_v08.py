# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test export file migration from export version 0.7 to 0.8"""
from aiida.tools.importexport.migration.v07_to_v08 import migrate_v7_to_v8, migration_default_link_label

from . import ArchiveMigrationTest


class TestMigrate(ArchiveMigrationTest):
    """Tests specific for this archive migration."""

    def test_migrate_external(self):
        """Test the migration on the test archive provided by the external test package."""
        _, data = self.migrate('export_v0.7_manual.aiida', '0.7', '0.8', migrate_v7_to_v8)

        # Check that no links have the label '_return', since it should now be 'result'
        illegal_label = '_return'
        for link in data.get('links_uuid'):
            self.assertFalse(
                link['label'] == illegal_label,
                msg='The illegal link label {} was not expected to be present - '
                "it should now be 'result'".format(illegal_label)
            )

    def test_migration_0043_default_link_label(self):
        """Check CorruptArchive is raised for different cases during migration 0040"""
        # data has one "valid" link, in the form of <label="a_good_label">.
        # data also has one "invalid" link, in form of <label="_return">.
        # After the migration, the "invalid" link should have been updated to the "valid" link <label="result">
        data = {
            'links_uuid': [{
                'input': 'some-random-uuid',
                'output': 'some-other-random-uuid',
                'label': '_return',
                'type': 'return'
            }, {
                'input': 'some-random-uuid',
                'output': 'some-other-random-uuid',
                'label': 'a_good_label',
                'type': 'return'
            }]
        }

        migration_default_link_label(data)

        self.assertEqual(
            data, {
                'links_uuid': [{
                    'input': 'some-random-uuid',
                    'output': 'some-other-random-uuid',
                    'label': 'result',
                    'type': 'return'
                }, {
                    'input': 'some-random-uuid',
                    'output': 'some-other-random-uuid',
                    'label': 'a_good_label',
                    'type': 'return'
                }]
            }
        )
