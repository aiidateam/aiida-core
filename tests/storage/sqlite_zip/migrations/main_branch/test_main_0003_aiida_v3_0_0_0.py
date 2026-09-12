###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test ``main_0003_aiida_v3_0_0_0.py``."""

from aiida.storage.sqlite_zip.migrator import _alembic_connect, _migration_context


def test_migration(tmp_path):
    """Test the empty migration updates the archive schema revision."""
    from alembic.command import upgrade

    database_path = tmp_path / 'database.sqlite'

    with _alembic_connect(database_path) as config:
        upgrade(config, 'main_0002')

    with _alembic_connect(database_path) as config:
        upgrade(config, 'main_0003')

    with _migration_context(database_path) as context:
        assert context.get_current_revision() == 'main_0003'


def test_downgrade(tmp_path):
    """Test that downgrading from ``main_0003`` restores the ``main_0002`` revision."""
    from alembic.command import downgrade, upgrade

    database_path = tmp_path / 'database.sqlite'

    with _alembic_connect(database_path) as config:
        upgrade(config, 'main_0003')

    with _alembic_connect(database_path) as config:
        downgrade(config, 'main_0002')

    with _migration_context(database_path) as context:
        assert context.get_current_revision() == 'main_0002'
