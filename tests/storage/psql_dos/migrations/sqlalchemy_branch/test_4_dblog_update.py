###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# ruff: noqa: N806
"""Tests DbLog migration: 7ca08c391c49 -> 375c2db70663"""

import json

import pytest
from sqlalchemy import column

from aiida.storage.psql_dos.migrations.utils import dblog_update
from aiida.storage.psql_dos.migrator import PsqlDosMigrator

# The values that will be exported for the log records that will be deleted
values_to_export = ('id', 'time', 'loggername', 'levelname', 'objpk', 'objname', 'message', 'metadata')


class TestDbLogMigrationRecordCleaning:
    """Test the migration of the keys of certain attribute for ProcessNodes and CalcJobNodes."""

    migrator: PsqlDosMigrator

    @pytest.fixture(autouse=True)
    def setup_db(self, perform_migrations: PsqlDosMigrator):
        """Setup the database schema."""
        from aiida.storage.psql_dos.migrations.utils.utils import dumps_json

        self.migrator = perform_migrations

        # starting revision
        perform_migrations.migrate_up('sqlalchemy@7ca08c391c49')  # 7ca08c391c49_calc_job_option_attribute_keys

        DbUser = perform_migrations.get_current_table('db_dbuser')
        DbNode = perform_migrations.get_current_table('db_dbnode')
        DbWorkflow = perform_migrations.get_current_table('db_dbworkflow')
        DbLog = perform_migrations.get_current_table('db_dblog')

        with perform_migrations.session() as session:
            user = DbUser(email='user@aiida.net', is_superuser=True)
            session.add(user)
            session.commit()

            calc_1 = DbNode(type='node.process.calculation.CalculationNode.', user_id=user.id)
            param = DbNode(type='data.core.dict.Dict.', user_id=user.id)
            leg_workf = DbWorkflow(label='Legacy WorkflowNode', user_id=user.id)
            calc_2 = DbNode(type='node.process.calculation.CalculationNode.', user_id=user.id)

            session.add(calc_1)
            session.add(param)
            session.add(leg_workf)
            session.add(calc_2)
            session.commit()

            log_1 = DbLog(
                loggername='CalculationNode logger',
                objpk=calc_1.id,
                objname='node.calculation.job.quantumespresso.pw.',
                message='calculation node 1',
                metadata={
                    'msecs': 719.0849781036377,
                    'objpk': calc_1.id,
                    'lineno': 350,
                    'thread': 140011612940032,
                    'asctime': '10/21/2018 12:39:51 PM',
                    'created': 1540118391.719085,
                    'levelno': 23,
                    'message': 'calculation node 1',
                    'objname': 'node.calculation.job.quantumespresso.pw.',
                },
            )
            log_2 = DbLog(
                loggername='something.else logger',
                objpk=param.id,
                objname='something.else.',
                message='parameter data with log message',
            )
            log_3 = DbLog(
                loggername='TopologicalWorkflow logger',
                objpk=leg_workf.id,
                objname='aiida.workflows.user.topologicalworkflows.topo.TopologicalWorkflow',
                message='parameter data with log message',
            )
            log_4 = DbLog(
                loggername='CalculationNode logger',
                objpk=calc_2.id,
                objname='node.calculation.job.quantumespresso.pw.',
                message='calculation node 2',
                metadata={
                    'msecs': 719.0849781036377,
                    'objpk': calc_2.id,
                    'lineno': 360,
                    'levelno': 23,
                    'message': 'calculation node 1',
                    'objname': 'node.calculation.job.quantumespresso.pw.',
                },
            )
            # Creating two more log records that don't correspond to a node
            log_5 = DbLog(
                loggername='CalculationNode logger',
                objpk=(calc_2.id + 1000),
                objname='node.calculation.job.quantumespresso.pw.',
                message='calculation node 1000',
                metadata={
                    'msecs': 718,
                    'objpk': (calc_2.id + 1000),
                    'lineno': 361,
                    'levelno': 25,
                    'message': 'calculation node 1000',
                    'objname': 'node.calculation.job.quantumespresso.pw.',
                },
            )
            log_6 = DbLog(
                loggername='CalculationNode logger',
                objpk=(calc_2.id + 1001),
                objname='node.calculation.job.quantumespresso.pw.',
                message='calculation node 10001',
                metadata={
                    'msecs': 722,
                    'objpk': (calc_2.id + 1001),
                    'lineno': 362,
                    'levelno': 24,
                    'message': 'calculation node 1001',
                    'objname': 'node.calculation.job.quantumespresso.pw.',
                },
            )

            session.add(log_1)
            session.add(log_2)
            session.add(log_3)
            session.add(log_4)
            session.add(log_5)
            session.add(log_6)

            session.commit()

            # Storing temporarily information needed for the check at the test
            self.to_check: dict = {}

            # Keeping calculation & calculation log ids
            self.to_check['CalculationNode'] = (
                calc_1.id,
                log_1.id,
                calc_2.id,
                log_4.id,
            )

            # The columns to project
            cols_to_project = []
            for val in values_to_export:
                cols_to_project.append(getattr(DbLog, val))

            # Getting the serialized Dict logs
            param_data = (
                session.query(DbLog)
                .filter(DbLog.objpk == param.id)
                .filter(DbLog.objname == 'something.else.')
                .with_entities(*cols_to_project)
                .one()
            )
            serialized_param_data = dumps_json([param_data._asdict()])
            # Getting the serialized logs for the unknown entity logs (as the export migration fuction
            # provides them) - this should coincide to the above
            serialized_unknown_exp_logs = dblog_update.get_serialized_unknown_entity_logs(session)
            # Getting their number
            unknown_exp_logs_number = dblog_update.get_unknown_entity_log_number(session)
            self.to_check['Dict'] = (serialized_param_data, serialized_unknown_exp_logs, unknown_exp_logs_number)

            # Getting the serialized legacy workflow logs

            leg_wf = (
                session.query(DbLog)
                .filter(DbLog.objpk == leg_workf.id)
                .filter(DbLog.objname == 'aiida.workflows.user.topologicalworkflows.topo.TopologicalWorkflow')
                .with_entities(*cols_to_project)
                .one()
            )
            serialized_leg_wf_logs = dumps_json([leg_wf._asdict()])
            # Getting the serialized logs for the legacy workflow logs (as the export migration function
            # provides them) - this should coincide to the above
            serialized_leg_wf_exp_logs = dblog_update.get_serialized_legacy_workflow_logs(session)
            eg_wf_exp_logs_number = dblog_update.get_legacy_workflow_log_number(session)
            self.to_check['WorkflowNode'] = (serialized_leg_wf_logs, serialized_leg_wf_exp_logs, eg_wf_exp_logs_number)

            # Getting the serialized logs that don't correspond to a DbNode record
            logs_no_node = (
                session.query(DbLog).filter(DbLog.id.in_([log_5.id, log_6.id])).with_entities(*cols_to_project)
            )
            logs_no_node_list = [log_no_node._asdict() for log_no_node in logs_no_node]
            serialized_logs_no_node = dumps_json(logs_no_node_list)

            # Getting the serialized logs that don't correspond to a node (as the export migration function
            # provides them) - this should coincide to the above
            serialized_logs_exp_no_node = dblog_update.get_serialized_logs_with_no_nodes(session)
            logs_no_node_number = dblog_update.get_logs_with_no_nodes_number(session)
            self.to_check['NoNode'] = (serialized_logs_no_node, serialized_logs_exp_no_node, logs_no_node_number)

        # migrate up
        perform_migrations.migrate_up('sqlalchemy@041a79fc615f')  # 041a79fc615f_dblog_cleaning

        yield

        # We need to manually delete all the workflows created for the test because the model does not exist any more.
        # Because the model does not exist anymore, they are no longer being cleaned in the database reset of the test
        # base class. To prevent foreign keys from other tables still referencing these tables, we have to make sure to
        # clean them here manually, before we call the parent, which will call the standard reset database methods.

        DbWorkflow = perform_migrations.get_current_table('db_dbworkflow')

        with perform_migrations.session() as session:
            session.query(DbWorkflow).delete()
            session.commit()

    def test_dblog_calculation_node(self):
        """Verify that after the migration there is only two log records left and verify that they corresponds to
        the CalculationNodes.
        """
        DbLog = self.migrator.get_current_table('db_dblog')

        with self.migrator.session() as session:
            # Check that only two log records exist
            assert session.query(DbLog).count() == 2, 'There should be two log records left'

            # Get the node id of the log record referencing the node and verify that it is the correct one
            dbnode_id_1 = (
                session.query(DbLog)
                .filter(DbLog.id == self.to_check['CalculationNode'][1])
                .with_entities(column('dbnode_id'))
                .one()[0]
            )
            assert dbnode_id_1 == self.to_check['CalculationNode'][0], (
                'The the referenced node is not ' 'the expected one'
            )
            dbnode_id_2 = (
                session.query(DbLog)
                .filter(DbLog.id == self.to_check['CalculationNode'][3])
                .with_entities(column('dbnode_id'))
                .one()[0]
            )
            assert dbnode_id_2 == self.to_check['CalculationNode'][2], (
                'The the referenced node is not ' 'the expected one'
            )

    def test_dblog_correct_export_of_logs(self):
        """Verify that export log methods for legacy workflows, unknown entities and log records that
        don't correspond to nodes, work as expected
        """
        assert self.to_check['Dict'][0] == self.to_check['Dict'][1]
        assert self.to_check['Dict'][2] == 1

        assert self.to_check['WorkflowNode'][0] == self.to_check['WorkflowNode'][1]
        assert self.to_check['WorkflowNode'][2] == 1

        assert sorted(list(json.loads(self.to_check['NoNode'][0])), key=lambda k: k['id']) == sorted(
            list(json.loads(self.to_check['NoNode'][1])), key=lambda k: k['id']
        )
        assert self.to_check['NoNode'][2] == 2

    def test_metadata_correctness(self):
        """Verify that the metadata of the remaining records don't have an objpk and objmetadata values."""
        DbLog = self.migrator.get_current_table('db_dblog')

        with self.migrator.session() as session:
            metadata = list(session.query(DbLog).with_entities(getattr(DbLog, 'metadata')).all())
            # Verify that the objpk and objname are no longer part of the metadata
            for (m_res,) in metadata:
                assert 'objpk' not in m_res.keys(), 'objpk should not exist any more in metadata'
                assert 'objname' not in m_res.keys(), 'objname should not exist any more in metadata'


def test_dblog_uuid_addition(perform_migrations: PsqlDosMigrator):
    """Test that the UUID column is correctly added to the DbLog table,
    and that the uniqueness constraint is added without problems
    (if the migration arrives until 375c2db70663 then the constraint is added properly).
    """
    # starting revision
    perform_migrations.migrate_up('sqlalchemy@041a79fc615f')  # 041a79fc615f_dblog_cleaning

    # setup the database
    DbLog = perform_migrations.get_current_table('db_dblog')
    DbNode = perform_migrations.get_current_table('db_dbnode')
    DbUser = perform_migrations.get_current_table('db_dbuser')
    with perform_migrations.session() as session:
        user = DbUser(email='user@aiida.net', is_superuser=True)
        session.add(user)
        session.commit()

        calc_1 = DbNode(type='node.process.calculation.CalculationNode.', user_id=user.id)
        calc_2 = DbNode(type='node.process.calculation.CalculationNode.', user_id=user.id)

        session.add(calc_1)
        session.add(calc_2)
        session.commit()

        log_1 = DbLog(loggername='CalculationNode logger', dbnode_id=calc_1.id, message='calculation node 1')
        log_2 = DbLog(loggername='CalculationNode logger', dbnode_id=calc_2.id, message='calculation node 2')

        session.add(log_1)
        session.add(log_2)

        session.commit()

    # migrate up
    perform_migrations.migrate_up('sqlalchemy@375c2db70663')  # 375c2db70663_dblog_uuid_uniqueness_constraint

    # perform some checks
    DbLog = perform_migrations.get_current_table('db_dblog')
    with perform_migrations.session() as session:
        l_uuids = list(session.query(DbLog).with_entities(getattr(DbLog, 'uuid')).all())
        s_uuids = set(l_uuids)
        assert len(l_uuids) == len(s_uuids), 'The UUIDs are not all unique.'
