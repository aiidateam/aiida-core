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
    """Store a data-node schema as one protobuf blob."""
    blob = encode_schema(schema, format_version=format_version)
    connection.execute(
        'INSERT OR REPLACE INTO schemas(schema_name, format_version, protobuf_blob) VALUES (?, ?, ?)',
        (schema.name, format_version, blob),
    )
    connection.commit()


def load_schema(connection: sqlite3.Connection, schema_name: str) -> tuple[int, SchemaSpec]:
    """Load and decode one data-node schema blob."""
    row = connection.execute(
        'SELECT protobuf_blob FROM schemas WHERE schema_name = ?',
        (schema_name,),
    ).fetchone()
    if row is None:
        msg = f'unknown schema {schema_name!r}'
        raise KeyError(msg)
    return decode_schema(t.cast(bytes, row[0]))


def store_node(connection: sqlite3.Connection, schema: SchemaSpec, values: dict[str, t.Any]) -> int:
    """Store one validated data node and return its database id."""
    blob = encode_values(schema, values)
    cursor = connection.execute(
        'INSERT INTO nodes(schema_name, value_blob) VALUES (?, ?)',
        (schema.name, blob),
    )
    connection.commit()
    return t.cast(int, cursor.lastrowid)


def load_node_values(connection: sqlite3.Connection, node_id: int) -> tuple[str, dict[str, t.Any]]:
    """Load one stored node payload and decode it to Python values."""
    row = connection.execute(
        'SELECT schema_name, value_blob FROM nodes WHERE id = ?',
        (node_id,),
    ).fetchone()
    if row is None:
        msg = f'unknown node id {node_id}'
        raise KeyError(msg)
    schema_name = t.cast(str, row[0])
    _, schema = load_schema(connection, schema_name)
    return schema_name, decode_values(schema, t.cast(bytes, row[1]))
