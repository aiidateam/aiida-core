###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the migration engine (Alembic) as well as for the AiiDA migrations for SQLAlchemy."""

import collections
import pathlib

import pytest
from sqlalchemy import text

from aiida.manage.configuration import Profile
from aiida.storage.sqlite_zip.utils import create_sqla_engine


@pytest.fixture
def uninitialised_profile(tmp_path):
    """Create a profile attached to an empty database and repository folder."""

    yield Profile(
        'test_migrate',
        {
            'test_profile': True,
            'storage': {
                'backend': 'core.sqlite_git',
                'config': {
                    'filepath': str(tmp_path),
                },
            },
            'process_control': {'backend': 'null', 'config': {}},
        },
    )


def _generate_schema(profile: Profile) -> dict:
    """Create a dict containing indexes of AiiDA tables."""
    with create_sqla_engine(pathlib.Path(profile.storage_config['filepath']) / 'database.sqlite').connect() as conn:
        data = collections.defaultdict(list)
        for type_, name, tbl_name, rootpage, sql in conn.execute(text('SELECT * FROM sqlite_master;')):
            lines_sql = sql.strip().split('\n') if sql else []

            # For an unknown reason, the ``sql`` is not deterministic as the order of the ``CONSTRAINTS`` rules seem to
            # be in random order. To make sure they are always in the same order, they have to be ordered manually.
            if type_ == 'table':
                lines_constraints = []
                lines_other = []
                for line in lines_sql:
                    stripped = line.strip().strip(',')

                    if 'CONSTRAINT' in stripped:
                        lines_constraints.append(stripped)
                    else:
                        lines_other.append(stripped)

                lines_sql = lines_other + sorted(lines_constraints)
            data[type_].append((name, tbl_name, lines_sql))

    for key in data.keys():
        data[key] = sorted(data[key], key=lambda v: v[0])

    return dict(data)


@pytest.fixture
def reflect_schema():
    """A fixture to generate the schema of AiiDA tables for a given profile."""

    def factory(profile: Profile) -> dict:
        """Create a dict containing all tables and fields of AiiDA tables."""
        return _generate_schema(profile)

    return factory
