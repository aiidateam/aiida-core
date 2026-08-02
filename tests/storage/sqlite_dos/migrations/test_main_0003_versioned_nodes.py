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
from aiida.storage.sqlite_dos.backend import SqliteDosMigrator


def test_migration(uninitialised_profile):
    """Test the migration adds the version lineage columns and constraints."""
    with SqliteDosMigrator(uninitialised_profile) as migrator:
        migrator.migrate_up('main@main_0003')

        inspector = sa.inspect(migrator.connection)
        columns = {column['name']: column for column in inspector.get_columns('db_dbnode')}
        indexes = {index['name'] for index in inspector.get_indexes('db_dbnode')}
        unique_constraints = {constraint['name'] for constraint in inspector.get_unique_constraints('db_dbnode')}

        assert columns['lineage_uuid']['nullable']
        assert not columns['version']['nullable']
        assert 'ix_db_dbnode_db_dbnode_lineage_uuid' in indexes
        assert 'uq_dbnode_lineage_version' in unique_constraints

        metadata = sa.MetaData()
        user_table = sa.Table('db_dbuser', metadata, autoload_with=migrator.connection)
        node_table = sa.Table('db_dbnode', metadata, autoload_with=migrator.connection)

        result = migrator.connection.execute(
            user_table.insert().values(email='test', first_name='test', last_name='test', institution='test')
        )
        user_id = result.inserted_primary_key[0]
        migrator.connection.commit()

        node_values = {
            'user_id': user_id,
            'ctime': timezone.now(),
            'mtime': timezone.now(),
            'label': 'test',
            'description': '',
            'node_type': 'data.Data.',
            'attributes': {},
            'repository_metadata': {},
            'extras': {},
        }
        result = migrator.connection.execute(node_table.insert().values(uuid=get_new_uuid(), **node_values))
        node_id = result.inserted_primary_key[0]
        migrator.connection.commit()

        node = migrator.connection.execute(
            sa.select(node_table.c.lineage_uuid, node_table.c.version).where(node_table.c.id == node_id)
        ).one()
        assert node.lineage_uuid is None
        assert node.version == 1

        lineage_uuid = get_new_uuid()
        with pytest.raises(sa.exc.IntegrityError):
            migrator.connection.execute(
                node_table.insert(),
                [
                    {**node_values, 'uuid': get_new_uuid(), 'lineage_uuid': lineage_uuid, 'version': 2},
                    {**node_values, 'uuid': get_new_uuid(), 'lineage_uuid': lineage_uuid, 'version': 2},
                ],
            )
            migrator.connection.commit()
        migrator.connection.rollback()

        migrator.migrate_down('main@main_0002')

        inspector = sa.inspect(migrator.connection)
        columns = {column['name']: column for column in inspector.get_columns('db_dbnode')}
        indexes = {index['name'] for index in inspector.get_indexes('db_dbnode')}
        unique_constraints = {constraint['name'] for constraint in inspector.get_unique_constraints('db_dbnode')}

        assert 'lineage_uuid' not in columns
        assert 'version' not in columns
        assert 'ix_db_dbnode_db_dbnode_lineage_uuid' not in indexes
        assert 'uq_dbnode_lineage_version' not in unique_constraints
