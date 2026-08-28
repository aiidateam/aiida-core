###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The copies drift apart: which divergences are the design and which would be defects.

A test whose expected outcome is a divergence, a refusal or a loss says which on its first docstring line, and
carries an entry in ``phase-15/deferred.md`` with what it costs the people using it.
"""

import pytest

from tests.tools.collab.conftest import move

DIRECTIONS = ('pull', 'push')


# -- deletion ---------------------------------------------------------------------------------------------------


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_a_deleted_node_is_not_resurrected(collab, direction):
    """EXPECTED (phase 5): a delete is local — the peer keeps its copy, and the next sync does not hand it back.

    What holds the second half here is the cursor: the calculation was sealed before it, so it is not a seed of
    any later delta and never reaches the wire at all. The tombstone is what covers the cases the cursor does
    not, which is the test below.
    """
    a, b, _ = collab(3)
    created = a.seal_calculation()

    move(a, b, direction)

    b.delete(created)

    assert created in b.state().tombstones

    move(a, b, direction)

    assert created not in b.uuids()
    assert created in a.uuids(), 'the deletion propagated to the peer'


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_deleted_work_of_this_profile_is_not_relayed_back(collab, direction):
    """EXPECTED (phase 5): the tombstone is what keeps a member's own deleted work from returning by another route.

    The case the cursor cannot cover. Bob produced this provenance, so it is in no import event of his and his
    claim would not name it; Alice took it and Carol took it from Alice; Bob then deleted it. Carol's first
    contact with Bob is unbounded — she offers everything she holds — and only the tombstone stands between that
    offer and the work coming back.

    It stands twice, which is why removing either defence alone leaves this green: Bob refuses the offered node
    at the manifest diff, so it is never cut into the delta, and his import filters the tombstones again out of
    whatever does arrive. Both have to go before the node returns.
    """
    a, b, c = collab(3)
    created = b.seal_calculation()

    move(b, a, direction)
    move(a, c, direction)

    b.delete(created)
    held = b.uuids()

    move(c, b, direction)

    assert created not in b.uuids()
    assert b.uuids() == held, 'a deleted node came back by relay'
    assert created in c.uuids()


def test_include_deleted_brings_a_deleted_node_back(collab):
    """Test that the escape hatch re-imports a tombstoned node and drops its tombstone.

    Pull-only: ``--include-deleted`` rewinds the receiver's own cursor, which only the receiver can do.
    """
    a, b, _ = collab(3)
    created = a.seal_calculation()

    b.run('pull', ['alice', '--force'])
    b.delete(created)
    b.run('pull', ['alice', '--force', '--include-deleted'])

    assert created in b.uuids()
    assert b.state().tombstones == set()


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_what_a_deleted_node_takes_with_it(collab, direction):
    """EXPECTED (phase 5): deleting a calculation takes what it created, and the peer keeps all of it.

    The input node is not a descendant and stays; the created node dies with its creator and is tombstoned with
    it, so neither comes back. What the peer holds is untouched by any of it.
    """
    a, b, _ = collab(3)
    created = a.seal_calculation()

    move(a, b, direction)

    calculation = b.creator(created)
    inputs = set(b.uuids()) - {created, calculation}
    b.delete(calculation)

    assert b.uuids() == inputs
    assert b.state().tombstones == {calculation, created}

    move(a, b, direction)

    assert b.uuids() == inputs
    assert len(a.uuids()) == 3


def test_a_deletion_during_a_pull_is_not_undone(collab, faults):
    """Test that a tombstone recorded while a delta is in flight is honoured by the import that lands it.

    The pull holds a state object across a handshake, a negotiation and a download — minutes of wall clock — and
    the import is what has to see the tombstones as they are when it runs, not as they were before any of it.
    Both defences fall to the same staleness: the refusal was computed before the deletion, so the node is asked
    for and cut into the delta, and the import's tombstone filter would read the same stale set. Pull-only: only
    the pull carries a state object across a network round trip; the endpoint re-reads its own inside the lock.
    """
    a, b, _c = collab(3)
    created = b.seal_calculation()

    # Carol's copy comes through Alice, so Carol's first contact with Bob is unbounded and offers everything she
    # holds — which is the only way work Bob produced himself can be handed back to him at all.
    b.run('push', ['alice', '--force'])
    a.run('push', ['carol', '--force'])

    faults.delete_during_negotiation(b, created)

    b.run('pull', ['carol', '--force'])

    assert created in b.state().tombstones
    assert created not in b.uuids(), 'the deletion was undone by the import it raced'


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_new_work_built_on_a_deleted_node_arrives_whole(collab, direction):
    """Test that provenance a peer built on a node Alice deleted arrives, while the rest of her deletion holds.

    The refusal happens at the manifest diff now, so the sender is what decides what it costs: the deleted node
    the new work *requires* is put back into the cut, and the deleted calculation that merely created it is not —
    its CREATE link goes with it, so the node lands creator-less instead of aborting the import over a boundary
    endpoint that exists nowhere. A restoration drops no tombstone; only ``--include-deleted`` does. Relayed
    through Carol, because Alice's own peer is not the only route the work can take back to her.
    """
    a, b, c = collab(3)
    created = a.seal_calculation()

    move(a, b, direction)
    move(a, c, direction)

    calculation = a.creator(created)
    a.delete(calculation)

    consumed = b.seal_calculation(inputs=created)

    move(b, c, direction)
    move(c, a, direction)

    assert consumed in a.uuids(), 'the new work has to arrive'
    assert created in a.uuids(), 'the deleted node that new work requires comes back with it'
    assert calculation not in a.uuids(), 'the deleted calculation nothing requires stays deleted'
    assert a.state().tombstones == {calculation, created}, 'a restoration drops no tombstone'

    # Held again, so the restored node is no longer refused and the links onto it are no longer dropped.
    second = b.seal_calculation(inputs=created)

    move(b, a, direction)

    assert second in a.uuids()
    assert a.graph()['nodes'] == [uuid for uuid in b.graph()['nodes'] if uuid != calculation]
    assert a.graph()['links'] == [link for link in b.graph()['links'] if calculation not in link]


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_a_restored_node_takes_part_in_extras_and_groups_again(collab, direction):
    """Test that a node Alice deleted and provenance brought back receives extras and memberships once more.

    The restoration leaves the tombstone standing — only ``--include-deleted`` expresses a change of mind — so
    held-and-tombstoned is a state a profile stays in for good. The tombstone gates delivery of the node, not the
    node's participation: were the mutable surfaces to keep reading it as "frozen", this one node would diverge
    from every peer forever, silently, with no command that surfaces it and none that heals it.
    """
    a, b, c = collab(3, extras_mode='sync', groups_mode='grow')
    created = a.seal_calculation()

    move(a, b, direction)
    move(a, c, direction)

    a.delete(a.creator(created))

    b.seal_calculation(inputs=created)

    move(b, c, direction)
    move(c, a, direction)

    assert created in a.uuids(), 'the deleted node that new work requires comes back with it'
    assert created in a.state().tombstones, 'a restoration drops no tombstone'

    b.set_extra(created, 'note', 'from-bob')
    group = b.curate('band', created)

    move(b, a, direction)

    assert a.extras(created) == {'note': 'from-bob'}
    assert (group, created) in a.graph()['members']


# -- extras -----------------------------------------------------------------------------------------------------


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_extras_diverge_permanently_under_local(collab, direction):
    """EXPECTED (phase 10): under the `local` policy an extra never travels once the node has, by any route.

    Not "may diverge" — never converges. Both sides keep their own value for as long as the collab exists, and
    no number of syncs changes that.
    """
    a, b, _ = collab(3, extras_mode='local')
    created = a.seal_calculation()

    move(a, b, direction)

    # Alice edits second, so under `sync` her value would win on both sides. Were Bob the later editor, the
    # assertion below would hold under either policy and this test would prove nothing about `local`.
    b.set_extra(created, 'note', 'bob')
    a.set_extra(created, 'note', 'alice')

    move(a, b, direction)
    move(b, a, direction)

    assert a.extras(created) == {'note': 'alice'}
    assert b.extras(created) == {'note': 'bob'}


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_the_most_recent_extras_replace_the_others(collab, direction):
    """Test that under `sync` the whole extras dict of the most recently edited side wins."""
    a, b, _ = collab(3, extras_mode='sync')
    created = a.seal_calculation()
    b.seal_calculation()

    # Provenance travels both ways first, which is what gives each side a cursor for the other -- and an extras
    # exchange carries nothing until it has one.
    move(a, b, direction)
    move(b, a, direction)

    a.set_extra(created, 'note', 'alice')
    b.set_extra(created, 'note', 'bob')
    b.set_extra(created, 'extra-of-bob', True)

    move(b, a, direction)

    assert a.extras(created) == {'note': 'bob', 'extra-of-bob': True}


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_an_extras_edit_made_before_the_cursor_exists_travels(collab, direction):
    """Test that an extra edited before the other side holds a cursor for this one still reaches it (phase 27).

    A peer that presents no cursor is not a peer holding nothing of this profile: it holds whatever it gave this
    profile in the first place, and those extras are in no delta. So ``refresh_offer`` answers a null cursor with
    every node's mtime, and the receiver's own comparison — which was always the authoritative one — asks for the
    single snapshot it turns out to need.

    See ``phase-15/deferred.md`` entry 13.
    """
    a, b, _ = collab(3, extras_mode='sync')
    created = a.seal_calculation()

    move(a, b, direction)

    b.set_extra(created, 'note', 'before-the-cursor')

    move(b, a, direction)

    assert a.extras(created) == {'note': 'before-the-cursor'}


def test_an_extras_edit_travels_once_a_cursor_exists(collab):
    """Test that the loss above is bounded: once the peer holds a cursor, later edits travel as designed.

    One direction is enough: what is under test is the bound of the gap above, which is parametrised over both.
    """
    a, b, _ = collab(3, extras_mode='sync')
    created = a.seal_calculation()

    move(a, b, 'pull')
    move(b, a, 'pull')

    b.set_extra(created, 'note', 'after-the-cursor')

    move(b, a, 'pull')

    assert a.extras(created) == {'note': 'after-the-cursor'}


def test_an_extras_only_change_can_be_pushed_first(collab):
    """Test that a push can start an extras exchange, with no node ever having travelled that way (phase 27).

    Push-only, because this is the half of the gap the null-cursor offer alone does not close: the receiver's
    cursor is written by an import and by nothing else, so the delta — empty of nodes, carrying the snapshot —
    has to ride through the upload and the import for the pusher to stop presenting a null cursor.

    See ``phase-15/deferred.md`` entry 13.
    """
    a, b, _ = collab(3, extras_mode='sync')
    created = a.seal_calculation()

    move(a, b, 'push')

    b.set_extra(created, 'note', 'bob')

    move(b, a, 'push')

    assert a.extras(created) == {'note': 'bob'}
    assert b.uuid in a.state().cursors, 'the import that carried the snapshot is what writes the cursor'


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_a_deleted_extra_travels_as_absence(collab, direction):
    """Test that removing an extra propagates, because the snapshot replaces the dict rather than merging into it."""
    a, b, _ = collab(3, extras_mode='sync')
    created = a.seal_calculation()

    a.set_extra(created, 'note', 'alice')
    a.set_extra(created, 'draft', True)

    move(a, b, direction)

    assert b.extras(created) == {'note': 'alice', 'draft': True}

    a.node(created).base.extras.delete('draft')

    move(a, b, direction)

    assert b.extras(created) == {'note': 'alice'}


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_private_extras_survive_an_incoming_snapshot(collab, direction):
    """Test that the `_` namespace is neither sent nor overwritten: it is the profile's own bookkeeping."""
    a, b, _ = collab(3, extras_mode='sync')
    created = a.seal_calculation()

    move(a, b, direction)

    b.set_extra(created, '_mine', 'bob-only')
    a.set_extra(created, 'note', 'alice')

    move(a, b, direction)

    assert b.node(created).base.extras.get('_mine') == 'bob-only'
    assert b.extras(created) == {'note': 'alice'}
    assert '_mine' not in a.node(created).base.extras.all


def test_clock_skew_decides_an_extras_exchange(collab):
    """KNOWN GAP (phase 10): "last write wins" is decided by machine clocks, so a skewed clock wins the argument.

    The one place in the design where instants generated on two different machines are compared. A profile whose
    clock runs ahead overwrites edits that were genuinely made after its own, and nothing detects it. Run one way
    round only: the comparison is between two node mtimes and does not know which route brought them together.
    See ``phase-15/deferred.md``.
    """
    from datetime import timedelta

    a, b, _ = collab(3, extras_mode='sync')
    created = a.seal_calculation()

    move(a, b, 'pull')

    a.set_extra(created, 'note', 'alice')
    # Alice's machine is an hour ahead. Bob edits afterwards, in real time, and still loses.
    a.set_mtime(created, a.mtime(created) + timedelta(hours=1))
    b.set_extra(created, 'note', 'bob')

    move(a, b, 'pull')
    move(b, a, 'pull')

    assert b.extras(created) == {'note': 'alice'}
    assert a.extras(created) == {'note': 'alice'}


# -- groups -----------------------------------------------------------------------------------------------------


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_a_group_removal_does_not_travel(collab, direction):
    """EXPECTED (phase 11): under `grow` the set of members only ever grows, so a removal is never sent onward.

    Upheld by the journal recording additions and nothing else: a removal is never offered, so there is nothing
    on the receiving side to refuse. That is the whole of the mechanism — there is no second gate behind it, and
    in particular nothing keeps the pair from coming back the other way, which the test below is about.
    """
    a, b, _ = collab(3, groups_mode='grow')
    created = a.seal_calculation()
    group = a.curate('band', created)

    move(a, b, direction)

    assert (group, created) in b.graph()['members']

    orm_group = _group_of(a, group)
    orm_group.remove_nodes([a.node(created)])

    move(a, b, direction)

    assert (group, created) in b.graph()['members']
    assert (group, created) not in a.graph()['members']


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_a_removal_is_resurrected_by_the_peer_that_kept_it(collab, direction):
    """EXPECTED (phase 28): a removal survives only until the peer that kept it curates into the same group.

    The other half of the test above, and the half that says what "local forever" is worth. The cursor protects
    the *pair* but the offer is keyed by the *group*: anything curated into it after the cursor puts its whole
    membership back on the wire, since a receiver that lacks the group needs the whole set to build it. So B,
    which removed nothing, hands A back exactly the membership A dropped — and under `grow` nothing refuses an
    addition on its merits.

    Consistent with the rule as written, which is that the set only ever grows; the cost is that the rule reads
    like a promise the removal is respected, and it is not. Recorded in this phase's `deferred.md`.
    """
    a, b, _ = collab(3, groups_mode='grow')
    created = a.seal_calculation()
    group = a.curate('band', created)

    move(a, b, direction)

    assert (group, created) in b.graph()['members']

    _group_of(a, group).remove_nodes([a.node(created)])

    assert (group, created) not in a.graph()['members'], 'the removal has to take effect, or there is none to resurrect'

    # Something else curated into the same group at B, so the group is offered again on the way back. Without it
    # the group is simply never mentioned again and the removal stands — by silence, not by any rule.
    second = b.seal_calculation()
    b.curate('band', second)

    move(b, a, direction)

    assert (group, second) in a.graph()['members'], 'the hop back has to carry the group, or nothing is tested'
    assert (group, created) in a.graph()['members'], 'the whole membership travels, the dropped pair with it'


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_a_group_relabel_does_not_travel(collab, direction):
    """EXPECTED (phase 11): only membership travels under `grow`; a group's label is a local name for it."""
    a, b, _ = collab(3, groups_mode='grow')
    created = a.seal_calculation()
    group = a.curate('band', created)

    move(a, b, direction)

    _group_of(a, group).label = 'orchestra'

    # A second node curated into the renamed group is what puts it back on the wire, now carrying the new label.
    # Without that hop the group is simply never offered again and the receiver is never asked to ignore
    # anything — the cursor would be upholding the assertion, not the design.
    second = a.seal_calculation()
    a.curate('orchestra', second)

    move(a, b, direction)

    assert (group, second) in b.graph()['members'], 'the renamed group was not re-offered at all'
    assert b.labels() == {'band'}
    assert a.labels() == {'orchestra'}


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_two_members_curating_the_same_label_keep_both_groups(collab, direction):
    """EXPECTED (phase 11): two people curating the same label end up with two groups, not one.

    Groups are identified by UUID, so a label collides where a UUID cannot and neither person's curation may be
    folded into the other's. The price is that an agreement made by voice is not one the collab can keep.
    """
    a, b, _ = collab(3, groups_mode='grow')
    mine, theirs = a.seal_calculation(), b.seal_calculation()
    group_a = a.curate('band', mine)
    group_b = b.curate('band', theirs)

    move(a, b, direction)
    move(b, a, direction)
    move(a, b, direction)

    for member in (a, b):
        assert {group for group, _ in member.graph()['members']} == {group_a, group_b}
        assert len(member.labels()) == 2, 'the two curations were folded into one group'
        assert 'band' in member.labels()


# -- what a diverged or tampered sender may not plant ------------------------------------------------------------


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_a_second_create_parent_is_refused(collab, faults, direction):
    """Test that a boundary link giving a shared node a second creator is refused and nothing lands.

    The boundary insertion bypasses the archive importer's validation, so this is the only guard there is.
    """
    a, b, _ = collab(3)
    first = a.seal_calculation()

    move(a, b, direction)

    second = a.seal_calculation()
    intruder = a.creator(second)
    faults.plant_boundary_link([intruder, first, 'create', 'result'])

    result = move(a, b, direction, raises=True)

    assert 'second incoming link' in result.output
    assert second not in b.uuids()
    assert b.creator(first) == a.creator(first)


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_a_self_link_is_refused(collab, faults, direction):
    """Test that a boundary link from a node to itself — which no real graph produces — is refused."""
    a, b, _ = collab(3)
    first = a.seal_calculation()

    move(a, b, direction)

    second = a.seal_calculation()
    faults.plant_boundary_link([first, first, 'create', 'result'])

    result = move(a, b, direction, raises=True)

    assert 'to itself' in result.output
    assert second not in b.uuids()


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_a_refused_delta_skips_only_its_peer(collab, faults, direction):
    """EXPECTED (phase 21): a delta that cannot land is one peer's answer, so it is skipped like any other.

    Every other unusable answer from a peer — offline, 401, busy, a version this profile cannot read, a policy
    that does not match — is warned about and skipped, and the loop moves on. A refusal reads the same, and names
    the peer it came from, because with several peers the message is the only thing that says which one diverged.
    What it does not do is exit 0: a transfer that started and did not land is a failure, unlike a peer that never
    started one.
    """
    a, b, c = collab(3)
    first = a.seal_calculation()

    move(a, b, direction)
    move(a, c, direction)

    second = a.seal_calculation()
    # Only the first delta of the round carries it, so the round has exactly one diverged peer in it.
    faults.plant_boundary_link([a.creator(second), first, 'create', 'result'])

    result = a.run(direction, ['--force'], raises=True)

    assert result.output.count('second incoming link') == 1
    assert f'peer {b.nickname}' in result.output, 'the refusal does not say which peer it came from'

    # Nothing landed from the refusal, and the peer after it is contacted and synced all the same.
    if direction == 'pull':
        assert set(a.state().cursors) == {c.uuid}
    else:
        assert second not in b.uuids()
        assert second in c.uuids()


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_a_generated_group_is_never_applied(collab, faults, direction):
    """EXPECTED (phase 14): a group of a type AiiDA generates for itself is refused, and refused in silence.

    An import group describes the history of the profile that made it and would mean nothing here. This profile
    decides what enters it, so the gate is on the receiving side — and the offer is dropped without a message.
    """
    a, b, _ = collab(3, groups_mode='grow')
    created = a.seal_calculation()
    a.curate('band', created)

    move(a, b, direction)

    second = a.seal_calculation()
    a.curate('band', second)
    planted = faults.offer_generated_group('alice-import', created)
    held = b.groups()

    move(a, b, direction)

    # Against the unfiltered group query: the digest leaves generated groups out by design, so asserting on it
    # here would be asserting on the test's own filter rather than on what the import wrote.
    assert planted['uuid'] not in b.groups()
    assert b.groups() == held
    assert b.labels() == {'band'}


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_a_peer_declaring_another_policy_is_refused(collab, direction):
    """EXPECTED (phase 14): a policy mismatch stops that one sync, and the loop carries on with everybody else.

    The policy of a collab is fixed at its creation and travels in the join code, so two members declaring
    different ones means a file was edited by hand — there is no legitimate way to reach this state.
    """
    from aiida.tools.collab.config import OPTION_POLICY

    a, b, c = collab(3, extras_mode='local')
    created = a.seal_calculation()
    theirs = c.seal_calculation()

    # The refusal has to be one the loop gets *past*, not one it ends on, so it has to be the first peer.
    assert list(a.peers()) == [b.uuid, c.uuid]
    b.set_option(OPTION_POLICY, {'extras_mode': 'sync', 'groups_mode': 'local'})

    result = a.run(direction, ['--force'])

    assert 'refusing to sync with bob' in result.output
    assert created not in b.uuids()
    # One event, for Carol: the loop carried on to the peer that agrees.
    assert [event.peer for event in a.state().events] == [c.uuid]
    assert (theirs in a.uuids()) if direction == 'pull' else (created in c.uuids())


def _group_of(member, uuid):
    """Return the ORM group of a member by UUID, valid until another profile is loaded."""
    from aiida import orm

    return orm.Group.get_collection(member.load()).get(uuid=uuid)
