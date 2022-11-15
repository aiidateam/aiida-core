# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test alterations to `db_dbnode.type`values."""
from aiida.common import timezone
from aiida.common.utils import get_new_uuid
from aiida.storage.psql_dos.migrator import PsqlDosMigrator


def test_node_repository(perform_migrations: PsqlDosMigrator):
    """Test migration adding the `repository_metadata` column to the `Node` model."""
    # starting revision
    perform_migrations.migrate_up('django@django_0027')

    # setup the database
    user_model = perform_migrations.get_current_table('db_dbuser')
    node_model = perform_migrations.get_current_table('db_dbnode')
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
        kwargs = dict(
            user_id=user.id,
            ctime=timezone.now(),
            mtime=timezone.now(),
            label='test',
            description='',
            nodeversion=1,
            public=True,
        )
        node_calc = node_model(uuid=get_new_uuid(), type='node.process.calculation.calcjob.CalcJobNode.', **kwargs)
        node_data = node_model(uuid=get_new_uuid(), type='node.data.int.Int.', **kwargs)
        node_paramdata = node_model(uuid=get_new_uuid(), type='node.data.parameter.ParameterData.', **kwargs)
        session.add_all((node_calc, node_data, node_paramdata))
        session.commit()
        node_calc_id = node_calc.id
        node_data_id = node_data.id
        node_paramdata_id = node_paramdata.id

    # final revision
    perform_migrations.migrate_up('django@django_0029')

    node_model = perform_migrations.get_current_table('db_dbnode')
    with perform_migrations.session() as session:
        node_calc = session.get(node_model, node_calc_id)
        assert node_calc.type == 'process.calculation.calcjob.CalcJobNode.'
        node_data = session.get(node_model, node_data_id)
        assert node_data.type == 'data.int.Int.'
        node_paramdata = session.get(node_model, node_paramdata_id)
        assert node_paramdata.type == 'data.dict.Dict.'
