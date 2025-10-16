###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test `TrajectoryData` nodes migration, moving symbol lists from repository array to attributes."""

import numpy
import pytest

from aiida.common import timezone
from aiida.common.utils import get_new_uuid
from aiida.storage.psql_dos.backend import get_filepath_container
from aiida.storage.psql_dos.migrations.utils import utils
from aiida.storage.psql_dos.migrations.utils.create_dbattribute import create_rows
from aiida.storage.psql_dos.migrator import PsqlDosMigrator


def test_traj_data(perform_migrations: PsqlDosMigrator):
    """Test `TrajectoryData` nodes migration, moving symbol lists from repository array to attributes."""
    # starting revision
    perform_migrations.migrate_up('django@django_0025')

    repo_path = get_filepath_container(perform_migrations.profile).parent

    # setup the database
    user_model = perform_migrations.get_current_table('db_dbuser')
    node_model = perform_migrations.get_current_table('db_dbnode')
    attr_model = perform_migrations.get_current_table('db_dbattribute')
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
        node = node_model(uuid=get_new_uuid(), type='node.data.array.trajectory.TrajectoryData.', **kwargs)
        session.add(node)
        session.commit()
        node_id = node.id
        node_uuid = node.uuid

        name = 'symbols'
        array = numpy.array(['H', 'O', 'C'])

        utils.store_numpy_array_in_repository(repo_path, node.uuid, name, array)
        array_key = f'array|{name}'
        array_shape = list(array.shape)
        rows = create_rows(array_key, array_shape, node_id)
        session.add_all([attr_model(**row) for row in rows])
        session.commit()

    # final revision
    perform_migrations.migrate_up('django@django_0027')

    # it should no longer be in the repository
    with pytest.raises(OSError):
        utils.load_numpy_array_from_repository(repo_path, node_uuid, name)

    # and instead, it should be in the attributes
    attr_model = perform_migrations.get_current_table('db_dbattribute')
    with perform_migrations.session() as session:
        rows = session.query(attr_model).filter(attr_model.key.startswith('array|')).order_by(attr_model.key).all()
        assert len(rows) == 0
        rows = session.query(attr_model).filter(attr_model.key.startswith(name)).order_by(attr_model.key).all()
        data = [{x.name: getattr(row, x.name) for x in row.__table__.columns if x.name != 'id'} for row in rows]
        assert data == [
            {
                'datatype': 'list',
                'dbnode_id': node_id,
                'key': 'symbols',
                'bval': None,
                'ival': 3,
                'fval': None,
                'tval': '',
                'dval': None,
            },
            {
                'datatype': 'txt',
                'dbnode_id': node_id,
                'key': 'symbols.0',
                'bval': None,
                'ival': None,
                'fval': None,
                'tval': 'H',
                'dval': None,
            },
            {
                'datatype': 'txt',
                'dbnode_id': node_id,
                'key': 'symbols.1',
                'bval': None,
                'ival': None,
                'fval': None,
                'tval': 'O',
                'dval': None,
            },
            {
                'datatype': 'txt',
                'dbnode_id': node_id,
                'key': 'symbols.2',
                'bval': None,
                'ival': None,
                'fval': None,
                'tval': 'C',
                'dval': None,
            },
        ]
