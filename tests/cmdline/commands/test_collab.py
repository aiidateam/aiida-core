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
from aiida.manage.configuration.config import Config
from aiida.tools.collab.config import (
    OPTION_ANNOUNCED,
    OPTION_BIND,
    OPTION_ENABLED,
    OPTION_PEERS,
    OPTION_POLICY,
    OPTION_PORT,
    OPTION_STAMP,
    OPTION_TOKEN,
    OPTION_UUID,
)

PEER_URL = 'http://100.64.0.2:9137'
PEER = 'alice'
PEER_UUID = 'uuid-of-alice'
COLLAB_UUID = 'uuid-of-the-collab'
TOKEN = 'the-token'
POLICY = {'extras_mode': 'local', 'groups_mode': 'local'}


def peer_entry(url=PEER_URL, nickname=PEER, **overrides):
    """Return a roster entry as a completed contact leaves it."""
    return {
        'url': url,
        'nickname': nickname,
        'name': nickname,
        'stamp': 1,
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
        OPTION_STAMP: 1,
        OPTION_ANNOUNCED: 'http://127.0.0.1:9137',
        OPTION_PEERS: {PEER_UUID: peer_entry()} if peers is None else peers,
        OPTION_POLICY: POLICY,
        **options,
    }

    for name, value in values.items():
        config.set_option(name, value, scope=scope)

    config.store()


def test_init(run_cli_command, config_with_profile, monkeypatch):
    """Test that ``verdi collab init`` asks for the policy and the address, and persists what it announces.

    The policy is chosen once and never again, so the prompt says so before asking; the port is persisted rather
    than picked per start, so the URL peers were handed keeps working across restarts.
    """
    monkeypatch.setattr(cmd_collab, 'reserve_port', lambda bind, port, default: 9200)

    # The policy is asked for first, then the address: extras, groups, bind.
    result = run_cli_command(cmd_collab.collab_init, use_subprocess=False, user_input='sync\ngrow\n127.0.0.1\n')

    scope = get_profile().name
    get = config_with_profile.get_option

    assert get(OPTION_ENABLED, scope=scope) is True
    assert get(OPTION_POLICY, scope=scope) == {'extras_mode': 'sync', 'groups_mode': 'grow'}
    assert 'no way to change it afterwards' in result.output, 'the permanence has to be stated before it is chosen'
    assert get(OPTION_PEERS, scope=scope) == {}
    assert get(OPTION_BIND, scope=scope) == '127.0.0.1'
    assert get(OPTION_PORT, scope=scope) == 9200
    assert get(OPTION_ANNOUNCED, scope=scope) == 'http://127.0.0.1:9200'
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
                {'uuid': PEER_UUID, 'url': PEER_URL, 'name': PEER, 'stamp': 1},
                {'uuid': 'uuid-of-bob', 'url': 'http://100.64.0.3:9137', 'name': 'bob', 'stamp': 4},
            ],
        )

    monkeypatch.setattr(cmd_collab, 'reserve_port', lambda bind, port, default: 9200)
    monkeypatch.setattr(cmd_collab, 'create_profile', lambda ctx, profile_name, non_interactive: get_profile())
    monkeypatch.setattr(CollabClient, 'join', join)

    code = JoinCode(collab=COLLAB_UUID, url=PEER_URL, token=TOKEN, policy=POLICY).encode()
    result = run_cli_command(cmd_collab.collab_init, ['--join', code, '--bind', '127.0.0.1'], use_subprocess=False)

    profile = get_profile()
    get = config_with_profile.get_option

    assert get(OPTION_UUID, scope=profile.name) == COLLAB_UUID
    assert get(OPTION_TOKEN, scope=profile.name) == TOKEN
    assert get(OPTION_PEERS, scope=profile.name) == {
        # The issuer just answered, so its address is proven; the members it told us about are not.
        PEER_UUID: peer_entry(),
        'uuid-of-bob': peer_entry(url='http://100.64.0.3:9137', nickname='bob', stamp=4, seen=False),
    }
    assert announced == [
        (PEER_URL, {'uuid': profile.uuid, 'url': 'http://127.0.0.1:9200', 'name': profile.name, 'stamp': 1})
    ], 'the joiner announces itself to the issuer of the code'
    assert f'learned about peer `{PEER}`' in result.output


def test_init_join_shows_the_policy_and_asks_before_creating_anything(
    run_cli_command, config_with_profile, monkeypatch
):
    """Test that joining an extras-syncing collab warns, defaults to no, and creates nothing when declined.

    The consent has to precede the profile it would govern, which is why the policy travels in the code: there is
    nothing to undo when the answer is no.
    """
    from aiida.tools.collab.protocol import JoinCode

    created = []
    monkeypatch.setattr(cmd_collab, 'reserve_port', lambda bind, port, default: 9200)
    monkeypatch.setattr(cmd_collab, 'create_profile', lambda *args: created.append(args) or get_profile())

    code = JoinCode(
        collab=COLLAB_UUID, url=PEER_URL, token=TOKEN, policy={'extras_mode': 'sync', 'groups_mode': 'local'}
    ).encode()
    # A bare Enter, which is the answer a script or an inattentive user gives.
    result = run_cli_command(
        cmd_collab.collab_init,
        ['--join', code, '--bind', '127.0.0.1'],
        use_subprocess=False,
        user_input='\n',
        raises=True,
    )

    assert 'This collab syncs extras' in result.output
    assert '[y/N]' in result.output, 'the consent prompt has to default to no'
    assert 'no profile was created' in result.output
    assert created == [], 'nothing may be created before the terms are accepted'
    assert config_with_profile.get_option(OPTION_ENABLED, scope=get_profile().name) is False


def test_init_join_refuses_to_choose_a_policy(run_cli_command, config_with_profile):
    """Test that a joiner cannot pick its own terms: the collab's policy is the only one there is."""
    from aiida.tools.collab.protocol import JoinCode

    code = JoinCode(collab=COLLAB_UUID, url=PEER_URL, token=TOKEN, policy=POLICY).encode()
    result = run_cli_command(
        cmd_collab.collab_init,
        ['--join', code, '--extras-mode', 'sync', '--bind', '127.0.0.1'],
        use_subprocess=False,
        raises=True,
    )

    assert 'joined on its own terms' in result.output


def test_join_copies_the_policy_along_the_chain(run_cli_command, config_with_profile, profile_factory, monkeypatch):
    """Test that the policy reaches a member that never contacted the creator.

    A creates the collab, B joins through A, C joins through B — and C, which never spoke to A, ends up holding
    exactly the policy A chose. Any member mints a code from its own stored copy, which is what makes that work.
    """
    from aiida.tools.collab.client import CollabClient
    from aiida.tools.collab.config import join_code
    from aiida.tools.collab.protocol import JoinResponse

    created = []
    asked = []
    ports = iter([9200, 9201, 9202])

    def create_profile(ctx, profile_name, non_interactive):
        profile = profile_factory(profile_name)
        config_with_profile.add_profile(profile)
        config_with_profile.store()
        created.append(profile)
        return profile

    def join(self, entry):
        asked.append(self._base_url)
        return JoinResponse(collab=COLLAB_UUID, roster=[])

    # A port of its own per member, so that whom each of them asked is visible in the URL it contacted.
    monkeypatch.setattr(cmd_collab, 'reserve_port', lambda bind, port, default: next(ports))
    monkeypatch.setattr(cmd_collab, 'create_profile', create_profile)
    monkeypatch.setattr(CollabClient, 'join', join)

    run_cli_command(
        cmd_collab.collab_init,
        ['--bind', '127.0.0.1', '--extras-mode', 'sync', '--groups-mode', 'grow', '-n'],
        use_subprocess=False,
    )

    for name, issuer in (('joiner-b', get_profile()), ('joiner-c', None)):
        code = join_code(config_with_profile, issuer or created[-1])
        run_cli_command(
            cmd_collab.collab_init,
            ['--join', code, '--profile-name', name, '--bind', '127.0.0.1', '-n'],
            use_subprocess=False,
        )

    policies = [config_with_profile.get_option(OPTION_POLICY, scope=profile.name) for profile in created]

    assert [profile.name for profile in created] == ['joiner-b', 'joiner-c']
    assert policies == [{'extras_mode': 'sync', 'groups_mode': 'grow'}] * 2
    assert asked == ['http://127.0.0.1:9200', 'http://127.0.0.1:9201'], 'C joined through B and never asked A'


def test_init_join_refuses_an_existing_profile(run_cli_command, config_with_profile):
    """Test that a join does not fold an existing profile into someone else's provenance graph."""
    from aiida.tools.collab.protocol import JoinCode

    code = JoinCode(collab=COLLAB_UUID, url=PEER_URL, token=TOKEN, policy=POLICY).encode()
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


def test_peer_set_url(run_cli_command, config_with_profile):
    """Test that a corrected address is stored as the provisional guess it is.

    Only the owner of an entry stamps it, so the stamp is left where it is and the owner's next announcement
    supersedes the correction; and the peer is unproven at the new address until it answers there.
    """
    init_collab(config_with_profile)

    result = run_cli_command(
        cmd_collab.collab_peer_set, [PEER, '--url', 'http://100.64.0.9:9137'], use_subprocess=False
    )

    entry = config_with_profile.get_option(OPTION_PEERS, scope=get_profile().name)[PEER_UUID]

    assert entry == peer_entry(url='http://100.64.0.9:9137', seen=False)
    assert 'http://100.64.0.9:9137' in result.output


def test_peer_set_keeps_what_the_daemon_merged(run_cli_command, config_with_profile):
    """Test that a command does not revert what the endpoint wrote to the configuration while it ran.

    ``Config.store`` writes the whole dictionary its holder loaded, and since this phase the daemon's endpoint is
    a second writer of that file: a command that stored its start-time copy would drop every entry gossiped in
    between — including a corrected address, which is the one write nothing ever re-applies.
    """
    init_collab(config_with_profile)

    profile = get_profile()
    bob = peer_entry(url='http://100.64.0.3:9137', nickname='bob', seen=False)

    # The endpoint merges a newly gossiped peer into the file, as it does while a command is running.
    daemon = Config.from_file(config_with_profile.filepath)
    merged = {**daemon.get_option(OPTION_PEERS, scope=profile.name), 'uuid-of-bob': bob}
    daemon.set_option(OPTION_PEERS, merged, scope=profile.name)
    daemon.store()

    run_cli_command(cmd_collab.collab_peer_set, [PEER, '--nickname', 'ali'], use_subprocess=False)

    stored = Config.from_file(config_with_profile.filepath).get_option(OPTION_PEERS, scope=profile.name)

    assert stored['uuid-of-bob'] == bob, 'the entry the endpoint merged must survive the command'
    assert stored[PEER_UUID]['nickname'] == 'ali'


def test_peer_set_refuses_a_used_nickname(run_cli_command, config_with_profile):
    """Test that two peers may not share a nickname: it is how a peer is named on the command line."""
    init_collab(
        config_with_profile,
        peers={PEER_UUID: peer_entry(), 'uuid-of-bob': peer_entry(url='http://100.64.0.3:9137', nickname='bob')},
    )

    result = run_cli_command(cmd_collab.collab_peer_set, ['bob', '--nickname', PEER], use_subprocess=False, raises=True)

    assert 'already in use' in result.output
    assert config_with_profile.get_option(OPTION_PEERS, scope=get_profile().name)['uuid-of-bob']['nickname'] == 'bob'


def test_complete_peer(run_cli_command, config_with_profile):
    """Test that the PEER argument completes to the nicknames of the collab, from the configuration alone."""
    import click

    init_collab(
        config_with_profile,
        peers={
            PEER_UUID: peer_entry(),
            'uuid-of-bob': peer_entry(url='http://100.64.0.3:9137', nickname='bob'),
        },
    )

    ctx = click.Context(cmd_collab.collab_peer_set)
    completions = [item.value for item in cmd_collab.complete_peer(ctx, None, 'a')]

    assert completions == ['alice']
