###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test the ownership migration for existing profiles."""

import pytest
import sqlalchemy as sa

from aiida.common import timezone
from aiida.common.utils import get_new_uuid


def _node(model, user_id: int, node_type: str):
    return model(
        uuid=get_new_uuid(),
        user_id=user_id,
        node_type=node_type,
        ctime=timezone.now(),
        mtime=timezone.now(),
        label='',
        description='',
        repository_metadata={},
        attributes={},
        extras={'_aiida_hash': 'unchanged'},
    )


@pytest.fixture
def existing_profile(migration_profile):
    """Create a main_0002 profile with real provenance links."""
    with migration_profile.storage_cls.migrator(migration_profile) as migrator:
        migrator.migrate_up('main@main_0002')
        assert not sa.inspect(migrator.connection).has_table('db_dbmembership')
        migrator.connection.commit()
        user_model = migrator.get_current_table('db_dbuser')
        node_model = migrator.get_current_table('db_dbnode')
        link_model = migrator.get_current_table('db_dblink')
        with migrator.session() as session:
            user = user_model(email='test@localhost', first_name='', last_name='', institution='')
            session.add(user)
            session.flush()
            leaf = _node(node_model, user.id, 'data.core.int.Int.')
            process = _node(node_model, user.id, 'process.calculation.calcjob.CalcJobNode.')
            session.add_all([leaf, process])
            session.flush()
            session.add(link_model(input_id=leaf.id, output_id=process.id, type='input_calc', label='input'))
            leaf_id, process_id = leaf.id, process.id
            session.commit()

        yield migrator, leaf_id, process_id


def test_upgrade_preserves_existing_nodes_and_links(existing_profile):
    """Add empty ownership storage without rewriting earlier data or provenance."""
    migrator, leaf_id, process_id = existing_profile
    migrator.migrate_up('main@main_0003')
    migrator.connection.commit()
    assert migrator.get_schema_version_profile() == 'main_0003'
    node_model = migrator.get_current_table('db_dbnode')
    link_model = migrator.get_current_table('db_dblink')
    member_model = migrator.get_current_table('db_dbmembership')
    with migrator.session() as session:
        leaf, process = (session.get(node_model, pk) for pk in (leaf_id, process_id))
        assert leaf.owner_id is process.owner_id is None
        assert leaf.extras == process.extras == {'_aiida_hash': 'unchanged'}
        assert session.query(member_model).count() == 0
        link = session.query(link_model).one()
        assert (link.input_id, link.output_id, link.label, link.type) == (leaf_id, process_id, 'input', 'input_calc')
