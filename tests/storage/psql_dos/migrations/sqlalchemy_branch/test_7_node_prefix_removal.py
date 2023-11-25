# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# ruff: noqa: N806
"""Tests ce56d84bcc35 -> 61fc0913fae9"""
from aiida.storage.psql_dos.migrator import PsqlDosMigrator


def test_node_prefix_removal(perform_migrations: PsqlDosMigrator):
    """Test the migration of Data nodes after the data module was moved within the node module.

    Verify that type string of the Data node was successfully adapted.
    """
    # starting revision
    perform_migrations.migrate_up('sqlalchemy@ce56d84bcc35')  # ce56d84bcc35_delete_trajectory_symbols_array

    # setup the database
    DbNode = perform_migrations.get_current_table('db_dbnode')
    DbUser = perform_migrations.get_current_table('db_dbuser')
    with perform_migrations.session() as session:
        user = DbUser(email='user@aiida.net', is_superuser=True)
        session.add(user)
        session.commit()

        node_calc = DbNode(type='node.process.calculation.calcjob.CalcJobNode.', user_id=user.id)
        node_data = DbNode(type='node.data.int.Int.', user_id=user.id)

        session.add(node_data)
        session.add(node_calc)
        session.commit()

        node_calc_id = node_calc.id
        node_data_id = node_data.id

    # migrate up
    perform_migrations.migrate_up('sqlalchemy@61fc0913fae9')  # 61fc0913fae9_remove_node_prefix

    # perform some checks
    DbNode = perform_migrations.get_current_table('db_dbnode')
    with perform_migrations.session() as session:
        # Verify that the `node.` prefix has been dropped from both the data as well as the process node
        node_data = session.query(DbNode).filter(DbNode.id == node_data_id).one()
        assert node_data.type == 'data.int.Int.'

        node_calc = session.query(DbNode).filter(DbNode.id == node_calc_id).one()
        assert node_calc.type == 'process.calculation.calcjob.CalcJobNode.'
