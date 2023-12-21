###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# ruff: noqa: N806
"""Tests for the provenance redesign: 140c971ae0a3 -> 239cea6d2452"""
from aiida.storage.psql_dos.migrator import PsqlDosMigrator


def test_provenance_redesign(perform_migrations: PsqlDosMigrator):
    """Test the data migration part of the provenance redesign migration.

    Verify that type string of the Data node are successfully adapted.
    """
    # starting revision
    perform_migrations.migrate_up('sqlalchemy@140c971ae0a3')  # 140c971ae0a3_migrate_builtin_calculations

    # setup the database
    DbNode = perform_migrations.get_current_table('db_dbnode')
    DbUser = perform_migrations.get_current_table('db_dbuser')
    with perform_migrations.session() as session:
        user = DbUser(email='user@aiida.net', is_superuser=True)
        session.add(user)
        session.commit()

        node_calc_job_known = DbNode(type='calculation.job.arithmetic.add.ArithmeticAddCalculation.', user_id=user.id)
        node_calc_job_unknown = DbNode(type='calculation.job.unknown.PluginJobCalculation.', user_id=user.id)
        node_process = DbNode(type='calculation.process.ProcessCalculation.', user_id=user.id)
        node_work_chain = DbNode(type='calculation.work.WorkCalculation.', user_id=user.id)
        node_work_function = DbNode(
            type='calculation.work.WorkCalculation.', attributes={'function_name': 'test'}, user_id=user.id
        )
        node_inline = DbNode(type='calculation.inline.InlineCalculation.', user_id=user.id)
        node_function = DbNode(type='calculation.function.FunctionCalculation.', user_id=user.id)

        session.add(node_calc_job_known)
        session.add(node_calc_job_unknown)
        session.add(node_process)
        session.add(node_work_chain)
        session.add(node_work_function)
        session.add(node_inline)
        session.add(node_function)
        session.commit()

        node_calc_job_known_id = node_calc_job_known.id
        node_calc_job_unknown_id = node_calc_job_unknown.id
        node_process_id = node_process.id
        node_work_chain_id = node_work_chain.id
        node_work_function_id = node_work_function.id
        node_inline_id = node_inline.id
        node_function_id = node_function.id

    # migrate up
    perform_migrations.migrate_up('sqlalchemy@239cea6d2452')  # 239cea6d2452_provenance_redesign

    # perform some checks
    DbNode = perform_migrations.get_current_table('db_dbnode')
    with perform_migrations.session() as session:
        # Migration of calculation job with known plugin class
        node_calc_job_known = session.query(DbNode).filter(DbNode.id == node_calc_job_known_id).one()
        assert node_calc_job_known.type == 'node.process.calculation.calcjob.CalcJobNode.'
        # The test below had to be changed when the `core.` prefix was added to the `arithmetic.add` prefix.
        # This indicates that the migration of the process type for these test processes would no longer no work
        # but that only applies to databases that are still at v0.x and this change will go into v2.0, so it is
        # fine to accept that at this point.
        assert node_calc_job_known.process_type == 'arithmetic.add.ArithmeticAddCalculation'

        # Migration of calculation job with unknown plugin class
        node_calc_job_unknown = session.query(DbNode).filter(DbNode.id == node_calc_job_unknown_id).one()
        assert node_calc_job_unknown.type == 'node.process.calculation.calcjob.CalcJobNode.'
        assert node_calc_job_unknown.process_type == 'unknown.PluginJobCalculation'

        # Migration of very old `ProcessNode` class
        node_process = session.query(DbNode).filter(DbNode.id == node_process_id).one()
        assert node_process.type == 'node.process.workflow.workchain.WorkChainNode.'

        # Migration of old `WorkCalculation` class
        node_work_chain = session.query(DbNode).filter(DbNode.id == node_work_chain_id).one()
        assert node_work_chain.type == 'node.process.workflow.workchain.WorkChainNode.'

        # Migration of old `WorkCalculation` class used for work function
        node_work_function = session.query(DbNode).filter(DbNode.id == node_work_function_id).one()
        assert node_work_function.type == 'node.process.workflow.workfunction.WorkFunctionNode.'

        # Migration of old `InlineCalculation` class
        node_inline = session.query(DbNode).filter(DbNode.id == node_inline_id).one()
        assert node_inline.type == 'node.process.calculation.calcfunction.CalcFunctionNode.'

        # Migration of old `FunctionCalculation` class
        node_function = session.query(DbNode).filter(DbNode.id == node_function_id).one()
        assert node_function.type == 'node.process.workflow.workfunction.WorkFunctionNode.'
