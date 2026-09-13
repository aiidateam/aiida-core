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
from sqlalchemy import inspect

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
                'backend': 'core.sqlite_dos',
                'config': {
                    'filepath': str(tmp_path),
                },
            },
            'process_control': {'backend': 'null', 'config': {}},
        },
    )


def _generate_schema(profile: Profile) -> dict:
    """Create a semantic representation of the SQLite database schema."""
    engine = create_sqla_engine(pathlib.Path(profile.storage_config['filepath']) / 'database.sqlite')
    inspector = inspect(engine)
    table_names = sorted(inspector.get_table_names())

    columns = {}
    primary_keys = {}
    unique_constraints = {}
    check_constraints = {}
    foreign_keys = {}
    indexes = {}

    for table_name in table_names:
        columns[table_name] = [
            {
                'name': column['name'],
                'type': str(column['type']),
                'nullable': column['nullable'],
                'default': column['default'],
            }
            for column in inspector.get_columns(table_name)
        ]
        primary_keys[table_name] = inspector.get_pk_constraint(table_name)
        unique_constraints[table_name] = sorted(
            inspector.get_unique_constraints(table_name), key=lambda constraint: constraint['name'] or ''
        )
        check_constraints[table_name] = sorted(
            inspector.get_check_constraints(table_name), key=lambda constraint: constraint['name'] or ''
        )
        foreign_keys[table_name] = sorted(
            inspector.get_foreign_keys(table_name),
            key=lambda constraint: (constraint['name'] or '', constraint['constrained_columns']),
        )
        indexes[table_name] = sorted(inspector.get_indexes(table_name), key=lambda index: index['name'])

    return {
        'columns': columns,
        'constraints': {
            'primary_keys': primary_keys,
            'unique': unique_constraints,
            'check': check_constraints,
        },
        'foreign_keys': foreign_keys,
        'indexes': indexes,
    }


@pytest.fixture
def reflect_schema():
    """A fixture to generate the schema of AiiDA tables for a given profile."""

    def factory(profile: Profile) -> dict:
        """Create a dict containing all tables and fields of AiiDA tables."""
        return _generate_schema(profile)

    return factory
