###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for ``verdi collab``."""

from aiida import get_profile
from aiida.cmdline.commands import cmd_collab
from aiida.tools.collab.config import (
    OPTION_BIND,
    OPTION_ENABLED,
    OPTION_PEERS,
    OPTION_PORT,
    OPTION_TOKEN,
    OPTION_UUID,
)

PEER_URL = 'http://100.64.0.2:9137'
PEER = 'alice'
PEER_UUID = 'uuid-of-alice'
COLLAB_UUID = 'uuid-of-the-collab'
TOKEN = 'the-token'


def peer_entry(url=PEER_URL, nickname=PEER, **overrides):
    """Return a roster entry as a completed contact leaves it."""
    return {
        'url': url,
        'nickname': nickname,
        'name': nickname,
        'seen': True,
        **overrides,
    }


def init_collab(config, peers=None, **options):
    """Set the loaded profile up as part of a collab, as ``verdi collab init`` and a join leave it."""
    scope = get_profile().name
    values = {
        OPTION_ENABLED: True,
        OPTION_UUID: COLLAB_UUID,
        OPTION_TOKEN: TOKEN,
        OPTION_BIND: '127.0.0.1',
        OPTION_PORT: 9137,
        OPTION_PEERS: {PEER_UUID: peer_entry()} if peers is None else peers,
        **options,
    }

    for name, value in values.items():
        config.set_option(name, value, scope=scope)

    config.store()


def test_init(run_cli_command, config_with_profile, monkeypatch):
    """Test that ``verdi collab init`` asks for the address and persists what it announces.

    The port is persisted rather than picked per start, so the URL peers were handed keeps working across restarts.
    """
    monkeypatch.setattr(cmd_collab, 'reserve_port', lambda bind, port, default: 9200)

    result = run_cli_command(cmd_collab.collab_init, use_subprocess=False, user_input='127.0.0.1\n')

    scope = get_profile().name
    get = config_with_profile.get_option

    assert get(OPTION_ENABLED, scope=scope) is True
    assert get(OPTION_PEERS, scope=scope) == {}
    assert get(OPTION_BIND, scope=scope) == '127.0.0.1'
    assert get(OPTION_PORT, scope=scope) == 9200
    assert get(OPTION_UUID, scope=scope)
    assert get(OPTION_TOKEN, scope=scope)
    assert 'http://127.0.0.1:9200' in result.output


def test_init_requires_a_bind_address(run_cli_command, config_with_profile):
    """Test that a non-interactive ``verdi collab init`` without an address fails naming the option.

    The enabled-but-unbound profile, whose endpoint circus restarts forever, is what this makes impossible.
    """
    result = run_cli_command(cmd_collab.collab_init, ['-n'], use_subprocess=False, raises=True)

    assert '--bind' in result.output
    assert config_with_profile.get_option(OPTION_ENABLED, scope=get_profile().name) is False


def test_init_refuses_all_interfaces(run_cli_command, config_with_profile):
    """Test that binding every interface stays refused: the token travels in cleartext over plain HTTP."""
    result = run_cli_command(cmd_collab.collab_init, ['--bind', '0.0.0.0', '-n'], use_subprocess=False, raises=True)

    assert 'refusing to bind' in result.output


def test_init_rejects_a_foreign_address(run_cli_command, config_with_profile):
    """Test that an address that is not this machine's is rejected by the test-bind, not served later."""
    # TEST-NET-1 (RFC 5737), reserved for documentation and therefore never an address of the machine running this.
    result = run_cli_command(cmd_collab.collab_init, ['--bind', '192.0.2.1', '-n'], use_subprocess=False, raises=True)

    assert 'is not an address of this machine' in result.output
    assert config_with_profile.get_option(OPTION_ENABLED, scope=get_profile().name) is False


def test_init_join(run_cli_command, config_with_profile, monkeypatch):
    """Test that joining with a code leaves this profile with the collab, its key and the issuer's whole roster.

    One code is all a newcomer needs: the collab it names, the member to ask and the key to ask with.
    """
    from aiida.tools.collab.client import CollabClient
    from aiida.tools.collab.protocol import JoinCode, JoinResponse

    announced = []

    def join(self, entry):
        announced.append((self._base_url, entry))
        return JoinResponse(
            collab=COLLAB_UUID,
            roster=[
                {'uuid': PEER_UUID, 'url': PEER_URL, 'name': PEER},
                {'uuid': 'uuid-of-bob', 'url': 'http://100.64.0.3:9137', 'name': 'bob'},
            ],
        )

    monkeypatch.setattr(cmd_collab, 'reserve_port', lambda bind, port, default: 9200)
    monkeypatch.setattr(cmd_collab, 'create_profile', lambda ctx, profile_name, non_interactive: get_profile())
    monkeypatch.setattr(CollabClient, 'join', join)

    code = JoinCode(collab=COLLAB_UUID, url=PEER_URL, token=TOKEN).encode()
    result = run_cli_command(cmd_collab.collab_init, ['--join', code, '--bind', '127.0.0.1'], use_subprocess=False)

    profile = get_profile()
    get = config_with_profile.get_option

    assert get(OPTION_UUID, scope=profile.name) == COLLAB_UUID
    assert get(OPTION_TOKEN, scope=profile.name) == TOKEN
    assert get(OPTION_PEERS, scope=profile.name) == {
        # The issuer just answered, so its address is proven; the members it told us about are not.
        PEER_UUID: peer_entry(),
        'uuid-of-bob': peer_entry(url='http://100.64.0.3:9137', nickname='bob', seen=False),
    }
    assert announced == [(PEER_URL, {'uuid': profile.uuid, 'url': 'http://127.0.0.1:9200', 'name': profile.name})], (
        'the joiner announces itself to the issuer of the code'
    )
    assert f'learned about peer `{PEER}`' in result.output


def test_init_join_refuses_an_existing_profile(run_cli_command, config_with_profile):
    """Test that a join does not fold an existing profile into someone else's provenance graph."""
    from aiida.tools.collab.protocol import JoinCode

    code = JoinCode(collab=COLLAB_UUID, url=PEER_URL, token=TOKEN).encode()
    result = run_cli_command(
        cmd_collab.collab_init,
        ['--join', code, '--profile-name', get_profile().name],
        use_subprocess=False,
        raises=True,
    )

    assert 'already exists' in result.output


def test_init_already_initialized(run_cli_command, config_with_profile):
    """Test that ``verdi collab init`` on a profile that is already part of a collab aborts, keeping the token."""
    init_collab(config_with_profile)

    scope = get_profile().name

    result = run_cli_command(cmd_collab.collab_init, ['--bind', '127.0.0.1'], use_subprocess=False, raises=True)

    assert 'already part of a collab' in result.output
    assert config_with_profile.get_option(OPTION_TOKEN, scope=scope) == TOKEN
