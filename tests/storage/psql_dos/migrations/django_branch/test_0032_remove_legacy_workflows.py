###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test removing legacy workflows."""

from aiida.common import timezone
from aiida.common.utils import get_new_uuid
from aiida.storage.psql_dos.migrator import PsqlDosMigrator


def test_node_repository(perform_migrations: PsqlDosMigrator):
    """Test removing legacy workflows."""
    # starting revision
    perform_migrations.migrate_up('django@django_0031')

    # setup the database
    user_model = perform_migrations.get_current_table('db_dbuser')
    node_model = perform_migrations.get_current_table('db_dbnode')
    wf_model = perform_migrations.get_current_table('db_dbworkflow')
    wfdata_model = perform_migrations.get_current_table('db_dbworkflowdata')
    wfstep_model = perform_migrations.get_current_table('db_dbworkflowstep')
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
        node_calc = node_model(
            uuid=get_new_uuid(),
            node_type='node.process.calculation.calcjob.CalcJobNode.',
            user_id=user.id,
            ctime=timezone.now(),
            mtime=timezone.now(),
            label='test',
            description='',
            nodeversion=1,
            public=True,
        )
        session.add(node_calc)
        session.commit()
        workflow = wf_model(
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
        session.add(workflow)
        session.commit()
        workflow_data = wfdata_model(
            parent_id=workflow.id,
            aiida_obj_id=node_calc.id,
            time=timezone.now(),
            name='',
            data_type='dict',
            value_type='dict',
            json_value='{}',
        )
        session.add(workflow_data)
        session.commit()
        workflow_step = wfstep_model(
            user_id=user.id,
            parent_id=workflow.id,
            time=timezone.now(),
            name='',
            nextcall='',
            state='',
        )
        session.add(workflow_step)
        session.commit()

    # final revision
    perform_migrations.migrate_up('django@django_0032')
