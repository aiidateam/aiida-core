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


def test_columns(backend, data_regression):
    """Test parity of table columns."""
    data = {}
    for tbl_name, col_name, data_type, is_nullable, column_default, char_max_length in get_table_fields(backend):
        data.setdefault(tbl_name, {})[col_name] = {
            'data_type': data_type,
            'is_nullable': is_nullable,
            'default': column_default,
        }
        if char_max_length:
            data[tbl_name][col_name]['max_length'] = char_max_length
    data_regression.check(data)


def test_primary_keys(backend, data_regression):
    """Test parity of primary key constraints."""
    data = {}
    for tbl_name, name, col_names in sorted(get_constraints(backend, 'p')):
        data.setdefault(tbl_name, {})[name] = col_names
    data_regression.check(data)


def test_unique_constraints(backend, data_regression):
    """Test parity of unique constraints."""
    data = {}
    for tbl_name, name, col_names in sorted(get_constraints(backend, 'u')):
        data.setdefault(tbl_name, {})[name] = sorted(col_names)
    data_regression.check(data)


def test_indexes(backend, data_regression):
    """Test parity of indexes."""
    data = {}
    for tbl_name, name, definition in sorted(get_indexes(backend)):
        data.setdefault(tbl_name, {})[name] = definition
    data_regression.check(data)


def get_table_fields(backend):
    """Get the fields of all AiiDA tables."""
    # see https://www.postgresql.org/docs/9.1/infoschema-columns.html
    rows = backend.execute_raw(
        'SELECT table_name,column_name,data_type,is_nullable,column_default,character_maximum_length '
        'FROM information_schema.columns '
        "WHERE table_schema = 'public' AND table_name LIKE 'db_%';"
    )
    rows = [list(row) for row in rows]
    for row in rows:
        row[3] = row[3].upper() == 'YES'
    return rows


def get_constraints(backend, ctype):
    """Get the constraints of all AiiDA tables, for a particular constraint type."""
    # see https://www.postgresql.org/docs/9.1/catalog-pg-constraint.html
    rows = backend.execute_raw(
        'SELECT tbl.relname,c.conname,ARRAY_AGG(a.attname) FROM pg_constraint AS c '
        'INNER JOIN pg_class AS tbl ON tbl.oid = c.conrelid '
        'INNER JOIN pg_attribute AS a ON a.attrelid = c.conrelid AND a.attnum = ANY(c.conkey) '
        f"WHERE c.contype='{ctype}' AND tbl.relname LIKE 'db_%' "
        'GROUP BY tbl.relname,c.conname;'
    )
    rows = [list(row) for row in rows]
    return rows


def get_indexes(backend):
    """Get the indexes of all AiiDA tables."""
    # see https://www.postgresql.org/docs/9.1/view-pg-indexes.html
    rows = backend.execute_raw(
        'SELECT tablename,indexname,indexdef FROM pg_indexes '
        "WHERE tablename LIKE 'db_%' "
        'ORDER BY tablename,indexname;'
    )
    rows = [list(row) for row in rows]
    return rows
