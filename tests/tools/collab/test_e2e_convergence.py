###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The core claim of the collab, over the wire: pairwise syncs converge, and nothing echoes.

Every member here is a real profile with a real endpoint running the real CLI, so a chain that converges does so
because the event union, the thin-delta negotiation, the cursors and the journals all agree — not because a stub
answered what the test wanted to hear.
"""

import pytest

from tests.tools.collab.conftest import move

DIRECTIONS = ('pull', 'push')


def transferred(member, since):
    """Return the nodes, refreshes and memberships a member's state gained since an event index."""
    state = member.state()
    events = state.events[since:]

    return {
        'nodes': [uuid for event in events if event.direction == 'pull' for uuid in event.uuids],
        'refreshes': [uuid for event in events if event.direction == 'refresh' for uuid in event.uuids],
        'memberships': len(state.memberships),
    }


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_nodes_relay_through_the_chain(collab, direction):
    """Test that provenance produced on A reaches C through B alone, with C never contacting A."""
    a, b, c = collab(3)
    created = a.seal_calculation()

    move(a, b, direction)
    move(b, c, direction)

    assert created in c.uuids()
    assert c.graph() == a.graph()


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_extras_relay_through_the_chain(collab, direction):
    """Test that an extra edited on A after the node was shared reaches C through B, under the `sync` policy."""
    a, b, c = collab(3, extras_mode='sync')
    created = a.seal_calculation()

    move(a, b, direction)
    move(b, c, direction)

    a.set_extra(created, 'note', 'from-alice')

    # Carol's cursor for Bob is advanced past the edit *before* the edit reaches Bob, so the node's mtime lies
    # behind it by the time Bob has it. B's plain "edited since your cursor" filter can no longer see the node;
    # only the union with what B itself refreshed since then can offer it, which is what makes a relay work.
    # Bob needs provenance of his own for that hop: an empty push is short-circuited before any import, and
    # Carol's cursor would not move at all.
    b.seal_calculation()
    move(b, c, direction)
    move(a, b, direction)
    move(b, c, direction)

    assert c.extras(created) == {'note': 'from-alice'}

    move(b, a, direction)

    assert c.graph() == a.graph()


def test_a_refreshed_extra_survives_a_failed_push_and_relays_through_the_chain(collab, faults):
    """Test that an extras edit whose push failed at the import still reaches C through B, once the retry lands it.

    What the retry's renegotiation is worth: an edit the retry dropped is not merely missing from the pair that
    had the failure — the node is shared, so no delta ever carries it again and it leaves the collab entirely.
    Push-only: the stash is the sender's.
    """
    a, b, c = collab(3, extras_mode='sync')
    created = a.seal_calculation()

    a.run('push', ['bob', '--force'])
    b.run('push', ['carol', '--force'])

    a.set_extra(created, 'note', 'from-alice')
    # Sealed so that the failed push has real bytes to stash: an extras-only push does travel once the receiver
    # holds a cursor, but the archive it stashes holds no node and the retry would have nothing to reuse.
    a.seal_calculation()

    faults.failing_import()
    a.run('push', ['bob', '--force'], raises=True)
    a.run('push', ['bob', '--force'])

    assert b.extras(created) == {'note': 'from-alice'}

    b.run('push', ['carol', '--force'])

    assert c.extras(created) == {'note': 'from-alice'}
    assert c.graph() == a.graph()
    assert c.state().cursors.get(a.uuid) is None, 'Carol took the edit from Alice rather than through Bob'


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_membership_relays_through_the_chain(collab, direction):
    """Test that a node curated into a group on A joins that group on C too, under the `grow` policy."""
    a, b, c = collab(3, groups_mode='grow')
    created = a.seal_calculation()
    group = a.curate('band', created)

    move(a, b, direction)
    move(b, c, direction)

    assert 'band' in c.labels()
    assert (group, created) in c.graph()['members']


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_membership_of_a_shared_node_relays_through_the_chain(collab, direction):
    """Test that curating a node everyone already holds still reaches C: no delta can carry it.

    The node travelled once and never will again, and its group is held by all three, so the membership rides the
    journal and the offer beside the delta or it rides nothing.
    """
    a, b, c = collab(3, groups_mode='grow')
    first, second = a.seal_calculation(), a.seal_calculation()
    group = a.curate('band', first)

    move(a, b, direction)
    move(b, c, direction)

    a.curate('band', second)

    move(a, b, direction)
    move(b, c, direction)

    assert (group, second) in c.graph()['members']
    assert c.graph() == a.graph()


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_dead_origin_relays_through_the_middle(collab, direction):
    """Test that provenance of a member that has gone offline for good still reaches the third one through B.

    C produces, B takes it, C's endpoint is closed for good. A must still receive C's nodes in full — with their
    links, their group and their extras — from B alone. This passes only if several decisions hold at once: the
    event union in ``compute_delta`` (B relays what it imported, whose mtimes predate the sync), the sender
    keeping no send-state (B has no record of who it served), and thin-delta negotiation resolving boundary links
    against what A already holds rather than against C.
    """
    a, b, c = collab(3, extras_mode='sync', groups_mode='grow')
    created = c.seal_calculation()
    c.set_extra(created, 'origin', 'carol')
    group = c.curate('band', created)

    # A takes a cursor for B *after* Carol produced, so Carol's mtimes lie behind it and the seed query alone can
    # never reach them again. Only the event union can, which is the point. A also gains nodes of its own here,
    # so the delta that follows is genuinely thin and its links genuinely cross the boundary.
    b.seal_calculation()
    move(b, a, direction)

    move(c, b, direction)
    c.stop()

    move(b, a, direction)

    assert created in a.uuids()
    assert a.extras(created) == {'origin': 'carol'}
    assert (group, created) in a.graph()['members']
    assert a.graph() == b.graph()

    # And the round that reaches for Carol as well: her endpoint is gone, which is a warning and not a failure.
    result = a.run(direction, ['--force'])

    assert f'peer {c.nickname}' in result.output
    assert a.graph() == b.graph()


def test_a_dead_origin_leaves_its_cursor_unset(collab):
    """EXPECTED (phase 7): relayed provenance does not advance the cursor of the member it originated on.

    The cursor means "I hold everything that peer had at T", and A has never spoken to C: were it advanced by
    what B relayed, C returning later would find A claiming a conversation that never happened. The complement of
    the relay above, and run one way only — it is about what a cursor means, not about how the nodes arrived.
    """
    a, b, c = collab(3)
    created = c.seal_calculation()

    move(c, b, 'pull')
    c.stop()
    move(b, a, 'pull')

    assert created in a.uuids()
    assert a.state().cursors.get(c.uuid) is None
    assert b.uuid in a.state().cursors


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_a_ring_reaches_a_fixpoint(collab, direction):
    """Test that a third round around A->B->C->A transfers nothing: no node, no refresh, no membership.

    This is the anti-echo test. Two separate defects — the mtime stamped by a remapped hash, and a refreshed node
    becoming the newest side — each made a ring re-deliver the same provenance forever, and each was invisible to
    a single pairwise sync.
    """
    a, b, c = collab(3, extras_mode='sync', groups_mode='grow')
    created = a.seal_calculation()
    a.curate('band', created)
    # Carol produces too, so the C->A hop carries something. A push with nothing to carry is short-circuited
    # before any import, which would leave A without a cursor for Carol and the ring without its third side —
    # and an echo that never completes a round trip is one no assertion here could see.
    c.seal_calculation()

    def circle():
        move(a, b, direction)
        move(b, c, direction)
        move(c, a, direction)

    circle()
    # Edited after the node has already gone round, so the second circle carries a real extras refresh rather
    # than the extras riding the delta. Only a refresh that lands can be echoed, which is what this rules out.
    a.set_extra(created, 'note', 'first')
    circle()

    marks = {member.nickname: len(member.state().events) for member in (a, b, c)}
    memberships = {member.nickname: len(member.state().memberships) for member in (a, b, c)}

    circle()

    for member in (a, b, c):
        gained = transferred(member, marks[member.nickname])
        assert gained['nodes'] == [], f'{member.nickname} received nodes on the third round'
        assert gained['refreshes'] == [], f'{member.nickname} received an extras refresh on the third round'
        assert gained['memberships'] == memberships[member.nickname], f'{member.nickname} journalled a membership'


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_a_mesh_converges_on_one_graph(collab, direction):
    """Test that three members each producing provenance converge on the same graph by pairwise syncs."""
    a, b, c = collab(3)

    for member in (a, b, c):
        member.seal_calculation()

    for _ in range(2):
        for source, target in ((a, b), (b, c), (c, a)):
            move(source, target, direction)

    assert a.graph() == b.graph() == c.graph()
    assert len(a.graph()['nodes']) == 9


def test_pull_and_push_reach_the_same_state(collab):
    """Test that the two routes are two spellings of one outcome, which is what the parametrisation assumes.

    The control of every other test in this file: the same starting state, synced once each way, has to end in
    the same digest — otherwise a test passing in both directions would prove less than it looks.
    """
    a, b, c, d = collab(4, extras_mode='sync', groups_mode='grow')
    created = a.seal_calculation()
    a.set_extra(created, 'note', 'shared')
    a.curate('band', created)

    a.run('push', ['bob', '--force'])
    c.run('pull', ['alice', '--force'])

    assert b.graph() == a.graph(), 'the push did not deliver what Alice holds'
    assert c.graph() == a.graph(), 'the pull did not deliver what Alice holds'
    assert d.graph()['nodes'] == []


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_a_second_peer_transfers_nothing_the_first_delivered(collab, direction):
    """Test that after A took B's provenance, syncing with C — who holds the same — moves no node.

    What is asserted is the outcome, not which of the two mechanisms produced it: A presents a claim naming what
    it just imported, and independently asks only for what it is missing, so nothing travels either way. The
    claim on its own is pinned by ``test_sync.py::test_export_subtracts_claim``.
    """
    a, b, c = collab(3)
    created = b.seal_calculation()

    move(b, c, direction)

    move(b, a, direction)
    mark = len(a.state().events)
    move(c, a, direction)

    assert created in a.uuids()
    assert transferred(a, mark)['nodes'] == []


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_repeating_a_sync_transfers_nothing_but_is_still_logged(collab, direction):
    """Test that running the same sync twice moves nothing and still records that it ran.

    The log answers "when did this last run", not only "when did this last transfer": a sync that had nothing to
    carry is a completed contact, and a user looking for one that failed must not find silence where it succeeded.
    """
    a, b, _ = collab(3)
    a.seal_calculation()

    move(a, b, direction)
    before = b.graph()
    marks = {member.nickname: len(member.state().events) for member in (a, b)}

    move(a, b, direction)

    assert b.graph() == before
    assert transferred(b, marks['bob'])['nodes'] == []

    caller, peer = (b, a) if direction == 'pull' else (a, b)
    events = caller.state().events[marks[caller.nickname] :]

    assert [(event.direction, event.peer, event.uuids) for event in events] == [(direction, peer.uuid, [])]


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_the_computer_marker_converges_through_the_chain(collab, direction):
    """EXPECTED (phase 26): a computer is `lumi@collab` on every member of the collab but the one that runs it.

    Every member that imports the computer writes the marker, and writing it onto a label that already carries
    it is a no-op, so C — which never contacts A — ends up with the label B has. That is what lets `verdi collab
    map-computer lumi@collab=...` mean the same thing wherever it is run, and the originator keeping the plain
    `lumi` is the importer matching its own row by UUID rather than an exception made for it.
    """
    a, b, c = collab(3)
    a.seal_calculation(computer='lumi')

    move(a, b, direction)
    move(b, c, direction)

    assert set(a.computers().values()) == {'lumi'}
    assert set(b.computers().values()) == {'lumi@collab'}
    assert set(c.computers().values()) == {'lumi@collab'}, 'the second hop stacked a marker on a marked label'


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_a_clashing_peer_computer_keeps_the_marker_last(collab, direction):
    """Test that a peer computer whose label is taken here is deduplicated with the marker still at the end.

    `lumi-2@collab`, never `lumi@collab-2` — with the marker displaced the next hop stops recognizing it and
    appends a second one, which is the ordering the convergence above rests on. Two peers who each run a `lumi`
    is the only shape the collision still takes once the marker exists.

    The last hop is where two computers of one delta want the same label: C receives B's own `lumi` beside the
    two marked ones B relayed, and a rename that named them in an arbitrary order would collide with a label
    another row of the same import still held, which the unique label column refuses mid-import. That regression
    escapes when the UUID order happens to name the rows in a workable sequence — two of the six orders here, so
    about one run in ten with both directions green. The labels asserted are the same either way.
    """
    a, b, c, d = collab(4)
    a.seal_calculation(computer='lumi')
    d.seal_calculation(computer='lumi')
    b.seal_calculation(computer='lumi')

    move(a, b, direction)

    assert set(b.computers().values()) == {'lumi', 'lumi@collab'}, "the importer's own `(Imported #0)` survived"

    move(d, b, direction)

    assert set(b.computers().values()) == {'lumi', 'lumi@collab', 'lumi-2@collab'}

    move(b, c, direction)

    assert set(c.computers().values()) == {'lumi@collab', 'lumi-2@collab', 'lumi-3@collab'}


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_two_peers_marked_computers_do_not_stack_the_marker(collab, direction):
    """Test that a marked computer arriving where its label is taken is deduplicated, not marked a second time.

    The one shape that reaches the marker being stripped before the dedup re-applies it: A's machine and D's are
    both `lumi@collab` by the time they meet at B, so the importer renames the second on the clash and its
    current label no longer says it is marked. Deriving the new label from *that* would give `lumi@collab@collab`
    — and stably, since the next hop leaves a marked label alone, so one collab-wide label per machine is lost
    for good.

    C's own machine rides in the same delta, which is what makes two rows of *one* import compete for one name:
    the dedup has to count the label it just handed out, not only the ones the profile already held.
    """
    a, b, c, d = collab(4)
    a.seal_calculation(computer='lumi')
    d.seal_calculation(computer='lumi')

    move(a, b, direction)
    move(d, c, direction)

    c.seal_calculation(computer='lumi')

    move(c, b, direction)

    assert set(b.computers().values()) == {'lumi@collab', 'lumi-2@collab', 'lumi-3@collab'}


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_a_computer_that_circles_back_is_recognized(collab, direction):
    """Test that a computer coming back to its owner around the collab creates no second row anywhere.

    Identity is the UUID, so the rename applies to the computers an import created and to nothing else: A already
    holds the machine coming back from C, the importer matches it, and nothing is renamed. An implementation that
    deduplicated by label would give one physical machine a second row on every lap of the circle, and split the
    mapping — and the cache hits it exists for — along with it.
    """
    a, b, c = collab(3)
    a.seal_calculation(computer='lumi')

    move(a, b, direction)
    move(b, c, direction)

    # A lap needs provenance of C's own to carry the computer home: an empty delta travels nowhere.
    c.seal_calculation(computer='lumi@collab')

    move(c, a, direction)
    move(c, b, direction)

    assert set(a.computers()) == set(b.computers()) == set(c.computers()), 'one machine became two rows'
    assert set(a.computers().values()) == {'lumi'}
    assert set(b.computers().values()) == {'lumi@collab'}
    assert set(c.computers().values()) == {'lumi@collab'}
