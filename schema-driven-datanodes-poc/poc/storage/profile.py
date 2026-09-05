###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tiny global storage profile for the schema-driven data-node PoC."""

from __future__ import annotations

import sqlite3

_connection: sqlite3.Connection | None = None


def load_profile(database_url: str) -> sqlite3.Connection:
    """Open the configured database and keep it as the active storage backend."""
    global _connection
    _connection = sqlite3.connect(database_url)
    _connection.execute(
        'CREATE TABLE IF NOT EXISTS schemas ('
        'schema_name TEXT PRIMARY KEY, '
        'format_version INTEGER NOT NULL, '
        'protobuf_blob BLOB NOT NULL)'
    )
    _connection.execute(
        'CREATE TABLE IF NOT EXISTS nodes ('
        'id INTEGER PRIMARY KEY AUTOINCREMENT, '
        'schema_name TEXT NOT NULL, '
        'value_blob BLOB NOT NULL)'
    )
    _connection.commit()
    return _connection


def get_profile() -> sqlite3.Connection:
    """Return the active storage backend connection."""
    if _connection is None:
        msg = 'no storage profile loaded; call poc.storage.load_profile(database_url) first'
        raise RuntimeError(msg)
    return _connection
