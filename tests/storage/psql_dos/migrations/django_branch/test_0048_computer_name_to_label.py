# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test the renaming of `name` to `label` for `db_dbcomputer`."""
from aiida.common.utils import get_new_uuid
from aiida.storage.psql_dos.migrator import PsqlDosMigrator


def test_computer_name_to_label(perform_migrations: PsqlDosMigrator):
    """Test the renaming of `name` to `label` for `db_dbcomputer`.

    Verify that the column was successfully renamed.
    """
    # starting revision
    perform_migrations.migrate_up('django@django_0047')

    # setup the database
    comp_model = perform_migrations.get_current_table('db_dbcomputer')
    with perform_migrations.session() as session:
        computer = comp_model(
            name='testing',
            uuid=get_new_uuid(),
            hostname='localhost',
            description='',
            transport_type='',
            scheduler_type='',
            metadata={},
        )
        session.add(computer)
        session.commit()
        computer_id = computer.id

    # migrate up
    perform_migrations.migrate_up('django@django_0048')

    # perform some checks
    comp_model = perform_migrations.get_current_table('db_dbcomputer')
    with perform_migrations.session() as session:
        computer = session.query(comp_model).filter(comp_model.id == computer_id).one()
        assert computer.label == 'testing'
