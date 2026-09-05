###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""SQLite persistence for data-node schema and value protobuf blobs."""

from __future__ import annotations

import sqlite3
import typing as t

from poc.orm._core.nodes.data.protobuf import decode_schema, decode_values, encode_schema, encode_values
from poc.orm.nodes.data.schema import SchemaSpec


def store_schema(connection: sqlite3.Connection, schema: SchemaSpec, *, format_version: int = 1) -> None:
    """Store a data-node schema as one protobuf blob, keyed by (name, format_version).

    The row id is preserved on re-install of the same version so that nodes referencing
    it stay pinned to exactly this schema version.
    """
    blob = encode_schema(schema, format_version=format_version)
    connection.execute(
        'INSERT INTO schemas(schema_name, format_version, protobuf_blob) VALUES (?, ?, ?) '
        'ON CONFLICT(schema_name, format_version) DO UPDATE SET protobuf_blob = excluded.protobuf_blob',
        (schema.name, format_version, blob),
    )
    connection.commit()


def load_schema(connection: sqlite3.Connection, schema_name: str) -> tuple[int, SchemaSpec]:
    """Load and decode the latest installed version of one data-node schema."""
    row = connection.execute(
        'SELECT protobuf_blob FROM schemas WHERE schema_name = ? ORDER BY format_version DESC LIMIT 1',
        (schema_name,),
    ).fetchone()
    if row is None:
        msg = f'unknown schema {schema_name!r}'
        raise KeyError(msg)
    return decode_schema(t.cast(bytes, row[0]))


def store_node(
    connection: sqlite3.Connection, schema: SchemaSpec, values: dict[str, t.Any], *, format_version: int = 1
) -> int:
    """Store one validated data node pinned to a schema version and return its id."""
    blob = encode_values(schema, values)
    row = connection.execute(
        'SELECT id FROM schemas WHERE schema_name = ? AND format_version = ?',
        (schema.name, format_version),
    ).fetchone()
    if row is None:
        msg = f'schema {schema.name!r} format version {format_version} is not installed'
        raise KeyError(msg)
    schema_id = t.cast(int, row[0])
    cursor = connection.execute(
        'INSERT INTO nodes(schema_id, value_blob) VALUES (?, ?)',
        (schema_id, blob),
    )
    connection.commit()
    return t.cast(int, cursor.lastrowid)


def load_node_values(connection: sqlite3.Connection, node_id: int) -> tuple[str, dict[str, t.Any]]:
    """Load one stored node payload and decode it against its pinned schema version."""
    row = connection.execute(
        'SELECT schema_id, value_blob FROM nodes WHERE id = ?',
        (node_id,),
    ).fetchone()
    if row is None:
        msg = f'unknown node id {node_id}'
        raise KeyError(msg)
    schema_id, blob = row
    schema_row = connection.execute(
        'SELECT schema_name, protobuf_blob FROM schemas WHERE id = ?',
        (schema_id,),
    ).fetchone()
    if schema_row is None:
        msg = f'schema row {schema_id} referenced by node {node_id} is missing'
        raise KeyError(msg)
    schema_name, schema_blob = schema_row
    _, schema = decode_schema(t.cast(bytes, schema_blob))
    return schema_name, decode_values(schema, t.cast(bytes, blob))
