# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test export file migration from export version 0.5 to 0.6"""
from aiida.backends.general.migrations.calc_state import STATE_MAPPING
from aiida.tools.importexport.migration.utils import verify_metadata_version
from aiida.tools.importexport.migration.v05_to_v06 import migrate_v5_to_v6

from tests.utils.archives import get_json_files
from . import ArchiveMigrationTest


class TestMigrate(ArchiveMigrationTest):
    """Tests specific for this archive migration."""

    def test_migrate_external(self):
        """Test the migration on the test archive provided by the external test package."""
        _, data = self.migrate('export_v0.5_manual.aiida', '0.5', '0.6', migrate_v5_to_v6)

        # Explicitly check that conversion dictionaries were removed
        illegal_data_dicts = {'node_attributes_conversion', 'node_extras_conversion'}
        for dict_ in illegal_data_dicts:
            self.assertNotIn(dict_, data, msg="dictionary '{}' should have been removed from data.json".format(dict_))

    def test_migrate_v5_to_v6_calc_states(self):
        """Test the data migration of legacy `JobCalcState` attributes.

        This test has to use a local archive because the current archive from the `aiida-export-migration-tests`
        module does not include a `CalcJobNode` with a legacy `state` attribute.
        """
        # Get metadata.json and data.json as dicts from v0.5 file archive
        metadata, data = get_json_files('export_v0.5_simple.aiida', **self.core_archive)
        verify_metadata_version(metadata, version='0.5')

        calc_job_node_type = 'process.calculation.calcjob.CalcJobNode.'
        node_data = data['export_data'].get('Node', {})
        node_attributes = data['node_attributes']
        calc_jobs = {}
        for pk, values in node_data.items():
            if values['node_type'] == calc_job_node_type and 'state' in data['node_attributes'].get(pk, {}):
                calc_jobs[pk] = data['node_attributes'][pk]['state']

        # Migrate to v0.6
        migrate_v5_to_v6(metadata, data)
        verify_metadata_version(metadata, version='0.6')

        node_attributes = data['node_attributes']

        # The export archive contains a single `CalcJobNode` that had `state=FINISHED`.
        for pk, state in calc_jobs.items():

            attributes = node_attributes[pk]

            if STATE_MAPPING[state].exit_status is not None:
                self.assertEqual(attributes['exit_status'], STATE_MAPPING[state].exit_status)

            if STATE_MAPPING[state].process_state is not None:
                self.assertEqual(attributes['process_state'], STATE_MAPPING[state].process_state)

            if STATE_MAPPING[state].process_status is not None:
                self.assertEqual(attributes['process_status'], STATE_MAPPING[state].process_status)

            self.assertEqual(attributes['process_label'], 'Legacy JobCalculation')

    def test_migrate_v5_to_v6_datetime(self):
        """Test the data migration of serialized datetime objects.

        Datetime attributes were serialized into strings, by first converting to UTC and then printing with the format
        '%Y-%m-%dT%H:%M:%S.%f'. In the database migration, datetimes were serialized *including* timezone information.
        Here we test that the archive migration correctly reattaches the timezone information. The archive that we are
        using `export_v0.5_simple.aiida` contains a node with the attribute "scheduler_lastchecktime".
        """
        # Get metadata.json and data.json as dicts from v0.5 file archive
        metadata, data = get_json_files('export_v0.5_simple.aiida', **self.core_archive)
        verify_metadata_version(metadata, version='0.5')

        for key, values in data['node_attributes'].items():
            if 'scheduler_lastchecktime' not in values:
                continue

            serialized_original = values['scheduler_lastchecktime']
            msg = 'the serialized datetime before migration should not contain a plus: {}'.format(serialized_original)
            self.assertTrue('+' not in serialized_original, msg=msg)

            # Migrate to v0.6
            migrate_v5_to_v6(metadata, data)
            verify_metadata_version(metadata, version='0.6')

            serialized_migrated = data['node_attributes'][key]['scheduler_lastchecktime']
            self.assertEqual(serialized_migrated, serialized_original + '+00:00')
            break

        else:
            raise RuntimeError(
                'the archive `export_v0.5_simple.aiida` did not contain a node with the attribute '
                '`scheduler_lastchecktime` which is required for this test.'
            )
