###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utilities for testing SQLite storage backends."""

from pathlib import Path

from sqlalchemy import inspect

from aiida.storage.sqlite_zip.utils import create_sqla_engine


def reflect_schema(database_path: Path) -> dict:
    """Create a semantic representation of a SQLite database schema."""
    engine = create_sqla_engine(database_path)
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
