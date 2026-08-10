###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""State that has to survive: what an interrupted sync leaves behind, and what the next one makes of it.

The collab keeps no send-state, so everything that has to survive a crash is on the receiving side: a partial
download, a stashed delta, a cursor that must not go backwards, boundary links journalled before an import that
never finished, and an event log that has been folded to keep it bounded.
"""

from tests.tools.collab.conftest import move


def test_a_recut_delta_is_served_whole_rather_than_spliced(collab, faults):
    """Test that the ``ETag`` invalidates a resumption when the sender re-cut its delta in the meantime.

    Resuming across two different deltas would splice two archives into one file, which is the one way a
    resumption can produce something worse than starting over. Pull-only: the validator guards a download.
    """
    a, b, _ = collab(3)
    chunk = 1024 * 1024
    created = a.seal_calculation(ballast=chunk + chunk // 2)

    dropped = faults.drop_next_download(after=chunk + 200)

    b.run('pull', ['alice', '--force'])

    assert (b.workdir / f'pull-{a.uuid}.aiida').stat().st_size == chunk

    # Alice produces more, so the delta is recomputed and re-exported: the bytes Bob holds describe a file that
    # no longer exists.
    second = a.seal_calculation()

    b.run('pull', ['alice', '--force'])

    assert {created, second} <= b.uuids()
    assert b.graph() == a.graph()
    # Served in full rather than from the offset Bob asked for, which is the ``If-Range`` mismatch doing its job.
    assert dropped['served'][1] > chunk


def test_a_stashed_push_is_retried_verbatim_with_its_memberships_renegotiated(collab, faults):
    """Test that a failed push re-sends the same bytes and negotiates the curation made since afresh.

    Push-only: the stash is the sender's. Retrying the bytes is what lets the upload resolve to what is already
    staged, but the memberships cannot ride along — the import advances the receiver's cursor to the stashed
    instant, past every journal entry older than it, so a retry that carried none would lose them for good.
    """
    a, b, _ = collab(3, groups_mode='grow')
    first = a.seal_calculation()

    a.run('push', ['bob', '--force'])

    second = a.seal_calculation()

    faults.failing_import()
    a.run('push', ['bob', '--force'], raises=True)

    assert second not in b.uuids()

    group = a.curate('band', first)
    result = a.run('push', ['bob', '--force'])

    assert 'retrying the delta of the previous failed push' in result.output
    assert second in b.uuids()
    assert (group, first) in b.graph()['members']


def test_a_stashed_push_renegotiates_its_extras_refresh(collab, faults):
    """Test that a retried push negotiates the extras of the failed one afresh, as it does its memberships.

    The import advances the receiver's cursor to the stashed instant, which is later than the mtime of the edit
    the failed push had already offered, so a retry that dropped it would leave it behind that cursor and no
    offer would name it again — and the node is shared already, so no later delta could carry it either.
    Push-only: the stash is the sender's.
    """
    a, b, _ = collab(3, extras_mode='sync')
    first = a.seal_calculation()

    a.run('push', ['bob', '--force'])
    b.seal_calculation()
    b.run('push', ['alice', '--force'])

    a.set_extra(first, 'note', 'alice')
    a.seal_calculation()

    faults.failing_import()
    a.run('push', ['bob', '--force'], raises=True)

    a.run('push', ['bob', '--force'])

    assert b.extras(first) == {'note': 'alice'}

    mark = len(b.state().events)

    for _ in range(3):
        a.run('push', ['bob', '--force'])

    assert b.extras(first) == {'note': 'alice'}, 'a later push moved the value the retry had landed'
    assert all(not event.uuids for event in b.state().events[mark:]), 'the landed refresh is re-delivered forever'


def test_a_retried_push_still_transfers_no_bytes(collab, faults):
    """Test that renegotiating the extras of a retry does not recompute the delta the stash exists to reuse.

    The guard on the fix above: the bytes are what the peer already staged, and re-cutting them would defeat the
    resumption the stash is for. Only the metadata beside them is negotiated again. Push-only: as its subject.
    """
    a, b, _ = collab(3, extras_mode='sync')
    first = a.seal_calculation()

    a.run('push', ['bob', '--force'])
    b.seal_calculation()
    b.run('push', ['alice', '--force'])

    a.set_extra(first, 'note', 'alice')
    second = a.seal_calculation()

    faults.failing_import()
    a.run('push', ['bob', '--force'], raises=True)

    result = a.run('push', ['bob', '--force'])

    assert 'transferred 0 bytes' in result.output
    assert second in b.uuids()
    assert b.extras(first) == {'note': 'alice'}


def test_a_cursor_never_moves_backwards(collab, faults):
    """Test that a retried push carrying the instant of its original export cannot rewind the receiver's cursor.

    The cursor means "I hold everything the peer had at T". A stashed delta describes an older T, and letting it
    win would make the receiver re-request everything the pull in between already delivered. Push-only: only a
    push carries an instant that can be older than the receiver's cursor, because only a push has a stash.
    """
    a, b, _ = collab(3)
    a.seal_calculation()

    faults.failing_import()
    a.run('push', ['bob', '--force'], raises=True)

    a.seal_calculation()
    b.run('pull', ['alice', '--force'])
    ahead = b.state().cursors[a.uuid]

    a.run('push', ['bob', '--force'])

    assert b.state().cursors[a.uuid] >= ahead
    assert b.graph() == a.graph()


def test_a_compacted_log_syncs_the_same_as_an_uncompacted_one(collab, monkeypatch):
    """Test that folding the event log loses nothing a peer still needs.

    What is pinned here is the union: every UUID a folded event named is still answered for, so a peer bounded
    by an instant inside the folded range is offered what it has not seen. That the fold also never *under*-states
    — the synthetic events sitting at the horizon of what they replaced — is a property of the fold itself and is
    pinned by ``test_state.py::test_compaction``.

    Run as pulls: the subject is one profile's own log, which both routes append to identically.
    """
    from aiida.tools.collab import state as collab_state

    monkeypatch.setattr(collab_state, 'COMPACT_THRESHOLD', 4)

    a, b, c = collab(3, extras_mode='sync', groups_mode='grow')
    created = b.seal_calculation()
    b.set_extra(created, 'note', 'bob')
    b.curate('band', created)

    # Carol takes her cursor for Alice before any of Bob's work reaches Alice, so those mtimes end up behind it.
    # Without that, Carol's later pull is a first contact whose unbounded seed query would reach everything on
    # its own and the folded log would never be consulted.
    c.run('pull', ['alice', '--force'])

    # Enough traffic through Alice for her log to be folded more than once.
    for _ in range(5):
        a.run('pull', ['bob', '--force'])
        b.seal_calculation()

    assert len(a.state().events) <= 4

    a.run('pull', ['bob', '--force'])
    c.run('pull', ['alice', '--force'])

    assert created in c.uuids(), 'the folded log lost provenance Carol had not seen'
    assert c.graph() == a.graph()
    assert c.extras(created) == {'note': 'bob'}
    assert 'band' in c.labels()


def test_a_link_left_pending_by_a_crash_waits_and_is_then_written(collab):
    """Test that boundary links journalled before an import that never finished are neither lost nor forced.

    They are written before the archive commits precisely so that a crash between the two leaves them recoverable.
    A link whose endpoints are not here yet stays pending across syncs; the one that delivers them writes it.
    Run as pulls: the journal and its replay live wholly on the receiving side, which both routes share.
    """
    from aiida.tools.collab.state import CollabState

    a, b, c = collab(3)
    first = a.seal_calculation()
    outside = c.creator(c.seal_calculation())

    move(a, b, 'pull')

    # What a crash between the archive commit and the state write leaves behind: a link naming one node this
    # profile holds and one it has never seen. The label is one no export produces, so what is asserted below
    # can only have come from the journal.
    pending = [first, outside, 'input_calc', 'recovered']

    with CollabState.mutate(b.state_filepath) as state:
        state.pending_links.append(pending)

    a.seal_calculation()
    b.run('pull', ['alice', '--force'])

    assert b.state().pending_links == [pending], 'a link whose node had not arrived was dropped'
    assert outside not in b.uuids()

    b.run('pull', ['carol', '--force'])

    assert b.state().pending_links == []
    assert tuple(pending) in b.graph()['links']
