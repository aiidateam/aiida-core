# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Basic tests for all migratios"""
import pytest


@pytest.mark.usefixtures('perform_migrations')
def test_all_empty_migrations():
    """Test migrating down to a particular version, then back up, using an empty database.

    Note, migrating down+up with 59edaf8a8b79_adding_indexes_and_constraints_to_the_.py raises::

        sqlalchemy.exc.ProgrammingError:
        (psycopg2.errors.DuplicateTable) relation "db_dbgroup_dbnodes_dbgroup_id_dbnode_id_key" already exists

    So we only run for all versions later than this.
    """
    from aiida.backends.sqlalchemy.manager import SqlaBackendManager
    migrator = SqlaBackendManager()
    all_versions = migrator.list_schema_versions()
    first_index = all_versions.index('a514d673c163') + 1
    # ideally we would pytest parametrize this, but then we would need to call list_schema_versions on module load
    for version in all_versions[first_index:]:
        print(version)
        migrator.migrate_down(version)
        assert migrator.get_schema_version_backend() == version
        migrator.migrate_up('head')
        assert migrator.get_schema_version_backend() == migrator.get_schema_version_head()
