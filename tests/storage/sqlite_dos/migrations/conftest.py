###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the migration engine (Alembic) as well as for the AiiDA migrations for SQLAlchemy."""

import pathlib

import pytest

from aiida.manage.configuration import Profile
from tests.storage.sqlite.utils import reflect_schema as reflect_sqlite_schema


@pytest.fixture
def uninitialised_profile(tmp_path):
    """Create a profile attached to an empty database and repository folder."""

    yield Profile(
        'test_migrate',
        {
            'test_profile': True,
            'storage': {
                'backend': 'core.sqlite_dos',
                'config': {
                    'filepath': str(tmp_path),
                },
            },
            'process_control': {'backend': 'null', 'config': {}},
        },
    )


@pytest.fixture
def reflect_schema():
    """A fixture to generate the schema of AiiDA tables for a given profile."""

    def factory(profile: Profile) -> dict:
        """Create a dict containing all tables and fields of AiiDA tables."""
        return reflect_sqlite_schema(pathlib.Path(profile.storage_config['filepath']) / 'database.sqlite')

    return factory
