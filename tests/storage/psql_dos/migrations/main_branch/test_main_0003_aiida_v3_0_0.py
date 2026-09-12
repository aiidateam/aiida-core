###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test ``main_0003_aiida_v3_0_0.py``."""

from aiida.storage.psql_dos.migrator import PsqlDosMigrator


def test_migration(perform_migrations: PsqlDosMigrator):
    """Test the empty migration updates the schema revision."""
    perform_migrations.migrate_up('main@main_0002')
    perform_migrations.migrate_up('main@main_0003')

    assert perform_migrations.get_schema_version_profile() == 'main_0003'


def test_downgrade(perform_migrations: PsqlDosMigrator):
    """Test that downgrading from ``main_0003`` restores the ``main_0002`` revision."""
    perform_migrations.migrate_up('main@main_0003')
    perform_migrations.migrate_down('main@main_0002')

    assert perform_migrations.get_schema_version_profile() == 'main_0002'
