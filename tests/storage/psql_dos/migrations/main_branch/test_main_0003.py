###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test ``main_0003.py``."""

import pathlib

import pytest

from aiida.common.utils import get_new_uuid
from aiida.storage.psql_dos.migrator import PsqlDosMigrator
from aiida.transports.plugins import ssh_legacy

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

ASYNC_AUTH_PARAMS = {'host': 'my-alias', 'use_login_shell': True}


@pytest.fixture(autouse=True)
def ssh_config(tmp_path, monkeypatch):
    """Write the configurations into a temporary directory, never the one of whoever runs the suite."""
    monkeypatch.setattr(ssh_legacy, 'config_path', lambda alias: tmp_path / f'{alias}.conf')
    return tmp_path


def test_migration(perform_migrations: PsqlDosMigrator):
    """Test the migration updates the schema revision."""
    perform_migrations.migrate_up('main@main_0002')
    perform_migrations.migrate_up('main@main_0003')

    assert perform_migrations.get_schema_version_profile() == 'main_0003'


def test_downgrade(perform_migrations: PsqlDosMigrator):
    """Test that downgrading from ``main_0003`` restores the ``main_0002`` revision.

    The transport rename has no inverse, so the downgrade only moves the revision back.
    """
    perform_migrations.migrate_up('main@main_0003')
    perform_migrations.migrate_down('main@main_0002')

    assert perform_migrations.get_schema_version_profile() == 'main_0002'


def test_rename_ssh_async_transport(perform_migrations: PsqlDosMigrator, ssh_config):
    """``core.ssh_async`` computers are renamed, and a legacy one is moved to a configuration entry."""
    perform_migrations.migrate_up('main@main_0002')

    computer_model = perform_migrations.get_current_table('db_dbcomputer')
    user_model = perform_migrations.get_current_table('db_dbuser')
    authinfo_model = perform_migrations.get_current_table('db_dbauthinfo')

    with perform_migrations.session() as session:
        for label, transport_type in (
            ('async', 'core.ssh_async'),
            ('async_two', 'core.ssh_async'),
            ('legacy', 'core.ssh'),
            ('local', 'core.local'),
        ):
            session.add(
                computer_model(
                    uuid=get_new_uuid(),
                    label=label,
                    hostname='localhost',
                    description='',
                    transport_type=transport_type,
                    scheduler_type='core.direct',
                    metadata={},
                )
            )
        user = user_model(email='a@b.c', first_name='', last_name='', institution='')
        session.add(user)
        session.commit()

        # The renamed computer is configured too, so that converting after the rename would catch it.
        for label, params in (('legacy', LEGACY_AUTH_PARAMS), ('async', ASYNC_AUTH_PARAMS)):
            computer = session.query(computer_model).filter(computer_model.label == label).one()
            session.add(
                authinfo_model(
                    aiidauser_id=user.id,
                    dbcomputer_id=computer.id,
                    metadata={},
                    auth_params=params,
                    enabled=True,
                )
            )
        session.commit()

    # Perform the migration that is being tested.
    perform_migrations.migrate_up('main@main_0003')

    computer_model = perform_migrations.get_current_table('db_dbcomputer')
    authinfo_model = perform_migrations.get_current_table('db_dbauthinfo')

    with perform_migrations.session() as session:
        transport_types = {computer.label: computer.transport_type for computer in session.query(computer_model).all()}
        stored = {
            computer.label: authinfo.auth_params
            for authinfo, computer in session.query(authinfo_model, computer_model).filter(
                authinfo_model.dbcomputer_id == computer_model.id
            )
        }
    auth_params = stored['legacy']

    # The legacy ``core.ssh`` computer keeps its transport type: it is now served by the asynchronous
    # plugin, which reaches it through the configuration entry written below.
    assert transport_types == {
        'async': 'core.ssh',
        'async_two': 'core.ssh',
        'legacy': 'core.ssh',
        'local': 'core.local',
    }

    # A computer that was already asynchronous is left exactly as it was.
    assert stored['async'] == ASYNC_AUTH_PARAMS

    # Every parameter the legacy plugin needed is gone, replaced by the alias of the entry; the ones
    # the asynchronous plugin shares with it stay.
    assert set(auth_params) == {'host', 'ssh_config_file', 'backend', 'use_login_shell'}
    assert auth_params['backend'] == 'asyncssh'
    assert auth_params['use_login_shell'] is False
    assert auth_params['host'].startswith('localhost_')

    assert auth_params['ssh_config_file'] == str(ssh_config / f'{auth_params["host"]}.conf')
    entry = pathlib.Path(auth_params['ssh_config_file']).read_text(encoding='utf8')
    assert f'Host {auth_params["host"]}' in entry
    assert 'Hostname localhost' in entry
    assert 'User alice' in entry
    assert 'Port 2222' in entry
    assert 'ConnectTimeout 30' in entry
    assert 'IdentityFile /home/alice/.ssh/id_rsa' in entry
    assert 'ProxyJump gw' in entry
    assert 'GSSAPIServerIdentity host/daint.cscs.ch' in entry
    assert 'StrictHostKeyChecking no' in entry
    # One configuration, for the one legacy computer: the renamed ones need none.
    assert len(list(ssh_config.glob('*.conf'))) == 1
