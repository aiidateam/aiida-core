###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The transfer breaks: what survives, what is retried, and what must never be half-landed.

Every failure here is injected into the real code path — a short body against a promised ``Content-Length``, a
half-staged upload, an import that raised — so the recovery under test is the one a collaborator would get.
"""

import threading

import pytest

from tests.tools.collab.conftest import move

DIRECTIONS = ('pull', 'push')


def test_a_dropped_download_resumes_on_the_next_pull(collab, faults):
    """Test that a connection cut mid-download is resumed, not restarted, and imported exactly once.

    Pull-only: the download is the receiver's, and only it has a partial file to resume from. The delta carries a
    payload larger than one transfer chunk, because a client buffers a chunk before it writes any of it: below
    that size an interrupted download has nothing to resume from and legitimately starts over.
    """
    a, b, _ = collab(3)
    chunk = 1024 * 1024
    created = a.seal_calculation(ballast=chunk + chunk // 2)

    dropped = faults.drop_next_download(after=chunk + 200)

    b.run('pull', ['alice', '--force'])

    partial = b.workdir / f'pull-{a.uuid}.aiida'

    # How much of the interrupted transfer reached the disk is the HTTP stack's business -- how much it buffers
    # before yielding, and whether it yields the short tail at all -- so what is asserted is that a prefix of the
    # delta survived to resume from, not where it happens to end.
    assert chunk <= partial.stat().st_size <= dropped['served'][0]
    assert created not in b.uuids()

    b.run('pull', ['alice', '--force'])

    assert created in b.uuids()
    assert b.graph() == a.graph()
    assert not partial.exists()
    assert len([event for event in b.state().events if event.uuids]) == 1
    # The resumption served only the tail, so the two transfers add up to the delta rather than to twice it.
    assert dropped['served'][1] < chunk


def test_a_dropped_upload_resumes_from_what_was_staged(collab, faults):
    """Test that a connection cut mid-upload re-sends only the missing tail on the next push.

    Push-only: the upload is the sender's, and the peer's staging directory is what holds the resumption point.
    """
    a, b, _ = collab(3)
    created = a.seal_calculation()

    dropped = faults.drop_upload(b, after=200)

    a.run('push', ['bob', '--force'])

    stash = a.workdir / f'push-{b.uuid}.aiida'

    assert dropped['staged'] == 200
    assert created not in b.uuids()
    assert stash.exists(), 'the cut delta was not stashed for the retry'

    size = stash.stat().st_size
    result = a.run('push', ['bob', '--force'])

    assert created in b.uuids()
    assert b.graph() == a.graph()
    # The staged prefix is not re-sent: the retry probes what the peer holds and continues from there.
    assert f'transferred {size - 200} bytes' in result.output


def test_a_peer_dying_before_the_import_keeps_the_upload_staged(collab, faults):
    """Test that a push whose import never answered retries the import alone, uploading nothing again."""
    a, b, _ = collab(3)
    created = a.seal_calculation()

    faults.drop_import(b)

    a.run('push', ['bob', '--force'], raises=True)

    assert created not in b.uuids()
    assert list(b.endpoint.staging_dir.iterdir()), 'the staged upload was discarded'

    result = a.run('push', ['bob', '--force'])

    assert created in b.uuids()
    assert 'transferred 0 bytes' in result.output
    assert not list(b.endpoint.staging_dir.iterdir())


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_an_import_that_never_ran_lands_nothing_and_is_retried_whole(collab, faults, direction):
    """Test that an import that raised before it started leaves no node, no event and no cursor, and retries."""
    a, b, _ = collab(3)
    created = a.seal_calculation()

    faults.failing_import()

    move(a, b, direction, raises=True)

    assert created not in b.uuids()
    assert b.state().events == []
    assert b.state().cursors == {}

    move(a, b, direction)

    assert b.graph() == a.graph()
    assert b.count() == 3
    assert len(b.state().events) == 1


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_an_import_that_died_after_its_archive_committed_claims_nothing(collab, faults, direction):
    """Test the window the ordering of the import exists for: nodes here, and no claim on any of them.

    The archive commits in its own transaction; the cursor, the event and the journalled boundary links are
    written after it. A crash in between therefore leaves the receiver holding provenance it does not yet claim —
    which is the safe direction, because the next sync re-offers what it has not claimed and the import dedupes.
    Claiming first and importing second is the arrangement that would lose nodes silently.
    """
    a, b, _ = collab(3)
    created = a.seal_calculation()

    faults.die_after_the_archive_commits()

    move(a, b, direction, raises=True)

    assert created in b.uuids(), 'the archive did not commit, so this is not the window under test'
    assert b.state().events == []
    assert b.state().cursors == {}

    move(a, b, direction)

    assert b.graph() == a.graph()
    assert b.count() == 3, 'the retry imported the delta a second time'
    assert b.state().cursors != {}


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_a_crash_after_the_archive_leaves_the_computer_to_the_retry(collab, faults, direction):
    """Test that the retry marks a computer the crashed import created and never got to name.

    Which computers an import created is a question only the state before it can answer: by the retry they are
    all held, so nothing distinguishes a peer's machine from one of this profile's own. Journalled before the
    archive for that reason, beside the boundary links and with the same window in mind.
    """
    a, b, _ = collab(3)
    a.seal_calculation(computer='lumi')

    faults.die_after_the_archive_commits()

    move(a, b, direction, raises=True)

    assert set(b.computers().values()) == {'lumi'}, 'the archive did not commit, so this is not the window'
    assert set(b.state().pending_computers.values()) == {'lumi'}

    move(a, b, direction)

    assert set(b.computers().values()) == {'lumi@collab'}
    assert b.state().pending_computers == {}


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_a_crashed_import_leaves_its_computer_to_whichever_peer_syncs_next(collab, faults, direction):
    """Test that the journal of a crashed import survives an import from a *different* peer, which finishes it.

    The journal is merged rather than replaced for this: the sync that comes after the crash is whichever peer
    the loop reaches next, and it clears the whole journal once it has marked it. A journal that only ever held
    the current delta's computers would drop the crashed one here, and the crashed peer's own retry cannot save
    it — by then its computer is held, so nothing journals it a second time.
    """
    a, b, c = collab(3)
    a.seal_calculation(computer='lumi')
    c.seal_calculation(computer='daint')

    faults.die_after_the_archive_commits()

    move(a, b, direction, raises=True)

    assert set(b.computers().values()) == {'lumi'}, 'the archive did not commit, so this is not the window'

    move(c, b, direction)

    assert set(b.computers().values()) == {'lumi@collab', 'daint@collab'}
    assert b.state().pending_computers == {}


def test_corrupt_staged_bytes_are_discarded_and_uploaded_again(collab, faults):
    """Test that an upload that does not match its checksum is refused, dropped, and re-sent by the next push."""
    a, b, _ = collab(3)
    created = a.seal_calculation()

    faults.corrupt_staged(b)

    result = a.run('push', ['bob', '--force'], raises=True)

    assert 'does not match its checksum' in result.output
    assert created not in b.uuids()
    assert not list(b.endpoint.staging_dir.iterdir()), 'corrupt bytes were left to rot in the staging directory'

    a.run('push', ['bob', '--force'])

    assert b.graph() == a.graph()


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_a_corrupt_delta_lands_nothing(collab, faults, direction):
    """Test that bytes that are not an archive land nothing, skip that peer by name, and leave the round running.

    An unreadable delta reaches a different guard from a refused one — the archive reader rather than the
    boundary check — and has to read the same way: nothing lands, the peers after it are still synced, and the
    run exits non-zero because a transfer that started did not land.
    """
    a, b, c = collab(3)
    mine = a.seal_calculation()
    theirs = b.seal_calculation()
    c.seal_calculation()

    # The corruption has to be one the loop gets past, not one it ends on.
    assert list(a.peers()) == [b.uuid, c.uuid]
    faults.corrupt_export()

    result = a.run(direction, ['--force'], raises=True)

    assert f'peer {b.nickname}' in result.output, 'the unreadable delta does not say which peer served it'
    assert ('not a folder, zip or tar file' if direction == 'pull' else 'provenance not landed') in result.output

    if direction == 'pull':
        assert theirs not in a.uuids()
        assert set(a.state().cursors) == {c.uuid}, 'a cursor moved on the corrupt delta, or the loop stopped'
    else:
        assert mine not in b.uuids()
        assert mine in c.uuids(), 'one corrupt cut stopped the sync with the peers after it'


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_an_import_failure_in_the_middle_of_a_round_syncs_the_rest(collab, faults, direction):
    """Test the general claim: one peer's import failing costs that peer alone, wherever it sits in the round.

    The refusal and the corrupt delta above are both the *first* peer of their round. What this adds is a failure
    with peers on either side of it, which is the only shape that shows the loop resuming rather than merely
    surviving its first step.
    """
    from aiida.common.exceptions import IntegrityError

    a, b, c, d = collab(4)
    mine = a.seal_calculation()
    theirs = {peer.nickname: peer.seal_calculation() for peer in (b, c, d)}

    assert list(a.peers()) == [b.uuid, c.uuid, d.uuid]
    faults.failing_import(after=1, error=IntegrityError)

    result = a.run(direction, ['--force'], raises=True)

    assert result.output.count('skipping peer') == 1
    assert f'peer {c.nickname}' in result.output

    if direction == 'pull':
        assert theirs['carol'] not in a.uuids()
        assert set(a.state().cursors) == {b.uuid, d.uuid}
    else:
        assert mine not in c.uuids()
        assert mine in b.uuids() and mine in d.uuids()


@pytest.mark.parametrize('status', (200, 500))
def test_a_peer_that_is_not_a_collab_endpoint_is_skipped(collab, stranger, status):
    """Test that a URL answering with anything but a collab endpoint is skipped, the other peers still syncing.

    The two statuses fail in different places — a 200 whose body is not the expected answer fails when the client
    parses it, a 500 when it checks the status — and both have to read as one unusable peer. Not parametrised
    over direction: both routes open with the same ``GET /info`` and handle its failure identically, so the
    second half of that matrix would assert nothing the first does not.
    """
    a, b, c = collab(3)
    created = c.seal_calculation()

    # The failure has to be one the loop gets *past*, not one it reaches after everything else succeeded.
    assert list(a.peers()) == [b.uuid, c.uuid]
    _repoint(a, b, stranger(status=status))

    result = a.run('pull', ['--force'])

    assert f'peer {b.nickname}' in result.output
    # One event, for Carol, who comes after Bob: the loop carried on past the stranger and finished the round.
    assert [event.peer for event in a.state().events] == [c.uuid]
    assert created in a.uuids()


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_an_unreachable_peer_does_not_stop_the_loop(collab, direction):
    """Test that a peer whose endpoint is closed is warned about and the remaining peers are still synced."""
    a, b, c = collab(3)
    created = a.seal_calculation()
    theirs = c.seal_calculation()

    # The failure has to be one the loop gets past, not one it ends on.
    assert list(a.peers()) == [b.uuid, c.uuid]
    b.stop()

    result = a.run(direction, ['--force'])

    assert f'peer {b.nickname}' in result.output
    # One event, for Carol, who comes after Bob: the loop finished the round despite the peer that is gone.
    assert [event.peer for event in a.state().events] == [c.uuid]
    assert (theirs in a.uuids()) if direction == 'pull' else (created in c.uuids())
    assert created not in b.uuids()


def test_a_peer_that_does_not_accept_pushes_is_skipped(collab):
    """EXPECTED (phase 3): a profile that has not opted in to being written to is skipped, and still serves pulls.

    Push-only, and asymmetric on purpose: ``collab.accept_push`` governs what may be written into a profile, not
    what it hands out, so the same peer that refuses the push delivers the identical provenance on a pull.
    """
    from aiida.tools.collab.config import OPTION_ACCEPT_PUSH

    a, b, c = collab(3)
    created = a.seal_calculation()

    # The refusal has to be one the loop gets past, not one it ends on.
    assert list(a.peers()) == [b.uuid, c.uuid]
    b.set_option(OPTION_ACCEPT_PUSH, False)

    result = a.run('push', ['--force'])

    assert 'does not accept pushes' in result.output
    assert created not in b.uuids()
    assert created in c.uuids(), 'one peer refusing pushes stopped the sync with the others'

    b.run('pull', ['alice', '--force'])

    assert b.graph() == a.graph()


def test_a_withdrawn_consent_refuses_the_handshake(collab, faults):
    """Test that consent withdrawn under a running endpoint refuses the next push before any delta is cut.

    A cooperating pusher reads ``accept_push`` from the peer's handshake and skips, so the only way it reaches the
    refusal is consent withdrawn between that read and the push itself. The peer here declares that it accepts
    pushes and refuses when asked, which is what the race looks like from the pusher's side — and neither side is
    restarted, since the option is read from the file per request.
    """
    from aiida.tools.collab.config import OPTION_ACCEPT_PUSH

    a, b, _ = collab(3)
    created = a.seal_calculation()

    b.set_option(OPTION_ACCEPT_PUSH, False)
    faults.claims(b, accept_push=True)

    result = a.run('push', ['bob', '--force'])

    assert '403' in result.output
    assert 'does not accept pushes' in result.output
    assert created not in b.uuids()
    assert not list(a.workdir.glob('push-*.aiida')), 'a delta was cut for a peer that had already refused it'


def test_a_push_that_skips_the_handshake_is_refused_at_the_import(collab, caplog, tmp_path):
    """Test that the import refuses a pusher that never asked, and that the refusal is not reported as a fault.

    The handshake is what a cooperating peer meets and nothing obliges a peer to ask it, so the import is what
    makes the option mean anything at all. Its refusal is the endpoint working as designed: the answer says
    refused rather than broken, and no traceback lands in the log of whoever hosts it.
    """
    from http import HTTPStatus

    from aiida.tools.collab.client import CollabClient
    from aiida.tools.collab.config import OPTION_ACCEPT_PUSH, OPTION_TOKEN, OPTION_UUID
    from aiida.tools.collab.protocol import CollabRequestError
    from aiida.tools.collab.sync import compute_delta, export_delta

    a, b, _ = collab(3)
    created = a.seal_calculation()

    b.set_option(OPTION_ACCEPT_PUSH, False)

    delta = compute_delta(state=a.state(), backend=a.backend, cursor=None, claim=frozenset())
    export = export_delta(tmp_path / 'delta.aiida', delta=delta, backend=a.backend)

    with CollabClient(b.url, a.option(OPTION_TOKEN), collab=a.option(OPTION_UUID)) as client:
        upload = client.upload_delta(export.filepath)

        with pytest.raises(CollabRequestError) as raised:
            client.trigger_import(upload.sha256, peer=a.uuid, instant=export.instant)

    assert raised.value.status == HTTPStatus.FORBIDDEN
    assert created not in b.uuids()
    assert 'Traceback' not in caplog.text, 'the refusal was logged as a malfunction of the endpoint'
    # The refused bytes stay staged, which is the residual the sweep of the staging directory bounds.
    assert list(b.endpoint.staging_dir.iterdir())


def test_a_stale_staged_upload_is_swept_and_a_fresh_one_is_not(collab, faults):
    """Test that a restart sweeps the uploads nobody came back for, and keeps the one a retry still needs.

    A staged upload is removed when its import succeeds, when it fails its checksum and when it is refused for
    good; every other outcome leaves it. Without the sweep a collab accumulates one abandoned upload per failed
    push forever, and with a sweep that took the fresh one the stash would stop being worth keeping at all.
    """
    import os
    import time

    from aiida.tools.collab.endpoint import STAGING_MAX_AGE

    a, b, _ = collab(3)
    created = a.seal_calculation()

    # A push whose import never answered: a retry is exactly what those bytes stay staged for.
    faults.drop_import(b)
    a.run('push', ['bob', '--force'], raises=True)

    (fresh,) = list(b.endpoint.staging_dir.iterdir())
    abandoned = b.endpoint.staging_dir / ('0' * 64)
    abandoned.write_bytes(b'an upload whose pusher never came back')
    os.utime(abandoned, (time.time() - STAGING_MAX_AGE - 1,) * 2)

    b.stop()
    b.serve()

    assert not abandoned.exists()
    assert fresh.exists(), 'the sweep took the upload the pusher is about to retry'

    result = a.run('push', ['bob', '--force'])

    assert 'transferred 0 bytes' in result.output
    assert created in b.uuids()


def test_a_push_against_a_running_import_is_answered_busy(collab):
    """Test that a peer whose import lock is held answers the handshake busy, before anything is exported.

    Push-only: the handshake is what a pusher asks for, and answering busy there is what serializes fan-in
    without any redundant bytes travelling.
    """
    from aiida.tools.collab.state import import_lock

    a, b, _ = collab(3)
    created = a.seal_calculation()

    with import_lock(b.state_filepath):
        result = a.run('push', ['bob', '--force'])

        assert 'busy right now' in result.output
        assert not list(b.endpoint.staging_dir.iterdir())

    a.run('push', ['bob', '--force'])

    assert created in b.uuids()


def test_a_full_endpoint_answers_busy_until_a_slot_expires(collab, monkeypatch):
    """EXPECTED (phase 9): a full endpoint refuses the next requester, and serves it once a slot ages out.

    What is pinned is the expiry, not the cap: a slot is refreshed per request, so a single transfer longer than
    ``SLOT_IDLE_SECONDS`` can still have its slot reclaimed under it. See ``phase-15/deferred.md``.

    Pull-only: the serving slots bound negotiations, which is what a pull opens; a pusher is bounded by the
    handshake instead.
    """
    from aiida.tools.collab import endpoint as collab_endpoint

    a, b, _ = collab(3)
    created = a.seal_calculation()

    # The cap is read once when the endpoint is built, so lowering it is a restart in production; here the slots
    # are replaced directly rather than pretending the option is re-read.
    a.endpoint._slots = collab_endpoint._Slots(1)

    # One negotiation takes the only slot and never downloads, so nothing releases it. Called directly, it names
    # no requester and is therefore a session of its own: the CLI below arrives under its profile UUID instead.
    a.endpoint.negotiate_delta(None, frozenset({'a-uuid-nobody-holds'}))

    result = b.run('pull', ['alice', '--force'])

    assert 'maximum number of peers' in result.output
    assert created not in b.uuids()

    monkeypatch.setattr(collab_endpoint, 'SLOT_IDLE_SECONDS', 0)

    b.run('pull', ['alice', '--force'])

    assert created in b.uuids()


def test_a_declined_pull_frees_the_slot_it_took(collab):
    """Test that declining the confirmation of a pull ends the negotiation, instead of holding a slot for nothing.

    The negotiation takes a serving slot before the user is asked anything. A decline that kept it would make
    saying "no" to one member the same as taking the endpoint away from another for ten minutes.
    """
    from aiida.tools.collab import endpoint as collab_endpoint

    a, b, c = collab(3)
    created = a.seal_calculation()

    a.endpoint._slots = collab_endpoint._Slots(1)

    result = b.run('pull', ['alice'], user_input='n\n')

    assert 'skipped alice' in result.output
    assert created not in b.uuids()

    c.run('pull', ['alice', '--force'])

    assert created in c.uuids(), 'the declined negotiation of bob was still counted against the cap'


def test_dry_runs_free_the_slots_they_took(collab):
    """Test that a dry run of a pull and of a push both end their session, in either direction.

    A dry run is the abandonment that happens most: it reports and stops, transferring nothing. Its slot is taken
    by the negotiation on the pull side and by the handshake on the push side, and both have to be given back.
    """
    from aiida.tools.collab import endpoint as collab_endpoint

    a, b, c = collab(3)
    created = a.seal_calculation()

    # One slot, so that a leak of either of the two is what the third member runs into: each dry run releases
    # before the next asks, and with two slots a leak of one of them would still leave one free.
    a.endpoint._slots = collab_endpoint._Slots(1)

    b.run('pull', ['alice', '--dry-run'])
    b.run('push', ['alice', '--dry-run'])

    c.run('pull', ['alice', '--force'])

    assert created in c.uuids(), 'the dry runs of bob were still counted against the cap'


def test_a_refused_import_frees_the_slot_of_the_pusher(collab, faults):
    """Test that a push whose import the receiver refuses ends its session, rather than holding a slot to expiry.

    The slot of a push is normally given back by the import; a refusal answered before the import runs — corrupt
    bytes here, a rotated token or a vanished staging file elsewhere — has nothing to give it back.
    """
    from aiida.tools.collab import endpoint as collab_endpoint

    a, b, c = collab(3)
    created = a.seal_calculation()

    b.endpoint._slots = collab_endpoint._Slots(1)
    faults.corrupt_staged(b)

    a.run('push', ['bob', '--force'], raises=True)

    result = c.run('pull', ['bob', '--force'])

    assert created not in c.uuids(), 'the refused push must not have landed on bob'
    # A pull that was served records a cursor even when the delta was empty; a refused one never imports at all.
    assert b.uuid in c.state().cursors, f'the failed push of alice was still counted against the cap: {result.output}'


def test_work_sealed_between_the_negotiation_and_the_request_renegotiates(collab, faults):
    """Test that a pull whose peer sealed work between its two round trips renegotiates instead of failing.

    The want was diffed against one manifest; the export request arrives at a peer that has computed another, and
    the new work links onto a node of the old one. Cut against the fresh computation, the archive carries a
    boundary link to a node this profile was never offered and its import refuses the whole delta — every time,
    against a peer whose daemon seals continuously. Pull-only: a pusher exports from the delta it diffed itself.
    """
    a, b, _ = collab(3)
    created = a.seal_calculation()

    faults.seal_after_the_negotiation(a, inputs=created)

    result = b.run('pull', ['alice', '--force'])

    assert 'renegotiate' in result.output
    assert b.graph() == a.graph()


def test_a_node_deleted_between_the_negotiation_and_the_request_renegotiates(collab, faults):
    """Test that a pull whose peer deleted a manifest node between its two round trips renegotiates.

    The quieter sibling: a local deletion is no staleness signal, so the peer would cut its cached computation and
    name a row that is gone. Pull-only, for the same reason.
    """
    a, b, _ = collab(3)
    kept = a.seal_calculation()
    dropped = a.seal_calculation()

    faults.delete_after_the_negotiation(a, dropped)

    result = b.run('pull', ['alice', '--force'])

    assert 'renegotiate' in result.output
    assert kept in b.uuids(), 'the computation that replaced the stale one still delivers what survives'
    assert dropped not in b.uuids()
    assert b.uuids() <= a.uuids(), 'nothing may be delivered that the sender no longer holds'


def test_a_negotiation_racing_the_closing_write_still_sees_the_import(collab, faults):
    """Test that what Alice pushed into Bob reaches Carol, though her negotiation raced Bob's closing write.

    A push into Bob and a negotiation out of Bob overlapping is routine — the endpoint serves both at once. The
    negotiation caches the computation it makes under the instant it read the state at, and only a pull event
    younger than that instant ever invalidates it. Stamping the event before waiting for the state lock puts it
    on the wrong side: no later negotiation for this cursor recomputes, the imported nodes carry Alice's older
    mtimes so no seed count notices them either, and Carol is never offered them by Bob again.
    """
    a, b, c = collab(3)
    created = a.seal_calculation()

    # Gives Carol a cursor for Bob, so that the negotiation the fault runs is the one her next pull repeats.
    c.run('pull', ['bob', '--force'])

    faults.negotiate_during_the_closing_write(b, c)

    a.run('push', ['bob', '--force'])

    c.run('pull', ['bob', '--force'])

    assert created in c.uuids()
    assert c.graph() == a.graph()


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_a_second_sync_of_one_profile_is_refused_before_any_contact(collab, faults, direction):
    """Test that a sync started while another one of the same profile runs is refused, contacting nobody.

    The per-peer transfer stashes are stable paths with no guard, and a cron pull beside a manual push is enough
    to have two writers on one of them. A torn push uploads cleanly — its checksum is taken from the torn bytes —
    then fails every import of those bytes forever, wedging that peer until a human deletes a file no message
    names. Refused before the first request, so a run that will not proceed costs no peer a serving slot.
    """
    from aiida.tools.collab.state import exclusive_lock

    a, b, _ = collab(3)
    created = a.seal_calculation()
    # The profile whose command it is, which is the one whose stashes two runs would tear.
    syncing, peer = (b, 'alice') if direction == 'pull' else (a, 'bob')

    move(a, b, direction)
    # A second run, which is refused unless the first one gave its lock back when it ended.
    move(a, b, direction)

    assert created in b.uuids()

    faults.refuse_every_contact()

    with exclusive_lock(syncing.workdir / 'sync.lock'):
        result = syncing.run(direction, [peer, '--force'], raises=True)

    assert 'another collab sync of this profile is running' in result.output


def test_concurrent_pushes_into_one_profile_serialize(collab, tmp_path):
    """Test that two peers importing into the same profile at once produce one correct graph, not a race.

    Driven against the endpoint directly rather than through two CLIs, because loading a profile is process-wide
    state: what is under test is the import lock, and this is the only way two imports genuinely overlap.
    """
    from aiida.tools.collab.state import CollabState
    from aiida.tools.collab.sync import compute_delta, export_delta

    a, b, c = collab(3)
    created = {member.nickname: member.seal_calculation() for member in (a, b)}

    def staged(member):
        state = CollabState.read(member.state_filepath)
        delta = compute_delta(state=state, backend=member.backend, cursor=None, claim=frozenset())

        return export_delta(tmp_path / f'{member.nickname}-delta.aiida', delta=delta, backend=member.backend)

    exports = {member.nickname: staged(member) for member in (a, b)}
    errors = []

    def push(member):
        export = exports[member.nickname]

        try:
            c.endpoint.import_staged(export.filepath, peer=member.uuid, instant=export.instant)
        except Exception as exception:
            errors.append(exception)

    threads = [threading.Thread(target=push, args=(member,)) for member in (a, b)]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join(timeout=60)

    assert not any(thread.is_alive() for thread in threads), 'an import never returned'
    assert errors == []
    assert set(created.values()) <= c.uuids()
    assert c.count() == 6
    assert set(c.state().cursors) == {a.uuid, b.uuid}


def _repoint(member, peer, url):
    """Point one of a member's roster entries at another address, as a moved peer would be corrected to."""
    from aiida.tools.collab.config import OPTION_PEERS

    peers = dict(member.peers())
    peers[peer.uuid] = {**peers[peer.uuid], 'url': url}
    member.set_option(OPTION_PEERS, peers)
