###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Shared node types and SQLite statements for migrating the deprecated ``Code`` plugin."""

from sqlalchemy import text

LEGACY_NODE_TYPE = 'data.core.code.Code.'
INSTALLED_NODE_TYPE = 'data.core.code.installed.InstalledCode.'
PORTABLE_NODE_TYPE = 'data.core.code.portable.PortableCode.'

# The node type is rewritten and one attribute key is renamed, so the stored hash no longer describes the node and is
# dropped. ``json_extract`` returns 1/0 for a JSON boolean, and ``json_remove`` ignores keys that are not present.
# Check both stored executable keys: some legacy codes already carry ``filepath_executable``.
SQLITE_MISSING_EXECUTABLE = f"""
    SELECT count(*) FROM db_dbnode
    WHERE node_type = '{LEGACY_NODE_TYPE}'
      AND COALESCE(
          CASE WHEN COALESCE(json_extract(attributes, '$.is_local'), 0) = 1
               THEN json_extract(attributes, '$.local_executable')
               ELSE json_extract(attributes, '$.remote_exec_path') END,
          json_extract(attributes, '$.filepath_executable'), ''
      ) = '';
"""


def check_sqlite_executables(conn) -> None:
    """Reject legacy codes whose executable cannot be recovered from stored attributes."""
    missing = conn.execute(text(SQLITE_MISSING_EXECUTABLE)).scalar()
    if missing:
        msg = f'Cannot migrate {missing} legacy Code node(s) without an executable path.'
        raise ValueError(msg)


SQLITE_UPGRADE_STATEMENTS = (
    f"""
    UPDATE db_dbnode
    SET node_type = '{INSTALLED_NODE_TYPE}',
        attributes = json_set(
            json_remove(attributes, '$.is_local', '$.local_executable', '$.remote_exec_path'),
            '$.filepath_executable', COALESCE(
                json_extract(attributes, '$.remote_exec_path'), json_extract(attributes, '$.filepath_executable')
            )
        ),
        extras = json_remove(extras, '$._aiida_hash')
    WHERE node_type = '{LEGACY_NODE_TYPE}'
      AND COALESCE(json_extract(attributes, '$.is_local'), 0) = 0;
    """,
    f"""
    UPDATE db_dbnode
    SET node_type = '{PORTABLE_NODE_TYPE}',
        attributes = json_set(
            json_remove(attributes, '$.is_local', '$.local_executable', '$.remote_exec_path'),
            '$.filepath_executable', COALESCE(
                json_extract(attributes, '$.local_executable'), json_extract(attributes, '$.filepath_executable')
            )
        ),
        extras = json_remove(extras, '$._aiida_hash')
    WHERE node_type = '{LEGACY_NODE_TYPE}'
      AND COALESCE(json_extract(attributes, '$.is_local'), 0) = 1;
    """,
)
