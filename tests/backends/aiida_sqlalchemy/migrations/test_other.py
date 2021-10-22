# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests"""
import numpy as np
import pytest

from aiida.backends.general.migrations import utils
from aiida.backends.sqlalchemy.utils import flag_modified

from .conftest import Migrator


def test_dblog_uuid_addition(perform_migrations: Migrator):
    """Test that the UUID column is correctly added to the DbLog table,
    and that the uniqueness constraint is added without problems
    (if the migration arrives until 375c2db70663 then the constraint is added properly).
    """
    # starting revision
    perform_migrations.migrate_down('041a79fc615f')  # 041a79fc615f_dblog_cleaning

    # setup the database
    DbLog = perform_migrations.get_current_table('db_dblog')  # pylint: disable=invalid-name
    DbNode = perform_migrations.get_current_table('db_dbnode')  # pylint: disable=invalid-name
    DbUser = perform_migrations.get_current_table('db_dbuser')  # pylint: disable=invalid-name
    with perform_migrations.session() as session:
        user = DbUser(email='user@aiida.net')
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
    perform_migrations.migrate_up('375c2db70663')  # 375c2db70663_dblog_uuid_uniqueness_constraint

    # perform some checks
    DbLog = perform_migrations.get_current_table('db_dblog')  # pylint: disable=invalid-name
    with perform_migrations.session() as session:
        l_uuids = list(session.query(DbLog).with_entities(getattr(DbLog, 'uuid')).all())
        s_uuids = set(l_uuids)
        assert len(l_uuids) == len(s_uuids), 'The UUIDs are not all unique.'


def test_data_move_with_node(perform_migrations: Migrator):
    """Test the migration of Data nodes after the data module was moved within the node module.

    Verify that type string of the Data node was successfully adapted.
    """
    # starting revision
    perform_migrations.migrate_down('041a79fc615f')  # 041a79fc615f_dblog_update

    # setup the database
    DbNode = perform_migrations.get_current_table('db_dbnode')  # pylint: disable=invalid-name
    DbUser = perform_migrations.get_current_table('db_dbuser')  # pylint: disable=invalid-name
    with perform_migrations.session() as session:
        user = DbUser(email='user@aiida.net')
        session.add(user)
        session.commit()

        node_calc = DbNode(type='node.process.calculation.calcjob.CalcJobNode.', user_id=user.id)
        node_data = DbNode(type='data.core.int.Int.', user_id=user.id)

        session.add(node_data)
        session.add(node_calc)
        session.commit()

        node_calc_id = node_calc.id
        node_data_id = node_data.id

    # migrate up
    perform_migrations.migrate_up('6a5c2ea1439d')  # 6a5c2ea1439d_move_data_within_node_module

    # perform some checks
    DbNode = perform_migrations.get_current_table('db_dbnode')  # pylint: disable=invalid-name
    with perform_migrations.session() as session:
        # The data node should have been touched and migrated
        node_data = session.query(DbNode).filter(DbNode.id == node_data_id).one()
        assert node_data.type == 'node.data.core.int.Int.'

        # The calc node by contrast should not have been changed
        node_calc = session.query(DbNode).filter(DbNode.id == node_calc_id).one()
        assert node_calc.type == 'node.process.calculation.calcjob.CalcJobNode.'


def set_node_array(node, name, array):
    """Store a new numpy array inside a node. Possibly overwrite the array if it already existed.

    Internally, it stores a name.npy file in numpy format.

    :param name: The name of the array.
    :param array: The numpy array to store.
    """
    utils.store_numpy_array_in_repository(node.uuid, name, array)
    attributes = node.attributes
    if attributes is None:
        attributes = {}
    attributes[f'array|{name}'] = list(array.shape)
    node.attributes = attributes
    flag_modified(node, 'attributes')


def get_node_array(node, name):
    """Retrieve a numpy array from a node."""
    return utils.load_numpy_array_from_repository(node.uuid, name)


def test_trajectory_data(perform_migrations: Migrator):
    """Test the migration of the symbols from numpy array to attribute for TrajectoryData nodes.

    Verify that migration of symbols from repository array to attribute works properly.
    """
    # starting revision
    perform_migrations.migrate_down('37f3d4882837')  # 37f3d4882837_make_all_uuid_columns_unique

    # setup the database
    stepids = np.array([60, 70])
    times = stepids * 0.01
    positions = np.array([[[0., 0., 0.], [0.5, 0.5, 0.5], [1.5, 1.5, 1.5]],
                          [[0., 0., 0.], [0.5, 0.5, 0.5], [1.5, 1.5, 1.5]]])
    velocities = np.array([[[0., 0., 0.], [0., 0., 0.], [0., 0., 0.]],
                           [[0.5, 0.5, 0.5], [0.5, 0.5, 0.5], [-0.5, -0.5, -0.5]]])
    cells = np.array([[[2., 0., 0.], [0., 2., 0.], [0., 0., 2.]], [[3., 0., 0.], [0., 3., 0.], [0., 0., 3.]]])
    DbNode = perform_migrations.get_current_table('db_dbnode')  # pylint: disable=invalid-name
    DbUser = perform_migrations.get_current_table('db_dbuser')  # pylint: disable=invalid-name
    with perform_migrations.session() as session:
        user = DbUser(email='user@aiida.net')
        session.add(user)
        session.commit()

        node = DbNode(type='node.data.array.trajectory.TrajectoryData.', user_id=user.id)
        session.add(node)
        session.commit()

        symbols = np.array(['H', 'O', 'C'])

        set_node_array(node, 'steps', stepids)
        set_node_array(node, 'cells', cells)
        set_node_array(node, 'symbols', symbols)
        set_node_array(node, 'positions', positions)
        set_node_array(node, 'times', times)
        set_node_array(node, 'velocities', velocities)
        session.commit()

        node_uuid = node.uuid

    # migrate up
    perform_migrations.migrate_up('ce56d84bcc35')  # ce56d84bcc35_delete_trajectory_symbols_array

    # perform some checks
    DbNode = perform_migrations.get_current_table('db_dbnode')  # pylint: disable=invalid-name
    with perform_migrations.session() as session:
        node = session.query(DbNode).filter(DbNode.uuid == node_uuid).one()

        assert node.attributes['symbols'] == ['H', 'O', 'C']
        assert get_node_array(node, 'velocities').tolist() == velocities.tolist()
        assert get_node_array(node, 'positions').tolist() == positions.tolist()
        with pytest.raises(IOError):
            get_node_array(node, 'symbols')


def test_node_prefix_removal(perform_migrations: Migrator):
    """Test the migration of Data nodes after the data module was moved within the node module.

    Verify that type string of the Data node was successfully adapted.
    """
    # starting revision
    perform_migrations.migrate_down('ce56d84bcc35')  # ce56d84bcc35_delete_trajectory_symbols_array

    # setup the database
    DbNode = perform_migrations.get_current_table('db_dbnode')  # pylint: disable=invalid-name
    DbUser = perform_migrations.get_current_table('db_dbuser')  # pylint: disable=invalid-name
    with perform_migrations.session() as session:
        user = DbUser(email='user@aiida.net')
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
    perform_migrations.migrate_up('61fc0913fae9')  # 61fc0913fae9_remove_node_prefix

    # perform some checks
    DbNode = perform_migrations.get_current_table('db_dbnode')  # pylint: disable=invalid-name
    with perform_migrations.session() as session:
        # Verify that the `node.` prefix has been dropped from both the data as well as the process node
        node_data = session.query(DbNode).filter(DbNode.id == node_data_id).one()
        assert node_data.type == 'data.int.Int.'

        node_calc = session.query(DbNode).filter(DbNode.id == node_calc_id).one()
        assert node_calc.type == 'process.calculation.calcjob.CalcJobNode.'


def test_parameter_data_to_dict(perform_migrations: Migrator):
    """Test the data migration after `ParameterData` was renamed to `Dict`.

    Verify that type string of the Data node was successfully adapted.
    """
    # starting revision
    perform_migrations.migrate_down('61fc0913fae9')  # 61fc0913fae9_remove_node_prefix

    # setup the database
    DbNode = perform_migrations.get_current_table('db_dbnode')  # pylint: disable=invalid-name
    DbUser = perform_migrations.get_current_table('db_dbuser')  # pylint: disable=invalid-name
    with perform_migrations.session() as session:
        user = DbUser(email='user@aiida.net')
        session.add(user)
        session.commit()

        node = DbNode(type='data.parameter.ParameterData.', user_id=user.id)

        session.add(node)
        session.commit()

        node_id = node.id

    # migrate up
    perform_migrations.migrate_up('d254fdfed416')  # d254fdfed416_rename_parameter_data_to_dict

    # perform some checks
    DbNode = perform_migrations.get_current_table('db_dbnode')  # pylint: disable=invalid-name
    with perform_migrations.session() as session:
        node = session.query(DbNode).filter(DbNode.id == node_id).one()
        assert node.type == 'data.dict.Dict.'


def test_legacy_jobcalcstate_data(perform_migrations: Migrator):
    """Test the migration that performs a data migration of legacy `JobCalcState`.

    Verify that the `process_state`, `process_status` and `exit_status` are set correctly.
    """
    from aiida.backends.general.migrations.calc_state import STATE_MAPPING

    # starting revision
    perform_migrations.migrate_down('07fac78e6209')

    # setup the database
    nodes = {}
    DbNode = perform_migrations.get_current_table('db_dbnode')  # pylint: disable=invalid-name
    DbUser = perform_migrations.get_current_table('db_dbuser')  # pylint: disable=invalid-name
    with perform_migrations.session() as session:
        user = DbUser(email='user@aiida.net')
        session.add(user)
        session.commit()

        for state in STATE_MAPPING:
            node = DbNode(
                node_type='process.calculation.calcjob.CalcJobNode.', user_id=user.id, attributes={'state': state}
            )
            session.add(node)
            session.commit()

            nodes[state] = node.id

    # migrate up
    perform_migrations.migrate_up('26d561acd560')

    # perform some checks
    DbNode = perform_migrations.get_current_table('db_dbnode')  # pylint: disable=invalid-name
    with perform_migrations.session() as session:
        for state, pk in nodes.items():
            node = session.query(DbNode).filter(DbNode.id == pk).one()
            attrs = node.attributes
            assert attrs.get('process_state', None) == STATE_MAPPING[state].process_state
            assert attrs.get('process_status', None) == STATE_MAPPING[state].process_status
            assert attrs.get('exit_status', None) == STATE_MAPPING[state].exit_status
            assert attrs.get('process_label') == 'Legacy JobCalculation'
            assert attrs.get('state', None) is None  # The old state should have been removed

            exit_status = attrs.get('exit_status', None)
            if exit_status is not None:
                assert isinstance(exit_status, int)


def test_reset_hash(perform_migrations: Migrator):
    """Test the migration that resets the node hash.

    Verify that only the _aiida_hash extra has been removed.
    """
    # starting revision
    perform_migrations.migrate_down('26d561acd560')

    # setup the database
    DbNode = perform_migrations.get_current_table('db_dbnode')  # pylint: disable=invalid-name
    DbUser = perform_migrations.get_current_table('db_dbuser')  # pylint: disable=invalid-name
    with perform_migrations.session() as session:
        user = DbUser(email='user@aiida.net')
        session.add(user)
        session.commit()

        node = DbNode(
            node_type='process.calculation.calcjob.CalcJobNode.',
            user_id=user.id,
            extras={
                'something': 123,
                '_aiida_hash': 'abcd'
            }
        )
        session.add(node)
        session.commit()

        node_id = node.id

    # migrate up
    perform_migrations.migrate_up('e797afa09270')

    # perform some checks
    DbNode = perform_migrations.get_current_table('db_dbnode')  # pylint: disable=invalid-name
    with perform_migrations.session() as session:
        node = session.query(DbNode).filter(DbNode.id == node_id).one()
        extras = node.extras
        assert extras.get('something') == 123  # Other extras should be untouched
        assert '_aiida_hash' not in extras  # The hash extra should have been removed


def test_legacy_process_attribute(perform_migrations: Migrator):
    """Test the migration that performs a data migration of legacy process attributes.

    Verify that the attributes for process node have been deleted and `_sealed` has been changed to `sealed`.
    """
    # starting revision
    perform_migrations.migrate_down('e797afa09270')

    # setup the database
    DbNode = perform_migrations.get_current_table('db_dbnode')  # pylint: disable=invalid-name
    DbUser = perform_migrations.get_current_table('db_dbuser')  # pylint: disable=invalid-name
    with perform_migrations.session() as session:
        user = DbUser(email='user@aiida.net')
        session.add(user)
        session.commit()

        node_process = DbNode(
            node_type='process.calculation.calcjob.CalcJobNode.',
            user_id=user.id,
            attributes={
                '_sealed': True,
                '_finished': True,
                '_failed': False,
                '_aborted': False,
                '_do_abort': False,
            }
        )

        # This is an "active" modern process, due to its `process_state` and should *not* receive the
        # `sealed` attribute
        node_process_active = DbNode(
            node_type='process.calculation.calcjob.CalcJobNode.',
            user_id=user.id,
            attributes={
                'process_state': 'created',
                '_finished': True,
                '_failed': False,
                '_aborted': False,
                '_do_abort': False,
            }
        )

        # Note that `Data` nodes should not have these attributes in real databases but the migration explicitly
        # excludes data nodes, which is what this test is verifying, by checking they are not deleted
        node_data = DbNode(
            node_type='data.core.dict.Dict.',
            user_id=user.id,
            attributes={
                '_sealed': True,
                '_finished': True,
                '_failed': False,
                '_aborted': False,
                '_do_abort': False,
            }
        )

        session.add(node_process)
        session.add(node_process_active)
        session.add(node_data)
        session.commit()

        node_process_id = node_process.id
        node_process_active_id = node_process_active.id
        node_data_id = node_data.id

    # migrate up
    perform_migrations.migrate_up('e734dd5e50d7')

    # perform some checks
    DbNode = perform_migrations.get_current_table('db_dbnode')  # pylint: disable=invalid-name
    with perform_migrations.session() as session:
        deleted_keys = ['_sealed', '_finished', '_failed', '_aborted', '_do_abort']

        node_process = session.query(DbNode).filter(DbNode.id == node_process_id).one()
        assert node_process.attributes['sealed'] is True
        for key in deleted_keys:
            assert key not in node_process.attributes

        node_process_active = session.query(DbNode).filter(DbNode.id == node_process_active_id).one()
        assert 'sealed' not in node_process_active.attributes
        for key in deleted_keys:
            assert key not in node_process_active.attributes

        node_data = session.query(DbNode).filter(DbNode.id == node_data_id).one()
        assert node_data.attributes.get('sealed', None) is None
        for key in deleted_keys:
            assert key in node_data.attributes


def test_seal_unsealed_processes(perform_migrations: Migrator):
    """Test the migration that performs a data migration of legacy process attributes.

    Verify that the attributes for process node have been deleted and `_sealed` has been changed to `sealed`.
    """
    # starting revision
    perform_migrations.migrate_down('e734dd5e50d7')

    # setup the database
    DbNode = perform_migrations.get_current_table('db_dbnode')  # pylint: disable=invalid-name
    DbUser = perform_migrations.get_current_table('db_dbuser')  # pylint: disable=invalid-name
    with perform_migrations.session() as session:
        user = DbUser(email='user@aiida.net')
        session.add(user)
        session.commit()

        node_process = DbNode(
            node_type='process.calculation.calcjob.CalcJobNode.',
            user_id=user.id,
            attributes={
                'process_state': 'finished',
                'sealed': True,
            }
        )

        # This is an "active" modern process, due to its `process_state` and should *not* receive the
        # `sealed` attribute
        node_process_active = DbNode(
            node_type='process.calculation.calcjob.CalcJobNode.',
            user_id=user.id,
            attributes={
                'process_state': 'created',
            }
        )

        # This is a legacy process that does not even have a `process_state`
        node_process_legacy = DbNode(
            node_type='process.calculation.calcfunction.CalcFunctionNode.', user_id=user.id, attributes={}
        )

        # Note that `Data` nodes should not have these attributes in real databases but the migration explicitly
        # excludes data nodes, which is what this test is verifying, by checking they are not deleted
        node_data = DbNode(node_type='data.core.dict.Dict.', user_id=user.id, attributes={})

        session.add(node_process)
        session.add(node_process_active)
        session.add(node_process_legacy)
        session.add(node_data)
        session.commit()

        node_process_id = node_process.id
        node_process_active_id = node_process_active.id
        node_process_legacy_id = node_process_legacy.id
        node_data_id = node_data.id

    # migrate up
    perform_migrations.migrate_up('7b38a9e783e7')

    # perform some checks
    DbNode = perform_migrations.get_current_table('db_dbnode')  # pylint: disable=invalid-name
    with perform_migrations.session() as session:
        node_process = session.query(DbNode).filter(DbNode.id == node_process_id).one()
        assert node_process.attributes['sealed'] is True

        node_process_active = session.query(DbNode).filter(DbNode.id == node_process_active_id).one()
        assert 'sealed' not in node_process_active.attributes

        node_process_legacy = session.query(DbNode).filter(DbNode.id == node_process_legacy_id).one()
        assert node_process_legacy.attributes['sealed'] is True

        node_data = session.query(DbNode).filter(DbNode.id == node_data_id).one()
        assert 'sealed' not in node_data.attributes


def test_default_link_label(perform_migrations: Migrator):
    """Test the migration that performs a data migration of legacy default link labels.

    Verify that the attributes for process node have been deleted and `_sealed` has been changed to `sealed`.
    """
    # starting revision
    perform_migrations.migrate_down('91b573400be5')

    # setup the database
    DbLink = perform_migrations.get_current_table('db_dblink')  # pylint: disable=invalid-name
    DbNode = perform_migrations.get_current_table('db_dbnode')  # pylint: disable=invalid-name
    DbUser = perform_migrations.get_current_table('db_dbuser')  # pylint: disable=invalid-name
    with perform_migrations.session() as session:
        user = DbUser(email='user@aiida.net')
        session.add(user)
        session.commit()

        node_process = DbNode(node_type='process.calculation.calcjob.CalcJobNode.', user_id=user.id)
        node_data = DbNode(node_type='data.core.dict.Dict.', user_id=user.id)
        link = DbLink(input_id=node_data.id, output_id=node_process.id, type='input', label='_return')

        session.add(node_process)
        session.add(node_data)
        session.add(link)
        session.commit()

        link_id = link.id

    # migrate up
    perform_migrations.migrate_up('118349c10896')

    # perform some checks
    DbLink = perform_migrations.get_current_table('db_dblink')  # pylint: disable=invalid-name
    with perform_migrations.session() as session:
        link = session.query(DbLink).filter(DbLink.id == link_id).one()
        assert link.label == 'result'


def test_group_typestring(perform_migrations: Migrator):
    """Test the migration that renames the DbGroup type strings.

    Verify that the type strings are properly migrated.
    """
    # starting revision
    perform_migrations.migrate_down('118349c10896')  # 118349c10896_default_link_label.py

    # setup the database
    DbGroup = perform_migrations.get_current_table('db_dbgroup')  # pylint: disable=invalid-name
    DbUser = perform_migrations.get_current_table('db_dbuser')  # pylint: disable=invalid-name
    with perform_migrations.session() as session:
        default_user = DbUser(email='user@aiida.net')
        session.add(default_user)
        session.commit()

        # test user group type_string: 'user' -> 'core'
        group_user = DbGroup(label='01', user_id=default_user.id, type_string='user')
        session.add(group_user)
        # test upf group type_string: 'data.upf' -> 'core.upf'
        group_data_upf = DbGroup(label='02', user_id=default_user.id, type_string='data.upf')
        session.add(group_data_upf)
        # test auto.import group type_string: 'auto.import' -> 'core.import'
        group_autoimport = DbGroup(label='03', user_id=default_user.id, type_string='auto.import')
        session.add(group_autoimport)
        # test auto.run group type_string: 'auto.run' -> 'core.auto'
        group_autorun = DbGroup(label='04', user_id=default_user.id, type_string='auto.run')
        session.add(group_autorun)

        session.commit()

        # Store values for later tests
        group_user_pk = group_user.id
        group_data_upf_pk = group_data_upf.id
        group_autoimport_pk = group_autoimport.id
        group_autorun_pk = group_autorun.id

    # migrate up
    perform_migrations.migrate_up('bf591f31dd12')  # bf591f31dd12_dbgroup_type_string.py

    # perform some checks
    DbGroup = perform_migrations.get_current_table('db_dbgroup')  # pylint: disable=invalid-name
    with perform_migrations.session() as session:
        group_user = session.query(DbGroup).filter(DbGroup.id == group_user_pk).one()
        assert group_user.type_string == 'core'

        # test upf group type_string: 'data.upf' -> 'core.upf'
        group_data_upf = session.query(DbGroup).filter(DbGroup.id == group_data_upf_pk).one()
        assert group_data_upf.type_string == 'core.upf'

        # test auto.import group type_string: 'auto.import' -> 'core.import'
        group_autoimport = session.query(DbGroup).filter(DbGroup.id == group_autoimport_pk).one()
        assert group_autoimport.type_string == 'core.import'

        # test auto.run group type_string: 'auto.run' -> 'core.auto'
        group_autorun = session.query(DbGroup).filter(DbGroup.id == group_autorun_pk).one()
        assert group_autorun.type_string == 'core.auto'


def test_group_extras(perform_migrations: Migrator):
    """Test migration to add the `extras` JSONB column to the `DbGroup` model.

    Verify that the model now has an extras column with empty dictionary as default.
    """
    # starting revision
    perform_migrations.migrate_down('bf591f31dd12')  # bf591f31dd12_dbgroup_type_string.py

    # setup the database
    DbGroup = perform_migrations.get_current_table('db_dbgroup')  # pylint: disable=invalid-name
    DbUser = perform_migrations.get_current_table('db_dbuser')  # pylint: disable=invalid-name
    with perform_migrations.session() as session:
        default_user = DbUser(email='user@aiida.net')
        session.add(default_user)
        session.commit()

        group = DbGroup(label='01', user_id=default_user.id, type_string='user')
        session.add(group)
        session.commit()

        group_pk = group.id

    # migrate up
    perform_migrations.migrate_up('0edcdd5a30f0')  # 0edcdd5a30f0_dbgroup_extras.py

    # perform some checks
    DbGroup = perform_migrations.get_current_table('db_dbgroup')  # pylint: disable=invalid-name
    with perform_migrations.session() as session:
        group = session.query(DbGroup).filter(DbGroup.id == group_pk).one()
        assert group.extras == {}
