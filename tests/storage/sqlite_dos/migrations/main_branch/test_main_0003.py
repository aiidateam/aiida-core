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
import os
import pathlib

import pytest
from sqlalchemy import inspect, text

from aiida.common.utils import get_new_uuid
from aiida.manage.configuration import Profile
from aiida.storage.migrations import legacy_ssh
from aiida.storage.sqlite_dos.backend import SqliteDosMigrator
from aiida.storage.sqlite_zip.models import SqliteBase
from aiida.storage.sqlite_zip.utils import create_sqla_engine
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
def ssh_dir(tmp_path, monkeypatch):
    """Write into a temporary directory, never into the ``~/.ssh`` of whoever runs the suite."""
    monkeypatch.setattr(legacy_ssh, 'ssh_dir', lambda: tmp_path / '.ssh')
    return tmp_path / '.ssh'


def _engine(profile: Profile):
    return create_sqla_engine(pathlib.Path(profile.storage_config['filepath']) / 'database.sqlite')


def _insert_computer(profile: Profile, label: str, transport_type: str, hostname: str = 'localhost') -> str:
    uuid = get_new_uuid()
    with _engine(profile).begin() as conn:
        conn.execute(
            text(
                'INSERT INTO db_dbcomputer (uuid, label, hostname, description, scheduler_type, transport_type, '
                "metadata) VALUES (:uuid, :label, :hostname, '', 'core.direct', :transport_type, '{}')"
            ),
            {'uuid': uuid, 'label': label, 'hostname': hostname, 'transport_type': transport_type},
        )
    return uuid


def _insert_authinfo(profile: Profile, label: str, auth_params: dict, email: str = 'a@b.c') -> None:
    """Store ``auth_params`` for the computer with the given label, as ``verdi computer configure`` would."""
    with _engine(profile).begin() as conn:
        conn.execute(
            text(
                'INSERT INTO db_dbuser (email, first_name, last_name, institution) '
                "VALUES (:email, '', '', '') ON CONFLICT DO NOTHING"
            ),
            {'email': email},
        )
        conn.execute(
            text(
                'INSERT INTO db_dbauthinfo (aiidauser_id, dbcomputer_id, metadata, auth_params, enabled) '
                'SELECT (SELECT id FROM db_dbuser WHERE email = :email), id, :metadata, :auth_params, TRUE '
                'FROM db_dbcomputer WHERE label = :label'
            ),
            {'label': label, 'email': email, 'metadata': '{}', 'auth_params': json.dumps(auth_params)},
        )


def _schema_version(profile: Profile) -> str:
    with _engine(profile).connect() as conn:
        return conn.execute(text('SELECT version_num FROM alembic_version')).scalar_one()


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


def test_rename_ssh_async_transport(uninitialised_profile, ssh_dir):
    """``core.ssh_async`` computers are renamed, and a legacy one is moved to a configuration entry."""
    with SqliteDosMigrator(uninitialised_profile) as migrator:
        migrator.migrate_up('main@main_0002')

    _insert_computer(uninitialised_profile, 'async', 'core.ssh_async')
    _insert_computer(uninitialised_profile, 'async_two', 'core.ssh_async')
    uuid = _insert_computer(uninitialised_profile, 'legacy', 'core.ssh')
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
    assert set(auth_params) == {'host', 'backend', 'use_login_shell', 'known_hosts', 'gss_host'}
    assert auth_params['backend'] == 'asyncssh'
    assert auth_params['use_login_shell'] is False
    assert auth_params['host'] == f'aiida-migrated-{uuid}'

    entry = (ssh_dir / legacy_ssh.CONFIG_NAME).read_text(encoding='utf8')
    assert f'Host {auth_params["host"]}' in entry
    assert 'User alice' in entry
    assert 'Port 2222' in entry
    assert 'ConnectTimeout 30' in entry
    assert 'IdentityFile /home/alice/.ssh/id_rsa' in entry
    assert 'ProxyJump gw' in entry
    assert 'GSSAPIServerIdentity host/daint.cscs.ch' in entry
    assert 'StrictHostKeyChecking no' in entry

    # Included from the top, so that a `Host *` of the user cannot override the entry.
    assert (ssh_dir / 'config').read_text(encoding='utf8').startswith(f'Include {legacy_ssh.CONFIG_NAME}\n')

    # What the migration stored has to be enough to build the transport it stored it for.
    transport = AsyncSshTransport(machine=auth_params['host'], **auth_params)
    assert transport.async_backend.connect_kwargs == {'known_hosts': None, 'gss_host': 'host/daint.cscs.ch'}


def test_two_computers_on_one_host_get_one_entry_each(uninitialised_profile, ssh_dir):
    """The alias is the computer, not the machine, so two computers cannot end up sharing an entry."""
    with SqliteDosMigrator(uninitialised_profile) as migrator:
        migrator.migrate_up('main@main_0002')

    for label in ('one', 'two'):
        _insert_computer(uninitialised_profile, label, 'core.ssh', hostname='daint.cscs.ch')
        _insert_authinfo(uninitialised_profile, label, LEGACY_AUTH_PARAMS)

    with SqliteDosMigrator(uninitialised_profile) as migrator:
        migrator.migrate_up('main@main_0003')

    hosts = {label: _auth_params(uninitialised_profile, label)['host'] for label in ('one', 'two')}
    entries = (ssh_dir / legacy_ssh.CONFIG_NAME).read_text(encoding='utf8')

    assert hosts['one'] != hosts['two']
    assert all(f'Host {host}' in entries for host in hosts.values())


def test_each_user_of_a_computer_gets_an_entry(uninitialised_profile, ssh_dir):
    """The parameters are per user and computer both, so one entry cannot serve two users."""
    with SqliteDosMigrator(uninitialised_profile) as migrator:
        migrator.migrate_up('main@main_0002')

    uuid = _insert_computer(uninitialised_profile, 'legacy', 'core.ssh')
    _insert_authinfo(uninitialised_profile, 'legacy', LEGACY_AUTH_PARAMS, email='alice@b.c')
    _insert_authinfo(uninitialised_profile, 'legacy', {**LEGACY_AUTH_PARAMS, 'username': 'bob'}, email='bob@b.c')

    with SqliteDosMigrator(uninitialised_profile) as migrator:
        migrator.migrate_up('main@main_0003')

    with _engine(uninitialised_profile).connect() as conn:
        stored = dict(
            conn.execute(
                text('SELECT u.email, a.auth_params FROM db_dbauthinfo a JOIN db_dbuser u ON u.id = a.aiidauser_id')
            ).fetchall()
        )
    hosts = {email: json.loads(params)['host'] for email, params in stored.items()}
    entries = (ssh_dir / legacy_ssh.CONFIG_NAME).read_text(encoding='utf8')

    assert hosts['alice@b.c'] != hosts['bob@b.c']
    assert all(host.startswith(f'aiida-migrated-{uuid}') for host in hosts.values())
    assert f'Host {hosts["alice@b.c"]}\n    Hostname localhost\n    User alice' in entries
    assert f'Host {hosts["bob@b.c"]}\n    Hostname localhost\n    User bob' in entries


def test_a_host_another_profile_defines_gets_an_entry_of_its_own(uninitialised_profile, ssh_dir):
    """Computers are imported by UUID, so two profiles can configure the same one differently."""
    with SqliteDosMigrator(uninitialised_profile) as migrator:
        migrator.migrate_up('main@main_0002')

    uuid = _insert_computer(uninitialised_profile, 'legacy', 'core.ssh')
    _insert_authinfo(uninitialised_profile, 'legacy', LEGACY_AUTH_PARAMS)

    ssh_dir.mkdir(parents=True)
    taken = ssh_dir / legacy_ssh.CONFIG_NAME
    taken.write_text(f'Host aiida-migrated-{uuid}\n    Hostname elsewhere\n', encoding='utf8')

    with SqliteDosMigrator(uninitialised_profile) as migrator:
        migrator.migrate_up('main@main_0003')

    entries = taken.read_text(encoding='utf8')

    assert _auth_params(uninitialised_profile, 'legacy')['host'] == f'aiida-migrated-{uuid}-2'
    assert f'Host aiida-migrated-{uuid}\n    Hostname elsewhere' in entries
    assert f'Host aiida-migrated-{uuid}-2\n    Hostname localhost' in entries


@pytest.mark.skipif(os.geteuid() == 0, reason='the superuser writes into a directory whatever its mode')
def test_a_configuration_that_cannot_be_written_aborts_the_migration(uninitialised_profile, monkeypatch, tmp_path):
    """The parameters must not be dropped from the database while the entry replacing them is lost."""
    unwritable = tmp_path / 'unwritable'
    unwritable.mkdir()
    monkeypatch.setattr(legacy_ssh, 'ssh_dir', lambda: unwritable / '.ssh')

    with SqliteDosMigrator(uninitialised_profile) as migrator:
        migrator.migrate_up('main@main_0002')

    _insert_computer(uninitialised_profile, 'legacy', 'core.ssh')
    _insert_authinfo(uninitialised_profile, 'legacy', LEGACY_AUTH_PARAMS)
    unwritable.chmod(0o500)

    try:
        with pytest.raises(PermissionError):
            with SqliteDosMigrator(uninitialised_profile) as migrator:
                migrator.migrate_up('main@main_0003')
    finally:
        unwritable.chmod(0o700)

    assert _auth_params(uninitialised_profile, 'legacy') == LEGACY_AUTH_PARAMS
    assert _schema_version(uninitialised_profile) == 'main_0002'

    # Once the cause is out of the way, the profile migrates as it would have the first time.
    with SqliteDosMigrator(uninitialised_profile) as migrator:
        migrator.migrate_up('main@main_0003')

    auth_params = _auth_params(uninitialised_profile, 'legacy')

    assert _schema_version(uninitialised_profile) == 'main_0003'
    assert auth_params['host'].startswith('aiida-migrated-')
    assert f'Host {auth_params["host"]}' in (unwritable / '.ssh' / legacy_ssh.CONFIG_NAME).read_text(encoding='utf8')


def test_the_permissive_host_key_policies_are_reported(uninitialised_profile, ssh_dir, caplog):
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


def test_rename_ssh_async_transport_without_computers(uninitialised_profile, ssh_dir):
    """The migration writes no configuration for a profile that has no SSH computers."""
    with SqliteDosMigrator(uninitialised_profile) as migrator:
        migrator.migrate_up('main@main_0002')

    with SqliteDosMigrator(uninitialised_profile) as migrator:
        migrator.migrate_up('main@main_0003')

    assert _transport_types(uninitialised_profile) == {}
    assert not ssh_dir.exists()


def test_a_renamed_computer_gets_no_entry(uninitialised_profile, ssh_dir):
    """A ``core.ssh_async`` computer already connects through the client configuration of the user."""
    with SqliteDosMigrator(uninitialised_profile) as migrator:
        migrator.migrate_up('main@main_0002')

    _insert_computer(uninitialised_profile, 'async', 'core.ssh_async')
    _insert_authinfo(uninitialised_profile, 'async', {'host': 'my-alias', 'use_login_shell': True})

    with SqliteDosMigrator(uninitialised_profile) as migrator:
        migrator.migrate_up('main@main_0003')

    assert _auth_params(uninitialised_profile, 'async') == {'host': 'my-alias', 'use_login_shell': True}
    assert not ssh_dir.exists()


def test_with_db_setting(uninitialised_profile):
    """Test upgrading a historically initialized database with the settings table.

    Before ``main_0003``, fresh ``sqlite_dos`` initialization created
    ``db_dbsetting`` through ORM metadata, while the migration schema omitted
    it. This models that database state before upgrading it to ``main_0003``.
    """
    with SqliteDosMigrator(uninitialised_profile) as migrator:
        SqliteBase.metadata.tables['db_dbsetting'].create(migrator.connection)
        migrator.connection.commit()
        migrator.migrate_up('main@main_0003')
        assert inspect(migrator.connection).has_table('db_dbsetting')


def test_downgrade(uninitialised_profile):
    """Test downgrading from ``main_0003`` to ``main_0002``."""
    with SqliteDosMigrator(uninitialised_profile) as migrator:
        migrator.migrate_up('main@main_0003')
        migrator.migrate_down('main_0002')
        migrator.connection.commit()

    with SqliteDosMigrator(uninitialised_profile) as migrator:
        assert migrator.get_schema_version_profile() == 'main_0002'
        assert inspect(migrator.connection).has_table('db_dbsetting')
