# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Check the schema parity between Django and SQLAlchemy."""
import pytest
from sqlalchemy import Table
from sqlalchemy.sql.schema import Index, UniqueConstraint
from sqlalchemy.sql.sqltypes import TEXT, String

from aiida.backends import BACKEND_DJANGO, BACKEND_SQLA
from aiida.manage.tests import get_test_backend_name


@pytest.mark.skipif(get_test_backend_name() != BACKEND_DJANGO, reason='Django only')
def test_schema_parity_django(aiida_profile, data_regression):  # pylint: disable=unused-argument
    """Check the schema parity for Django."""
    from django.apps import apps

    data = {}
    for model in apps.get_models(include_auto_created=True):
        sqla_table: Table = model.sa.__table__
        # ignore django specific tables
        if not sqla_table.name.startswith('db_'):
            continue

        add_django_data(sqla_table, model)

        data[str(sqla_table.name)] = create_table_data(sqla_table)

    data_regression.check(data, basename='shared_database_schema')


@pytest.mark.skipif(get_test_backend_name() != BACKEND_SQLA, reason='Sqlalchemy only')
def test_schema_parity_sqla(aiida_profile, data_regression):  # pylint: disable=unused-argument
    """Check the schema parity for SQLAlchemy."""
    from aiida.backends.sqlalchemy.models.base import Base
    data = {}
    for table in Base.metadata.sorted_tables:
        data[str(table.name)] = create_table_data(table)

    data_regression.check(data, basename='shared_database_schema')


def add_django_data(table: Table, model):
    """Add data from django that aldjemy omits"""
    from django.db import connections
    schema_editor = connections['default'].schema_editor()
    django_fields = {f.column: f for f in model._meta.get_fields() if hasattr(f, 'column')}
    for column in table.columns:
        field = django_fields[column.name]
        # add whether columns are nullable
        column.nullable = field.null
        # add indexes
        if field.db_index or field.unique:
            # standard index
            if not field.primary_key:
                name = schema_editor._create_index_name(table.name, [column.name], '_uniq' if field.unique else '')  # pylint: disable=protected-access
                table.indexes.add(Index(name, column, unique=field.unique))
            # postgresql specific indexes
            for ctype, op_name in ((String, 'varchar_pattern_ops'), (TEXT, 'text_pattern_ops')):
                if isinstance(column.type, ctype):
                    # see DatabaseSchemaEditor._create_like_index_sql
                    name = schema_editor._create_index_name(table.name, [column.name], '_like')  # pylint: disable=protected-access
                    table.indexes.add(Index(name, column, postgresql_using='btree', postgresql_ops={'data': op_name}))
    # for columns in model._meta.unique_together or []:
    #     name = schema_editor._create_index_name(table.name, columns, '_uniq')


def create_table_data(table: Table):
    """Create a dictionary with the table name and the columns."""
    data = {'columns': {}, 'indexes': {}, 'constraints': []}

    for column in table.columns:
        data['columns'][str(column.name)] = {
            'dtype': column.type.__class__.__name__,
            'nullable': column.nullable,
        }
        if column.primary_key:
            data['columns'][str(column.name)]['primary_key'] = True
        if isinstance(column.type, String):
            data['columns'][str(column.name)]['length'] = column.type.length
    for index in table.indexes:
        data['indexes'][str(index.name)] = {
            'columns': [str(column.name) for column in index.columns],
            'unique': index.unique,
            'dialect_kwargs': dict(index.dialect_kwargs.items())
        }
    # note primary key and unique constraint indexes are automatically created
    for constraint in table.constraints:
        if isinstance(constraint, UniqueConstraint):
            pass
    #         data['constraints'].append({
    #             'name': constraint.name or '',
    #             'type': constraint.__class__.__name__,
    #             'columns': [str(column.name) for column in constraint.columns],
    #         })
    # ensure deterministic order of constraints
    data['constraints'] = sorted(data['constraints'], key=lambda x: (x['name'], x['type'], tuple(x['columns'])))
    return data
