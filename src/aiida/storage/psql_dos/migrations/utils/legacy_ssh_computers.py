###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Conversion of the computers configured with the legacy ``core.ssh`` (paramiko) transport plugin.

Shared by the ``psql_dos`` and ``sqlite_dos`` backends, whose ``main_0003`` revisions both perform
it. The archive backend only renames: it has no configuration directory to write into, and
authentication parameters are left out of an archive unless explicitly asked for.
"""

import json
import uuid

from sqlalchemy.engine import Connection
from sqlalchemy.sql import text

from aiida.storage.log import MIGRATE_LOGGER
from aiida.transports.plugins import ssh_legacy


def _alias(hostname: str) -> str:
    """Return the ``Host`` name to define for a computer.

    The hostname is kept as a prefix so the entry can be recognised by eye, while the ``uuid`` keeps
    two computers on the same host apart. An alias is matched literally, so anything ``ssh`` would
    read as a pattern or as a second token is replaced.
    """
    prefix = ''.join(character if character.isalnum() or character in '.-_' else '-' for character in hostname)
    return f'{prefix}_{uuid.uuid4()}'


def migrate_legacy_ssh_computers(connection: Connection) -> int:
    """Replace the stored connection parameters of every legacy computer with a configuration entry.

    Must run *before* the ``core.ssh_async`` computers are renamed, which is what still tells the two
    kinds of computer apart.

    :return: the number of authentication parameter sets that were converted.
    """
    rows = connection.execute(
        text(
            'SELECT a.id, a.auth_params, c.hostname, c.label FROM db_dbauthinfo AS a '
            'JOIN db_dbcomputer AS c ON c.id = a.dbcomputer_id '
            "WHERE c.transport_type = 'core.ssh'"
        )
    ).fetchall()

    if not rows:
        return 0

    # ``auth_params`` is a ``JSONB`` column on PostgreSQL, which will not take a string as it stands.
    params_value = 'CAST(:params AS JSONB)' if connection.dialect.name == 'postgresql' else ':params'
    statement = text(f'UPDATE db_dbauthinfo SET auth_params = {params_value} WHERE id = :id')
    paths = []
    permissive = []

    for authinfo_id, auth_params, hostname, label in rows:
        params = json.loads(auth_params) if isinstance(auth_params, str) else auth_params
        alias = _alias(hostname)

        if params.get('key_policy') in ('AutoAddPolicy', 'WarningPolicy'):
            permissive.append(label)

        # Written before the database is touched, so that a configuration that cannot be written
        # aborts the migration rather than leaving a computer whose parameters have gone nowhere.
        paths.append(
            ssh_legacy.write_stanza(
                alias,
                ssh_legacy.render_stanza(alias, hostname, params),
                f'computer `{label}`, migrated from the legacy `core.ssh` transport plugin',
            )
        )

        migrated = {key: value for key, value in params.items() if key not in ssh_legacy.LEGACY_PARAM_NAMES}
        migrated['host'] = alias
        # Recorded rather than derived, so that a computer whose configuration has gone missing can
        # be told from one that never had any.
        migrated['ssh_config_file'] = str(paths[-1])
        migrated['backend'] = 'asyncssh'

        connection.execute(statement, {'id': authinfo_id, 'params': json.dumps(migrated)})

    MIGRATE_LOGGER.report(
        f'Moved the connection parameters of {len(rows)} computer configuration(s) from the legacy '
        f'`core.ssh` transport plugin into client configurations under `{paths[0].parent}`. '
        'Please verify each of them with `verdi computer test`.'
    )

    if permissive:
        MIGRATE_LOGGER.warning(
            f'{", ".join(sorted(set(permissive)))}: the `AutoAddPolicy`/`WarningPolicy` host key policy became '
            '`StrictHostKeyChecking no`, which is more permissive than it was. The old policies accepted a host '
            'missing from `known_hosts` but still refused a *changed* key for a known host; this also accepts the '
            "changed key. Set `StrictHostKeyChecking yes` in the computer's configuration file to tighten it again."
        )

    return len(rows)
