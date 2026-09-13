###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test migrating from the base of the django branch, to the main head."""

from aiida.storage.psql_dos.migrator import PsqlDosMigrator


def test_all_tests_marked_as_nightly(request):
    """Test that all tests in this folder are tagged with 'nightly' marker"""
    own_markers = [marker.name for marker in request.node.own_markers]

    assert len(own_markers) == 2
    assert 'nightly' in own_markers
    assert 'requires_psql' in own_markers


def test_migrate(perform_migrations: PsqlDosMigrator):
    """Test that the migrator can migrate from the base of the django branch, to the main head."""
    perform_migrations.migrate_up('django@django_0001')  # the base of the django branch
    perform_migrations.migrate()
    perform_migrations.validate_storage()
