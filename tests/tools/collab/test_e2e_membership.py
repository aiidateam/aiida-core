###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Who is in the collab, over the real wire: joining, moving, rotating, rekeying and being refused.

The three identities of the design are what these tests pull on. The **token** is the current key, and rotating
it is how a collab excludes a member. The **profile UUID** is the permanent identity of a member, which is why a
member survives changing its address and can be recognized after a rotation. The **collab UUID** is the permanent
identity of the collab, which is what keeps a token shared too widely from splicing two collabs into one.
"""

import pytest

from tests.tools.collab.conftest import move


@pytest.fixture
def joining(monkeypatch):
    """Let ``verdi collab init --join`` adopt a profile the harness already built.

    Joining creates a fresh profile through ``verdi presto``, which has its own tests and would dominate the
    runtime here. Everything the collab owns — the code, the announcement, the roster the issuer answers with and
    the options that are written — runs for real.
    """
    from aiida.cmdline.commands import cmd_collab

    pending = []

    def create_profile(ctx, profile_name, non_interactive):
        from aiida.manage.configuration import get_profile, load_profile

        member = pending.pop(0)
        load_profile(member.profile.name, allow_switch=True)

        return get_profile()

    monkeypatch.setattr(cmd_collab, 'create_profile', create_profile)

    return pending


def code_of(member):
    """Return the join code a member hands out, as ``verdi collab link`` mints it."""
    from aiida.manage.configuration.config import Config
    from aiida.tools.collab.config import join_code

    return join_code(Config.from_file(member.config.filepath), member.profile)


def test_the_printed_link_is_what_a_newcomer_joins_with(collab, joining):
    """Test that a second profile joins on exactly what ``verdi collab link`` wrote to the screen.

    The command exists because the code carries the token and ``verdi status`` may therefore not print it. It is
    worth having only if what it prints is the whole of what a newcomer needs, so that claim is made end to end
    rather than against the code the same function would have minted.
    """
    a, b = collab(2, bare=True)

    a.run('init', ['--bind', '127.0.0.1', '--port', '0', '--non-interactive'])
    a.serve()

    printed = a.run('link').output.strip()

    joining.append(b)
    b.run('init', ['--join', printed, '--bind', '127.0.0.1', '--port', '0', '--non-interactive'])

    assert set(b.peers()) == {a.uuid}
    assert set(a.peers()) == {b.uuid}, 'the join announced the newcomer to the member whose code it used'
    assert b.option('collab.token') == a.option('collab.token')


def test_joining_a_collab_three_members_deep(collab, joining):
    """Test that a collab founded on A admits B, that B admits C, and that provenance then flows A to C via B.

    C never contacts A: it holds A only because B vouched for it in the roster it answered the join with.
    """
    a, b, c = collab(3, bare=True)

    a.run('init', ['--bind', '127.0.0.1', '--port', '0', '--non-interactive'])
    a.serve()

    joining.append(b)
    b.run('init', ['--join', code_of(a), '--bind', '127.0.0.1', '--port', '0', '--non-interactive'])
    b.serve()

    joining.append(c)
    c.run('init', ['--join', code_of(b), '--bind', '127.0.0.1', '--port', '0', '--non-interactive'])
    c.serve()

    # Carol holds Alice because Bob vouched for her in the roster it answered the join with; Alice has not heard
    # of Carol at all yet, since nobody has made contact with her since Carol arrived.
    assert set(b.peers()) == {a.uuid, c.uuid}
    assert set(c.peers()) == {a.uuid, b.uuid}
    assert set(a.peers()) == {b.uuid}

    created = a.seal_calculation()

    b.run('pull', ['alice', '--force'])
    c.run('pull', ['bob', '--force'])

    assert created in c.uuids()
    assert set(a.peers()) == {b.uuid, c.uuid}, 'the gossip of the pull did not carry Carol to Alice'


def test_a_moved_endpoint_heals_by_its_own_announcement(collab):
    """Test that a member that changed address corrects its peers by raising its own stamp.

    Only the owner of an entry ever stamps it, so a moved address spreads exactly one way: the mover makes
    contact, and the raised stamp is what makes its peers take the new URL over the one they hold.
    """
    a, b, _ = collab(3)
    created = b.seal_calculation()

    b.rebind()

    stale = a.peers()[b.uuid]['url']
    result = a.run('pull', ['bob', '--force'])

    assert 'skipping' in result.output
    assert created not in a.uuids()

    # Bob makes contact, which is what carries its own announcement.
    b.run('push', ['alice', '--force'])

    assert a.peers()[b.uuid]['url'] != stale
    assert a.peers()[b.uuid]['url'] == b.url
    assert created in a.uuids()


def test_stale_gossip_loses_to_a_fresher_stamp(collab):
    """Test that a stale address cannot undo a correction, whichever way it travels.

    The stamp decides, not who is speaking and not who spoke last. One contact settles it both ways round: the
    stale entry Carol gossips does not overwrite the fresh one Alice holds, and the same exchange hands Alice's
    fresher entry back to Carol — third-party hearsay, which a stamp makes as good as the owner's own word.
    """
    a, b, c = collab(3)

    b.rebind()
    b.run('push', ['alice', '--force'])

    assert a.peers()[b.uuid]['url'] == b.url

    # Carol still holds the address Bob used to be at, and gossips it to Alice at the next contact.
    assert c.peers()[b.uuid]['url'] != b.url

    c.run('push', ['alice', '--force'])

    assert a.peers()[b.uuid]['url'] == b.url, 'stale gossip overwrote the address its owner had corrected'
    assert c.peers()[b.uuid]['url'] == b.url, 'the fresher entry was not relayed back in the same exchange'


def test_a_rotation_retires_the_old_token_at_once(collab):
    """Test that a rotated token stops opening the endpoint immediately, without a restart of anything."""
    a, b, _ = collab(3)
    a.seal_calculation()

    a.run('rotate')

    result = b.run('pull', ['alice', '--force'])

    assert '401' in result.output
    assert b.count() == 0


def test_the_rotation_signal_only_asks_for_a_rekey(collab):
    """Test that the advisory signal is recorded and changes nothing else.

    Acting on it would be the defect: the signal is authenticated by the very token being retired, so an excluded
    member — who holds that same token — could otherwise freeze the whole collab by sending it.
    """
    a, b, _ = collab(3)

    a.run('rotate')

    assert b.peers()[a.uuid]['signalled'] is True
    assert b.peers()[a.uuid]['active'] is True
    assert b.option('collab.token') == 'collab-token'


def test_a_pair_that_did_not_rotate_keeps_syncing(collab):
    """Test that a rotation splits the collab rather than stopping it: the members left out still sync together.

    A scope assertion rather than a mechanism one — `rotate` writes only its own profile's options, so there is
    nothing between B and C for it to touch. It is here because that is the property the command's design rests
    on, and because a rotation that reached further would be a serious defect with no other test to catch it.
    """
    a, b, c = collab(3)
    created = b.seal_calculation()

    a.run('rotate')

    move(b, c, 'pull')

    assert created in c.uuids()


def test_a_rekeyed_member_resumes_at_its_cursor(collab):
    """Test that rekeying keeps the cursors and the history, and that syncing resumes without re-transferring.

    Two claims, upheld by two different things: the cursor survives the rekey (asserted directly), and nothing
    already held travels again (which the manifest diff would uphold even without it).
    """
    a, b, _ = collab(3)
    created = a.seal_calculation()

    b.run('pull', ['alice', '--force'])
    cursor = b.state().cursors[a.uuid]

    a.run('rotate')
    b.run('rekey', [code_of(a)])

    assert b.option('collab.token') == a.option('collab.token')
    assert b.peers()[a.uuid]['active'] is True
    assert b.state().cursors[a.uuid] == cursor

    mark = len(b.state().events)
    b.run('pull', ['alice', '--force'])

    assert created in b.uuids()
    assert [uuid for event in b.state().events[mark:] for uuid in event.uuids] == []


def test_a_rotation_racing_a_sync_is_not_undone_by_it(collab, faults):
    """Test that a sync completing after a rotation does not put the roster back the way it was.

    A ``verdi collab rotate`` in another terminal sets the whole roster dormant. The sync that was already in
    flight is finished under the old token, so pinning its peer — and everyone that peer vouched for, the
    excluded member included — would mark them all active again under a key none of them holds.

    Pull-only, and driven from inside the import: that is where a sync spends its time, and two ``verdi`` runs
    cannot genuinely overlap in one interpreter.
    """
    a, b, _ = collab(3)
    created = a.seal_calculation()

    faults.rotate_during_import(b)

    result = b.run('pull', ['alice', '--force'])

    assert 'rekeyed while syncing' in result.output
    # The provenance landed: the import committed before the roster was reached, and is not rolled back.
    assert created in b.uuids()
    # The roster is the rotation's to decide, and the rotation left it dormant.
    assert all(not entry['active'] for entry in b.peers().values())


def test_a_dormant_peer_is_never_contacted(collab):
    """Test that after a rotation the whole roster rests dormant and no sync reaches for it.

    Dormancy deletes nothing: the URL, the nickname and the stamp are kept, which is what lets a member returning
    under the new token be recognized rather than re-added.
    """
    a, b, c = collab(3)

    a.run('rotate')

    result = a.run('pull', ['--force'], raises=True)

    assert 'dormant' in result.output
    assert set(a.peers()) == {b.uuid, c.uuid}
    assert all(not entry['active'] for entry in a.peers().values())


def test_a_rekey_with_the_code_of_another_collab_is_refused(collab):
    """Test that a code of a different collab is refused: rotation replaces a key, never an identity."""
    a, b, _ = collab(3)

    a.run('rotate')
    b.set_option('collab.uuid', 'some-other-collab')

    result = b.run('rekey', [code_of(a)], raises=True)

    assert 'belongs to collab' in result.output


@pytest.mark.parametrize('direction', ['pull', 'push'])
def test_a_peer_of_another_collab_is_refused(collab, direction):
    """Test that a token shared too widely cannot splice two collabs: the collab UUID is held against every peer.

    Both directions, since one check guards the routes of both; the rest of the collab keeps syncing, because it
    is the member that drifted that is refused and not the collab that is stopped.
    """
    a, b, c = collab(3)
    created = a.seal_calculation()

    b.set_option('collab.uuid', 'some-other-collab')

    result = move(a, b, direction)

    assert 'takes part in collab' in result.output
    assert created not in b.uuids()

    move(a, c, direction)

    assert created in c.uuids()


def test_a_client_that_skips_the_handshake_is_still_refused(collab, tmp_path):
    """Test that the routes a push carries its payload over refuse a foreign collab with no handshake in front.

    The handshake is the client's to send, so a guard standing only there guards nothing: a holder of a token
    shared too widely reaches the manifest diff, the upload and the import directly, and those are what land
    foreign provenance in this profile.
    """
    from http import HTTPStatus

    from aiida.common import timezone
    from aiida.tools.collab.client import CollabClient
    from aiida.tools.collab.config import OPTION_TOKEN
    from aiida.tools.collab.protocol import CollabRequestError

    a, b, _ = collab(3)
    a.seal_calculation()
    before = b.graph()

    filepath = tmp_path / 'push.aiida'
    filepath.write_bytes(b'a delta that never gets to be one')

    with CollabClient(b.url, b.option(OPTION_TOKEN), collab='some-other-collab') as client:
        for attempt in (
            lambda: client.diff_manifest(['uuid-of-a-node']),
            lambda: client.upload_delta(filepath),
            lambda: client.trigger_import('d' * 64, peer=a.uuid, instant=timezone.now()),
        ):
            with pytest.raises(CollabRequestError) as excinfo:
                attempt()

            assert excinfo.value.status == HTTPStatus.CONFLICT

    assert list(b.endpoint.staging_dir.iterdir()) == []
    assert b.graph() == before


def test_the_discovery_route_answers_a_caller_of_another_collab(collab, capsys):
    """EXPECTED (phase 18): ``/info`` answers a caller of another collab, which is what the refusal is built on.

    It is the one route whose purpose is to say which collab this is, so it cannot demand that the caller
    already know. What the exemption buys is asserted rather than described: the answer it serves is what
    ``peer_agrees`` turns into a refusal naming both collabs, where the guard would give a bare 409.
    """
    from aiida.cmdline.commands.cmd_collab import peer_agrees
    from aiida.tools.collab.client import CollabClient
    from aiida.tools.collab.config import OPTION_TOKEN, OPTION_UUID

    a, b, _ = collab(3)
    theirs = b.option(OPTION_UUID)

    a.set_option(OPTION_UUID, 'some-other-collab')

    with CollabClient(b.url, b.option(OPTION_TOKEN), collab='some-other-collab') as client:
        info = client.info()

    assert info.collab == theirs

    a.load()
    entry = a.peers()[b.uuid]
    capsys.readouterr()

    agrees = peer_agrees(a.config, a.profile, b.uuid, entry, info)
    warning = capsys.readouterr().out

    assert agrees is False
    assert theirs in warning
    assert 'some-other-collab' in warning


def test_another_profile_at_a_known_address_is_refused(collab):
    """Test that a reprovisioned machine does not inherit the sync history of the profile that was there.

    The address is where a peer is; the profile UUID is who it is, and only the second keys the cursors.
    """
    from aiida.tools.collab.config import OPTION_PEERS

    a, b, c = collab(3)

    peers = dict(a.peers())
    peers[b.uuid] = {**peers[b.uuid], 'url': c.url}
    a.set_option(OPTION_PEERS, peers)

    result = a.run('pull', ['bob', '--force'])

    assert 'is not the one this collab knows' in result.output
    assert a.state().cursors == {}


def test_a_corrected_address_is_provisional_until_the_peer_answers(collab):
    """Test that ``peer set --url`` marks the peer unproven, and that a contact at that address proves it."""
    from aiida.tools.collab.config import OPTION_PEERS

    a, b, _ = collab(3)

    peers = dict(a.peers())
    peers[b.uuid] = {**peers[b.uuid], 'url': 'http://127.0.0.1:1', 'seen': True}
    a.set_option(OPTION_PEERS, peers)

    a.run('peer set', ['bob', '--url', b.url])

    assert a.peers()[b.uuid]['seen'] is False

    a.run('pull', ['bob', '--force'])

    assert a.peers()[b.uuid]['seen'] is True


def test_deleting_a_profile_takes_its_collab_state_with_it(collab, tmp_path):
    """Test that the state dies with the profile, and that a profile recreated under its name starts empty.

    Deleting a profile is the one moment its collab state must not outlive it: what it describes is what *that*
    profile held of its peers, and a namesake holds none of it. (The keying by profile UUID rather than by name
    is a second guard against the same thing, and one this test cannot distinguish — `delete_state` removes the
    file under whichever key it computes.)
    """
    from aiida.manage.configuration import create_profile
    from aiida.tools.collab.state import CollabState

    a, b, _ = collab(3)
    a.seal_calculation()

    b.run('pull', ['alice', '--force'])

    filepath, workdir = b.state_filepath, b.workdir

    assert filepath.exists()
    assert workdir.exists()

    b.stop()
    b.backend.close()
    b.config.delete_profile(b.profile.name, delete_storage=True)

    assert not filepath.exists()
    assert not workdir.exists()

    namesake = create_profile(
        b.config,
        storage_backend='core.sqlite_dos',
        storage_config={'filepath': str(tmp_path / 'namesake' / 'storage')},
        name=b.profile.name,
        email='bob@localhost',
        is_test_profile=True,
    )

    assert namesake.uuid != b.uuid
    assert CollabState.load(namesake).cursors == {}
