# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test the update to the ``DbLog`` table."""
import json

from aiida.common import timezone
from aiida.common.utils import get_new_uuid
from aiida.storage.psql_dos.migrator import PsqlDosMigrator


def test_dblog_update(perform_migrations: PsqlDosMigrator):  # pylint: disable=too-many-locals
    """Test the update to the ``DbLog`` table."""
    # starting revision
    perform_migrations.migrate_up('django@django_0023')

    # setup the database
    user_model = perform_migrations.get_current_table('db_dbuser')
    node_model = perform_migrations.get_current_table('db_dbnode')
    wf_model = perform_migrations.get_current_table('db_dbworkflow')
    log_model = perform_migrations.get_current_table('db_dblog')
    with perform_migrations.session() as session:
        user = user_model(
            email='user@aiida.net',
            first_name='John',
            last_name='Doe',
            institution='EPFL',
            password='',
            is_superuser=False,
            is_staff=False,
            is_active=True,
            last_login=timezone.now(),
            date_joined=timezone.now(),
        )
        session.add(user)
        session.commit()
        node_kwargs = {
            'user_id': user.id,
            'ctime': timezone.now(),
            'mtime': timezone.now(),
            'label': 'test',
            'description': '',
            'nodeversion': 1,
            'public': True,
        }
        calc_1 = node_model(uuid=get_new_uuid(), type='node.process.calculation.CalculationNode.', **node_kwargs)
        calc_2 = node_model(uuid=get_new_uuid(), type='node.process.calculation.CalculationNode.', **node_kwargs)
        param = node_model(uuid=get_new_uuid(), type='data.core.dict.Dict.', **node_kwargs)
        session.add_all([calc_1, calc_2, param])
        session.commit()
        leg_workf = wf_model(
            label='Legacy WorkflowNode',
            uuid=get_new_uuid(),
            user_id=user.id,
            ctime=timezone.now(),
            mtime=timezone.now(),
            module='',
            module_class='',
            lastsyncedversion=1,
            nodeversion=1,
            report='',
            script_md5='',
            script_path='',
            state='',
            description='',
        )
        session.add(leg_workf)
        session.commit()

        # Creating the corresponding log records
        log_1 = log_model(
            loggername='CalculationNode logger',
            levelname='INFO',
            time=timezone.now(),
            objpk=calc_1.id,
            objname='node.calculation.job.quantumespresso.pw.',
            message='calculation node 1',
            metadata=json.dumps({
                'msecs': 719.0849781036377,
                'objpk': calc_1.id,
                'lineno': 350,
                'thread': 140011612940032,
                'asctime': '10/21/2018 12:39:51 PM',
                'created': 1540118391.719085,
                'levelno': 23,
                'message': 'calculation node 1',
                'objname': 'node.calculation.job.quantumespresso.pw.',
            })
        )
        log_2 = log_model(
            loggername='something.else logger',
            levelname='INFO',
            time=timezone.now(),
            objpk=param.id,
            objname='something.else.',
            message='parameter data with log message',
            metadata='{}'
        )
        log_3 = log_model(
            loggername='TopologicalWorkflow logger',
            levelname='INFO',
            time=timezone.now(),
            objpk=leg_workf.id,
            objname='aiida.workflows.user.topologicalworkflows.topo.TopologicalWorkflow',
            message='parameter data with log message',
            metadata='{}'
        )
        log_4 = log_model(
            loggername='CalculationNode logger',
            levelname='INFO',
            time=timezone.now(),
            objpk=calc_2.id,
            objname='node.calculation.job.quantumespresso.pw.',
            message='calculation node 2',
            metadata=json.dumps({
                'msecs': 719.0849781036377,
                'objpk': calc_2.id,
                'lineno': 360,
                'levelno': 23,
                'message': 'calculation node 1',
                'objname': 'node.calculation.job.quantumespresso.pw.',
            })
        )
        # Creating two more log records that don't correspond to a node
        log_5 = log_model(
            loggername='CalculationNode logger',
            levelname='INFO',
            time=timezone.now(),
            objpk=(calc_2.id + 1000),
            objname='node.calculation.job.quantumespresso.pw.',
            message='calculation node 1000',
            metadata=json.dumps({
                'msecs': 718,
                'objpk': (calc_2.id + 1000),
                'lineno': 361,
                'levelno': 25,
                'message': 'calculation node 1000',
                'objname': 'node.calculation.job.quantumespresso.pw.',
            })
        )
        log_6 = log_model(
            loggername='CalculationNode logger',
            levelname='INFO',
            time=timezone.now(),
            objpk=(calc_2.id + 1001),
            objname='node.calculation.job.quantumespresso.pw.',
            message='calculation node 10001',
            metadata=json.dumps({
                'msecs': 722,
                'objpk': (calc_2.id + 1001),
                'lineno': 362,
                'levelno': 24,
                'message': 'calculation node 1001',
                'objname': 'node.calculation.job.quantumespresso.pw.',
            })
        )
        session.add_all([log_1, log_2, log_3, log_4, log_5, log_6])
        session.commit()

        log_1_id = log_1.id
        log_4_id = log_4.id

    # final revision
    perform_migrations.migrate_up('django@django_0024')

    log_model = perform_migrations.get_current_table('db_dblog')
    with perform_migrations.session() as session:
        logs = session.query(log_model).all()
        # verify that there are only two log records left
        assert len(logs) == 2
        # verify that they correspond to the CalculationNodes
        assert {log.id for log in logs} == {log_1_id, log_4_id}
        # check the uuid's are unique
        assert len({log.uuid for log in logs}) == 2
