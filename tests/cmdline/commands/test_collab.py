###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for ``verdi collab``."""

from datetime import timedelta

import pytest

from aiida import get_profile
from aiida.cmdline.commands import cmd_collab
from aiida.common import timezone
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
from aiida.tools.collab.state import CollabEvent, CollabState

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
        'active': True,
        'signalled': False,
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


def printed_code(result):
    """Return the join code a command printed: the last thing it writes, so it can be copied off the screen."""
    from aiida.tools.collab.protocol import JoinCode

    return JoinCode.decode(result.output_lines[-1])


@pytest.fixture
def stub_signal(monkeypatch):
    """Record the rotation signals a command sends, with the key they go out under, sending nothing anywhere."""
    from aiida.tools.collab.client import CollabClient

    signals = []

    def signal_retired(self, peer):
        signals.append((self._base_url, peer, self._session.headers['Authorization']))

    monkeypatch.setattr(CollabClient, 'signal_retired', signal_retired)

    return signals


def test_rotate(run_cli_command, config_with_profile, stub_signal):
    """Test that rotating mints a new key, prints it as a code and tells the peers it holds — and no more.

    The collab UUID is untouched: a rotation replaces the key of a collab, never its identity, so the code still
    names the same collab and every cross-check against it keeps working.
    """
    init_collab(config_with_profile)

    profile = get_profile()
    result = run_cli_command(cmd_collab.collab_rotate, use_subprocess=False)

    get = config_with_profile.get_option
    token = get(OPTION_TOKEN, scope=profile.name)
    code = printed_code(result)

    assert token != TOKEN
    assert (code.collab, code.token, code.url) == (COLLAB_UUID, token, 'http://127.0.0.1:9137')
    assert stub_signal == [(PEER_URL, profile.uuid, f'Bearer {TOKEN}')], (
        'the signal goes out under the token it retires: the peers know no other one yet'
    )
    assert get(OPTION_PEERS, scope=profile.name) == {PEER_UUID: peer_entry(active=False)}, (
        'dormancy is not deletion: the whole record is kept as the history a returning member is recognized by'
    )


def test_rotate_leaves_dormant_peers_alone(run_cli_command, config_with_profile, stub_signal):
    """Test that a rotation signals the members it holds and not the ones it already rotated away from.

    Signalling the other branch of a split, or the member that was just excluded, would tell them to come and
    ask for a code they are not meant to get.
    """
    init_collab(
        config_with_profile,
        peers={PEER_UUID: peer_entry(), 'uuid-of-bob': peer_entry(url='http://100.64.0.3:9137', active=False)},
    )

    run_cli_command(cmd_collab.collab_rotate, use_subprocess=False)

    assert [url for url, _, _ in stub_signal] == [PEER_URL]


def test_rotate_survives_an_unreachable_peer(run_cli_command, config_with_profile, monkeypatch):
    """Test that a peer that cannot be told about the rotation is a warning, not a half-done rotation.

    The signal is a courtesy; the rotation is the point. Aborting on it would leave the token swapped on some
    machines and not others depending on who happened to be up.
    """
    from aiida.tools.collab.client import CollabClient
    from aiida.tools.collab.protocol import CollabRequestError

    init_collab(config_with_profile)
    monkeypatch.setattr(
        CollabClient, 'signal_retired', lambda self, peer: (_ for _ in ()).throw(CollabRequestError('offline'))
    )

    result = run_cli_command(cmd_collab.collab_rotate, use_subprocess=False)

    assert 'could not tell alice' in result.output
    assert printed_code(result).token == config_with_profile.get_option(OPTION_TOKEN, scope=get_profile().name)


def test_rotate_does_not_stop_a_peer_that_has_not_rotated(
    run_cli_command, config_with_profile, stub_environment, stub_transfer
):
    """Test that the signal is advisory: a member that received one still syncs with the collab as before.

    Enforcement is the 401 of the endpoints that rotated, and only that. If the signal itself stopped anything,
    an excluded member — who still holds the retired token — could freeze the collab by sending it around.
    """
    init_collab(config_with_profile, peers={PEER_UUID: peer_entry(signalled=True)})

    result = run_cli_command(cmd_collab.collab_pull, ['--force'], use_subprocess=False)

    assert 'pulled 1 node(s)' in result.output
    assert config_with_profile.get_option(OPTION_TOKEN, scope=get_profile().name) == TOKEN


def rekey_code(token='the-new-token', collab=COLLAB_UUID, url=PEER_URL):
    from aiida.tools.collab.protocol import JoinCode

    return JoinCode(collab=collab, url=url, token=token, policy=POLICY).encode()


@pytest.fixture
def stub_join(monkeypatch):
    """Answer the announcement a rekey makes with the issuer's roster, recording what was announced."""
    from aiida.tools.collab.client import CollabClient
    from aiida.tools.collab.protocol import JoinResponse

    announced = []

    def join(self, entry):
        announced.append((self._base_url, entry))
        return JoinResponse(collab=COLLAB_UUID, roster=[{'uuid': PEER_UUID, 'url': PEER_URL, 'name': PEER, 'stamp': 1}])

    monkeypatch.setattr(CollabClient, 'join', join)

    return announced


def test_rekey_swaps_the_token_and_recognizes_the_issuer(run_cli_command, config_with_profile, stub_join):
    """Test that rekeying changes the key and nothing else, and that the member whose code it was comes back.

    Recognition is by profile UUID, so the entry is the one that was there before: the nickname stays, and the
    cursor kept under that UUID means the next sync resumes instead of re-transferring the whole history.
    """
    init_collab(config_with_profile, peers={PEER_UUID: peer_entry(nickname='ali')})

    profile = get_profile()
    before = Config.from_file(config_with_profile.filepath).dictionary

    run_cli_command(cmd_collab.collab_rekey, [rekey_code()], use_subprocess=False)

    get = config_with_profile.get_option
    after = Config.from_file(config_with_profile.filepath).dictionary
    changed = {
        option
        for option in {*before['profiles'][profile.name]['options'], *after['profiles'][profile.name]['options']}
        if before['profiles'][profile.name]['options'].get(option)
        != after['profiles'][profile.name]['options'].get(option)
    }

    assert changed == {OPTION_TOKEN}, 'a rekey swaps the key and leaves everything else where it was'
    assert get(OPTION_TOKEN, scope=profile.name) == 'the-new-token'
    assert get(OPTION_PEERS, scope=profile.name) == {PEER_UUID: peer_entry(nickname='ali')}, (
        'the roster went dormant and the issuer came straight back out of it: same entry, same nickname'
    )
    assert stub_join == [
        (PEER_URL, {'uuid': profile.uuid, 'url': 'http://127.0.0.1:9137', 'name': profile.name, 'stamp': 1})
    ], 'the returning member announces itself: nothing else would tell the issuer it is back'


def test_rekey_without_a_reachable_issuer_leaves_everyone_dormant(
    run_cli_command, config_with_profile, monkeypatch, stub_environment
):
    """Test that a rekey nobody answered swaps the key anyway and leaves no peer to contact.

    Until some peer is seen under the new token there is nobody to sync with, and a pull must say so rather than
    knock on addresses whose owners are still on the old key.
    """
    from aiida.tools.collab.client import CollabClient
    from aiida.tools.collab.protocol import CollabRequestError

    init_collab(config_with_profile)

    contacted = []

    monkeypatch.setattr(CollabClient, 'join', lambda self, entry: (_ for _ in ()).throw(CollabRequestError('offline')))
    monkeypatch.setattr(
        CollabClient, 'check_version_skew', lambda self, local, **kwargs: contacted.append(self._base_url)
    )

    result = run_cli_command(cmd_collab.collab_rekey, [rekey_code()], use_subprocess=False)

    assert 'could not reach' in result.output
    assert config_with_profile.get_option(OPTION_TOKEN, scope=get_profile().name) == 'the-new-token'

    for command in (cmd_collab.collab_pull, cmd_collab.collab_push):
        result = run_cli_command(command, ['--force'], use_subprocess=False, raises=True)

        assert 'dormant' in result.output

    assert contacted == [], 'a dormant peer is not polled, so nothing goes out at all'


def test_rotate_then_rekey_onto_another_code(run_cli_command, config_with_profile, stub_signal, stub_join):
    """Test that a member that has just rotated can adopt somebody else's fresh code all the same.

    Two members rotating at once need no arbitration: a rotator is nobody special, so the way out of the mutual
    401s is that one of them simply rekeys onto the other's code and the collab converges socially.
    """
    init_collab(config_with_profile)

    profile = get_profile()
    mine = printed_code(run_cli_command(cmd_collab.collab_rotate, use_subprocess=False)).token

    run_cli_command(cmd_collab.collab_rekey, [rekey_code(token='the-other-rotation')], use_subprocess=False)

    get = config_with_profile.get_option

    assert mine != TOKEN
    assert get(OPTION_TOKEN, scope=profile.name) == 'the-other-rotation', 'the code wins over the self-minted key'
    assert get(OPTION_PEERS, scope=profile.name) == {PEER_UUID: peer_entry()}, (
        'the issuer comes back out of the roster the rotation had just set dormant'
    )


def test_a_rotation_during_a_sync_is_not_undone_by_it(
    run_cli_command, config_with_profile, stub_environment, stub_transfer, monkeypatch
):
    """Test that a pull finishing after a rotation does not put the peers it talked to back on their feet.

    A pin belongs to the key its sync was negotiated under. Merging this one into the roster the rotation had
    just set dormant would mark the peer active again — and with it everyone that peer vouched for, the member
    that was just excluded included — under a key none of them holds.
    """
    from aiida.tools.collab.client import CollabClient

    init_collab(config_with_profile)

    profile = get_profile()

    def download_delta(self, filepath, delta_id):
        # `verdi collab rotate` in another terminal, landing while the delta is being transferred here.
        cmd_collab.set_key(Config.from_file(config_with_profile.filepath), profile, 'the-rotated-token')
        filepath.write_bytes(b'delta')
        return len(b'delta')

    monkeypatch.setattr(CollabClient, 'download_delta', download_delta)

    result = run_cli_command(cmd_collab.collab_pull, ['--force'], use_subprocess=False)

    peers = Config.from_file(config_with_profile.filepath).get_option(OPTION_PEERS, scope=profile.name)

    assert 'rekeyed while syncing' in result.output
    assert peers == {PEER_UUID: peer_entry(active=False)}, 'the rotation stands; the peer waits for its rekey'


def test_rekey_refuses_this_profiles_own_code(run_cli_command, config_with_profile):
    """Test that the one code that cannot help is refused before it dormants the roster.

    Every member's `verdi status` prints a code, this profile's own included, and `rekey` sends the user there
    for one — but one's own endpoint is the only member that can teach one nothing.
    """
    init_collab(config_with_profile)

    own = rekey_code(url='http://127.0.0.1:9137')
    result = run_cli_command(cmd_collab.collab_rekey, [own], use_subprocess=False, raises=True)

    assert 'this very profile' in result.output
    assert config_with_profile.get_option(OPTION_PEERS, scope=get_profile().name) == {PEER_UUID: peer_entry()}


def test_rekey_with_a_superseded_code_says_so(run_cli_command, config_with_profile, monkeypatch):
    """Test that a code the issuer itself refuses is reported as superseded, not as waiting for contact.

    A code minted before its issuer rotated again leaves this profile holding a key no member accepts: nobody
    can reach it and it can reach nobody, so telling the user to wait for a contact would be a false promise.
    """
    from http import HTTPStatus

    from aiida.tools.collab.client import CollabClient
    from aiida.tools.collab.protocol import CollabRequestError

    init_collab(config_with_profile)

    def refused(self, entry):
        raise CollabRequestError('responded 401', status=HTTPStatus.UNAUTHORIZED)

    monkeypatch.setattr(CollabClient, 'join', refused)

    result = run_cli_command(cmd_collab.collab_rekey, [rekey_code()], use_subprocess=False, raises=True)

    assert 'superseded by a later rotation' in result.output


def test_rekey_refuses_a_code_of_another_collab(run_cli_command, config_with_profile):
    """Test that a code of a different collab is refused naming both, and changes nothing.

    Rotation keeps the identity of a collab, so a code naming another one can only be somebody else's — and
    adopting its token would leave this profile unable to talk to either side.
    """
    init_collab(config_with_profile)

    result = run_cli_command(
        cmd_collab.collab_rekey, [rekey_code(collab='uuid-of-another-collab')], use_subprocess=False, raises=True
    )

    assert 'uuid-of-another-collab' in result.output
    assert COLLAB_UUID in result.output
    assert config_with_profile.get_option(OPTION_TOKEN, scope=get_profile().name) == TOKEN


def test_rekey_resumes_at_the_cursor_it_had(
    run_cli_command, config_with_profile, stub_join, stub_environment, stub_transfer
):
    """Test that a member that rekeys picks up where it stopped: same cursor, nothing re-transferred.

    Cursors key on the profile UUID and dormancy keeps the entry, so a rotation costs a member nothing beyond
    the code it has to be handed.
    """
    init_collab(config_with_profile)

    cursor = timezone.now()
    state = CollabState.load(get_profile())
    state.cursors[PEER_UUID] = cursor
    state.save()

    run_cli_command(cmd_collab.collab_rekey, [rekey_code()], use_subprocess=False)
    run_cli_command(cmd_collab.collab_pull, ['--force'], use_subprocess=False)

    assert stub_transfer[0] == ('negotiate', cursor, set()), 'nothing already held is asked for again'


def reload_peers(config, profile):
    """Adopt the roster as the endpoint left it on the file, as the next `verdi` process reads it."""
    stored = Config.from_file(config.filepath).get_option(OPTION_PEERS, scope=profile.name)
    config.set_option(OPTION_PEERS, stored, scope=profile.name)


def test_branching_and_reunion(
    run_cli_command, config_with_profile, stub_environment, stub_transfer, stub_signal, monkeypatch
):
    """Test the whole lifecycle from the side of the member that rotates: split, sync within, reunion.

    Two members rekey and one does not. The one that does not is neither contacted nor visible, and syncing
    goes on within the branch. When it rekeys later it is recognized by its UUID — same entry, same cursor —
    and the branches are one collab again, which is what keeping the collab UUID across a rotation buys.
    """
    from unittest.mock import MagicMock

    from aiida.tools.collab.client import CollabClient
    from aiida.tools.collab.endpoint import CollabEndpoint

    init_collab(
        config_with_profile,
        peers={
            PEER_UUID: peer_entry(),
            'uuid-of-bob': peer_entry(url='http://100.64.0.3:9137', nickname='bob'),
        },
    )

    profile = get_profile()
    state = CollabState.load(profile)
    state.cursors['uuid-of-bob'] = timezone.now()
    state.save()

    # Rotating puts both peers out of reach until they come back under the new token.
    run_cli_command(cmd_collab.collab_rotate, use_subprocess=False)
    run_cli_command(cmd_collab.collab_pull, ['--force'], use_subprocess=False, raises=True)

    assert stub_transfer == [], 'a rotation stops every peer from being contacted until one of them rekeys'

    # Alice rekeys and announces herself to this profile: that inbound contact is what brings her back.
    endpoint = CollabEndpoint(profile, backend=MagicMock())
    endpoint.handshake(PEER_UUID, [{'uuid': PEER_UUID, 'url': PEER_URL, 'name': PEER, 'stamp': 1}])
    reload_peers(config_with_profile, profile)

    run_cli_command(cmd_collab.collab_pull, ['--force'], use_subprocess=False)

    assert [call for call in stub_transfer if call[0] == 'negotiate'] == [('negotiate', None, set())], (
        'the branch syncs within itself and never reaches across to the members that stayed behind'
    )

    # Bob rekeys much later, is recognized by his UUID and resumes at the cursor his dormant entry kept.
    stub_transfer.clear()
    monkeypatch.setattr(
        CollabClient, 'check_version_skew', lambda self, local, **kw: make_peer_info(uuid='uuid-of-bob')
    )
    bob = {'uuid': 'uuid-of-bob', 'url': 'http://100.64.0.3:9137', 'name': 'bob', 'stamp': 1}
    endpoint.handshake('uuid-of-bob', [bob])
    reload_peers(config_with_profile, profile)

    run_cli_command(cmd_collab.collab_pull, ['bob', '--force'], use_subprocess=False)

    assert stub_transfer[0] == ('negotiate', state.cursors['uuid-of-bob'], set())


def test_gossip_reactivates_a_third_member(
    run_cli_command, config_with_profile, stub_environment, stub_transfer, monkeypatch
):
    """Test the relay: C rekeys through B, and A learns that C is back from B's gossip alone.

    A never contacts C — nobody polls a dormant peer — so without this path a member that rekeyed through
    somebody else would stay invisible to everyone it did not personally call.
    """
    from aiida.tools.collab.client import CollabClient
    from aiida.tools.collab.protocol import DeltaManifest

    carol_url = 'http://100.64.0.4:9137'

    init_collab(
        config_with_profile,
        peers={PEER_UUID: peer_entry(), 'uuid-of-carol': peer_entry(url=carol_url, nickname='carol', active=False)},
    )

    def negotiate_delta(self, cursor, claim, roster=None):
        # B vouches for C, having just seen it under the current token; it says nothing about anyone else.
        return DeltaManifest(
            manifest=[],
            instant=OFFER_INSTANT,
            roster=[{'uuid': 'uuid-of-carol', 'url': carol_url, 'name': 'carol', 'stamp': 1}],
        )

    monkeypatch.setattr(CollabClient, 'negotiate_delta', negotiate_delta)

    result = run_cli_command(cmd_collab.collab_pull, ['alice', '--force'], use_subprocess=False)

    peers = config_with_profile.get_option(OPTION_PEERS, scope=get_profile().name)

    assert peers['uuid-of-carol']['active'] is True
    assert peers['uuid-of-carol']['nickname'] == 'carol', 'a vouched member is the one that was there, not a new one'
    assert 'carol` is back' in result.output, 'membership is auto-trusted, but never silent'


def test_pull_without_collab(run_cli_command, config_with_profile):
    """Test that a profile which is not part of a collab refuses to pull, as it refuses every other collab command.

    Leaving a collab is switching `collab.enabled` off, so this guard is what stops the sync half of it; the
    endpoint half is the daemon watcher, covered in `tests/tools/collab/test_endpoint.py`.
    """
    result = run_cli_command(cmd_collab.collab_pull, use_subprocess=False, raises=True)

    assert 'not part of a collab' in result.output


def test_log_without_events(run_cli_command, config_with_profile):
    """Test that ``verdi collab log`` reports that nothing was synced yet instead of failing."""
    init_collab(config_with_profile)

    result = run_cli_command(cmd_collab.collab_log, use_subprocess=False)

    assert 'no sync events recorded yet' in result.output


def test_log(run_cli_command, config_with_profile):
    """Test that ``verdi collab log`` shows one row per event, with the peer shown under its nickname."""
    init_collab(config_with_profile)

    profile = get_profile()
    state = CollabState.load(profile)
    state.events.append(
        CollabEvent(time=timezone.now(), direction='push', peer=PEER_UUID, uuids=['uuid-one', 'uuid-two'], size=1024)
    )
    state.save()

    result = run_cli_command(cmd_collab.collab_log, use_subprocess=False)
    row = next(line for line in result.output_lines if 'push' in line)

    assert row.split() == [state.events[0].time.isoformat(timespec='seconds'), 'push', PEER, '2', '1024']


def test_log_without_collab(run_cli_command, config_with_profile):
    """Test that ``verdi collab log`` aborts on a profile that is not part of a collab."""
    result = run_cli_command(cmd_collab.collab_log, use_subprocess=False, raises=True)

    assert 'not part of a collab' in result.output


def test_complete_peer(run_cli_command, config_with_profile):
    """Test that the PEER argument completes to the nicknames of the collab, from the configuration alone."""
    import click

    init_collab(
        config_with_profile,
        peers={
            PEER_UUID: peer_entry(),
            'uuid-of-bob': peer_entry(url='http://100.64.0.3:9137', nickname='bob'),
            'uuid-of-amir': peer_entry(url='http://100.64.0.4:9137', nickname='amir', active=False),
        },
    )

    ctx = click.Context(cmd_collab.collab_pull)
    completions = [item.value for item in cmd_collab.complete_peer(ctx, None, 'a')]

    assert completions == ['alice'], 'a dormant peer is not offered: the command would only refuse it'


def make_peer_info(**overrides):
    from aiida.tools.collab.protocol import PeerInfo

    values = {
        'version': '2.9.0',
        'backend': 'core.sqlite_dos',
        'storage_schema': 'main_0002',
        'archive_schema': 'main_0001',
        'pending_count': 7,
        'accept_push': True,
        'extras_mode': 'local',
        'groups_mode': 'local',
        'uuid': PEER_UUID,
        'collab': COLLAB_UUID,
    }
    values.update(overrides)
    return PeerInfo(**values)


@pytest.fixture
def stub_environment(monkeypatch):
    """Stub the storage backend and the local handshake, neither of which CLI tests should touch for real."""
    from unittest.mock import MagicMock

    from aiida.manage import get_manager
    from aiida.tools.collab import endpoint

    monkeypatch.setattr(get_manager(), 'get_profile_storage', MagicMock())
    monkeypatch.setattr(endpoint, 'local_info', lambda profile, backend: make_peer_info(pending_count=3))


def test_pull_sqlite_running_workers_aborts(run_cli_command, config_with_profile_factory, monkeypatch):
    """Test that ``verdi collab pull`` on SQLite with running workers aborts, naming ``--pause-my-daemon``."""
    from aiida.engine.daemon.client import DaemonClient

    init_collab(config_with_profile_factory(storage_backend='core.sqlite_dos'))
    monkeypatch.setattr(DaemonClient, 'is_daemon_running', property(lambda self: True))

    result = run_cli_command(cmd_collab.collab_pull, use_subprocess=False, raises=True)

    assert 'please pause your daemon' in result.output
    assert '--pause-my-daemon' in result.output


def test_pull_unknown_peer(run_cli_command, config_with_profile, stub_environment):
    """Test that a pull naming an unknown nickname aborts, listing the known ones."""
    init_collab(config_with_profile)

    result = run_cli_command(cmd_collab.collab_pull, ['bob'], use_subprocess=False, raises=True)

    assert 'unknown peer(s) bob' in result.output
    assert PEER in result.output


OFFER_INSTANT = timezone.now()


@pytest.fixture
def stub_transfer(monkeypatch):
    """Stub the negotiation, download and import of a pull, recording circus commands and sync kwargs in order."""
    from aiida.engine.daemon.client import DaemonClient
    from aiida.tools.collab import sync
    from aiida.tools.collab.client import CollabClient
    from aiida.tools.collab.protocol import DeltaManifest, DeltaOffer
    from aiida.tools.collab.sync import DeltaReport

    calls = []

    def negotiate_delta(self, cursor, claim, roster=None):
        calls.append(('negotiate', cursor, set(claim)))
        return DeltaManifest(manifest=['uuid-offered', 'uuid-held'], instant=OFFER_INSTANT)

    def missing_uuids(backend, uuids):
        return [uuid for uuid in uuids if uuid != 'uuid-held']

    def request_delta(self, cursor, claim, want, refresh_want=frozenset()):
        calls.append(('request', set(want)))
        # A later instant than the negotiated one, as served by a peer that recomputed its delta in between:
        # the import must advance the cursor to the negotiated instant, not this one, or in-window nodes are
        # silently never delivered.
        return DeltaOffer(delta='0' * 64, instant=OFFER_INSTANT + timedelta(minutes=1), size=5)

    def download_delta(self, filepath, delta_id):
        filepath.write_bytes(b'delta')
        return len(b'delta')

    def import_delta(filepath, **kwargs):
        calls.append(('import', kwargs['include_deleted'], kwargs['instant']))
        return DeltaReport(uuids=['uuid-offered'], skipped=[], size=5)

    monkeypatch.setattr(DaemonClient, 'call_client', lambda self, command: calls.append(command) or {})
    monkeypatch.setattr(CollabClient, 'check_version_skew', lambda self, local, **kwargs: make_peer_info())
    monkeypatch.setattr(CollabClient, 'negotiate_delta', negotiate_delta)
    monkeypatch.setattr(CollabClient, 'request_delta', request_delta)
    monkeypatch.setattr(CollabClient, 'download_delta', download_delta)
    monkeypatch.setattr(sync, 'missing_uuids', missing_uuids)
    monkeypatch.setattr(sync, 'import_delta', import_delta)

    return calls


def test_pull_pause_my_daemon(
    run_cli_command, config_with_profile_factory, stub_environment, stub_transfer, monkeypatch
):
    """Test that ``--pause-my-daemon`` stops the workers, runs the import and restarts them."""
    from aiida.engine.daemon.client import DaemonClient

    init_collab(config_with_profile_factory(storage_backend='core.sqlite_dos'))
    monkeypatch.setattr(DaemonClient, 'is_daemon_running', property(lambda self: True))

    result = run_cli_command(cmd_collab.collab_pull, ['--pause-my-daemon', '--force'], use_subprocess=False)

    name = f'aiida-{get_profile().name}'
    assert stub_transfer == [
        ('negotiate', None, set()),
        ('request', {'uuid-offered'}),
        {'command': 'stop', 'properties': {'name': name, 'waiting': True}},
        ('import', False, OFFER_INSTANT),
        {'command': 'start', 'properties': {'name': name, 'waiting': True}},
    ]
    assert 'pulled 1 node(s)' in result.output


def test_pull_presents_cursor_and_claim(run_cli_command, config_with_profile, stub_environment, stub_transfer):
    """Test that a pull presents the cursor of the peer and claims imported nodes and tombstones."""
    init_collab(config_with_profile)

    cursor = timezone.now()
    state = CollabState.load(get_profile())
    state.cursors[PEER_UUID] = cursor
    state.tombstones.add('uuid-dead')
    state.events.append(
        CollabEvent(time=timezone.now(), direction='pull', peer='http://other:9137', uuids=['uuid-held'], size=1)
    )
    state.save()

    run_cli_command(cmd_collab.collab_pull, ['--force'], use_subprocess=False)

    assert stub_transfer == [
        ('negotiate', cursor, {'uuid-held', 'uuid-dead'}),
        ('request', {'uuid-offered'}),
        ('import', False, OFFER_INSTANT),
    ]


def test_pull_include_deleted(run_cli_command, config_with_profile, stub_environment, stub_transfer):
    """Test that ``--include-deleted`` rewinds the cursor, drops tombstones from the claim and reaches the import."""
    init_collab(config_with_profile)

    state = CollabState.load(get_profile())
    state.cursors[PEER_UUID] = timezone.now()
    state.tombstones.add('uuid-dead')
    state.events.append(
        CollabEvent(time=timezone.now(), direction='pull', peer=PEER_UUID, uuids=['uuid-held', 'uuid-dead'], size=1)
    )
    state.save()

    run_cli_command(cmd_collab.collab_pull, ['--include-deleted', '--force'], use_subprocess=False)

    assert stub_transfer == [
        ('negotiate', None, {'uuid-held'}),
        ('request', {'uuid-offered'}),
        ('import', True, OFFER_INSTANT),
    ]


def test_pull_prompts_and_decline_leaves_no_trace(
    run_cli_command, config_with_profile, stub_environment, stub_transfer
):
    """Test that a pull prompts with the exact count and size, and that declining writes nothing durable."""
    init_collab(config_with_profile)

    profile = get_profile()
    peers_before = config_with_profile.get_option(OPTION_PEERS, scope=profile.name)

    # A bare Enter, which now declines: the prompt defaults to no, so nothing moves by inattention.
    result = run_cli_command(cmd_collab.collab_pull, use_subprocess=False, user_input='\n')

    assert f'pull 1 node(s) (5 bytes) from {PEER}? [y/N]' in result.output
    assert f'skipped {PEER}' in result.output
    assert [call[0] for call in stub_transfer] == ['negotiate', 'request'], 'nothing may be transferred or imported'
    assert not CollabState.get_filepath(profile).exists(), 'no cursor or event may be recorded'
    assert config_with_profile.get_option(OPTION_PEERS, scope=profile.name) == peers_before


def test_pull_dry_run(run_cli_command, config_with_profile, stub_environment, stub_transfer):
    """Test that ``--dry-run`` reports the pending count per peer after the manifest diff and stops there."""
    init_collab(config_with_profile)

    scope = get_profile().name
    # This machine's endpoint moved, so a sync would announce the new address under a raised stamp.
    config_with_profile.set_option(OPTION_PORT, 9200, scope=scope)
    config_with_profile.store()

    result = run_cli_command(cmd_collab.collab_pull, ['--dry-run'], use_subprocess=False)

    assert f'{PEER}: 1 node(s) to pull' in result.output
    assert [call[0] for call in stub_transfer] == ['negotiate'], 'no archive may be requested, let alone imported'
    assert not CollabState.get_filepath(get_profile()).exists()

    # Read from the file, since that is where a sync writes the stamp and the announcement.
    stored = Config.from_file(config_with_profile.filepath)

    assert stored.get_option(OPTION_STAMP, scope=scope) == 1, 'a report-only run must stamp nothing'
    assert stored.get_option(OPTION_ANNOUNCED, scope=scope) == 'http://127.0.0.1:9137'


def test_pull_verifies_identity(run_cli_command, config_with_profile, stub_environment, stub_transfer, monkeypatch):
    """Test that a URL answering with another profile UUID than the entry's key is refused before anything travels.

    A reprovisioned machine, or a stranger, must not inherit the sync history of the profile that URL used to hold.
    """
    from aiida.tools.collab.client import CollabClient

    init_collab(config_with_profile)
    monkeypatch.setattr(
        CollabClient, 'check_version_skew', lambda self, local, **kwargs: make_peer_info(uuid='uuid-of-somebody-else')
    )

    result = run_cli_command(cmd_collab.collab_pull, ['--force'], use_subprocess=False)

    assert 'is not the one this collab knows' in result.output
    assert stub_transfer == []


def test_pull_refuses_a_foreign_collab(
    run_cli_command, config_with_profile, stub_environment, stub_transfer, monkeypatch
):
    """Test that a peer serving another collab is refused naming both, so a shared token cannot splice two."""
    from aiida.tools.collab.client import CollabClient

    init_collab(config_with_profile)
    monkeypatch.setattr(
        CollabClient, 'check_version_skew', lambda self, local, **kwargs: make_peer_info(collab='another-collab')
    )

    result = run_cli_command(cmd_collab.collab_pull, ['--force'], use_subprocess=False)

    assert 'another-collab' in result.output
    assert COLLAB_UUID in result.output
    assert stub_transfer == []


def test_pull_refuses_a_peer_declaring_another_policy(
    run_cli_command, config_with_profile, stub_environment, stub_transfer, monkeypatch
):
    """Test that a peer declaring a different policy is refused naming both, and that the loop goes on.

    The policy is fixed when the collab is created and travels in the join code, so a mismatch can only mean a
    hand-edited configuration — here staged the way a user would produce it, by editing the stored policy.
    """
    from aiida.tools.collab.client import CollabClient

    init_collab(
        config_with_profile,
        peers={PEER_UUID: peer_entry(), 'uuid-of-bob': peer_entry(url='http://100.64.0.3:9137', nickname='bob')},
    )

    scope = get_profile().name
    config_with_profile.set_option(OPTION_POLICY, {'extras_mode': 'sync', 'groups_mode': 'local'}, scope=scope)
    monkeypatch.setattr(
        CollabClient,
        'check_version_skew',
        lambda self, local, **kwargs: make_peer_info(uuid=PEER_UUID if PEER_URL in self._base_url else 'uuid-of-bob'),
    )

    result = run_cli_command(cmd_collab.collab_pull, ['--force'], use_subprocess=False)

    assert result.output.count('refusing to sync') == 2, 'both peers declare the collab policy, this profile another'
    assert 'extras `local`' in result.output, 'the policy the peers declare'
    assert 'extras `sync`' in result.output, 'the policy this profile holds'
    assert 'fixed when it is created' in result.output
    assert stub_transfer == [], 'nothing may travel with the two sides disagreeing'


def test_pull_refuses_a_changed_policy_and_continues(
    run_cli_command, config_with_profile, stub_environment, stub_transfer, monkeypatch
):
    """Test that one peer's mismatch does not stop the sync with the others, like every other per-peer refusal."""
    from aiida.tools.collab.client import CollabClient

    init_collab(
        config_with_profile,
        peers={PEER_UUID: peer_entry(), 'uuid-of-bob': peer_entry(url='http://100.64.0.3:9137', nickname='bob')},
    )

    def check_version_skew(self, local, **kwargs):
        if PEER_URL in self._base_url:
            return make_peer_info(extras_mode='sync')

        return make_peer_info(uuid='uuid-of-bob')

    monkeypatch.setattr(CollabClient, 'check_version_skew', check_version_skew)

    result = run_cli_command(cmd_collab.collab_pull, ['--force'], use_subprocess=False)

    assert f'refusing to sync with {PEER}' in result.output
    assert 'pulled 1 node(s)' in result.output, 'the peer that agrees is synced with all the same'


def test_pull_records_the_contact_without_pinning_a_policy(
    run_cli_command, config_with_profile, stub_environment, stub_transfer
):
    """Test that a completed sync leaves the peer entry with nothing but its identity and its standing.

    The policy is no longer duplicated onto every link — it is the collab's, held once — so what marks a peer as
    paired is its profile UUID and nothing else.
    """
    init_collab(config_with_profile, peers={PEER_UUID: peer_entry(seen=False)})

    run_cli_command(cmd_collab.collab_pull, ['--force'], use_subprocess=False)

    peers = config_with_profile.get_option(OPTION_PEERS, scope=get_profile().name)

    assert peers == {PEER_UUID: peer_entry(seen=True)}, 'the contact proves the address and pins no policy'


def test_pull_reports_the_refresh_count(
    run_cli_command, config_with_profile, stub_environment, stub_transfer, monkeypatch
):
    """Test that the pull prompt and its dry run name how many nodes' extras an incoming refresh replaces."""
    from aiida.tools.collab import sync
    from aiida.tools.collab.client import CollabClient

    init_collab(config_with_profile, **{OPTION_POLICY: {'extras_mode': 'sync', 'groups_mode': 'local'}})
    monkeypatch.setattr(
        CollabClient, 'check_version_skew', lambda self, local, **kwargs: make_peer_info(extras_mode='sync')
    )
    monkeypatch.setattr(sync, 'refresh_wanted', lambda backend, offer, tombstones: ['uuid-stale'])

    result = run_cli_command(cmd_collab.collab_pull, ['--dry-run', '--force'], use_subprocess=False)

    assert f'{PEER}: 1 node(s) to pull, extras of 1 node(s) to be replaced by theirs' in result.output

    result = run_cli_command(cmd_collab.collab_pull, use_subprocess=False, user_input='n\n')

    assert 'letting their extras replace yours on 1 node(s)' in result.output


def test_pull_keys_the_cursor_by_profile_uuid(
    run_cli_command, config_with_profile, stub_environment, stub_transfer, monkeypatch
):
    """Test that the cursor a pull presents and advances is the one held under the peer's profile UUID."""
    from aiida.tools.collab import sync

    init_collab(config_with_profile)

    imports = []

    def import_delta(filepath, **kwargs):
        imports.append(kwargs['peer'])
        return sync.DeltaReport(uuids=['uuid-offered'], skipped=[], size=5)

    monkeypatch.setattr(sync, 'import_delta', import_delta)

    cursor = timezone.now()
    state = CollabState.load(get_profile())
    state.cursors[PEER_UUID] = cursor
    state.save()

    run_cli_command(cmd_collab.collab_pull, ['--force'], use_subprocess=False)

    assert imports == [PEER_UUID]
    assert stub_transfer[0] == ('negotiate', cursor, set())


def test_pull_gossips_a_move(run_cli_command, config_with_profile, stub_environment, stub_transfer, monkeypatch):
    """Test that a changed address travels: this profile announces its own, and relays a peer's to a third one.

    Nobody can discover an address nobody knows, so a move is repaired by the mover initiating one sync; from
    there the raised stamp is what lets the correction win wherever it arrives.
    """
    from aiida.tools.collab.client import CollabClient
    from aiida.tools.collab.protocol import DeltaManifest

    moved = 'http://100.64.0.9:9137'
    init_collab(
        config_with_profile,
        peers={
            PEER_UUID: peer_entry(),
            'uuid-of-bob': peer_entry(url='http://100.64.0.3:9137', nickname='bob'),
            'uuid-of-carol': peer_entry(url='http://100.64.0.4:9137', nickname='carol'),
        },
    )

    profile = get_profile()

    # This machine moved to another port: its own configuration is corrected, and the next sync spreads it.
    config_with_profile.set_option(OPTION_PORT, 9200, scope=profile.name)
    config_with_profile.store()

    gossiped = []

    def negotiate_delta(self, cursor, claim, roster=None):
        gossiped.append(roster)
        # Alice has bob's own announcement, whose raised stamp is what makes it supersede the address held here,
        # and announces that she has moved too — while still answering at the address this profile reached her at.
        theirs = [
            {'uuid': 'uuid-of-bob', 'url': moved, 'name': 'bob', 'stamp': 2},
            {'uuid': PEER_UUID, 'url': 'http://100.64.0.8:9137', 'name': PEER, 'stamp': 2},
        ]

        return DeltaManifest(manifest=[], instant=OFFER_INSTANT, roster=theirs if PEER_URL in self._base_url else [])

    monkeypatch.setattr(
        CollabClient,
        'check_version_skew',
        lambda self, local, **kwargs: make_peer_info(uuid=PEER_UUID if PEER_URL in self._base_url else 'uuid-of-carol'),
    )
    monkeypatch.setattr(CollabClient, 'negotiate_delta', negotiate_delta)

    result = run_cli_command(cmd_collab.collab_pull, [PEER, 'carol', '--force'], use_subprocess=False)

    peers = config_with_profile.get_option(OPTION_PEERS, scope=profile.name)

    assert gossiped[0][0] == {
        'uuid': profile.uuid,
        'url': 'http://127.0.0.1:9200',
        'name': profile.name,
        'stamp': 2,
    }, 'the mover announces its new address under a raised stamp'
    assert peers['uuid-of-bob'] == peer_entry(url=moved, nickname='bob', stamp=2, seen=False)
    assert peers[PEER_UUID]['url'] == 'http://100.64.0.8:9137'
    assert peers[PEER_UUID]['seen'] is False, 'answering at the old address is no proof of the new one'
    assert f'peer `bob` moved to {moved}' in result.output
    assert {'uuid': 'uuid-of-bob', 'url': moved, 'name': 'bob', 'stamp': 2} in gossiped[1], (
        'the second contact of the same run relays what the first one taught'
    )


def test_pull_flags_a_peer_that_never_answered(run_cli_command, config_with_profile, stub_environment, monkeypatch):
    """Test that a peer which has never answered is called out apart from one that is merely down.

    An address announced at join is only ever proven by a contact — a joiner's endpoint starts with its daemon,
    long after the join finished — so a wrong one surfaces here and nowhere else.
    """
    from aiida.tools.collab.client import CollabClient
    from aiida.tools.collab.protocol import CollabRequestError

    init_collab(config_with_profile, peers={PEER_UUID: peer_entry(seen=False)})

    def offline(self, local, **kwargs):
        raise CollabRequestError('connection refused')

    monkeypatch.setattr(CollabClient, 'check_version_skew', offline)

    result = run_cli_command(cmd_collab.collab_pull, use_subprocess=False)

    assert f'skipping never-answering peer {PEER}' in result.output


def test_pull_does_not_call_a_peer_that_answered_offline(
    run_cli_command, config_with_profile, stub_environment, monkeypatch
):
    """Test that a peer refusing the key is skipped as itself, not reported as unreachable.

    After a rotation this is the routine outcome for every member that has not rekeyed yet: the peer is up and
    answers, and what it answers — with the rekey hint in it — is the whole message.
    """
    from http import HTTPStatus

    from aiida.tools.collab.client import CollabClient
    from aiida.tools.collab.protocol import REKEY_HINT, CollabRequestError

    init_collab(config_with_profile)

    def refused(self, local, **kwargs):
        raise CollabRequestError(f'responded 401: {REKEY_HINT}', status=HTTPStatus.UNAUTHORIZED)

    monkeypatch.setattr(CollabClient, 'check_version_skew', refused)

    result = run_cli_command(cmd_collab.collab_pull, use_subprocess=False)

    assert f'skipping peer {PEER}' in result.output
    assert 'offline' not in result.output
    assert 'verdi collab rekey' in result.output


def test_pull_version_skew(run_cli_command, config_with_profile, stub_environment, stub_transfer, monkeypatch):
    """Test that a peer whose archives this profile cannot read is warned about and skipped, not fatal.

    The middle peer of the three is skewed: an aiida-core that is too new on one machine must not stop the sync
    with everybody else, exactly as an offline or push-refusing peer does not.
    """
    from aiida.tools.collab.client import CollabClient
    from aiida.tools.collab.protocol import VersionSkew

    init_collab(
        config_with_profile,
        peers={
            PEER_UUID: peer_entry(),
            'uuid-of-bob': peer_entry(url='http://100.64.0.3:9137', nickname='bob'),
            'uuid-of-carol': peer_entry(url='http://100.64.0.4:9137', nickname='carol'),
        },
    )

    directions = []

    def check_version_skew(self, local, *, direction):
        directions.append(direction)

        if 'http://100.64.0.3:9137' in self._base_url:
            raise VersionSkew('the peer runs a newer version')

        return make_peer_info(uuid=PEER_UUID if PEER_URL in self._base_url else 'uuid-of-carol')

    monkeypatch.setattr(CollabClient, 'check_version_skew', check_version_skew)

    result = run_cli_command(cmd_collab.collab_pull, ['--force'], use_subprocess=False)

    assert result.output.count('the peer runs a newer version') == 1, 'the skewed peer is warned about once'
    assert 'skipping peer bob' in result.output
    assert result.output.count('pulled 1 node(s)') == 2, 'the other two peers sync all the same'
    assert directions == ['pull'] * 3, 'the pull must be checked in the direction the delta would travel'


def test_push_failed_import_then_retry(run_cli_command, config_with_profile, stub_environment, monkeypatch):
    """Test that a push exports against the receiver's handshake and that a retry reuses the delta and instant."""
    from aiida.tools.collab import sync
    from aiida.tools.collab.client import CollabClient, UploadReport
    from aiida.tools.collab.protocol import CollabRequestError, ManifestDiff, PushHandshake
    from aiida.tools.collab.sync import Delta, DeltaExport

    init_collab(config_with_profile)

    computes = []
    exports = []
    handshakes = []
    imports = []
    instant = timezone.now()
    receiver_cursor = timezone.now()
    delta = Delta(uuid_by_pk={1: 'uuid-one', 2: 'uuid-held'}, links=[], instant=instant)

    def push_handshake(self, requester, roster=None):
        handshakes.append(requester)
        return PushHandshake(busy=False, cursor=receiver_cursor, claim=['uuid-claimed'])

    def compute_delta(*, state, backend, cursor, claim=frozenset()):
        computes.append((cursor, set(claim)))
        return delta

    def export_delta(filepath, *, delta, backend, want=None):
        filepath.write_bytes(b'delta')
        exports.append(set(want))
        return DeltaExport(filepath=filepath, uuids=sorted(want), instant=delta.instant)

    def trigger_import_failing(self, sha256, *, peer, instant, refresh=None):
        raise CollabRequestError('the peer failed to import')

    monkeypatch.setattr(sync, 'compute_delta', compute_delta)
    monkeypatch.setattr(sync, 'export_delta', export_delta)
    monkeypatch.setattr(CollabClient, 'check_version_skew', lambda self, local, **kwargs: make_peer_info())
    monkeypatch.setattr(CollabClient, 'push_handshake', push_handshake)
    monkeypatch.setattr(
        CollabClient,
        'diff_manifest',
        lambda self, uuids, refresh=None: ManifestDiff(missing=['uuid-one'], refresh=[]),
    )
    monkeypatch.setattr(
        CollabClient, 'upload_delta', lambda self, filepath: UploadReport(sha256='0' * 64, sent=5, staged=5)
    )
    monkeypatch.setattr(CollabClient, 'trigger_import', trigger_import_failing)

    result = run_cli_command(cmd_collab.collab_push, ['--force'], use_subprocess=False, raises=True)

    assert 'files transferred, provenance not landed' in result.output
    assert result.exit_code != 0
    assert computes == [(receiver_cursor, {'uuid-claimed'})], 'the delta must be bounded by the handshake'
    assert exports == [{'uuid-one'}], 'only what the receiver reported missing may be exported and uploaded'

    profile = get_profile()
    state = CollabState.load(profile)
    assert state.events == []

    # The retry has to reuse the exported delta: the same bytes are what the peer already staged, and the
    # original instant is what describes them.
    def trigger_import(self, sha256, *, peer, instant, refresh=None):
        imports.append((peer, instant))
        return {'uuids': ['uuid-one']}

    monkeypatch.setattr(
        CollabClient, 'upload_delta', lambda self, filepath: UploadReport(sha256='0' * 64, sent=0, staged=5)
    )
    monkeypatch.setattr(CollabClient, 'trigger_import', trigger_import)

    # Not forced, because the retry reaches the confirmation prompt without having negotiated anything: whatever
    # the prompt reports has to be sound on a path that computed none of it.
    result = run_cli_command(cmd_collab.collab_push, use_subprocess=False, user_input='y\n')

    assert 'push 1 node(s) (5 bytes) to alice?' in result.output
    assert len(exports) == 1, 'the retry should not export a new delta'
    assert 'retrying the delta of the previous failed push' in result.output
    assert 'transferred 0 bytes' in result.output

    identity = profile.uuid
    assert handshakes == [identity, identity], 'the pusher identifies itself with its profile UUID'
    assert imports == [(identity, instant)]

    state = CollabState.load(profile)
    assert state.cursors == {}, 'the sender keeps no send-state; what the peer holds is tracked on its side'
    assert [(event.direction, event.peer, event.uuids) for event in state.events] == [
        ('push', PEER_UUID, ['uuid-one'])
    ], 'the event keys the peer by its profile UUID'


def test_push_prompts_and_decline_drops_cut(run_cli_command, config_with_profile, stub_environment, monkeypatch):
    """Test that a push prompts with the exact count and size, and that declining drops the cut archive."""
    from aiida.tools.collab import sync
    from aiida.tools.collab.client import CollabClient
    from aiida.tools.collab.protocol import ManifestDiff, PushHandshake
    from aiida.tools.collab.sync import Delta, DeltaExport

    init_collab(config_with_profile)

    def export_delta(filepath, *, delta, backend, want=None):
        filepath.write_bytes(b'delta')
        return DeltaExport(filepath=filepath, uuids=['uuid-one'], instant=timezone.now())

    def untouched(*args, **kwargs):
        raise AssertionError('a declined prompt must stop the push before any upload')

    monkeypatch.setattr(
        sync, 'compute_delta', lambda **kwargs: Delta(uuid_by_pk={1: 'uuid-one'}, links=[], instant=timezone.now())
    )
    monkeypatch.setattr(sync, 'export_delta', export_delta)
    monkeypatch.setattr(CollabClient, 'check_version_skew', lambda self, local, **kwargs: make_peer_info())
    monkeypatch.setattr(
        CollabClient,
        'push_handshake',
        lambda self, requester, roster=None: PushHandshake(busy=False, cursor=None, claim=[]),
    )
    monkeypatch.setattr(
        CollabClient,
        'diff_manifest',
        lambda self, uuids, refresh=None: ManifestDiff(missing=uuids, refresh=[]),
    )
    monkeypatch.setattr(CollabClient, 'upload_delta', untouched)

    # A bare Enter, which now declines: the prompt defaults to no in both directions.
    result = run_cli_command(cmd_collab.collab_push, use_subprocess=False, user_input='\n')

    assert f'push 1 node(s) (5 bytes) to {PEER}? [y/N]' in result.output
    assert f'skipped {PEER}' in result.output
    assert not CollabState.get_filepath(get_profile()).exists(), 'no event may be recorded'

    workdir = CollabState.get_workdir(get_profile())
    assert not any(workdir.glob('push-*')), 'the cut archive and its meta file should be dropped'


def test_push_dry_run(run_cli_command, config_with_profile, stub_environment, monkeypatch):
    """Test that ``--dry-run`` reports the pending count after the manifest diff, exporting nothing."""
    from aiida.tools.collab import sync
    from aiida.tools.collab.client import CollabClient
    from aiida.tools.collab.protocol import ManifestDiff, PushHandshake
    from aiida.tools.collab.sync import Delta

    init_collab(config_with_profile)

    def untouched(*args, **kwargs):
        raise AssertionError('a dry run must not export or upload anything')

    monkeypatch.setattr(
        sync, 'compute_delta', lambda **kwargs: Delta(uuid_by_pk={1: 'uuid-one'}, links=[], instant=timezone.now())
    )
    monkeypatch.setattr(sync, 'export_delta', untouched)
    monkeypatch.setattr(CollabClient, 'check_version_skew', lambda self, local, **kwargs: make_peer_info())
    monkeypatch.setattr(
        CollabClient,
        'push_handshake',
        lambda self, requester, roster=None: PushHandshake(busy=False, cursor=None, claim=[]),
    )
    monkeypatch.setattr(
        CollabClient,
        'diff_manifest',
        lambda self, uuids, refresh=None: ManifestDiff(missing=uuids, refresh=[]),
    )
    monkeypatch.setattr(CollabClient, 'upload_delta', untouched)

    result = run_cli_command(cmd_collab.collab_push, ['--dry-run'], use_subprocess=False)

    assert f'{PEER}: 1 node(s) to push' in result.output


def test_push_reports_the_refresh_count(run_cli_command, config_with_profile, stub_environment, monkeypatch):
    """Test that the push prompt and its dry run name how many nodes' extras the receiver asked for."""
    from aiida.tools.collab import sync
    from aiida.tools.collab.client import CollabClient
    from aiida.tools.collab.protocol import ExtrasSnapshot, ManifestDiff, PushHandshake
    from aiida.tools.collab.sync import Delta, DeltaExport

    init_collab(config_with_profile, **{OPTION_POLICY: {'extras_mode': 'sync', 'groups_mode': 'local'}})

    def export_delta(filepath, *, delta, backend, want=None):
        filepath.write_bytes(b'delta')
        return DeltaExport(filepath=filepath, uuids=['uuid-one'], instant=timezone.now())

    monkeypatch.setattr(
        sync, 'compute_delta', lambda **kwargs: Delta(uuid_by_pk={1: 'uuid-one'}, links=[], instant=timezone.now())
    )
    monkeypatch.setattr(sync, 'export_delta', export_delta)
    monkeypatch.setattr(sync, 'refresh_offer', lambda **kwargs: {'uuid-stale': timezone.now()})
    monkeypatch.setattr(
        sync,
        'refresh_snapshots',
        lambda backend, uuids: [ExtrasSnapshot(uuid=uuid, mtime=timezone.now(), extras={}) for uuid in uuids],
    )
    monkeypatch.setattr(
        CollabClient, 'check_version_skew', lambda self, local, **kwargs: make_peer_info(extras_mode='sync')
    )
    monkeypatch.setattr(
        CollabClient,
        'push_handshake',
        lambda self, requester, roster=None: PushHandshake(busy=False, cursor=None, claim=[]),
    )
    monkeypatch.setattr(
        CollabClient,
        'diff_manifest',
        lambda self, uuids, refresh=None: ManifestDiff(missing=uuids, refresh=['uuid-stale']),
    )

    result = run_cli_command(cmd_collab.collab_push, ['--dry-run', '--force'], use_subprocess=False)

    assert f'{PEER}: 1 node(s) to push, extras of 1 node(s) to be replaced by yours' in result.output

    result = run_cli_command(cmd_collab.collab_push, use_subprocess=False, user_input='n\n')

    assert 'replacing their extras with yours on 1 node(s)' in result.output


def test_push_offers_no_refresh_under_local(run_cli_command, config_with_profile, stub_environment, monkeypatch):
    """Test that a collab that keeps extras local exchanges no refresh metadata, in the push direction either."""
    from aiida.tools.collab import sync
    from aiida.tools.collab.client import CollabClient
    from aiida.tools.collab.protocol import ManifestDiff, PushHandshake
    from aiida.tools.collab.sync import Delta

    init_collab(config_with_profile)

    offered = []

    def diff_manifest(self, uuids, refresh=None):
        offered.append(refresh)
        return ManifestDiff(missing=[], refresh=[])

    monkeypatch.setattr(
        sync, 'compute_delta', lambda **kwargs: Delta(uuid_by_pk={1: 'uuid-one'}, links=[], instant=timezone.now())
    )
    monkeypatch.setattr(sync, 'refresh_offer', lambda **kwargs: {'uuid-edited': timezone.now()})
    monkeypatch.setattr(CollabClient, 'check_version_skew', lambda self, local, **kwargs: make_peer_info())
    monkeypatch.setattr(
        CollabClient,
        'push_handshake',
        lambda self, requester, roster=None: PushHandshake(busy=False, cursor=timezone.now(), claim=[]),
    )
    monkeypatch.setattr(CollabClient, 'diff_manifest', diff_manifest)

    run_cli_command(cmd_collab.collab_push, ['--dry-run'], use_subprocess=False)

    assert offered == [{}], 'nothing about extras may be offered to a peer of a collab that keeps them local'


def test_push_refused_delta_drops_stash(run_cli_command, config_with_profile, stub_environment, monkeypatch):
    """Test that a 422-refused push drops its retry stash, so the next push negotiates afresh.

    Retrying the same bytes would abort forever: the peer deleted a node the delta's boundary links to, and only
    a fresh negotiation, whose diff includes the hole, can deliver it.
    """
    from http import HTTPStatus

    from aiida.tools.collab import sync
    from aiida.tools.collab.client import CollabClient, UploadReport
    from aiida.tools.collab.protocol import CollabRequestError, ManifestDiff, PushHandshake
    from aiida.tools.collab.sync import Delta, DeltaExport

    init_collab(config_with_profile)

    instant = timezone.now()

    def export_delta(filepath, *, delta, backend, want=None):
        filepath.write_bytes(b'delta')
        return DeltaExport(filepath=filepath, uuids=['uuid-one'], instant=instant)

    def trigger_import_refused(self, sha256, *, peer, instant, refresh=None):
        raise CollabRequestError('it links to node gone-uuid', status=HTTPStatus.UNPROCESSABLE_ENTITY)

    monkeypatch.setattr(
        sync, 'compute_delta', lambda **kwargs: Delta(uuid_by_pk={1: 'uuid-one'}, links=[], instant=instant)
    )
    monkeypatch.setattr(sync, 'export_delta', export_delta)
    monkeypatch.setattr(CollabClient, 'check_version_skew', lambda self, local, **kwargs: make_peer_info())
    monkeypatch.setattr(
        CollabClient,
        'push_handshake',
        lambda self, requester, roster=None: PushHandshake(busy=False, cursor=None, claim=[]),
    )
    monkeypatch.setattr(
        CollabClient,
        'diff_manifest',
        lambda self, uuids, refresh=None: ManifestDiff(missing=uuids, refresh=[]),
    )
    monkeypatch.setattr(
        CollabClient, 'upload_delta', lambda self, filepath: UploadReport(sha256='0' * 64, sent=5, staged=5)
    )
    monkeypatch.setattr(CollabClient, 'trigger_import', trigger_import_refused)

    result = run_cli_command(cmd_collab.collab_push, ['--force'], use_subprocess=False, raises=True)

    assert 'negotiates afresh' in result.output

    workdir = CollabState.get_workdir(get_profile())
    assert not any(workdir.glob('push-*')), 'the stashed delta should be dropped'


def test_push_busy_peer(run_cli_command, config_with_profile, stub_environment, monkeypatch):
    """Test that a push against a busy peer warns and skips it, before exporting or uploading anything."""
    from aiida.tools.collab import sync
    from aiida.tools.collab.client import CollabClient
    from aiida.tools.collab.protocol import PushHandshake

    init_collab(config_with_profile)

    def untouched(*args, **kwargs):
        raise AssertionError('a busy handshake must stop the push before any export or upload')

    monkeypatch.setattr(CollabClient, 'check_version_skew', lambda self, local, **kwargs: make_peer_info())
    monkeypatch.setattr(
        CollabClient,
        'push_handshake',
        lambda self, requester, roster=None: PushHandshake(busy=True, cursor=None, claim=[]),
    )
    monkeypatch.setattr(sync, 'compute_delta', untouched)
    monkeypatch.setattr(sync, 'export_delta', untouched)
    monkeypatch.setattr(CollabClient, 'upload_delta', untouched)

    result = run_cli_command(cmd_collab.collab_push, use_subprocess=False)

    assert 'busy right now' in result.output


def test_push_offline_peer_warns_and_continues(run_cli_command, config_with_profile, stub_environment, monkeypatch):
    """Test that an offline peer is warned about and skipped by a push, not a failure."""
    from aiida.tools.collab.client import CollabClient
    from aiida.tools.collab.protocol import CollabRequestError

    init_collab(config_with_profile)

    def offline(self, local, **kwargs):
        raise CollabRequestError('connection refused')

    monkeypatch.setattr(CollabClient, 'check_version_skew', offline)

    result = run_cli_command(cmd_collab.collab_push, use_subprocess=False)

    assert 'skipping offline peer' in result.output


def test_push_dying_peer_warns_and_continues(run_cli_command, config_with_profile, stub_environment, monkeypatch):
    """Test that a peer dying after the version check — handshake, diff or upload — is skipped like an offline one."""
    from aiida.tools.collab.client import CollabClient
    from aiida.tools.collab.protocol import CollabRequestError

    init_collab(config_with_profile)

    def dying(self, requester, roster=None):
        raise CollabRequestError('connection reset by peer')

    monkeypatch.setattr(CollabClient, 'check_version_skew', lambda self, local, **kwargs: make_peer_info())
    monkeypatch.setattr(CollabClient, 'push_handshake', dying)

    result = run_cli_command(cmd_collab.collab_push, use_subprocess=False)

    assert f'skipping peer {PEER}: connection reset by peer' in result.output


def test_push_refusing_peer_warns_and_continues(run_cli_command, config_with_profile, stub_environment, monkeypatch):
    """Test that a peer that does not accept pushes is warned about and skipped, not a failure."""
    from aiida.tools.collab import sync
    from aiida.tools.collab.client import CollabClient

    init_collab(config_with_profile)

    def untouched(*args, **kwargs):
        raise AssertionError('a refusing peer must stop the push before any handshake or export')

    monkeypatch.setattr(
        CollabClient, 'check_version_skew', lambda self, local, **kwargs: make_peer_info(accept_push=False)
    )
    monkeypatch.setattr(CollabClient, 'push_handshake', untouched)
    monkeypatch.setattr(sync, 'compute_delta', untouched)

    result = run_cli_command(cmd_collab.collab_push, use_subprocess=False)

    assert 'does not accept pushes' in result.output


def test_pull_push_end_to_end(run_cli_command, aiida_profile_clean, monkeypatch, tmp_path):
    """Test push and pull against two real peers over loopback.

    Provenance produced on C and pulled by B reaches A through a pull from B alone (chain convergence), after
    which the pull from C in the same round transfers nothing, because A claims what B just delivered.
    """
    import dataclasses
    import threading
    import uuid as uuid_module

    from aiida import orm
    from aiida.common.links import LinkType
    from aiida.manage import get_manager
    from aiida.manage.configuration import get_config
    from aiida.manage.configuration.profile import Profile
    from aiida.storage.sqlite_dos.backend import SqliteDosStorage
    from aiida.tools.collab.client import CollabClient
    from aiida.tools.collab.endpoint import local_info
    from aiida.tools.collab.protocol import (
        DeltaManifest,
        DeltaOffer,
        JoinResponse,
        ManifestDiff,
        PushHandshake,
        delta_id,
    )
    from aiida.tools.collab.server import CollabServer
    from aiida.tools.collab.sync import (
        compute_delta,
        export_delta,
        import_delta,
        missing_uuids,
        refresh_offer,
        refresh_snapshots,
        refresh_wanted,
    )

    # The whole loopback collab syncs extras, so that the wire carries the refresh negotiation as well.
    extras_mode = 'sync'

    def seal_calculation(backend, inputs=None, heavy=False):
        import hashlib

        inputs = inputs or orm.Int(1, backend=backend).store()
        calculation = orm.CalcJobNode(backend=backend)
        calculation.base.links.add_incoming(inputs, link_type=LinkType.INPUT_CALC, link_label='term')

        if heavy:
            # Incompressible ballast, so that archive sizes are dominated by which nodes travel.
            blob = b''.join(hashlib.sha256(str(index).encode()).digest() for index in range(3200))
            calculation.base.repository.put_object_from_bytes(blob, 'aiida.in')

        calculation.store()
        outputs = orm.Int(2, backend=backend)
        outputs.base.links.add_incoming(calculation, link_type=LinkType.CREATE, link_label='result')
        outputs.store()
        calculation.seal()

        return outputs

    def node_count(backend):
        return orm.QueryBuilder(backend=backend).append(orm.Node).count()

    profile = get_profile()
    backend_a = get_manager().get_profile_storage()
    token = 'end-to-end-token'

    # The peers mirror this profile's schema versions, so the handshake passes regardless of backend type.
    local = dataclasses.replace(local_info(profile, backend_a), pending_count=0)

    # Keep the collab state and transfer files of this test out of the session configuration directory.
    monkeypatch.setattr(CollabState, 'get_filepath', staticmethod(lambda profile: tmp_path / 'state.json'))
    monkeypatch.setattr(CollabState, 'get_workdir', staticmethod(lambda profile: tmp_path / 'work'))

    servers, threads, backends = [], [], []

    def serve_peer(name):
        """Create a real file-backed peer profile served over loopback, wired to the real sync core.

        A real storage is needed because the import runs in the server's handler thread, which an in-memory
        ``SqliteTempBackend`` cannot serve.
        """
        peer_uuid = uuid_module.uuid4().hex
        profile_peer = Profile(
            name,
            {
                'default_user_email': f'{name}@localhost',
                'PROFILE_UUID': peer_uuid,
                'storage': {'backend': 'core.sqlite_dos', 'config': {'filepath': str(tmp_path / f'{name}-storage')}},
                'process_control': {'backend': None, 'config': {}},
                'test_profile': True,
            },
        )
        SqliteDosStorage.initialise(profile_peer)
        backend = SqliteDosStorage(profile_peer)
        backends.append(backend)
        orm.User(email=f'{name}@localhost', backend=backend).store()

        state_path = tmp_path / f'{name}-state.json'
        workdir = tmp_path / f'{name}-work'
        workdir.mkdir()
        computed = {}
        deltas = {}

        def negotiate_delta(cursor, claim, roster=None):
            state = CollabState.read(state_path)
            delta = compute_delta(state=state, backend=backend, cursor=cursor, claim=claim)
            computed[delta_id(cursor, claim)] = delta
            return DeltaManifest(
                manifest=delta.uuids,
                instant=delta.instant,
                refresh=refresh_offer(state=state, backend=backend, cursor=cursor),
            )

        def request_delta(cursor, claim, want, refresh_want):
            delta = computed[delta_id(cursor, claim)]
            key = delta_id(cursor, claim, want)
            deltas[key] = export_delta(workdir / f'{key}.aiida', delta=delta, backend=backend, want=want)
            return DeltaOffer(
                delta=key,
                instant=deltas[key].instant,
                size=deltas[key].filepath.stat().st_size,
                refresh=refresh_snapshots(backend, sorted(refresh_want)),
            )

        def handshake(requester, roster=None):
            state = CollabState.read(state_path)
            cursor = state.cursors.get(requester)
            claim = sorted(state.imported_uuids_since(cursor) | state.tombstones)
            return PushHandshake(busy=False, cursor=cursor, claim=claim)

        def diff_manifest(uuids, refresh):
            state = CollabState.read(state_path)
            return ManifestDiff(
                missing=missing_uuids(backend, uuids),
                refresh=refresh_wanted(backend, refresh, state.tombstones),
            )

        def import_staged(filepath, peer, instant, refresh):
            report = import_delta(
                filepath,
                state=CollabState.read(state_path),
                backend=backend,
                extras_mode=extras_mode,
                peer=peer,
                instant=instant,
                refresh=refresh,
            )
            return dataclasses.asdict(report)

        server = CollabServer(
            '127.0.0.1',
            0,
            token=lambda: token,
            collab=COLLAB_UUID,
            staging_dir=tmp_path / f'{name}-staging',
            info=lambda cursor: dataclasses.replace(
                local, uuid=peer_uuid, collab=COLLAB_UUID, extras_mode=extras_mode, accept_push=True
            ),
            join=lambda entry: JoinResponse(collab=COLLAB_UUID, roster=[entry]),
            retired=lambda peer: None,
            negotiate_delta=negotiate_delta,
            request_delta=request_delta,
            resolve_delta=lambda key: deltas[key].filepath if key in deltas else None,
            diff_manifest=diff_manifest,
            handshake=handshake,
            import_staged=import_staged,
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        servers.append(server)
        threads.append(thread)

        return backend, state_path, f'http://127.0.0.1:{server.server_address[1]}', peer_uuid

    backend_b, state_path_b, url_b, uuid_b = serve_peer('peer-b')
    backend_c, state_path_c, url_c, uuid_c = serve_peer('peer-c')

    # Written to the configuration file rather than into the loaded profile: the commands re-read the file before
    # writing it, so that they do not revert what a daemon endpoint merged into it while they ran.
    config = get_config()
    options = {
        'collab.enabled': True,
        # Both peers start unproven, as a roster adopted at join leaves them: only a contact proves an address.
        'collab.peers': {
            uuid_b: peer_entry(url=url_b, nickname='peer-b', seen=False),
            uuid_c: peer_entry(url=url_c, nickname='peer-c', seen=False),
        },
        'collab.token': token,
        'collab.uuid': COLLAB_UUID,
        'collab.bind': '127.0.0.1',
        'collab.announced': 'http://127.0.0.1:9137',
        'collab.policy': {'extras_mode': extras_mode, 'groups_mode': 'local'},
    }

    for option, value in options.items():
        config.set_option(option, value, scope=profile.name)

    config.store()

    try:
        # A pushes its own work to B.
        output_a = seal_calculation(backend_a, heavy=True)
        result = run_cli_command(cmd_collab.collab_push, ['peer-b', '--force'], use_subprocess=False)

        assert 'pushed 3 node(s)' in result.output
        assert node_count(backend_b) == node_count(backend_a) == 3

        # C produces work of its own, which B pulls: B now relays provenance it did not produce.
        seal_calculation(backend_c)

        with CollabClient(url_c, token, collab=COLLAB_UUID) as client:
            manifest = client.negotiate_delta(None, frozenset())
            offer = client.request_delta(None, frozenset(), frozenset(missing_uuids(backend_b, manifest.manifest)))
            filepath = tmp_path / 'b-pulls-c.aiida'
            client.download_delta(filepath, offer.delta)

        import_delta(
            filepath,
            state=CollabState.read(state_path_b),
            backend=backend_b,
            extras_mode=extras_mode,
            peer=uuid_c,
            instant=offer.instant,
        )

        assert node_count(backend_b) == 6

        # A pulls from both peers: B's delta carries C's nodes, after which A claims them and C owes nothing.
        result = run_cli_command(cmd_collab.collab_pull, ['--force'], use_subprocess=False)

        assert node_count(backend_a) == 6

        line_b = next(line for line in result.output_lines if 'peer-b' in line and 'pulled' in line)
        line_c = next(line for line in result.output_lines if 'peer-c' in line and 'pulled' in line)

        assert 'pulled 3 node(s)' in line_b, 'B relays what it pulled from C; what A pushed is not re-delivered'
        assert 'pulled 0 node(s)' in line_c, 'everything C offers is already held'

        state_a = CollabState.read(tmp_path / 'state.json')
        assert set(state_a.cursors) == {uuid_b, uuid_c}, 'cursors key by the profile UUID the peers revealed'
        assert [event.direction for event in state_a.events] == ['push', 'pull', 'pull']

        # The pulls proved both addresses, which is the only thing that ever clears the never-answered flag.
        assert all(entry['seen'] for entry in config.get_option('collab.peers', scope=profile.name).values())

        # The push advanced B's cursor for A, under A's profile UUID.
        state_b = CollabState.read(state_path_b)
        assert profile.uuid in state_b.cursors

        # A restarts its calculation, reusing the heavy one's output: the second push transfers only the new
        # nodes, so its bytes shrink although the closure still covers the heavy ancestor.
        seal_calculation(backend_a, inputs=output_a)
        result = run_cli_command(cmd_collab.collab_push, ['peer-b', '--force'], use_subprocess=False)

        assert 'pushed 2 node(s)' in result.output
        assert node_count(backend_b) == 8

        pushes = [event.size for event in CollabState.read(tmp_path / 'state.json').events if event.direction == 'push']
        assert pushes[1] < pushes[0], 'the second sync of the restart chain must transfer fewer bytes'

        # B edits an extra of a node both hold: under the `sync` policy the next pull carries it over, without any
        # node travelling with it.
        shared = orm.QueryBuilder(backend=backend_b).append(orm.Node, filters={'uuid': output_a.uuid}).one()[0]
        shared.base.extras.set('reviewed', 'by b')

        result = run_cli_command(cmd_collab.collab_pull, ['peer-b', '--force'], use_subprocess=False)

        assert 'pulled 0 node(s)' in result.output
        assert 'refreshed the extras of 1 node(s)' in result.output
        assert orm.load_node(output_a.uuid).base.extras.get('reviewed') == 'by b'

        # And back the other way: an edit here reaches B by a push that carries no node at all, replacing B's whole
        # extras dict — which is why the key B set survives only because this side holds it too.
        orm.load_node(output_a.uuid).base.extras.set('checked', 'by a')

        result = run_cli_command(cmd_collab.collab_push, ['peer-b', '--force'], use_subprocess=False)

        assert 'pushed 0 node(s)' in result.output
        assert 'refreshed the extras of 1 node(s)' in result.output
        assert shared.base.extras.all == {'reviewed': 'by b', 'checked': 'by a'}
    finally:
        for option in options:
            config.unset_option(option, scope=profile.name)

        config.store()

        for server in servers:
            server.shutdown()
            server.server_close()
        for thread in threads:
            thread.join()
        for backend in backends:
            backend.close()


def test_push_nothing_is_still_logged(run_cli_command, config_with_profile, stub_environment, monkeypatch):
    """Test that a push finding the peer up to date records an event, so the log says when it last ran."""
    from aiida.tools.collab import sync
    from aiida.tools.collab.client import CollabClient
    from aiida.tools.collab.protocol import ManifestDiff, PushHandshake
    from aiida.tools.collab.sync import Delta, DeltaExport

    init_collab(config_with_profile)

    def export_delta(filepath, *, delta, backend, want=None):
        filepath.write_bytes(b'')
        return DeltaExport(filepath=filepath, uuids=[], instant=timezone.now())

    monkeypatch.setattr(sync, 'compute_delta', lambda **kwargs: Delta(uuid_by_pk={}, links=[], instant=timezone.now()))
    monkeypatch.setattr(sync, 'export_delta', export_delta)
    monkeypatch.setattr(
        CollabClient, 'check_version_skew', lambda self, local, **kwargs: make_peer_info(uuid='uuid-of-alice')
    )
    gossiped = []

    def push_handshake(self, requester, roster=None):
        gossiped.append(roster)
        return PushHandshake(busy=False, cursor=None, claim=[])

    monkeypatch.setattr(CollabClient, 'push_handshake', push_handshake)
    monkeypatch.setattr(
        CollabClient,
        'diff_manifest',
        lambda self, uuids, refresh=None: ManifestDiff(missing=[], refresh=[]),
    )

    result = run_cli_command(cmd_collab.collab_push, ['--force'], use_subprocess=False)

    assert f'{PEER} is up to date' in result.output
    assert gossiped[0][0] == {
        'uuid': get_profile().uuid,
        'url': 'http://127.0.0.1:9137',
        'name': get_profile().name,
        'stamp': 1,
    }, 'a push announces this profile as a pull does, so a move heals whichever way the sync goes'

    events = CollabState.load(get_profile()).events

    assert [(event.direction, event.peer, event.uuids, event.size) for event in events] == [
        ('push', 'uuid-of-alice', [], 0)
    ]

    result = run_cli_command(cmd_collab.collab_log, use_subprocess=False)
    row = next(line for line in result.output_lines if 'push' in line)

    assert row.split()[1:] == ['push', PEER, '0', '0'], 'the empty push should show under the nickname'


def test_push_version_skew(run_cli_command, config_with_profile, stub_environment, monkeypatch):
    """Test that a peer that cannot read this profile's archives is warned about, skipped, and the loop goes on.

    Nothing is uploaded to the skewed peer — the check precedes the handshake — and the peer after it in the list
    is pushed to as if the skewed one were merely offline.
    """
    from aiida.tools.collab import sync
    from aiida.tools.collab.client import CollabClient
    from aiida.tools.collab.protocol import ManifestDiff, PushHandshake, VersionSkew
    from aiida.tools.collab.sync import Delta

    init_collab(
        config_with_profile,
        peers={
            PEER_UUID: peer_entry(),
            'uuid-of-bob': peer_entry(url='http://100.64.0.3:9137', nickname='bob'),
            'uuid-of-carol': peer_entry(url='http://100.64.0.4:9137', nickname='carol'),
        },
    )

    directions = []
    handshakes = []

    def check_version_skew(self, local, *, direction):
        directions.append(direction)

        if 'http://100.64.0.3:9137' in self._base_url:
            raise VersionSkew('the peer reads an older archive format')

        return make_peer_info(uuid=PEER_UUID if PEER_URL in self._base_url else 'uuid-of-carol')

    def push_handshake(self, requester, roster=None):
        handshakes.append(self._base_url)
        return PushHandshake(busy=False, cursor=None, claim=[])

    monkeypatch.setattr(CollabClient, 'check_version_skew', check_version_skew)
    monkeypatch.setattr(CollabClient, 'push_handshake', push_handshake)
    monkeypatch.setattr(CollabClient, 'diff_manifest', lambda self, uuids, refresh=None: ManifestDiff([], []))
    monkeypatch.setattr(sync, 'compute_delta', lambda **kwargs: Delta(uuid_by_pk={}, links=[], instant=timezone.now()))

    result = run_cli_command(cmd_collab.collab_push, ['--force'], use_subprocess=False)

    assert result.output.count('skipping peer bob: the peer reads an older archive format') == 1
    assert f'{PEER} is up to date' in result.output, 'the peer before the skewed one is pushed to'
    assert 'carol is up to date' in result.output, 'and so is the peer after it'
    assert handshakes == [PEER_URL, 'http://100.64.0.4:9137'], 'nothing may be negotiated with the skewed peer'
    assert directions == ['push'] * 3, 'the push must be checked in the direction the delta would travel'
