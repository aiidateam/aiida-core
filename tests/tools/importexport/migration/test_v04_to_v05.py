# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test export file migration from export version 0.4 to 0.5"""
from aiida.tools.importexport.migration.v04_to_v05 import migrate_v4_to_v5

from . import ArchiveMigrationTest


class TestMigrate(ArchiveMigrationTest):
    """Tests specific for this archive migration."""

    def test_migrate_external(self):
        """Test the migration on the test archive provided by the external test package."""
        metadata, data = self.migrate('export_v0.4.aiida', '0.4', '0.5', migrate_v4_to_v5)

        # Check schema-changes
        removed_computer_attrs = {'transport_params'}
        removed_node_attrs = {'nodeversion', 'public'}
        for change in removed_computer_attrs:
            # data.json
            for computer in data['export_data']['Computer'].values():
                self.assertNotIn(change, computer, msg="'{}' unexpectedly found for {}".format(change, computer))
            # metadata.json
            self.assertNotIn(
                change,
                metadata['all_fields_info']['Computer'],
                msg="'{}' unexpectedly found in metadata.json for Computer".format(change)
            )
        for change in removed_node_attrs:
            # data.json
            for node in data['export_data']['Node'].values():
                self.assertNotIn(change, node, msg="'{}' unexpectedly found for {}".format(change, node))
            # metadata.json
            self.assertNotIn(
                change,
                metadata['all_fields_info']['Node'],
                msg="'{}' unexpectedly found in metadata.json for Node".format(change)
            )
