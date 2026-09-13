###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the PostgreSQL storage migrator."""

from aiida.storage.psql_dos.migrator import PsqlDosMigrator


def test_initialise_reset(uninitialised_profile):
    """Test reset initialization of a previously uninitialized storage."""
    with PsqlDosMigrator(uninitialised_profile) as migrator:
        assert migrator.initialise(reset=True)
        assert migrator.is_initialised
        assert migrator.get_schema_version_profile() == migrator.get_schema_version_head()
        # Resetting the repository is idempotent and tolerates an already removed folder.
        migrator.reset_repository()
        migrator.reset_repository()
