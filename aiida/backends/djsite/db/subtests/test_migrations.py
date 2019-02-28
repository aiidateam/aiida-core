# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from six.moves import range

import numpy
import tempfile

from django.apps import apps
from django.db.migrations.executor import MigrationExecutor
from django.db import connection
from aiida.backends.testbase import AiidaTestCase
from aiida.common.exceptions import IntegrityError
from aiida.manage.database.integrity.duplicate_uuid import deduplicate_uuids, verify_uuid_uniqueness


class TestMigrations(AiidaTestCase):
    @property
    def app(self):
        return apps.get_containing_app_config(type(self).__module__).name.split('.')[-1]

    migrate_from = None
    migrate_to = None

    def setUp(self):
        """Go to a specific schema version before running tests."""
        from aiida.orm import autogroup

        self.current_autogroup = autogroup.current_autogroup
        autogroup.current_autogroup = None
        assert self.migrate_from and self.migrate_to, \
            "TestCase '{}' must define migrate_from and migrate_to properties".format(type(self).__name__)
        self.migrate_from = [(self.app, self.migrate_from)]
        self.migrate_to = [(self.app, self.migrate_to)]
        executor = MigrationExecutor(connection)
        self.apps = executor.loader.project_state(self.migrate_from).apps

        # Reverse to the original migration
        executor.migrate(self.migrate_from)

        try:
            self.setUpBeforeMigration()
            # Run the migration to test
            executor = MigrationExecutor(connection)
            executor.loader.build_graph()
            executor.migrate(self.migrate_to)

            self.apps = executor.loader.project_state(self.migrate_to).apps
        except Exception:
            # Bring back the DB to the correct state if this setup part fails
            self._revert_database_schema()
            raise

    def tearDown(self):
        """At the end make sure we go back to the latest schema version."""
        from aiida.orm import autogroup
        self._revert_database_schema()
        autogroup.current_autogroup = self.current_autogroup

    def setUpBeforeMigration(self):
        """Anything to do before running the migrations, which should be implemented in test subclasses."""

    def _revert_database_schema(self):
        """Bring back the DB to the correct state."""
        from ..migrations import LATEST_MIGRATION
        self.migrate_to = [(self.app, LATEST_MIGRATION)]
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)


class TestNoMigrations(AiidaTestCase):

    def test_no_remaining_migrations(self):
        """Verify that no django migrations remain.

        Equivalent to python manage.py makemigrations --check"""

        from django.core.management import call_command

        # Raises SystemExit, if migrations remain
        call_command('makemigrations', '--check', verbosity=0)


class TestDuplicateNodeUuidMigration(TestMigrations):
    migrate_from = '0013_django_1_8'
    migrate_to = '0014_add_node_uuid_unique_constraint'

    def setUpBeforeMigration(self):
        from aiida.orm import Bool, Int

        self.file_name = 'test.temp'
        self.file_content = '#!/bin/bash\n\necho test run\n'

        with tempfile.NamedTemporaryFile(mode='w+') as handle:
            handle.write(self.file_content)
            handle.flush()

            self.nodes_boolean = []
            self.nodes_integer = []
            self.n_bool_duplicates = 2
            self.n_int_duplicates = 4

            node_bool = Bool(True)
            node_bool.put_object_from_file(handle.name, self.file_name)
            node_bool.store()

            node_int = Int(1)
            node_int.put_object_from_file(handle.name, self.file_name)
            node_int.store()

            self.nodes_boolean.append(node_bool)
            self.nodes_integer.append(node_int)

            for i in range(self.n_bool_duplicates):
                node = Bool(True)
                node.backend_entity.dbmodel.uuid = node_bool.uuid
                node.put_object_from_file(handle.name, self.file_name)
                node.store()
                self.nodes_boolean.append(node)

            for i in range(self.n_int_duplicates):
                node = Int(1)
                node.backend_entity.dbmodel.uuid = node_int.uuid
                node.put_object_from_file(handle.name, self.file_name)
                node.store()
                self.nodes_integer.append(node)

        # Verify that there are duplicate UUIDs by checking that the following function raises
        with self.assertRaises(IntegrityError):
            verify_uuid_uniqueness(table='db_dbnode')

        # Now run the function responsible for solving duplicate UUIDs which would also be called by the user
        # through the `verdi database integrity detect-duplicate-uuid` command
        deduplicate_uuids(table='db_dbnode', dry_run=False)

    def test_deduplicated_uuids(self):
        """Verify that after the migration, all expected nodes are still there with unique UUIDs."""
        from aiida.orm import load_node

        # If the duplicate UUIDs were successfully fixed, the following should not raise.
        verify_uuid_uniqueness(table='db_dbnode')

        # Reload the nodes by PK and check that all UUIDs are now unique
        nodes_boolean = [load_node(node.pk) for node in self.nodes_boolean]
        uuids_boolean = [node.uuid for node in nodes_boolean]
        self.assertEqual(len(set(uuids_boolean)), len(nodes_boolean))

        nodes_integer = [load_node(node.pk) for node in self.nodes_integer]
        uuids_integer = [node.uuid for node in nodes_integer]
        self.assertEqual(len(set(uuids_integer)), len(nodes_integer))

        for node in nodes_boolean:
            with node.open(self.file_name) as handle:
                content = handle.read()
                self.assertEqual(content, self.file_content)


class TestUuidMigration(TestMigrations):
    migrate_from = '0017_drop_dbcalcstate'
    migrate_to = '0018_django_1_11'

    def setUpBeforeMigration(self):
        from aiida.orm import Data

        n = Data().store()
        self.node_uuid = n.uuid
        self.node_id = n.id

    def test_uuid_untouched(self):
        """Verify that Node uuids remain unchanged."""
        from aiida.orm import load_node

        n = load_node(self.node_id)
        self.assertEqual(self.node_uuid, n.uuid)


class TestGroupRenamingMigration(TestMigrations):

    migrate_from = '0021_dbgroup_name_to_label_type_to_type_string'
    migrate_to = '0022_dbgroup_type_string_change_content'

    def setUpBeforeMigration(self):
        # Create group
        DbGroup = self.apps.get_model('db', 'DbGroup')
        default_user = self.backend.users.create("{}@aiida.net".format(self.id())).store()

        # test user group type_string: '' -> 'user'
        group_user = DbGroup(label='test_user_group', user_id=default_user.id, type_string='')
        group_user.save()
        self.group_user_pk = group_user.pk

        # test data.upf group type_string: 'data.upf.family' -> 'data.upf'
        group_data_upf = DbGroup(label='test_data_upf_group', user_id=default_user.id, type_string='data.upf.family')
        group_data_upf.save()
        self.group_data_upf_pk = group_data_upf.pk

        # test auto.import group type_string: 'aiida.import' -> 'auto.import'
        group_autoimport = DbGroup(label='test_import_group', user_id=default_user.id, type_string='aiida.import')
        group_autoimport.save()
        self.group_autoimport_pk = group_autoimport.pk

        # test auto.run group type_string: 'autogroup.run' -> 'auto.run'
        group_autorun = DbGroup(label='test_autorun_group', user_id=default_user.id, type_string='autogroup.run')
        group_autorun.save()
        self.group_autorun_pk = group_autorun.pk

    def test_group_string_update(self):
        DbGroup = self.apps.get_model('db', 'DbGroup')

        # test user group type_string: '' -> 'user'
        group_user = DbGroup.objects.get(pk=self.group_user_pk)
        self.assertEqual(group_user.type_string, 'user')

        # test data.upf group type_string: 'data.upf.family' -> 'data.upf'
        group_data_upf = DbGroup.objects.get(pk=self.group_data_upf_pk)
        self.assertEqual(group_data_upf.type_string, 'data.upf')

        # test auto.import group type_string: 'aiida.import' -> 'auto.import'
        group_autoimport = DbGroup.objects.get(pk=self.group_autoimport_pk)
        self.assertEqual(group_autoimport.type_string, 'auto.import')

        # test auto.run group type_string: 'autogroup.run' -> 'auto.run'
        group_autorun = DbGroup.objects.get(pk=self.group_autorun_pk)
        self.assertEqual(group_autorun.type_string, 'auto.run')


class TestCalcAttributeKeysMigration(TestMigrations):

    migrate_from = '0022_dbgroup_type_string_change_content'
    migrate_to = '0023_calc_job_option_attribute_keys'

    KEY_RESOURCES_OLD = 'jobresource_params'
    KEY_RESOURCES_NEW = 'resources'
    KEY_PARSER_NAME_OLD = 'parser'
    KEY_PARSER_NAME_NEW = 'parser_name'
    KEY_PROCESS_LABEL_OLD = '_process_label'
    KEY_PROCESS_LABEL_NEW = 'process_label'
    KEY_ENVIRONMENT_VARIABLES_OLD = 'custom_environment_variables'
    KEY_ENVIRONMENT_VARIABLES_NEW = 'environment_variables'

    def setUpBeforeMigration(self):
        from aiida.orm import WorkflowNode, CalcJobNode

        self.process_label = 'TestLabel'
        self.resources = {'number_machines': 1}
        self.environment_variables = {}
        self.parser_name = 'aiida.parsers:parser'

        # We need to explicitly set the node type here to what they were at the time of this migration, because that
        # is also what the SQL targets. If we weren't to set it, it would get the current ORM node types which are not
        # considered by the update SQL statements, as they should not be
        self.node_work = WorkflowNode()
        self.node_work.backend_entity.dbmodel.type = 'node.process.workflow.WorkflowNode.'
        self.node_work.set_attribute(self.KEY_PROCESS_LABEL_OLD, self.process_label)
        self.node_work.store()

        self.node_calc = CalcJobNode(computer=self.computer)
        self.node_calc.backend_entity.dbmodel.type = 'node.process.calculation.calcjob.CalcJobNode.'
        self.node_calc._validate = lambda: True  # Need to disable the validation because we cannot set `resources`
        self.node_calc.set_attribute(self.KEY_PROCESS_LABEL_OLD, self.process_label)
        self.node_calc.set_attribute(self.KEY_RESOURCES_OLD, self.resources)
        self.node_calc.set_attribute(self.KEY_ENVIRONMENT_VARIABLES_OLD, self.environment_variables)
        self.node_calc.set_attribute(self.KEY_PARSER_NAME_OLD, self.parser_name)
        self.node_calc.store()

    def test_attribute_key_changes(self):
        """Verify that the keys are successfully changed of the affected attributes."""
        from aiida.orm import load_node

        NOT_FOUND = tuple([0])

        node_work = load_node(self.node_work.pk)
        self.assertEqual(node_work.get_attribute(self.KEY_PROCESS_LABEL_NEW), self.process_label)
        self.assertEqual(node_work.get_attribute(self.KEY_PROCESS_LABEL_OLD, default=NOT_FOUND), NOT_FOUND)

        node_calc = load_node(self.node_calc.pk)
        self.assertEqual(node_calc.get_attribute(self.KEY_PROCESS_LABEL_NEW), self.process_label)
        self.assertEqual(node_calc.get_attribute(self.KEY_RESOURCES_NEW), self.resources)
        self.assertEqual(node_calc.get_attribute(self.KEY_ENVIRONMENT_VARIABLES_NEW), self.environment_variables)
        self.assertEqual(node_calc.get_attribute(self.KEY_PARSER_NAME_NEW), self.parser_name)
        self.assertEqual(node_calc.get_attribute(self.KEY_PROCESS_LABEL_OLD, default=NOT_FOUND), NOT_FOUND)
        self.assertEqual(node_calc.get_attribute(self.KEY_RESOURCES_OLD, default=NOT_FOUND), NOT_FOUND)
        self.assertEqual(node_calc.get_attribute(self.KEY_ENVIRONMENT_VARIABLES_OLD, default=NOT_FOUND), NOT_FOUND)
        self.assertEqual(node_calc.get_attribute(self.KEY_PARSER_NAME_OLD, default=NOT_FOUND), NOT_FOUND)


class TestDbLogMigrationRecordCleaning(TestMigrations):

    migrate_from = '0023_calc_job_option_attribute_keys'
    migrate_to = '0024_dblog_update'

    def setUpBeforeMigration(self):
        import json
        import importlib
        from aiida.backends.sqlalchemy.utils import dumps_json

        update_024 = importlib.import_module('aiida.backends.djsite.db.migrations.0024_dblog_update')

        DbUser = self.apps.get_model('db', 'DbUser')
        DbNode = self.apps.get_model('db', 'DbNode')
        DbWorkflow = self.apps.get_model('db', 'DbWorkflow')
        DbLog = self.apps.get_model('db', 'DbLog')

        # Creating the user & saving it
        user = DbUser(is_superuser=False, email="{}@aiida.net".format(self.id()))
        user.save()

        # Creating the needed nodes & workflows
        calc_1 = DbNode(type="node.process.calculation.CalculationNode.", user_id=user.id)
        param = DbNode(type="data.dict.Dict.", user_id=user.id)
        leg_workf = DbWorkflow(label="Legacy WorkflowNode", user_id=user.id)
        calc_2 = DbNode(type="node.process.calculation.CalculationNode.", user_id=user.id)

        # Storing them
        calc_1.save()
        param.save()
        leg_workf.save()
        calc_2.save()

        # Creating the corresponding log records and storing them
        log_1 = DbLog(
            loggername='CalculationNode logger',
            objpk=calc_1.pk,
            objname='node.calculation.job.quantumespresso.pw.',
            message='calculation node 1',
            metadata=json.dumps({
                "msecs": 719.0849781036377,
                "objpk": calc_1.pk,
                "lineno": 350,
                "thread": 140011612940032,
                "asctime": "10/21/2018 12:39:51 PM",
                "created": 1540118391.719085,
                "levelno": 23,
                "message": "calculation node 1",
                "objname": "node.calculation.job.quantumespresso.pw.",
            }))
        log_2 = DbLog(
            loggername='something.else logger',
            objpk=param.pk,
            objname='something.else.',
            message='parameter data with log message')
        log_3 = DbLog(
            loggername='TopologicalWorkflow logger',
            objpk=leg_workf.pk,
            objname='aiida.workflows.user.topologicalworkflows.topo.TopologicalWorkflow',
            message='parameter data with log message')
        log_4 = DbLog(
            loggername='CalculationNode logger',
            objpk=calc_2.pk,
            objname='node.calculation.job.quantumespresso.pw.',
            message='calculation node 2',
            metadata=json.dumps({
                "msecs": 719.0849781036377,
                "objpk": calc_2.pk,
                "lineno": 360,
                "levelno": 23,
                "message": "calculation node 1",
                "objname": "node.calculation.job.quantumespresso.pw.",
            }))
        # Creating two more log records that don't correspond to a node
        log_5 = DbLog(
            loggername='CalculationNode logger',
            objpk=(calc_2.pk + 1000),
            objname='node.calculation.job.quantumespresso.pw.',
            message='calculation node 1000',
            metadata=json.dumps({
                "msecs": 718,
                "objpk": (calc_2.pk + 1000),
                "lineno": 361,
                "levelno": 25,
                "message": "calculation node 1000",
                "objname": "node.calculation.job.quantumespresso.pw.",
            }))
        log_6 = DbLog(
            loggername='CalculationNode logger',
            objpk=(calc_2.pk + 1001),
            objname='node.calculation.job.quantumespresso.pw.',
            message='calculation node 10001',
            metadata=json.dumps({
                "msecs": 722,
                "objpk": (calc_2.pk + 1001),
                "lineno": 362,
                "levelno": 24,
                "message": "calculation node 1001",
                "objname": "node.calculation.job.quantumespresso.pw.",
            }))

        # Storing the log records
        log_1.save()
        log_2.save()
        log_3.save()
        log_4.save()
        log_5.save()
        log_6.save()

        # Storing temporarily information needed for the check at the test
        self.to_check = dict()

        # Keeping calculation & calculation log ids
        self.to_check['CalculationNode'] = (
            calc_1.pk,
            log_1.pk,
            calc_2.pk,
            log_4.pk,
        )

        # Getting the serialized Dict logs
        param_data = DbLog.objects.filter(objpk=param.pk).filter(objname='something.else.').values(
            *update_024.values_to_export)[:1]
        serialized_param_data = dumps_json(list(param_data))
        # Getting the serialized logs for the unknown entity logs (as the export migration fuction
        # provides them) - this should coincide to the above
        serialized_unknown_exp_logs = update_024.get_serialized_unknown_entity_logs(DbLog)
        # Getting their number
        unknown_exp_logs_number = update_024.get_unknown_entity_log_number(DbLog)
        self.to_check['Dict'] = (serialized_param_data, serialized_unknown_exp_logs,
                                          unknown_exp_logs_number)

        # Getting the serialized legacy workflow logs
        leg_wf = DbLog.objects.filter(
            objpk=leg_workf.pk).filter(
            objname='aiida.workflows.user.topologicalworkflows.topo.TopologicalWorkflow').values(
            *update_024.values_to_export)[:1]
        serialized_leg_wf_logs = dumps_json(list(leg_wf))
        # Getting the serialized logs for the legacy workflow logs (as the export migration function
        # provides them) - this should coincide to the above
        serialized_leg_wf_exp_logs = update_024.get_serialized_legacy_workflow_logs(DbLog)
        eg_wf_exp_logs_number = update_024.get_legacy_workflow_log_number(DbLog)
        self.to_check['WorkflowNode'] = (serialized_leg_wf_logs, serialized_leg_wf_exp_logs, eg_wf_exp_logs_number)

        # Getting the serialized logs that don't correspond to a DbNode record
        logs_no_node = DbLog.objects.filter(
            id__in=[log_5.id, log_6.id]).values(
            *update_024.values_to_export)
        serialized_logs_no_node = dumps_json(list(logs_no_node))
        # Getting the serialized logs that don't correspond to a node (as the export migration function
        # provides them) - this should coincide to the above
        serialized_logs_exp_no_node = update_024.get_serialized_logs_with_no_nodes(DbLog, DbNode)
        logs_no_node_number = update_024.get_logs_with_no_nodes_number(DbLog, DbNode)
        self.to_check['NoNode'] = (serialized_logs_no_node, serialized_logs_exp_no_node, logs_no_node_number)

    def tearDown(self):
        """Cleaning the DbLog, DbUser, DbWorkflow and DbNode records"""
        DbUser = self.apps.get_model('db', 'DbUser')
        DbNode = self.apps.get_model('db', 'DbNode')
        DbWorkflow = self.apps.get_model('db', 'DbWorkflow')
        DbLog = self.apps.get_model('db', 'DbLog')

        DbLog.objects.all().delete()
        DbNode.objects.all().delete()  # pylint: disable=no-member
        DbWorkflow.objects.all().delete()  # pylint: disable=no-member
        DbUser.objects.all().delete()  # pylint: disable=no-member
        super(TestDbLogMigrationRecordCleaning, self).tearDown()

    def test_dblog_calculation_node(self):
        """
        Verify that after the migration there is only two log records left and verify that they corresponds to
        the CalculationNodes.
        """
        DbLog = self.apps.get_model('db', 'DbLog')

        # Check that only two log records exist
        self.assertEqual(DbLog.objects.count(), 2, "There should be two log records left")

        # Get the node id of the log record referencing the node and verify that it is the correct one
        dbnode_id_1 = DbLog.objects.filter(
            pk=self.to_check['CalculationNode'][1]).values('dbnode_id')[:1].get()['dbnode_id']
        self.assertEqual(dbnode_id_1, self.to_check['CalculationNode'][0], "The referenced node is not "
                          "the expected one")
        dbnode_id_2 = DbLog.objects.filter(
            pk=self.to_check['CalculationNode'][3]).values('dbnode_id')[:1].get()['dbnode_id']
        self.assertEqual(dbnode_id_2, self.to_check['CalculationNode'][2], "The referenced node is not "
                          "the expected one")

    def test_dblog_correct_export_of_logs(self):
        """
        Verify that export log methods for legacy workflows, unknown entities and log records that
        don't correspond to nodes, work as expected
        """
        import json

        self.assertEqual(self.to_check['Dict'][0], self.to_check['Dict'][1])
        self.assertEqual(self.to_check['Dict'][2], 1)

        self.assertEqual(self.to_check['WorkflowNode'][0], self.to_check['WorkflowNode'][1])
        self.assertEqual(self.to_check['WorkflowNode'][2], 1)

        self.assertEqual(sorted(list(json.loads(self.to_check['NoNode'][0])), key=lambda k: k['id']),
                          sorted(list(json.loads(self.to_check['NoNode'][1])), key=lambda k: k['id']))
        self.assertEqual(self.to_check['NoNode'][2], 2)

    def test_dblog_unique_uuids(self):
        """
        Verify that the UUIDs of the log records are unique
        """
        DbLog = self.apps.get_model('db', 'DbLog')

        l_uuids = list(_['uuid'] for _ in DbLog.objects.values('uuid'))
        s_uuids = set(l_uuids)
        self.assertEqual(len(l_uuids), len(s_uuids), "The UUIDs are not all unique.")

    def test_metadata_correctness(self):
        """
        Verify that the metadata of the remaining records don't have an objpk and objmetadata values.
        """
        import json

        DbLog = self.apps.get_model('db', 'DbLog')

        metadata = list(json.loads(_['metadata']) for _ in DbLog.objects.values('metadata'))
        # Verify that the objpk and objname are no longer part of the metadata
        for m_res in metadata:
            self.assertNotIn('objpk', m_res.keys(), "objpk should not exist any more in metadata")
            self.assertNotIn('objname', m_res.keys(), "objname should not exist any more in metadata")


class TestDbLogMigrationBackward(TestMigrations):
    """
    Check that backward migrations work also for the DbLog migration(s).
    """
    migrate_from = '0024_dblog_update'
    migrate_to = '0023_calc_job_option_attribute_keys'

    def setUpBeforeMigration(self):
        import json

        DbUser = self.apps.get_model('db', 'DbUser')
        DbNode = self.apps.get_model('db', 'DbNode')
        DbLog = self.apps.get_model('db', 'DbLog')

        # Creating the user & saving it
        user = DbUser(is_superuser=False, email="{}@aiida.net".format(self.id()))
        user.save()

        # Creating the needed nodes & workflows
        calc_1 = DbNode(type="node.process.calculation.CalculationNode.1", user_id=user.id)
        calc_2 = DbNode(type="node.process.calculation.CalculationNode.2", user_id=user.id)

        # Storing them
        calc_1.save()
        calc_2.save()

        # Creating the corresponding log records and storing them
        log_1 = DbLog(
            loggername='CalculationNode logger',
            dbnode_id=calc_1.pk,
            message='calculation node 1',
            metadata=json.dumps({
                "msecs": 719.0849781036377,
                "lineno": 350,
                "thread": 140011612940032,
                "asctime": "10/21/2018 12:39:51 PM",
                "created": 1540118391.719085,
                "levelno": 23,
                "message": "calculation node 1",
            }))
        log_2 = DbLog(
            loggername='CalculationNode logger',
            dbnode_id=calc_2.pk,
            message='calculation node 2',
            metadata=json.dumps({
                "msecs": 719.0849781036377,
                "lineno": 360,
                "levelno": 23,
                "message": "calculation node 1",
            }))

        # Storing the log records
        log_1.save()
        log_2.save()

        # Keeping what is needed to be verified at the test
        self.to_check = dict()
        self.to_check[log_1.pk] = (log_1.dbnode_id, calc_1.type)
        self.to_check[log_2.pk] = (log_2.dbnode_id, calc_2.type)

    def test_objpk_objname(self):
        """
        This test verifies that the objpk and objname have the right values
        after a forward and a backward migration.
        """
        import json
        DbLog = self.apps.get_model('db', 'DbLog')

        # Check that only two log records exist with the correct objpk objname
        for log_pk in self.to_check.keys():
            log_entry = DbLog.objects.filter(pk=log_pk)[:1].get()
            log_dbnode_id, node_type = self.to_check[log_pk]
            self.assertEqual(log_dbnode_id, log_entry.objpk,
                             "The dbnode_id ({}) of the 0024 schema version should be identical to the objpk ({}) of "
                             "the 0023 schema version.".format(log_dbnode_id, log_entry.objpk))
            self.assertEqual(node_type, log_entry.objname,
                             "The type ({}) of the linked node of the 0024 schema version should be identical to the "
                             "objname ({}) of the 0023 schema version.".format(node_type, log_entry.objname))
            self.assertEqual(log_dbnode_id, json.loads(log_entry.metadata)['objpk'],
                             "The dbnode_id ({}) of the 0024 schema version should be identical to the objpk ({}) of "
                             "the 0023 schema version stored in the metadata.".format(
                                 log_dbnode_id, json.loads(log_entry.metadata)['objpk']))
            self.assertEqual(node_type, json.loads(log_entry.metadata)['objname'],
                             "The type ({}) of the linked node of the 0024 schema version should be identical to the "
                             "objname ({}) of the 0023 schema version stored in the metadata.".format(
                                 node_type, json.loads(log_entry.metadata)['objname']))


class TestDataMoveWithinNodeMigration(TestMigrations):

    migrate_from = '0024_dblog_update'
    migrate_to = '0025_move_data_within_node_module'

    def setUpBeforeMigration(self):
        DbNode = self.apps.get_model('db', 'DbNode')

        default_user = self.backend.users.create("{}@aiida.net".format(self.id())).store()

        node_calc = DbNode(type='node.process.calculation.calcjob.CalcJobNode.', user_id=default_user.id)
        node_data = DbNode(type='data.int.Int.', user_id=default_user.id)
        node_calc.save()
        node_data.save()

        self.node_calc_id = node_calc.id
        self.node_data_id = node_data.id

    def test_data_node_type_string(self):
        """Verify that type string of the Data node was successfully adapted."""
        from aiida.orm import load_node

        node_calc = load_node(self.node_calc_id)
        node_data = load_node(self.node_data_id)

        self.assertEqual(node_data.type, 'node.data.int.Int.')
        self.assertEqual(node_calc.type, 'node.process.calculation.calcjob.CalcJobNode.')


class TestTrajectoryDataMigration(TestMigrations):

    migrate_from = '0025_move_data_within_node_module'
    migrate_to = '0027_delete_trajectory_symbols_array'

    # I create sample data
    stepids = numpy.array([60, 70])
    times = stepids * 0.01
    positions = numpy.array([[[0., 0., 0.], [0.5, 0.5, 0.5], [1.5, 1.5, 1.5]], [[0., 0., 0.], [0.5, 0.5, 0.5],
                                                                                     [1.5, 1.5, 1.5]]])
    velocities = numpy.array([[[0., 0., 0.], [0., 0., 0.], [0., 0., 0.]], [[0.5, 0.5, 0.5], [0.5, 0.5, 0.5],
                                                                                [-0.5, -0.5, -0.5]]])
    cells = numpy.array([[[
        2.,
        0.,
        0.,
    ], [
        0.,
        2.,
        0.,
    ], [
        0.,
        0.,
        2.,
    ]], [[
        3.,
        0.,
        0.,
    ], [
        0.,
        3.,
        0.,
    ], [
        0.,
        0.,
        3.,
    ]]])

    def setUpBeforeMigration(self):
        from aiida.orm import TrajectoryData

        # Create a TrajectoryData node
        node = TrajectoryData()
        # We need to explicitly set the node type here to what they were at the time of this migration, because that
        # is also what the SQL targets. If we weren't to set it, it would get the current ORM node types which are not
        # considered by the update SQL statements, as they should not be
        node.backend_entity.dbmodel.type = 'node.data.array.trajectory.TrajectoryData.'
        symbols = numpy.array(['H', 'O', 'C'])

        # I set the node
        node.set_array('steps', self.stepids)
        node.set_array('cells', self.cells)
        node.set_array('symbols', symbols)
        node.set_array('positions', self.positions)
        node.set_array('times', self.times)
        node.set_array('velocities', self.velocities)

        # Reset validate to avoid raising of validation error according to the new TrajectoryData definition
        node._validate = lambda: True
        node.store()

        self.trajectory_pk = node.pk

    def test_trajectory_symbols(self):
        from aiida.orm import load_node
        trajectory = load_node(self.trajectory_pk)
        self.assertSequenceEqual(trajectory.get_attribute('symbols'), ['H', 'O', 'C'])
        self.assertSequenceEqual(trajectory.get_array('velocities').tolist(), self.velocities.tolist())
        self.assertSequenceEqual(trajectory.get_array('positions').tolist(), self.positions.tolist())
        with self.assertRaises(KeyError):
            trajectory.get_array('symbols')


class TestNodePrefixRemovalMigration(TestMigrations):

    migrate_from = '0027_delete_trajectory_symbols_array'
    migrate_to = '0028_remove_node_prefix'

    def setUpBeforeMigration(self):
        DbNode = self.apps.get_model('db', 'DbNode')

        default_user = self.backend.users.create('{}@aiida.net'.format(self.id())).store()

        node_calc = DbNode(type='node.process.calculation.calcjob.CalcJobNode.', user_id=default_user.id)
        node_data = DbNode(type='node.data.int.Int.', user_id=default_user.id)
        node_calc.save()
        node_data.save()

        self.node_calc_id = node_calc.id
        self.node_data_id = node_data.id

    def test_data_node_type_string(self):
        """Verify that type string of the nodes was successfully adapted."""
        from aiida.orm import load_node

        node_calc = load_node(self.node_calc_id)
        node_data = load_node(self.node_data_id)

        self.assertEqual(node_data.type, 'data.int.Int.')
        self.assertEqual(node_calc.type, 'process.calculation.calcjob.CalcJobNode.')


class TestParameterDataToDictMigration(TestMigrations):

    migrate_from = '0028_remove_node_prefix'
    migrate_to = '0029_rename_parameter_data_to_dict'

    def setUpBeforeMigration(self):
        DbNode = self.apps.get_model('db', 'DbNode')

        default_user = self.backend.users.create('{}@aiida.net'.format(self.id())).store()

        node = DbNode(type='data.parameter.ParameterData.', user_id=default_user.id)
        node.save()

        self.node_id = node.id

    def test_data_node_type_string(self):
        """Verify that type string of the nodes was successfully adapted."""
        from aiida.orm import load_node

        node = load_node(self.node_id)

        self.assertEqual(node.type, 'data.dict.Dict.')
