###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for :mod:`aiida.storage.migrations.legacy_ssh`."""

import shutil
import subprocess

import pytest
from asyncssh.config import SSHClientConfig

from aiida.storage.migrations import legacy_ssh

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
def ssh_dir(tmp_path, monkeypatch):
    """Write into a temporary directory, never into the ``~/.ssh`` of whoever runs the suite."""
    monkeypatch.setattr(legacy_ssh, 'ssh_dir', lambda: tmp_path)
    return tmp_path


def directives_of(stanza):
    """Return the directives of a rendered stanza, in order, as ``(keyword, value)`` pairs."""
    return [tuple(line.strip().split(' ', 1)) for line in stanza.splitlines() if line.strip()]


def install(host, params=None, label='daint'):
    """Write the configuration of a migrated computer, as the storage migration does."""
    stanza = legacy_ssh.render_stanza(host, 'daint.cscs.ch', LEGACY_PARAMS if params is None else params)
    return legacy_ssh.write_config({host: stanza}, {host: f'computer `{label}`'})


class TestRenderStanza:
    """Tests for :func:`legacy_ssh.render_stanza`."""

    def test_pins_the_connection_parameters(self):
        """The parameters the legacy plugin stored are all expressed as directives."""
        stanza = legacy_ssh.render_stanza('aiida-migrated-abc', 'daint.cscs.ch', LEGACY_PARAMS)

        assert directives_of(stanza) == [
            ('Host', 'aiida-migrated-abc'),
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
            ('StrictHostKeyChecking', 'yes'),
        ]

    def test_omits_the_directives_a_stock_client_would_reject(self):
        """``GSSAPIKeyExchange`` is a patched-client keyword, and a stock client aborts on it."""
        off = legacy_ssh.render_stanza('h', 'host', LEGACY_PARAMS)
        on = legacy_ssh.render_stanza('h', 'host', {**LEGACY_PARAMS, 'gss_kex': True})

        assert 'GSSAPIKeyExchange' not in off
        assert ('GSSAPIKeyExchange', 'yes') in directives_of(on)

    def test_pins_the_parameters_that_are_switched_off(self):
        """The entry is read before the user's own, so a parameter left off is pinned rather than inherited."""
        directives = directives_of(legacy_ssh.render_stanza('h', 'host', {**LEGACY_PARAMS, 'compress': False}))

        assert ('Compression', 'no') in directives

    @pytest.mark.parametrize('key_policy', ('AutoAddPolicy', 'WarningPolicy'))
    def test_translates_the_permissive_host_key_policies(self, key_policy):
        """Both permissive paramiko policies become ``no``, the permissive OpenSSH setting."""
        stanza = legacy_ssh.render_stanza('h', 'host', {**LEGACY_PARAMS, 'key_policy': key_policy})

        assert ('StrictHostKeyChecking', 'no') in directives_of(stanza)

    def test_pins_the_strict_host_key_policy(self):
        """A ``StrictHostKeyChecking no`` of the user must not loosen a computer that rejected."""
        stanza = legacy_ssh.render_stanza('h', 'host', {**LEGACY_PARAMS, 'key_policy': 'RejectPolicy'})

        assert ('StrictHostKeyChecking', 'yes') in directives_of(stanza)

    def test_offers_no_key_of_its_own_when_none_was_looked_for(self):
        """``IdentitiesOnly`` would leave the default ``~/.ssh/id_*`` in place; ``none`` empties them."""
        params = {**LEGACY_PARAMS, 'key_filename': ''}
        directives = directives_of(legacy_ssh.render_stanza('h', 'host', params))

        assert ('IdentityFile', 'none') in directives
        assert 'IdentitiesOnly' not in dict(directives)

    def test_restricts_to_the_named_key_when_one_was_given(self):
        """With an ``IdentityFile`` to restrict them to, ``IdentitiesOnly`` drops the default keys."""
        directives = directives_of(legacy_ssh.render_stanza('h', 'host', LEGACY_PARAMS))

        assert ('IdentityFile', '/home/aiida/.ssh/id_daint') in directives
        assert ('IdentitiesOnly', 'yes') in directives

    def test_discards_the_known_hosts_when_they_were_not_loaded(self):
        """Without loaded host keys no host was ever known, which ``/dev/null`` reproduces."""
        params = {**LEGACY_PARAMS, 'load_system_host_keys': False}
        directives = directives_of(legacy_ssh.render_stanza('h', 'host', params))

        assert ('UserKnownHostsFile', '/dev/null') in directives
        assert ('GlobalKnownHostsFile', '/dev/null') in directives

    def test_quotes_values_containing_whitespace(self):
        """An unquoted value with a space in it would be read as a directive with extra arguments."""
        params = {**LEGACY_PARAMS, 'key_filename': '/home/aiida/my keys/id_rsa'}
        stanza = legacy_ssh.render_stanza('h', 'host', params)

        assert ('IdentityFile', '"/home/aiida/my keys/id_rsa"') in directives_of(stanza)

    def test_omits_the_parameters_that_are_unset(self):
        """An empty legacy parameter has no directive, rather than one with an empty value."""
        keywords = [keyword for keyword, *_ in directives_of(legacy_ssh.render_stanza('h', 'host', {}))]

        assert 'User' not in keywords
        assert 'IdentityFile' not in keywords
        assert 'ProxyJump' not in keywords

    def test_keeps_the_proxy_command_as_the_rest_of_the_line(self):
        """``ProxyCommand`` takes everything after it, and must not be quoted despite its spaces."""
        params = {**LEGACY_PARAMS, 'proxy_jump': '', 'proxy_command': 'ssh -W %h:%p gateway'}
        stanza = legacy_ssh.render_stanza('h', 'host', params)

        assert ('ProxyCommand', 'ssh -W %h:%p gateway') in directives_of(stanza)


class TestRenderedStanzaIsValid:
    """The rendered configuration has to be understood by the clients that will read it."""

    def test_asyncssh_resolves_the_alias(self):
        """``asyncssh`` reads the directives it knows out of the file it is given."""
        path = install('aiida-migrated-abc')

        # last_config, paths, reload, canonical, final, local_user, user, host, port.
        config = SSHClientConfig.load(None, [str(path)], False, False, False, 'local', (), 'aiida-migrated-abc', ())

        assert config.get('Hostname') == 'daint.cscs.ch'
        assert config.get('User') == 'aiidauser'
        assert config.get('Port') == 2222
        assert config.get('ProxyJump') == 'ela.cscs.ch'

    @pytest.mark.skipif(shutil.which('ssh') is None, reason='requires the `ssh` client')
    def test_the_ssh_client_accepts_every_directive(self):
        """``ssh`` rejects a keyword it does not know, unlike ``asyncssh``, which skips it."""
        params = {**LEGACY_PARAMS, 'gss_host': 'host/daint.cscs.ch', 'load_system_host_keys': False}
        path = install('aiida-migrated-abc', params)

        process = subprocess.run(
            ['ssh', '-G', '-F', str(path), 'aiida-migrated-abc'], capture_output=True, text=True, check=False
        )

        assert process.returncode == 0, process.stderr
        assert 'user aiidauser' in process.stdout
        assert 'port 2222' in process.stdout

    @pytest.mark.skipif(shutil.which('ssh') is None, reason='requires the `ssh` client')
    def test_the_entry_wins_over_a_wildcard_of_the_user(self, ssh_dir, tmp_path):
        """A client takes the first value it obtains, which is why the include goes first."""
        # An absolute include, because a relative one resolves against the real `~/.ssh`.
        config = tmp_path / 'config'
        config.write_text(f'Include {install("aiida-migrated-abc")}\n\nHost *\n    User someone\n', encoding='utf8')

        process = subprocess.run(
            ['ssh', '-G', '-F', str(config), 'aiida-migrated-abc'], capture_output=True, text=True, check=False
        )

        assert process.returncode == 0, process.stderr
        assert 'user aiidauser' in process.stdout


class TestWriteConfig:
    """Tests for :func:`legacy_ssh.write_config`."""

    def test_writes_the_entry(self, ssh_dir):
        assert install('aiida-migrated-abc') == ssh_dir / legacy_ssh.CONFIG_NAME
        assert 'Host aiida-migrated-abc' in (ssh_dir / legacy_ssh.CONFIG_NAME).read_text(encoding='utf8')

    def test_records_which_computer_the_entry_belongs_to(self):
        """The host names are opaque, so the entry says what it is for."""
        assert '# computer `daint`' in install('aiida-migrated-abc').read_text(encoding='utf8')

    def test_is_readable_only_by_its_owner(self):
        """The entry names an identity file and a user, as ``~/.ssh/config`` would."""
        assert install('aiida-migrated-abc').stat().st_mode & 0o777 == 0o600

    def test_creates_the_ssh_directory(self, tmp_path, monkeypatch):
        """A profile can be migrated on a machine where no client has ever run."""
        monkeypatch.setattr(legacy_ssh, 'ssh_dir', lambda: tmp_path / '.ssh')

        assert install('aiida-migrated-abc').is_file()
        assert (tmp_path / '.ssh').stat().st_mode & 0o777 == 0o700

    def test_includes_it_from_the_top_of_the_client_configuration(self, ssh_dir):
        """Anything below a ``Host *`` of the user would lose every keyword that entry sets."""
        (ssh_dir / 'config').write_text('Host *\n    User someone\n', encoding='utf8')
        install('aiida-migrated-abc')

        content = (ssh_dir / 'config').read_text(encoding='utf8')

        assert content.startswith(f'Include {legacy_ssh.CONFIG_NAME}\n')
        assert 'User someone' in content

    def test_writes_the_client_configuration_when_there_is_none(self, ssh_dir):
        install('aiida-migrated-abc')

        assert (ssh_dir / 'config').read_text(encoding='utf8').startswith(f'Include {legacy_ssh.CONFIG_NAME}\n')

    def test_includes_it_once(self, ssh_dir):
        """Migrating a second profile must not add the directive again."""
        install('aiida-migrated-abc')
        install('aiida-migrated-def')

        assert (ssh_dir / 'config').read_text(encoding='utf8').count(f'Include {legacy_ssh.CONFIG_NAME}') == 1

    def test_keeps_the_entries_of_the_computers_migrated_before(self, ssh_dir):
        """Every profile migrated on this machine writes into the same file."""
        install('aiida-migrated-abc')
        install('aiida-migrated-def')

        content = (ssh_dir / legacy_ssh.CONFIG_NAME).read_text(encoding='utf8')

        assert 'Host aiida-migrated-abc' in content
        assert 'Host aiida-migrated-def' in content

    def test_writes_nothing_for_an_entry_that_is_already_there(self, ssh_dir):
        """A migration that aborted and is run again finds its own entry and leaves it alone."""
        before = install('aiida-migrated-abc').read_text(encoding='utf8')
        install('aiida-migrated-abc')

        assert (ssh_dir / legacy_ssh.CONFIG_NAME).read_text(encoding='utf8') == before

    def test_never_rewrites_what_is_already_in_the_file(self, ssh_dir):
        """Whatever the user put here, however they formatted it, is theirs and stays byte for byte."""
        path = ssh_dir / legacy_ssh.CONFIG_NAME
        mine = 'Host mine\n    User bob\n    # this key expires in June\n\nMatch host foo\n    User matched\n'
        path.write_text(mine, encoding='utf8')
        install('aiida-migrated-abc')
        install('aiida-migrated-def')

        assert path.read_text(encoding='utf8').startswith(mine.strip('\n'))

    def test_keeps_an_entry_written_by_hand(self, ssh_dir):
        """The file is an ordinary client configuration, which the user may have edited."""
        path = ssh_dir / legacy_ssh.CONFIG_NAME
        path.write_text('# mine\nHost mine\n    Hostname myhost\n', encoding='utf8')
        install('aiida-migrated-abc')

        content = path.read_text(encoding='utf8')

        assert '# mine\nHost mine\n    Hostname myhost' in content
        assert 'Host aiida-migrated-abc' in content


class TestIncludeIsWrittenOnce:
    """The directive is prepended to a file of the user, so recognising it again matters."""

    @pytest.mark.parametrize(
        'existing',
        (
            'Include aiida-migrated-configs\n',
            'include aiida-migrated-configs\n',
            'Include ~/.ssh/aiida-migrated-configs\n',
            'Include aiida-migrated-configs other\n',
        ),
    )
    def test_recognises_a_directive_of_the_user(self, ssh_dir, existing):
        ssh_dir.mkdir(parents=True, exist_ok=True)
        (ssh_dir / 'config').write_text(existing, encoding='utf8')
        install('aiida-migrated-abc')

        assert (ssh_dir / 'config').read_text(encoding='utf8') == existing

    def test_keeps_the_permissions_of_the_client_configuration(self, ssh_dir):
        """The file belongs to the user, who may well have chosen its mode."""
        ssh_dir.mkdir(parents=True, exist_ok=True)
        config = ssh_dir / 'config'
        config.write_text('Host mine\n', encoding='utf8')
        config.chmod(0o644)
        install('aiida-migrated-abc')

        assert config.stat().st_mode & 0o777 == 0o644

    def test_follows_a_symlinked_client_configuration(self, ssh_dir, tmp_path):
        """A `~/.ssh/config` kept in a dotfiles repository must stay a link to it."""
        ssh_dir.mkdir(parents=True, exist_ok=True)
        dotfiles = tmp_path / 'dotfiles-config'
        dotfiles.write_text('Host mine\n', encoding='utf8')
        (ssh_dir / 'config').symlink_to(dotfiles)
        install('aiida-migrated-abc')

        assert (ssh_dir / 'config').is_symlink()
        assert dotfiles.read_text(encoding='utf8').startswith(f'Include {legacy_ssh.CONFIG_NAME}\n')


class TestRefusesToCorruptTheConfiguration:
    """A directive no client understands breaks every connection the user makes, not only AiiDA's."""

    @pytest.mark.parametrize('parameter', ('username', 'key_filename', 'proxy_command'))
    def test_a_value_with_a_line_break(self, parameter):
        params = {**LEGACY_PARAMS, parameter: 'value\nProxyCommand /bin/evil'}

        with pytest.raises(ValueError, match='contains a line break'):
            legacy_ssh.render_stanza('aiida-migrated-abc', 'daint.cscs.ch', params)


class TestConnectFlags:
    """Tests for :func:`legacy_ssh.connect_flags`, the directives ``asyncssh`` has no handler for."""

    def test_lifts_a_permissive_host_key_policy(self):
        """``StrictHostKeyChecking no`` means trusting any host key."""
        assert legacy_ssh.connect_flags({**LEGACY_PARAMS, 'key_policy': 'AutoAddPolicy'})['known_hosts'] is False

    def test_leaves_a_strict_policy_to_asyncssh(self):
        """``StrictHostKeyChecking yes`` is what ``asyncssh`` does by default."""
        assert 'known_hosts' not in legacy_ssh.connect_flags(LEGACY_PARAMS)

    def test_lifts_an_empty_identity_list(self):
        """``asyncssh`` would read ``IdentityFile none`` as a file name, and load the defaults."""
        assert legacy_ssh.connect_flags({**LEGACY_PARAMS, 'key_filename': ''})['client_keys'] is False

    def test_leaves_a_named_key_to_asyncssh(self):
        """An ``IdentityFile`` naming a real key is one of the directives it parses itself."""
        assert 'client_keys' not in legacy_ssh.connect_flags(LEGACY_PARAMS)

    def test_lifts_the_server_identity(self):
        """``GSSAPIServerIdentity`` has no handler either."""
        params = {**LEGACY_PARAMS, 'gss_auth': True, 'gss_host': 'host/daint.cscs.ch'}

        assert legacy_ssh.connect_flags(params)['gss_host'] == 'host/daint.cscs.ch'

    def test_a_computer_that_needs_nothing_lifted(self):
        assert legacy_ssh.connect_flags(LEGACY_PARAMS) == {}
