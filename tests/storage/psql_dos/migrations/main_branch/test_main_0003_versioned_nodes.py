###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test ``main_0003_versioned_nodes.py``."""

import pytest
import sqlalchemy as sa

from aiida.common import timezone
from aiida.common.utils import get_new_uuid
from aiida.storage.psql_dos.migrator import PsqlDosMigrator


def test_migration(perform_migrations: PsqlDosMigrator):
    """Test the migration adds the version lineage columns and constraints."""
    perform_migrations.migrate_up('main@main_0002')
    perform_migrations.migrate_up('main@main_0003')

    inspector = sa.inspect(perform_migrations.connection)
    columns = {column['name']: column for column in inspector.get_columns('db_dbnode')}
    indexes = {index['name'] for index in inspector.get_indexes('db_dbnode')}
    unique_constraints = {constraint['name'] for constraint in inspector.get_unique_constraints('db_dbnode')}

    assert columns['lineage_uuid']['nullable']
    assert not columns['version']['nullable']
    assert 'ix_db_dbnode_db_dbnode_lineage_uuid' in indexes
    assert 'uq_dbnode_lineage_version' in unique_constraints

    user_model = perform_migrations.get_current_table('db_dbuser')
    node_model = perform_migrations.get_current_table('db_dbnode')

    with perform_migrations.session() as session:
        user = user_model(email='test', first_name='test', last_name='test', institution='test')
        session.add(user)
        session.commit()

        node = node_model(
            uuid=get_new_uuid(),
            user_id=user.id,
            ctime=timezone.now(),
            mtime=timezone.now(),
            label='test',
            description='',
            node_type='data.Data.',
            attributes={},
            repository_metadata={},
            extras={},
        )
        session.add(node)
        session.commit()

        assert node.lineage_uuid is None
        assert node.version == 1

        lineage_uuid = get_new_uuid()
        session.add_all(
            [
                node_model(
                    uuid=get_new_uuid(),
                    lineage_uuid=lineage_uuid,
                    version=2,
                    user_id=user.id,
                    ctime=timezone.now(),
                    mtime=timezone.now(),
                    label='test-1',
                    description='',
                    node_type='data.Data.',
                    attributes={},
                    repository_metadata={},
                    extras={},
                ),
                node_model(
                    uuid=get_new_uuid(),
                    lineage_uuid=lineage_uuid,
                    version=2,
                    user_id=user.id,
                    ctime=timezone.now(),
                    mtime=timezone.now(),
                    label='test-2',
                    description='',
                    node_type='data.Data.',
                    attributes={},
                    repository_metadata={},
                    extras={},
                ),
            ]
        )
        with pytest.raises(sa.exc.IntegrityError):
            session.commit()
        session.rollback()

    perform_migrations.migrate_down('main@main_0002')

    inspector = sa.inspect(perform_migrations.connection)
    columns = {column['name']: column for column in inspector.get_columns('db_dbnode')}
    indexes = {index['name'] for index in inspector.get_indexes('db_dbnode')}
    unique_constraints = {constraint['name'] for constraint in inspector.get_unique_constraints('db_dbnode')}

    assert 'lineage_uuid' not in columns
    assert 'version' not in columns
    assert 'ix_db_dbnode_db_dbnode_lineage_uuid' not in indexes
    assert 'uq_dbnode_lineage_version' not in unique_constraints
