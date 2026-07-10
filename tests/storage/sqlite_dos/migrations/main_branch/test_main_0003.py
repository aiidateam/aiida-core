###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test ``main_0003.py``."""

import json
import logging
import pathlib

import pytest
from sqlalchemy import text

from aiida.common.utils import get_new_uuid
from aiida.manage.configuration import Profile
from aiida.storage.sqlite_dos.backend import SqliteDosMigrator
from aiida.storage.sqlite_zip.utils import create_sqla_engine
from aiida.transports.plugins import ssh_legacy
from aiida.transports.plugins.ssh import AsyncSshTransport

LEGACY_AUTH_PARAMS = {
    'username': 'alice',
    'port': 2222,
    'look_for_keys': False,
    'key_filename': '/home/alice/.ssh/id_rsa',
    'timeout': 30,
    'allow_agent': False,
    'proxy_jump': 'gw',
    'proxy_command': '',
    'compress': True,
    'gss_auth': True,
    'gss_kex': True,
    'gss_deleg_creds': True,
    'gss_host': 'host/daint.cscs.ch',
    'load_system_host_keys': True,
    'key_policy': 'AutoAddPolicy',
    # Shared with the asynchronous plugin, and so kept as it is.
    'use_login_shell': False,
}


@pytest.fixture(autouse=True)
def ssh_config(tmp_path, monkeypatch):
    """Write the configurations into a temporary directory, never the one of whoever runs the suite."""
    monkeypatch.setattr(ssh_legacy, 'config_path', lambda alias: tmp_path / f'{alias}.conf')
    return tmp_path


def _engine(profile: Profile):
    return create_sqla_engine(pathlib.Path(profile.storage_config['filepath']) / 'database.sqlite')


def _insert_computer(profile: Profile, label: str, transport_type: str, hostname: str = 'localhost') -> None:
    with _engine(profile).begin() as conn:
        conn.execute(
            text(
                'INSERT INTO db_dbcomputer (uuid, label, hostname, description, scheduler_type, transport_type, '
                "metadata) VALUES (:uuid, :label, :hostname, '', 'core.direct', :transport_type, '{}')"
            ),
            {'uuid': get_new_uuid(), 'label': label, 'hostname': hostname, 'transport_type': transport_type},
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


def test_rename_ssh_async_transport(uninitialised_profile, ssh_config):
    """``core.ssh_async`` computers are renamed, and a legacy one is moved to a configuration entry."""
    with SqliteDosMigrator(uninitialised_profile) as migrator:
        migrator.migrate_up('main@main_0002')

    _insert_computer(uninitialised_profile, 'async', 'core.ssh_async')
    _insert_computer(uninitialised_profile, 'async_two', 'core.ssh_async')
    _insert_computer(uninitialised_profile, 'legacy', 'core.ssh')
    _insert_computer(uninitialised_profile, 'local', 'core.local')
    _insert_authinfo(uninitialised_profile, 'legacy', LEGACY_AUTH_PARAMS)

    with SqliteDosMigrator(uninitialised_profile) as migrator:
        migrator.migrate_up('main@main_0003')

    assert _transport_types(uninitialised_profile) == {
        'async': 'core.ssh',
        'async_two': 'core.ssh',
        'legacy': 'core.ssh',
        'local': 'core.local',
    }

    # Every parameter the legacy plugin needed is gone, replaced by the alias of the entry; the ones
    # the asynchronous plugin shares with it stay.
    auth_params = _auth_params(uninitialised_profile, 'legacy')
    assert set(auth_params) == {'host', 'ssh_config_file', 'backend', 'use_login_shell'}
    assert auth_params['backend'] == 'asyncssh'
    assert auth_params['use_login_shell'] is False

    assert auth_params['ssh_config_file'] == str(ssh_config / f'{auth_params["host"]}.conf')
    entry = pathlib.Path(auth_params['ssh_config_file']).read_text(encoding='utf8')
    assert f'Host {auth_params["host"]}' in entry
    assert 'User alice' in entry
    assert 'Port 2222' in entry
    assert 'ConnectTimeout 30' in entry
    assert 'IdentityFile /home/alice/.ssh/id_rsa' in entry
    assert 'ProxyJump gw' in entry
    assert 'GSSAPIServerIdentity host/daint.cscs.ch' in entry
    assert 'StrictHostKeyChecking no' in entry

    # What the migration stored has to be enough to build the transport it stored it for.
    transport = AsyncSshTransport(machine=auth_params['host'], **auth_params)
    assert transport.async_backend.ssh_config_file == pathlib.Path(auth_params['ssh_config_file'])


def test_the_alias_is_a_single_literal_pattern(uninitialised_profile, ssh_config):
    """A hostname is not a host name: unescaped, a space would split it and a ``*`` would match all."""
    with SqliteDosMigrator(uninitialised_profile) as migrator:
        migrator.migrate_up('main@main_0002')

    _insert_computer(uninitialised_profile, 'legacy', 'core.ssh', hostname='my host*')
    _insert_authinfo(uninitialised_profile, 'legacy', LEGACY_AUTH_PARAMS)

    with SqliteDosMigrator(uninitialised_profile) as migrator:
        migrator.migrate_up('main@main_0003')

    host = _auth_params(uninitialised_profile, 'legacy')['host']

    assert host.startswith('my-host-_')
    assert ' ' not in host
    assert '*' not in host


def test_the_permissive_host_key_policies_are_reported(uninitialised_profile, ssh_config, caplog):
    """Loosening the host key policy is a security change, so it cannot happen silently."""
    with SqliteDosMigrator(uninitialised_profile) as migrator:
        migrator.migrate_up('main@main_0002')

    _insert_computer(uninitialised_profile, 'legacy', 'core.ssh')
    _insert_authinfo(uninitialised_profile, 'legacy', LEGACY_AUTH_PARAMS)

    with caplog.at_level(logging.WARNING, logger='aiida.storage.migrate'):
        with SqliteDosMigrator(uninitialised_profile) as migrator:
            migrator.migrate_up('main@main_0003')

    assert 'legacy' in caplog.text
    assert 'AutoAddPolicy' in caplog.text


def test_rename_ssh_async_transport_without_computers(uninitialised_profile, ssh_config):
    """The migration writes no configuration for a profile that has no SSH computers."""
    with SqliteDosMigrator(uninitialised_profile) as migrator:
        migrator.migrate_up('main@main_0002')

    with SqliteDosMigrator(uninitialised_profile) as migrator:
        migrator.migrate_up('main@main_0003')

    assert _transport_types(uninitialised_profile) == {}
    assert not list(ssh_config.glob('*.conf'))


def test_a_renamed_computer_gets_no_entry(uninitialised_profile, ssh_config):
    """A ``core.ssh_async`` computer already connects through the client configuration of the user."""
    with SqliteDosMigrator(uninitialised_profile) as migrator:
        migrator.migrate_up('main@main_0002')

    _insert_computer(uninitialised_profile, 'async', 'core.ssh_async')
    _insert_authinfo(uninitialised_profile, 'async', {'host': 'my-alias', 'use_login_shell': True})

    with SqliteDosMigrator(uninitialised_profile) as migrator:
        migrator.migrate_up('main@main_0003')

    assert _auth_params(uninitialised_profile, 'async') == {'host': 'my-alias', 'use_login_shell': True}
    assert not list(ssh_config.glob('*.conf'))
