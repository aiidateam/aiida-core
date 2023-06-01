# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for legacy process migrations: 07fac78e6209 -> 118349c10896"""
from aiida.storage.psql_dos.migrator import PsqlDosMigrator


def test_legacy_jobcalcstate_data(perform_migrations: PsqlDosMigrator):
    """Test the migration that performs a data migration of legacy `JobCalcState`.

    Verify that the `process_state`, `process_status` and `exit_status` are set correctly.
    """
    from aiida.storage.psql_dos.migrations.utils.calc_state import STATE_MAPPING

    # starting revision
    perform_migrations.migrate_up('sqlalchemy@07fac78e6209')

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
    perform_migrations.migrate_up('sqlalchemy@26d561acd560')

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


def test_reset_hash(perform_migrations: PsqlDosMigrator):
    """Test the migration that resets the node hash.

    Verify that only the _aiida_hash extra has been removed.
    """
    # starting revision
    perform_migrations.migrate_up('sqlalchemy@26d561acd560')

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
    perform_migrations.migrate_up('sqlalchemy@e797afa09270')

    # perform some checks
    DbNode = perform_migrations.get_current_table('db_dbnode')  # pylint: disable=invalid-name
    with perform_migrations.session() as session:
        node = session.query(DbNode).filter(DbNode.id == node_id).one()
        extras = node.extras
        assert extras.get('something') == 123  # Other extras should be untouched
        assert '_aiida_hash' not in extras  # The hash extra should have been removed


def test_legacy_process_attribute(perform_migrations: PsqlDosMigrator):
    """Test the migration that performs a data migration of legacy process attributes.

    Verify that the attributes for process node have been deleted and `_sealed` has been changed to `sealed`.
    """
    # starting revision
    perform_migrations.migrate_up('sqlalchemy@e797afa09270')

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
    perform_migrations.migrate_up('sqlalchemy@e734dd5e50d7')

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


def test_seal_unsealed_processes(perform_migrations: PsqlDosMigrator):
    """Test the migration that performs a data migration of legacy process attributes.

    Verify that the attributes for process node have been deleted and `_sealed` has been changed to `sealed`.
    """
    # starting revision
    perform_migrations.migrate_up('sqlalchemy@e734dd5e50d7')

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
    perform_migrations.migrate_up('sqlalchemy@7b38a9e783e7')

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


def test_default_link_label(perform_migrations: PsqlDosMigrator):
    """Test the migration that performs a data migration of legacy default link labels.

    Verify that the attributes for process node have been deleted and `_sealed` has been changed to `sealed`.
    """
    # starting revision
    perform_migrations.migrate_up('sqlalchemy@91b573400be5')

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
    perform_migrations.migrate_up('sqlalchemy@118349c10896')

    # perform some checks
    DbLink = perform_migrations.get_current_table('db_dblink')  # pylint: disable=invalid-name
    with perform_migrations.session() as session:
        link = session.query(DbLink).filter(DbLink.id == link_id).one()
        assert link.label == 'result'
