# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests 61fc0913fae9 -> d254fdfed416"""
from aiida.storage.psql_dos.migrator import PsqlDosMigrator


def test_parameter_data_to_dict(perform_migrations: PsqlDosMigrator):
    """Test the data migration after `ParameterData` was renamed to `Dict`.

    Verify that type string of the Data node was successfully adapted.
    """
    # starting revision
    perform_migrations.migrate_up('sqlalchemy@61fc0913fae9')  # 61fc0913fae9_remove_node_prefix

    # setup the database
    DbNode = perform_migrations.get_current_table('db_dbnode')  # pylint: disable=invalid-name
    DbUser = perform_migrations.get_current_table('db_dbuser')  # pylint: disable=invalid-name
    with perform_migrations.session() as session:
        user = DbUser(email='user@aiida.net', is_superuser=True)
        session.add(user)
        session.commit()

        node = DbNode(type='data.parameter.ParameterData.', user_id=user.id)

        session.add(node)
        session.commit()

        node_id = node.id

    # migrate up
    perform_migrations.migrate_up('sqlalchemy@d254fdfed416')  # d254fdfed416_rename_parameter_data_to_dict

    # perform some checks
    DbNode = perform_migrations.get_current_table('db_dbnode')  # pylint: disable=invalid-name
    with perform_migrations.session() as session:
        node = session.query(DbNode).filter(DbNode.id == node_id).one()
        assert node.type == 'data.dict.Dict.'
