###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Fixtures for SQLite migration schema regression tests."""

import pytest

from aiida.manage.configuration import Profile


@pytest.fixture
def sqlite_dos_migration_profile(tmp_path):
    """Return an uninitialised profile backed by a temporary SQLite database."""
    return Profile(
        'test_migrate',
        {
            'test_profile': True,
            'storage': {
                'backend': 'core.sqlite_dos',
                'config': {'filepath': str(tmp_path)},
            },
            'process_control': {'backend': 'null', 'config': {}},
        },
    )
