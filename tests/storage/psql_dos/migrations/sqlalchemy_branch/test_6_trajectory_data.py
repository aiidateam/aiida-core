###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# ruff: noqa: N806
# mypy: disable_error_code=var-annotated
"""Tests 37f3d4882837 -> ce56d84bcc35"""

import numpy as np
import pytest

from aiida.storage.psql_dos.backend import get_filepath_container
from aiida.storage.psql_dos.migrations.utils import utils
from aiida.storage.psql_dos.migrator import PsqlDosMigrator
from aiida.storage.psql_dos.utils import flag_modified


def set_node_array(node, repo_path, name, array):
    """Store a new numpy array inside a node. Possibly overwrite the array if it already existed.

    Internally, it stores a name.npy file in numpy format.

    :param name: The name of the array.
    :param array: The numpy array to store.
    """
    utils.store_numpy_array_in_repository(repo_path, node.uuid, name, array)
    attributes = node.attributes
    if attributes is None:
        attributes = {}
    attributes[f'array|{name}'] = list(array.shape)
    node.attributes = attributes
    flag_modified(node, 'attributes')


def get_node_array(node, repo_path, name):
    """Retrieve a numpy array from a node."""
    return utils.load_numpy_array_from_repository(repo_path, node.uuid, name)


def test_trajectory_data(perform_migrations: PsqlDosMigrator):
    """Test the migration of the symbols from numpy array to attribute for TrajectoryData nodes.

    Verify that migration of symbols from repository array to attribute works properly.
    """
    repo_path = get_filepath_container(perform_migrations.profile).parent

    # starting revision
    perform_migrations.migrate_up('sqlalchemy@37f3d4882837')  # 37f3d4882837_make_all_uuid_columns_unique

    # setup the database
    stepids = np.array([60, 70])
    times = stepids * 0.01
    positions = np.array(
        [[[0.0, 0.0, 0.0], [0.5, 0.5, 0.5], [1.5, 1.5, 1.5]], [[0.0, 0.0, 0.0], [0.5, 0.5, 0.5], [1.5, 1.5, 1.5]]]
    )
    velocities = np.array(
        [[[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], [[0.5, 0.5, 0.5], [0.5, 0.5, 0.5], [-0.5, -0.5, -0.5]]]
    )
    cells = np.array(
        [[[2.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 2.0]], [[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]]]
    )
    DbNode = perform_migrations.get_current_table('db_dbnode')
    DbUser = perform_migrations.get_current_table('db_dbuser')
    with perform_migrations.session() as session:
        user = DbUser(email='user@aiida.net', is_superuser=True)
        session.add(user)
        session.commit()

        node = DbNode(type='node.data.array.trajectory.TrajectoryData.', user_id=user.id)
        session.add(node)
        session.commit()

        symbols = np.array(['H', 'O', 'C'])

        set_node_array(node, repo_path, 'steps', stepids)
        set_node_array(node, repo_path, 'cells', cells)
        set_node_array(node, repo_path, 'symbols', symbols)
        set_node_array(node, repo_path, 'positions', positions)
        set_node_array(node, repo_path, 'times', times)
        set_node_array(node, repo_path, 'velocities', velocities)
        session.commit()

        node_uuid = node.uuid

    # migrate up
    perform_migrations.migrate_up('sqlalchemy@ce56d84bcc35')  # ce56d84bcc35_delete_trajectory_symbols_array

    # perform some checks
    DbNode = perform_migrations.get_current_table('db_dbnode')
    with perform_migrations.session() as session:
        node = session.query(DbNode).filter(DbNode.uuid == node_uuid).one()

        assert node.attributes['symbols'] == ['H', 'O', 'C']
        assert get_node_array(node, repo_path, 'velocities').tolist() == velocities.tolist()
        assert get_node_array(node, repo_path, 'positions').tolist() == positions.tolist()
        with pytest.raises(OSError):
            get_node_array(node, repo_path, 'symbols')
