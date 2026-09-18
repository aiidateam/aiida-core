###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for :mod:`aiida.transports.plugins.ssh_legacy`."""

import logging
import shutil
import subprocess
from unittest.mock import AsyncMock, patch

import pytest
from asyncssh.config import SSHClientConfig

from aiida.common.exceptions import ConfigurationError
from aiida.manage.configuration.settings import AiiDAConfigDir
from aiida.transports.plugins import ssh_legacy
from aiida.transports.plugins.async_backend import _AsyncSSH, _OpenSSH
from aiida.transports.plugins.ssh import AsyncSshTransport

#: Bound before the fixture below replaces it, so one test can still reach the real one.
CONFIG_PATH = ssh_legacy.config_path

LEGACY_PARAMS = {
    'username': 'aiidauser',
    'port': 2222,
    'look_for_keys': False,
    'key_filename': '/home/aiida/.ssh/id_daint',
    'timeout': 60,
    'allow_agent': False,
    'proxy_jump': 'ela.cscs.ch',
    'proxy_command': '',
    'compress': True,
    'gss_auth': False,
    'gss_kex': False,
    'gss_deleg_creds': False,
    'gss_host': '',
    'load_system_host_keys': True,
    'key_policy': 'RejectPolicy',
}


@pytest.fixture(autouse=True)
def config_dir(tmp_path, monkeypatch):
    """Write the configurations into a temporary directory, never the one of whoever runs the suite."""
    monkeypatch.setattr(ssh_legacy, 'config_path', lambda alias: tmp_path / f'{alias}.conf')
    return tmp_path


def directives_of(stanza):
    """Return the directives of a rendered stanza, in order, as ``(keyword, value)`` pairs."""
    return [tuple(line.strip().split(' ', 1)) for line in stanza.splitlines() if line.strip()]


def install(alias, params=None):
    """Write the configuration of a migrated computer, as the storage migration does."""
    stanza = ssh_legacy.render_stanza(alias, 'daint.cscs.ch', LEGACY_PARAMS if params is None else params)
    return ssh_legacy.write_stanza(alias, stanza, 'computer `daint`')


class TestRenderStanza:
    """Tests for :func:`ssh_legacy.render_stanza`."""

    def test_pins_the_connection_parameters(self):
        """The parameters the legacy plugin stored are all expressed as directives."""
        stanza = ssh_legacy.render_stanza('daint_abc123', 'daint.cscs.ch', LEGACY_PARAMS)

        assert directives_of(stanza) == [
            ('Host', 'daint_abc123'),
            ('Hostname', 'daint.cscs.ch'),
            ('User', 'aiidauser'),
            ('Port', '2222'),
            ('ConnectTimeout', '60'),
            ('IdentityFile', '/home/aiida/.ssh/id_daint'),
            ('IdentitiesOnly', 'yes'),
            ('IdentityAgent', 'none'),
            ('Compression', 'yes'),
            ('ProxyJump', 'ela.cscs.ch'),
            ('GSSAPIAuthentication', 'no'),
            ('GSSAPIDelegateCredentials', 'no'),
        ]

    def test_omits_the_directives_a_stock_client_would_reject(self):
        """``GSSAPIKeyExchange`` is a patched-client keyword, and a stock client aborts on it."""
        off = ssh_legacy.render_stanza('h_abc123', 'host', LEGACY_PARAMS)
        on = ssh_legacy.render_stanza('h_abc123', 'host', {**LEGACY_PARAMS, 'gss_kex': True})

        assert 'GSSAPIKeyExchange' not in off
        assert ('GSSAPIKeyExchange', 'yes') in directives_of(on)

    def test_pins_the_parameters_that_are_switched_off(self):
        """This configuration replaces the client's own, so a parameter left off is still pinned."""
        directives = directives_of(ssh_legacy.render_stanza('h_abc123', 'host', {**LEGACY_PARAMS, 'compress': False}))

        assert ('Compression', 'no') in directives

    @pytest.mark.parametrize('key_policy', ('AutoAddPolicy', 'WarningPolicy'))
    def test_translates_the_permissive_host_key_policies(self, key_policy):
        """Both permissive paramiko policies become ``no``, the permissive OpenSSH setting."""
        stanza = ssh_legacy.render_stanza('h_abc123', 'host', {**LEGACY_PARAMS, 'key_policy': key_policy})

        assert ('StrictHostKeyChecking', 'no') in directives_of(stanza)

    def test_leaves_the_strict_host_key_policy_to_the_client(self):
        """``RejectPolicy`` is what every client does unasked, so pinning it would only add noise."""
        stanza = ssh_legacy.render_stanza('h_abc123', 'host', {**LEGACY_PARAMS, 'key_policy': 'RejectPolicy'})

        assert 'StrictHostKeyChecking' not in stanza

    def test_offers_no_key_of_its_own_when_none_was_looked_for(self):
        """``IdentitiesOnly`` would leave the default ``~/.ssh/id_*`` in place; ``none`` empties them."""
        params = {**LEGACY_PARAMS, 'key_filename': ''}
        directives = directives_of(ssh_legacy.render_stanza('h_abc123', 'host', params))

        assert ('IdentityFile', 'none') in directives
        assert 'IdentitiesOnly' not in dict(directives)

    def test_restricts_to_the_named_key_when_one_was_given(self):
        """With an ``IdentityFile`` to restrict them to, ``IdentitiesOnly`` drops the default keys."""
        directives = directives_of(ssh_legacy.render_stanza('h_abc123', 'host', LEGACY_PARAMS))

        assert ('IdentityFile', '/home/aiida/.ssh/id_daint') in directives
        assert ('IdentitiesOnly', 'yes') in directives

    def test_discards_the_known_hosts_when_they_were_not_loaded(self):
        """Without loaded host keys no host was ever known, which ``/dev/null`` reproduces."""
        params = {**LEGACY_PARAMS, 'load_system_host_keys': False}
        directives = directives_of(ssh_legacy.render_stanza('h_abc123', 'host', params))

        assert ('UserKnownHostsFile', '/dev/null') in directives
        assert ('GlobalKnownHostsFile', '/dev/null') in directives

    def test_quotes_values_containing_whitespace(self):
        """An unquoted value with a space in it would be read as a directive with extra arguments."""
        params = {**LEGACY_PARAMS, 'key_filename': '/home/aiida/my keys/id_rsa'}
        stanza = ssh_legacy.render_stanza('h_abc123', 'host', params)

        assert ('IdentityFile', '"/home/aiida/my keys/id_rsa"') in directives_of(stanza)

    def test_omits_the_parameters_that_are_unset(self):
        """An empty legacy parameter has no directive, rather than one with an empty value."""
        keywords = [keyword for keyword, *_ in directives_of(ssh_legacy.render_stanza('h_abc123', 'host', {}))]

        assert 'User' not in keywords
        assert 'IdentityFile' not in keywords
        assert 'ProxyJump' not in keywords

    def test_keeps_the_proxy_command_as_the_rest_of_the_line(self):
        """``ProxyCommand`` takes everything after it, and must not be quoted despite its spaces."""
        params = {**LEGACY_PARAMS, 'proxy_jump': '', 'proxy_command': 'ssh -W %h:%p gateway'}
        stanza = ssh_legacy.render_stanza('h_abc123', 'host', params)

        assert ('ProxyCommand', 'ssh -W %h:%p gateway') in directives_of(stanza)


class TestRenderedStanzaIsValid:
    """The rendered configuration has to be understood by the clients that will be given it."""

    def test_asyncssh_resolves_the_alias(self):
        """``asyncssh`` reads the directives it knows out of the file it is passed."""
        path = install('daint_abc123')

        # last_config, paths, reload, canonical, final, local_user, user, host, port.
        config = SSHClientConfig.load(None, [str(path)], False, False, False, 'local', (), 'daint_abc123', ())

        assert config.get('Hostname') == 'daint.cscs.ch'
        assert config.get('User') == 'aiidauser'
        assert config.get('Port') == 2222
        assert config.get('ProxyJump') == 'ela.cscs.ch'

    @pytest.mark.skipif(shutil.which('ssh') is None, reason='requires the `ssh` client')
    def test_the_ssh_client_accepts_every_directive(self):
        """``ssh`` rejects a keyword it does not know, unlike ``asyncssh``, which skips it."""
        params = {**LEGACY_PARAMS, 'gss_host': 'host/daint.cscs.ch', 'load_system_host_keys': False}
        path = install('daint_abc123', params)

        process = subprocess.run(
            ['ssh', '-G', '-F', str(path), 'daint_abc123'], capture_output=True, text=True, check=False
        )

        assert process.returncode == 0, process.stderr
        assert 'user aiidauser' in process.stdout
        assert 'port 2222' in process.stdout


class TestWriteStanza:
    """Tests for :func:`ssh_legacy.write_stanza`."""

    def test_writes_one_file_per_host(self, config_dir):
        """Two computers on the same machine must not end up sharing a configuration."""
        install('one_abc123')
        install('two_def456')

        assert 'Host one_abc123' in (config_dir / 'one_abc123.conf').read_text(encoding='utf8')
        assert 'Host two_def456' in (config_dir / 'two_def456.conf').read_text(encoding='utf8')

    def test_records_which_computer_the_file_belongs_to(self):
        """The host names are opaque, so the file says what it is for."""
        assert install('daint_abc123').read_text(encoding='utf8').startswith('# computer `daint`')

    def test_is_readable_only_by_its_owner(self):
        """The file names an identity file and a user, as ``~/.ssh/config`` would."""
        assert install('daint_abc123').stat().st_mode & 0o777 == 0o600

    def test_goes_into_the_aiida_configuration_directory(self, tmp_path, monkeypatch):
        """The real destination, which every other test in this module replaces."""
        monkeypatch.setattr(AiiDAConfigDir, 'get', classmethod(lambda cls: tmp_path))

        assert CONFIG_PATH('h_abc123') == tmp_path / '_migration_ssh_config' / 'h_abc123.conf'


class TestResolveConfigFile:
    """Whether a computer carries a configuration is answered by the database, not by the filesystem."""

    def test_an_unset_parameter_means_the_default_location(self):
        assert ssh_legacy.resolve_config_file(None) is None
        assert ssh_legacy.resolve_config_file('') is None

    def test_a_recorded_configuration_is_returned(self):
        path = install('daint_abc123')

        assert ssh_legacy.resolve_config_file(str(path)) == path

    def test_a_missing_configuration_is_reported(self):
        """Deleting the file must not quietly fall back to the default location, and cannot be undone."""
        path = install('daint_abc123')
        path.unlink()

        with pytest.raises(ConfigurationError, match=r'daint_abc123\.conf` is missing.*--host <YOUR-ALIAS>'):
            ssh_legacy.resolve_config_file(str(path))


class TestBackendsUseTheConfiguration:
    """The configuration is of no use unless both backends hand it to their client."""

    def test_openssh_points_ssh_at_it(self):
        """Every ``ssh`` invocation has to select the file, or the host does not resolve."""
        path = install('daint_abc123')
        backend = _OpenSSH(
            'daint_abc123', 'daint_abc123', logging.getLogger(__name__), 'bash ', True, ssh_config_file=path
        )

        assert backend.ssh_command_generator('whoami')[:4] == ['ssh', '-F', str(path), 'daint_abc123']

    def test_openssh_points_scp_at_it(self):
        """Switching a migrated computer to the ``openssh`` backend has to keep working."""
        path = install('daint_abc123')
        backend = _OpenSSH(
            'daint_abc123', 'daint_abc123', logging.getLogger(__name__), 'bash ', True, ssh_config_file=path
        )

        assert backend.scp_options[:2] == ['-F', str(path)]

    def test_openssh_leaves_a_native_computer_alone(self):
        """A computer that carries no configuration must be invoked exactly as before."""
        backend = _OpenSSH('my-alias', 'my-alias', logging.getLogger(__name__), 'bash ', True)

        assert backend.ssh_command_generator('whoami')[:2] == ['ssh', 'my-alias']
        assert backend.scp_options == []

    @pytest.mark.asyncio
    async def test_asyncssh_is_given_it(self):
        """``asyncssh`` reads the file it is passed, rather than the default location."""
        path = install('daint_abc123')
        backend = _AsyncSSH('daint_abc123', 'daint_abc123', logging.getLogger(__name__), 'bash ', ssh_config_file=path)

        with patch('asyncssh.connect', new=AsyncMock()) as connect:
            await backend._connect('daint_abc123')

        assert connect.await_args.kwargs['config'] == [path]

    @pytest.mark.asyncio
    async def test_asyncssh_is_given_nothing_for_a_native_computer(self):
        """A computer that carries no configuration keeps reading the default location."""
        backend = _AsyncSSH('my-alias', 'my-alias', logging.getLogger(__name__), 'bash ')

        with patch('asyncssh.connect', new=AsyncMock()) as connect:
            await backend._connect('my-alias')

        assert connect.await_args.kwargs == {}

    def test_the_transport_refuses_to_be_built_without_it(self, config_dir):
        """A computer whose recorded configuration is gone fails where it is built."""
        with pytest.raises(ConfigurationError, match='is missing'):
            AsyncSshTransport(
                machine='daint.cscs.ch', host='daint_abc123', ssh_config_file=str(config_dir / 'gone.conf')
            )

    def test_the_transport_passes_it_on(self):
        path = install('daint_abc123')

        transport = AsyncSshTransport(machine='daint.cscs.ch', host='daint_abc123', ssh_config_file=str(path))

        assert transport.async_backend.ssh_config_file == path
        assert transport.gotocomputer_command('/scratch').startswith(f'ssh -t -F {path} daint_abc123')


class TestConnectKwargs:
    """Tests for :func:`ssh_legacy.connect_kwargs`, the two directives ``asyncssh`` skips."""

    def test_lifts_the_server_identity(self):
        """``GSSAPIServerIdentity`` has no handler in ``asyncssh`` and is passed as an argument."""
        path = install('daint_abc123', {**LEGACY_PARAMS, 'gss_auth': True, 'gss_host': 'host/daint.cscs.ch'})

        assert ssh_legacy.connect_kwargs(path)['gss_host'] == 'host/daint.cscs.ch'

    def test_lifts_a_permissive_host_key_policy(self):
        """``StrictHostKeyChecking no`` has no handler either, and means trusting any host key."""
        path = install('daint_abc123', {**LEGACY_PARAMS, 'key_policy': 'AutoAddPolicy'})

        assert ssh_legacy.connect_kwargs(path) == {'known_hosts': None}

    def test_lifts_an_empty_identity_list(self):
        """``asyncssh`` would read ``IdentityFile none`` as a file name, and load the defaults."""
        path = install('daint_abc123', {**LEGACY_PARAMS, 'key_filename': ''})

        assert ssh_legacy.connect_kwargs(path)['client_keys'] is None

    def test_a_named_key_is_left_to_asyncssh(self):
        """An ``IdentityFile`` naming a real key is one of the directives it parses itself."""
        assert 'client_keys' not in ssh_legacy.connect_kwargs(install('daint_abc123'))

    def test_a_strict_policy_leaves_the_validation_to_asyncssh(self):
        """``StrictHostKeyChecking yes`` is what ``asyncssh`` does by default."""
        assert ssh_legacy.connect_kwargs(install('daint_abc123')) == {}
