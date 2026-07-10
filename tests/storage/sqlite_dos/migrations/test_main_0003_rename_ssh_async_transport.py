###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test ``main_0003_rename_ssh_async_transport.py``."""

import json
import logging
import pathlib

from sqlalchemy import text

from aiida.common.utils import get_new_uuid
from aiida.manage.configuration import Profile
from aiida.storage.sqlite_dos.backend import SqliteDosMigrator
from aiida.storage.sqlite_zip.utils import create_sqla_engine

LEGACY_AUTH_PARAMS = {'username': 'alice', 'port': 2222, 'proxy_jump': 'gw', 'key_policy': 'AutoAddPolicy'}


def _engine(profile: Profile):
    return create_sqla_engine(pathlib.Path(profile.storage_config['filepath']) / 'database.sqlite')


def _insert_computer(profile: Profile, label: str, transport_type: str) -> None:
    with _engine(profile).begin() as conn:
        conn.execute(
            text(
                'INSERT INTO db_dbcomputer (uuid, label, hostname, description, scheduler_type, transport_type, '
                "metadata) VALUES (:uuid, :label, 'localhost', '', 'core.direct', :transport_type, '{}')"
            ),
            {'uuid': get_new_uuid(), 'label': label, 'transport_type': transport_type},
        )


def _insert_authinfo(profile: Profile, label: str, auth_params: dict) -> None:
    """Store ``auth_params`` for the computer with the given label, as ``verdi computer configure`` would."""
    with _engine(profile).begin() as conn:
        conn.execute(
            text(
                "INSERT INTO db_dbuser (email, first_name, last_name, institution) VALUES ('a@b.c', '', '', '')"
                ' ON CONFLICT DO NOTHING'
            )
        )
        conn.execute(
            text(
                'INSERT INTO db_dbauthinfo (aiidauser_id, dbcomputer_id, metadata, auth_params, enabled) '
                'SELECT (SELECT id FROM db_dbuser LIMIT 1), id, :metadata, :auth_params, TRUE '
                'FROM db_dbcomputer WHERE label = :label'
            ),
            {'label': label, 'metadata': '{}', 'auth_params': json.dumps(auth_params)},
        )


def _transport_types(profile: Profile) -> dict:
    with _engine(profile).connect() as conn:
        return dict(conn.execute(text('SELECT label, transport_type FROM db_dbcomputer')).fetchall())


def _auth_params(profile: Profile, label: str) -> dict:
    with _engine(profile).connect() as conn:
        row = conn.execute(
            text(
                'SELECT a.auth_params FROM db_dbauthinfo a JOIN db_dbcomputer c ON c.id = a.dbcomputer_id '
                'WHERE c.label = :label'
            ),
            {'label': label},
        ).scalar_one()
    return row if isinstance(row, dict) else json.loads(row)


def test_migration(uninitialised_profile, caplog):
    """The ``core.ssh_async`` transport is renamed to ``core.ssh``, and legacy ``core.ssh`` is kept."""
    with SqliteDosMigrator(uninitialised_profile) as migrator:
        migrator.migrate_up('main@main_0002')

    _insert_computer(uninitialised_profile, 'async', 'core.ssh_async')
    _insert_computer(uninitialised_profile, 'async_two', 'core.ssh_async')
    _insert_computer(uninitialised_profile, 'legacy', 'core.ssh')
    _insert_computer(uninitialised_profile, 'local', 'core.local')
    _insert_authinfo(uninitialised_profile, 'legacy', LEGACY_AUTH_PARAMS)

    with caplog.at_level(logging.WARNING, logger='aiida'):
        with SqliteDosMigrator(uninitialised_profile) as migrator:
            migrator.migrate_up('main@main_0003')

    assert _transport_types(uninitialised_profile) == {
        'async': 'core.ssh',
        'async_two': 'core.ssh',
        'legacy': 'core.ssh',
        'local': 'core.local',
    }

    # The legacy computer keeps the connection parameters that the asynchronous plugin now honors.
    assert _auth_params(uninitialised_profile, 'legacy') == LEGACY_AUTH_PARAMS

    # Only the legacy computer is reported, not the two that were just renamed.
    assert '1 computer(s) use the legacy `core.ssh` transport plugin' in caplog.text


def test_migration_without_computers(uninitialised_profile, caplog):
    """The migration is a no-op on a profile that has no SSH computers."""
    with SqliteDosMigrator(uninitialised_profile) as migrator:
        migrator.migrate_up('main@main_0002')

    with caplog.at_level(logging.WARNING, logger='aiida'):
        with SqliteDosMigrator(uninitialised_profile) as migrator:
            migrator.migrate_up('main@main_0003')

    assert _transport_types(uninitialised_profile) == {}
    assert 'legacy `core.ssh` transport plugin' not in caplog.text
