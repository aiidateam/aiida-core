# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""orm.Log tests for the export and import routines"""
# pylint: disable=too-many-locals,too-many-statements

import os

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.tools.importexport import import_data, export

from tests.utils.configuration import with_temp_dir


class TestLogs(AiidaTestCase):
    """Test ex-/import cases related to Logs"""

    def setUp(self):
        """Reset database prior to all tests"""
        super().setUp()
        self.reset_database()

    def tearDown(self):
        """
        Delete all the created log entries
        """
        super().tearDown()
        orm.Log.objects.delete_all()

    @with_temp_dir
    def test_critical_log_msg_and_metadata(self, temp_dir):
        """ Testing logging of critical message """
        message = 'Testing logging of critical failure'
        calc = orm.CalculationNode()

        # Firing a log for an unstored node should not end up in the database
        calc.logger.critical(message)
        # There should be no log messages for the unstored object
        self.assertEqual(len(orm.Log.objects.all()), 0)

        # After storing the node, logs above log level should be stored
        calc.store()
        calc.seal()
        calc.logger.critical(message)

        # Store Log metadata
        log_metadata = orm.Log.objects.get(dbnode_id=calc.id).metadata

        export_file = os.path.join(temp_dir, 'export.tar.gz')
        export([calc], outfile=export_file, silent=True)

        self.reset_database()

        import_data(export_file, silent=True)

        # Finding all the log messages
        logs = orm.Log.objects.all()

        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].message, message)
        self.assertEqual(logs[0].metadata, log_metadata)

    @with_temp_dir
    def test_exclude_logs_flag(self, temp_dir):
        """Test that the `include_logs` argument for `export` works."""
        log_msg = 'Testing logging of critical failure'

        # Create node
        calc = orm.CalculationNode()
        calc.store()
        calc.seal()

        # Create log message
        calc.logger.critical(log_msg)

        # Save uuids prior to export
        calc_uuid = calc.uuid

        # Export, excluding logs
        export_file = os.path.join(temp_dir, 'export.tar.gz')
        export([calc], outfile=export_file, silent=True, include_logs=False)

        # Clean database and reimport exported data
        self.reset_database()
        import_data(export_file, silent=True)

        # Finding all the log messages
        import_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid']).all()
        import_logs = orm.QueryBuilder().append(orm.Log, project=['uuid']).all()

        # There should be exactly: 1 orm.CalculationNode, 0 Logs
        self.assertEqual(len(import_calcs), 1)
        self.assertEqual(len(import_logs), 0)

        # Check it's the correct node
        self.assertEqual(str(import_calcs[0][0]), calc_uuid)

    @with_temp_dir
    def test_export_of_imported_logs(self, temp_dir):
        """Test export of imported Log"""
        log_msg = 'Testing export of imported log'

        # Create node
        calc = orm.CalculationNode()
        calc.store()
        calc.seal()

        # Create log message
        calc.logger.critical(log_msg)

        # Save uuids prior to export
        calc_uuid = calc.uuid
        log_uuid = orm.QueryBuilder().append(orm.Log, project=['uuid']).all()
        log_uuid = str(log_uuid[0][0])

        # Export
        export_file = os.path.join(temp_dir, 'export.tar.gz')
        export([calc], outfile=export_file, silent=True)

        # Clean database and reimport exported data
        self.reset_database()
        import_data(export_file, silent=True)

        # Finding all the log messages
        import_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid']).all()
        import_logs = orm.QueryBuilder().append(orm.Log, project=['uuid']).all()

        # There should be exactly: 1 CalculationNode, 1 Log
        self.assertEqual(len(import_calcs), 1)
        self.assertEqual(len(import_logs), 1)

        # Check the UUIDs are the same
        self.assertEqual(str(import_calcs[0][0]), calc_uuid)
        self.assertEqual(str(import_logs[0][0]), log_uuid)

        # Re-export
        calc = orm.load_node(import_calcs[0][0])
        re_export_file = os.path.join(temp_dir, 're_export.tar.gz')
        export([calc], outfile=re_export_file, silent=True)

        # Clean database and reimport exported data
        self.reset_database()
        import_data(re_export_file, silent=True)

        # Finding all the log messages
        import_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid']).all()
        import_logs = orm.QueryBuilder().append(orm.Log, project=['uuid']).all()

        # There should be exactly: 1 CalculationNode, 1 Log
        self.assertEqual(len(import_calcs), 1)
        self.assertEqual(len(import_logs), 1)

        # Check the UUIDs are the same
        self.assertEqual(str(import_calcs[0][0]), calc_uuid)
        self.assertEqual(str(import_logs[0][0]), log_uuid)

    @with_temp_dir
    def test_multiple_imports_for_single_node(self, temp_dir):
        """Test multiple imports for single node with different logs are imported correctly"""
        log_msgs = ['Life is like riding a bicycle.', 'To keep your balance,', 'you must keep moving.']

        # Create Node and initial log message and save UUIDs prior to export
        node = orm.CalculationNode().store()
        node.seal()
        node.logger.critical(log_msgs[0])
        node_uuid = node.uuid
        log_uuid_existing = orm.QueryBuilder().append(orm.Log, project=['uuid']).all()
        log_uuid_existing = str(log_uuid_existing[0][0])

        # Export as "EXISTING" DB
        export_file_existing = os.path.join(temp_dir, 'export_EXISTING.tar.gz')
        export([node], outfile=export_file_existing, silent=True)

        # Add 2 more Logs and save UUIDs for all three Logs prior to export
        node.logger.critical(log_msgs[1])
        node.logger.critical(log_msgs[2])
        log_uuids_full = orm.QueryBuilder().append(orm.Log, project=['uuid']).all()
        log_uuids_full = [str(log[0]) for log in log_uuids_full]

        # Export as "FULL" DB
        export_file_full = os.path.join(temp_dir, 'export_FULL.tar.gz')
        export([node], outfile=export_file_full, silent=True)

        # Clean database and reimport "EXISTING" DB
        self.reset_database()
        import_data(export_file_existing, silent=True)

        # Check correct import
        builder = orm.QueryBuilder().append(orm.Node, tag='node', project=['uuid'])
        builder.append(orm.Log, with_node='node', project=['uuid', 'message'])
        builder = builder.all()

        self.assertEqual(len(builder), 1)  # There is 1 Log in "EXISTING" DB

        imported_node_uuid = builder[0][0]
        self.assertEqual(imported_node_uuid, node_uuid)

        imported_log_uuid = builder[0][1]
        imported_log_message = builder[0][2]
        self.assertEqual(imported_log_uuid, log_uuid_existing)
        self.assertEqual(imported_log_message, log_msgs[0])

        # Import "FULL" DB
        import_data(export_file_full, silent=True)

        # Since the UUID of the node is identical with the node already in the DB,
        # the Logs should be added to the existing node, avoiding the addition of
        # the single Log already present.
        # Check this by retrieving all Logs for the node.
        builder = orm.QueryBuilder().append(orm.Node, tag='node', project=['uuid'])
        builder.append(orm.Log, with_node='node', project=['uuid', 'message'])
        builder = builder.all()

        self.assertEqual(len(builder), len(log_msgs))  # There should now be 3 Logs

        imported_node_uuid = builder[0][0]
        self.assertEqual(imported_node_uuid, node_uuid)
        for log in builder:
            imported_log_uuid = log[1]
            imported_log_content = log[2]

            self.assertIn(imported_log_uuid, log_uuids_full)
            self.assertIn(imported_log_content, log_msgs)

    @with_temp_dir
    def test_reimport_of_logs_for_single_node(self, temp_dir):
        """
        When a node with logs already exist in the DB, and more logs are imported
        for the same node (same UUID), test that only new log-entries are added.

        Part I:
        Create CalculationNode and 1 Log for it.
        Export CalculationNode with its 1 Log to export file #1 "EXISTING database".
        Add 2 Logs to CalculationNode.
        Export CalculationNode with its 3 Logs to export file #2 "FULL database".
        Reset database.

        Part II:
        Reimport export file #1 "EXISTING database".
        Add 2 Logs to CalculationNode (different UUID than for "FULL database").
        Export CalculationNode with its 3 Logs to export file #3 "NEW database".
        Reset database.

        Part III:
        Reimport export file #1 "EXISTING database" (1 CalculationNode, 1 Log).
        Import export file #2 "FULL database" (1 CalculationNode, 3 Logs).
        Check the database EXACTLY contains 1 CalculationNode and 3 Logs,
        with matching UUIDS all the way through all previous Parts.

        Part IV:
        Import export file #3 "NEW database" (1 CalculationNode, 3 Logs).
        Check the database EXACTLY contains 1 CalculationNode and 5 Logs,
        with matching UUIDS all the way through all previous Parts.
        NB! There should now be 5 Logs in the database. 4 of which are identical
        in pairs, except for their UUID.
        """
        export_filenames = {
            'EXISTING': 'export_EXISTING_db.tar.gz',
            'FULL': 'export_FULL_db.tar.gz',
            'NEW': 'export_NEW_db.tar.gz'
        }

        log_msgs = ['Life is like riding a bicycle.', 'To keep your balance,', 'you must keep moving.']

        ## Part I
        # Create node and save UUID
        calc = orm.CalculationNode()
        calc.store()
        calc.seal()
        calc_uuid = calc.uuid

        # Create first log message
        calc.logger.critical(log_msgs[0])

        # There should be exactly: 1 CalculationNode, 1 Log
        export_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid'])
        export_logs = orm.QueryBuilder().append(orm.Log, project=['uuid'])
        self.assertEqual(export_calcs.count(), 1)
        self.assertEqual(export_logs.count(), 1)

        # Save Log UUID before export
        existing_log_uuids = [str(export_logs.all()[0][0])]

        # Export "EXISTING" DB
        export_file_existing = os.path.join(temp_dir, export_filenames['EXISTING'])
        export([calc], outfile=export_file_existing, silent=True)

        # Add remaining Log messages
        for log_msg in log_msgs[1:]:
            calc.logger.critical(log_msg)

        # There should be exactly: 1 CalculationNode, 3 Logs (len(log_msgs))
        export_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid'])
        export_logs = orm.QueryBuilder().append(orm.Log, project=['uuid'])
        self.assertEqual(export_calcs.count(), 1)
        self.assertEqual(export_logs.count(), len(log_msgs))

        # Save Log UUIDs before export, there should be 3 UUIDs in total (len(log_msgs))
        full_log_uuids = set(existing_log_uuids)
        for log_uuid in export_logs.all():
            full_log_uuids.add(str(log_uuid[0]))
        self.assertEqual(len(full_log_uuids), len(log_msgs))

        # Export "FULL" DB
        export_file_full = os.path.join(temp_dir, export_filenames['FULL'])
        export([calc], outfile=export_file_full, silent=True)

        # Clean database
        self.reset_database()

        ## Part II
        # Reimport "EXISTING" DB
        import_data(export_file_existing, silent=True)

        # Check the database is correctly imported.
        # There should be exactly: 1 CalculationNode, 1 Log
        import_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid'])
        import_logs = orm.QueryBuilder().append(orm.Log, project=['uuid'])
        self.assertEqual(import_calcs.count(), 1)
        self.assertEqual(import_logs.count(), 1)
        # Furthermore, the UUIDs should be the same
        self.assertEqual(str(import_calcs.all()[0][0]), calc_uuid)
        self.assertIn(str(import_logs.all()[0][0]), existing_log_uuids)

        # Add remaining Log messages (again)
        calc = orm.load_node(import_calcs.all()[0][0])
        for log_msg in log_msgs[1:]:
            calc.logger.critical(log_msg)

        # There should be exactly: 1 CalculationNode, 3 Logs (len(log_msgs))
        export_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid'])
        export_logs = orm.QueryBuilder().append(orm.Log, project=['uuid'])
        self.assertEqual(export_calcs.count(), 1)
        self.assertEqual(export_logs.count(), len(log_msgs))

        # Save Log UUIDs before export, there should be 3 UUIDs in total (len(log_msgs))
        new_log_uuids = set(existing_log_uuids)
        for log_uuid in export_logs.all():
            new_log_uuids.add(str(log_uuid[0]))
        self.assertEqual(len(new_log_uuids), len(log_msgs))

        # Export "NEW" DB
        export_file_new = os.path.join(temp_dir, export_filenames['NEW'])
        export([calc], outfile=export_file_new, silent=True)

        # Clean database
        self.reset_database()

        ## Part III
        # Reimport "EXISTING" DB
        import_data(export_file_existing, silent=True)

        # Check the database is correctly imported.
        # There should be exactly: 1 CalculationNode, 1 Log
        import_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid'])
        import_logs = orm.QueryBuilder().append(orm.Log, project=['uuid'])
        self.assertEqual(import_calcs.count(), 1)
        self.assertEqual(import_logs.count(), 1)
        # Furthermore, the UUIDs should be the same
        self.assertEqual(str(import_calcs.all()[0][0]), calc_uuid)
        self.assertIn(str(import_logs.all()[0][0]), existing_log_uuids)

        # Import "FULL" DB
        import_data(export_file_full, silent=True)

        # Check the database is correctly imported.
        # There should be exactly: 1 CalculationNode, 3 Logs (len(log_msgs))
        import_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid'])
        import_logs = orm.QueryBuilder().append(orm.Log, project=['uuid'])
        self.assertEqual(import_calcs.count(), 1)
        self.assertEqual(import_logs.count(), len(log_msgs))
        # Furthermore, the UUIDs should be the same
        self.assertEqual(str(import_calcs.all()[0][0]), calc_uuid)
        for log in import_logs.all():
            log_uuid = str(log[0])
            self.assertIn(log_uuid, full_log_uuids)

        ## Part IV
        # Import "NEW" DB
        import_data(export_file_new, silent=True)

        # Check the database is correctly imported.
        # There should be exactly: 1 CalculationNode, 5 Logs (len(log_msgs))
        # 4 of the logs are identical in pairs, except for the UUID.
        import_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid'])
        import_logs = orm.QueryBuilder().append(orm.Log, project=['uuid', 'message'])
        self.assertEqual(import_calcs.count(), 1)
        self.assertEqual(import_logs.count(), 5)
        # Furthermore, the UUIDs should be the same
        self.assertEqual(str(import_calcs.all()[0][0]), calc_uuid)
        total_log_uuids = full_log_uuids.copy()
        total_log_uuids.update(new_log_uuids)
        for log in import_logs.all():
            log_uuid = str(log[0])
            log_message = str(log[1])
            self.assertIn(log_uuid, total_log_uuids)
            self.assertIn(log_message, log_msgs)
