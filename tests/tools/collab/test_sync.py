###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the export and import of the delta of a collab."""

import json
from uuid import uuid4

import pytest

from aiida import orm
from aiida.common import timezone
from aiida.common.links import LinkType
from aiida.storage.sqlite_temp import SqliteTempBackend
from aiida.tools.collab.config import COLLAB_PEER_KEY
from aiida.tools.collab.protocol import GroupMembers, member_pairs
from aiida.tools.collab.state import CollabEvent, CollabState, Membership
from aiida.tools.collab.sync import (
    _boundary_links,
    apply_computer_map,
    apply_members,
    compute_delta,
    export_delta,
    import_delta,
    members_wanted,
    membership_offer,
    missing_uuids,
    refresh_offer,
    refresh_snapshots,
    refresh_wanted,
    required_refused,
)

PEER = 'http://100.64.0.2:9137'


def seal_calculation(backend, label):
    """Store a calculation with one input and one output in ``backend`` and seal it."""
    inputs = orm.Int(1, backend=backend).store()
    calculation = orm.CalcJobNode(backend=backend, label=label)
    calculation.base.links.add_incoming(inputs, link_type=LinkType.INPUT_CALC, link_label='input')
    calculation.store()
    outputs = orm.Int(2, backend=backend)
    outputs.base.links.add_incoming(calculation, link_type=LinkType.CREATE, link_label='result')
    outputs.store()
    calculation.seal()

    return calculation


@pytest.fixture
def peers(tmp_path):
    """Return a factory for the storage of a profile of a collab and the state of that profile."""
    backends = []

    def factory(name):
        backend = SqliteTempBackend(SqliteTempBackend.create_profile(filepath=str(tmp_path / name)))
        backends.append(backend)
        return backend, CollabState(filepath=tmp_path / f'{name}.json')

    yield factory

    for backend in backends:
        backend.close()


def node_count(backend):
    return orm.QueryBuilder(backend=backend).append(orm.Node).count()


def load_node(backend, uuid):
    return orm.QueryBuilder(backend=backend).append(orm.Node, filters={'uuid': uuid}).one()[0]


def delete_nodes(backend, uuids):
    """Delete nodes and their links from a profile, as ``verdi node delete`` would.

    Through raw rows, because ``SqliteTempBackend`` does not implement ``delete_nodes_and_connections``.
    """
    from aiida.storage.sqlite_zip.models import DbLink, DbNode

    query = orm.QueryBuilder(backend=backend).append(orm.Node, filters={'uuid': {'in': list(uuids)}}, project='id')
    pks = query.all(flat=True)

    with backend.transaction() as session:
        session.query(DbLink).filter(DbLink.input_id.in_(pks) | DbLink.output_id.in_(pks)).delete(
            synchronize_session=False
        )
        session.query(DbNode).filter(DbNode.id.in_(pks)).delete(synchronize_session=False)


def linked_uuids(calculation):
    """Return the UUIDs of a calculation and of the nodes directly linked to it."""
    links = calculation.base.links.get_incoming().all() + calculation.base.links.get_outgoing().all()

    return {calculation.uuid} | {link.node.uuid for link in links}


def export_full(filepath, *, state, backend, cursor, claim=frozenset()):
    """Compute the delta and export all of it, as a requester that holds none of its nodes would receive it."""
    delta = compute_delta(state=state, backend=backend, cursor=cursor, claim=claim)

    return export_delta(filepath, delta=delta, backend=backend)


def test_export_only_sealed(tmp_path, peers):
    """Test that a sealed calculation is exported with its inputs and outputs, and an unsealed one is not."""
    backend, state = peers('one')
    sealed = seal_calculation(backend, 'sealed')
    unsealed = orm.CalcJobNode(backend=backend, label='unsealed').store()

    export = export_full(tmp_path / 'delta.aiida', state=state, backend=backend, cursor=None)

    assert set(export.uuids) == linked_uuids(sealed)
    assert unsealed.uuid not in export.uuids


def excepted_over_running(backend):
    """Store a sealed workchain that called a calculation which is still running, and return both.

    The workchain has an input of its own, which is reachable only through it.
    """
    excepted = orm.WorkChainNode(backend=backend, label='excepted')
    excepted.base.links.add_incoming(orm.Int(1, backend=backend).store(), link_type=LinkType.INPUT_WORK, link_label='x')
    excepted.store()
    running = orm.CalcJobNode(backend=backend, label='running')
    running.base.links.add_incoming(excepted, link_type=LinkType.CALL_CALC, link_label='child')
    running.store()
    excepted.seal()

    return excepted, running


def test_export_skips_unsealed_children(tmp_path, peers):
    """Test that a sealed process that called one which is still running is left out instead of aborting the export."""
    backend, state = peers('one')
    sealed = seal_calculation(backend, 'sealed')
    excepted_over_running(backend)

    export = export_full(tmp_path / 'delta.aiida', state=state, backend=backend, cursor=None)

    assert set(export.uuids) == linked_uuids(sealed)


def test_export_withheld_seed_travels_later(tmp_path, peers):
    """Test that a seed withheld for an unsealed child is offered again once that child seals.

    The export instant is pinned to the withheld seed, so a requester that stores it as its cursor presents one
    the seed still re-enters at.
    """
    backend, state = peers('one')
    excepted, running = excepted_over_running(backend)

    instant = export_full(tmp_path / 'delta.aiida', state=state, backend=backend, cursor=None).instant
    running.seal()

    export = export_full(tmp_path / 'delta-later.aiida', state=state, backend=backend, cursor=instant)

    assert linked_uuids(excepted) | {running.uuid} <= set(export.uuids)


def test_compute_delta_instants_under_a_withheld_seed(peers):
    """Test that a withheld seed pulls back the export instant alone, leaving the computation instant where it is.

    Both values are the design. The export instant is what a requester stores as its cursor, so it may not pass
    the seed; the computation instant is what a cache of the computation is measured against, and pulling that
    one back too would report the profile as having gained content for as long as the seed is withheld.
    """
    backend, state = peers('one')
    excepted, _ = excepted_over_running(backend)

    delta = compute_delta(state=state, backend=backend, cursor=None)

    assert delta.uuid_by_pk == {}, 'the seed is withheld, so the delta is empty'
    assert delta.instant == excepted.mtime
    assert delta.computed > excepted.mtime


def test_export_bounded_by_cursor(tmp_path, peers):
    """Test that a requester presenting the instant of the previous export is served nothing it already has."""
    backend, state = peers('one')
    seal_calculation(backend, 'sealed')

    export = export_full(tmp_path / 'delta.aiida', state=state, backend=backend, cursor=None)

    assert export.uuids

    again = export_full(tmp_path / 'delta-again.aiida', state=state, backend=backend, cursor=export.instant)

    assert again.uuids == []


def test_export_ignores_push_history(tmp_path, peers):
    """Test that the sender keeps no send-state: a recorded push does not diminish what a later requester is served."""
    backend, state = peers('one')
    seal_calculation(backend, 'sealed')

    export = export_full(tmp_path / 'delta.aiida', state=state, backend=backend, cursor=None)
    state.events.append(CollabEvent(time=timezone.now(), direction='push', peer=PEER, uuids=export.uuids, size=1))

    again = export_full(tmp_path / 'delta-again.aiida', state=state, backend=backend, cursor=None)

    assert set(again.uuids) == set(export.uuids)


@pytest.mark.parametrize('extras_mode, expected', (('local', 'mine'), ('sync', 'theirs')))
def test_import_extras_mode(tmp_path, peers, extras_mode, expected):
    """Test that the extras mode decides whether an incoming extra overwrites the local one."""
    backend_one, state_one = peers('one')
    backend_two, state_two = peers('two')
    calculation = seal_calculation(backend_one, 'sealed')

    filepath = tmp_path / 'delta.aiida'
    export = export_full(filepath, state=state_one, backend=backend_one, cursor=None)
    import_delta(filepath, state=state_two, backend=backend_two, extras_mode='local', peer=PEER, instant=export.instant)

    calculation.base.extras.set('note', 'theirs')
    load_node(backend_two, calculation.uuid).base.extras.set('note', 'mine')

    export = export_full(filepath, state=state_one, backend=backend_one, cursor=None)
    import_delta(
        filepath, state=state_two, backend=backend_two, extras_mode=extras_mode, peer=PEER, instant=export.instant
    )

    assert load_node(backend_two, calculation.uuid).base.extras.get('note') == expected


def test_import_strips_private_extras(tmp_path, peers):
    """Test that the caching extras of a peer, which are local to their profile, do not travel."""
    backend_one, state_one = peers('one')
    backend_two, state_two = peers('two')
    calculation = seal_calculation(backend_one, 'sealed')
    calculation.base.extras.set('_aiida_hash', 'a-hash-of-the-peer')
    calculation.base.extras.set('_aiida_cached_from', 'a-uuid-of-the-peer')

    filepath = tmp_path / 'delta.aiida'
    export = export_full(filepath, state=state_one, backend=backend_one, cursor=None)
    import_delta(filepath, state=state_two, backend=backend_two, extras_mode='local', peer=PEER, instant=export.instant)

    assert load_node(backend_two, calculation.uuid).base.extras.all == {COLLAB_PEER_KEY: PEER}


@pytest.mark.parametrize('extras_mode', ('local', 'sync'))
def test_import_keeps_local_caching_extras(tmp_path, peers, extras_mode):
    """Test that the caching extras of a peer cannot overwrite the local ones of a node that already exists."""
    backend_one, state_one = peers('one')
    backend_two, state_two = peers('two')
    calculation = seal_calculation(backend_one, 'sealed')

    filepath = tmp_path / 'delta.aiida'
    export = export_full(filepath, state=state_one, backend=backend_one, cursor=None)
    import_delta(filepath, state=state_two, backend=backend_two, extras_mode='local', peer=PEER, instant=export.instant)

    calculation.base.extras.set('_aiida_hash', 'a-hash-of-the-peer')
    calculation.base.extras.set('_aiida_cached_from', 'a-uuid-of-the-peer')
    load_node(backend_two, calculation.uuid).base.extras.set('_aiida_hash', 'my-own-hash')

    export = export_full(filepath, state=state_one, backend=backend_one, cursor=None)
    import_delta(
        filepath, state=state_two, backend=backend_two, extras_mode=extras_mode, peer=PEER, instant=export.instant
    )

    extras = load_node(backend_two, calculation.uuid).base.extras.all

    assert extras['_aiida_hash'] == 'my-own-hash'
    assert '_aiida_cached_from' not in extras


def test_import_empty_delta(tmp_path, peers):
    """Test that importing a delta of a peer that has nothing new is a no-op."""
    backend_one, state_one = peers('one')
    backend_two, state_two = peers('two')

    filepath = tmp_path / 'delta.aiida'
    export = export_full(filepath, state=state_one, backend=backend_one, cursor=None)
    report = import_delta(
        filepath, state=state_two, backend=backend_two, extras_mode='sync', peer=PEER, instant=export.instant
    )

    assert report.uuids == []
    assert node_count(backend_two) == 0


def test_import_skips_tombstoned(tmp_path, peers):
    """Test that provenance that was deleted locally is not imported again."""
    backend_one, state_one = peers('one')
    backend_two, state_two = peers('two')
    kept = seal_calculation(backend_one, 'kept')
    deleted = seal_calculation(backend_one, 'deleted')

    filepath = tmp_path / 'delta.aiida'
    export = export_full(filepath, state=state_one, backend=backend_one, cursor=None)
    deleted_uuids = linked_uuids(deleted)
    state_two.tombstones.update(deleted_uuids)

    report = import_delta(
        filepath, state=state_two, backend=backend_two, extras_mode='local', peer=PEER, instant=export.instant
    )

    assert set(report.skipped) == deleted_uuids
    assert set(report.uuids) == set(export.uuids) - deleted_uuids
    assert node_count(backend_two) == len(export.uuids) - len(deleted_uuids)
    assert orm.QueryBuilder(backend=backend_two).append(orm.Node, filters={'uuid': kept.uuid}).count() == 1


def test_import_skips_tombstoned_caller(tmp_path, peers):
    """Test that a tombstoned caller is not pulled back in by the process it called."""
    backend_one, state_one = peers('one')
    backend_two, state_two = peers('two')
    caller = orm.WorkChainNode(backend=backend_one, label='caller').store()
    called = orm.CalcJobNode(backend=backend_one, label='called')
    called.base.links.add_incoming(caller, link_type=LinkType.CALL_CALC, link_label='child')
    called.store()
    called.seal()
    caller.seal()

    filepath = tmp_path / 'delta.aiida'
    export = export_full(filepath, state=state_one, backend=backend_one, cursor=None)
    state_two.tombstones.add(caller.uuid)

    report = import_delta(
        filepath, state=state_two, backend=backend_two, extras_mode='local', peer=PEER, instant=export.instant
    )

    assert report.skipped == [caller.uuid]
    assert caller.uuid not in report.uuids


def test_import_skips_tombstoned_creator(tmp_path, peers):
    """Test that a tombstoned calculation is not pulled back in by the output it created."""
    backend_one, state_one = peers('one')
    backend_two, state_two = peers('two')
    calculation = seal_calculation(backend_one, 'sealed')

    filepath = tmp_path / 'delta.aiida'
    export = export_full(filepath, state=state_one, backend=backend_one, cursor=None)
    state_two.tombstones.add(calculation.uuid)

    report = import_delta(
        filepath, state=state_two, backend=backend_two, extras_mode='local', peer=PEER, instant=export.instant
    )

    assert report.skipped == [calculation.uuid]
    assert calculation.uuid not in report.uuids


def test_import_tombstone_loses_to_provenance(tmp_path, peers):
    """Test that a tombstoned node the remaining provenance depends on is imported, and not reported as skipped."""
    backend_one, state_one = peers('one')
    backend_two, state_two = peers('two')
    calculation = seal_calculation(backend_one, 'sealed')
    inputs = calculation.base.links.get_incoming().one().node

    filepath = tmp_path / 'delta.aiida'
    export = export_full(filepath, state=state_one, backend=backend_one, cursor=None)
    state_two.tombstones.add(inputs.uuid)

    report = import_delta(
        filepath, state=state_two, backend=backend_two, extras_mode='local', peer=PEER, instant=export.instant
    )

    assert report.skipped == []
    assert inputs.uuid in report.uuids


def test_import_twice(tmp_path, peers):
    """Test that importing the same delta again adds nothing but is recorded as its own event."""
    backend_one, state_one = peers('one')
    backend_two, state_two = peers('two')
    seal_calculation(backend_one, 'sealed')

    filepath = tmp_path / 'delta.aiida'
    export = export_full(filepath, state=state_one, backend=backend_one, cursor=None)
    import_delta(filepath, state=state_two, backend=backend_two, extras_mode='local', peer=PEER, instant=export.instant)
    count = node_count(backend_two)

    import_delta(filepath, state=state_two, backend=backend_two, extras_mode='local', peer=PEER, instant=export.instant)

    assert node_count(backend_two) == count
    # Read back from disk, since the log is what `verdi collab log` loads, not the dataclass in memory.
    assert len(json.loads(state_two.filepath.read_text(encoding='utf-8'))['events']) == 2


def test_import_advances_cursor_per_peer(tmp_path, peers):
    """Test that an import advances only the cursor of the peer the delta came from, to the carried instant."""
    backend_one, state_one = peers('one')
    backend_two, state_two = peers('two')
    seal_calculation(backend_one, 'sealed')

    other = timezone.now()
    state_two.cursors['http://other:9137'] = other
    state_two.save()

    filepath = tmp_path / 'delta.aiida'
    export = export_full(filepath, state=state_one, backend=backend_one, cursor=None)
    import_delta(filepath, state=state_two, backend=backend_two, extras_mode='local', peer=PEER, instant=export.instant)

    cursors = CollabState.read(state_two.filepath).cursors

    assert cursors[PEER] == export.instant
    assert cursors['http://other:9137'] == other


def test_import_cursor_never_moves_back(tmp_path, peers):
    """Test that a delta carrying an older instant, such as a retried push, cannot regress the cursor."""
    backend_one, state_one = peers('one')
    backend_two, state_two = peers('two')
    seal_calculation(backend_one, 'sealed')

    filepath = tmp_path / 'delta.aiida'
    export = export_full(filepath, state=state_one, backend=backend_one, cursor=None)
    newer = timezone.now()
    state_two.cursors[PEER] = newer
    state_two.save()

    import_delta(filepath, state=state_two, backend=backend_two, extras_mode='local', peer=PEER, instant=export.instant)

    assert CollabState.read(state_two.filepath).cursors[PEER] == newer


def test_import_include_deleted(tmp_path, peers):
    """Test that ``include_deleted`` imports a tombstoned node again and drops its tombstone."""
    backend_one, state_one = peers('one')
    backend_two, state_two = peers('two')
    calculation = seal_calculation(backend_one, 'sealed')

    filepath = tmp_path / 'delta.aiida'
    export = export_full(filepath, state=state_one, backend=backend_one, cursor=None)
    state_two.tombstones.add(calculation.uuid)
    state_two.save()

    report = import_delta(
        filepath,
        state=state_two,
        backend=backend_two,
        extras_mode='local',
        peer=PEER,
        instant=export.instant,
        include_deleted=True,
    )

    assert calculation.uuid in report.uuids
    assert report.skipped == []
    assert orm.QueryBuilder(backend=backend_two).append(orm.Node, filters={'uuid': calculation.uuid}).count() == 1
    assert CollabState.read(state_two.filepath).tombstones == set()


def test_chain_convergence(tmp_path, peers):
    """Test that provenance produced on C and relayed through B reaches A by a pull from B alone.

    B imported C's nodes long after their production mtime — later than A's cursor for B — so the mtime term of
    B's delta misses them: only the union with B's own import events makes them travel.
    """
    backend_a, state_a = peers('a')
    backend_b, state_b = peers('b')
    backend_c, state_c = peers('c')
    produced = seal_calculation(backend_c, 'produced-on-c')

    # A first syncs with an empty B, so A's cursor for B postdates the production of C's nodes.
    empty = export_full(tmp_path / 'b-empty.aiida', state=state_b, backend=backend_b, cursor=None)
    import_delta(
        tmp_path / 'b-empty.aiida',
        state=state_a,
        backend=backend_a,
        extras_mode='local',
        peer='b',
        instant=empty.instant,
    )

    # B pulls from C; the imported nodes keep their original, old timestamps.
    from_c = export_full(tmp_path / 'c.aiida', state=state_c, backend=backend_c, cursor=None)
    import_delta(
        tmp_path / 'c.aiida',
        state=state_b,
        backend=backend_b,
        extras_mode='local',
        peer='c',
        instant=from_c.instant,
    )

    # A pulls from B, presenting its cursor; the import event of B is what carries C's nodes over.
    cursor = CollabState.read(state_a.filepath).cursors['b']
    export = export_full(
        tmp_path / 'b.aiida', state=CollabState.read(state_b.filepath), backend=backend_b, cursor=cursor
    )
    import_delta(
        tmp_path / 'b.aiida',
        state=state_a,
        backend=backend_a,
        extras_mode='local',
        peer='b',
        instant=export.instant,
    )

    assert linked_uuids(produced) <= set(export.uuids)
    assert orm.QueryBuilder(backend=backend_a).append(orm.Node, filters={'uuid': produced.uuid}).count() == 1


def test_export_subtracts_claim(tmp_path, peers):
    """Test that a pull from a second peer transfers none of the nodes named in the requester's claim."""
    backend_a, state_a = peers('a')
    backend_b, state_b = peers('b')
    backend_c, state_c = peers('c')
    seal_calculation(backend_a, 'shared')

    # B holds the same nodes as A, as it would after pulling from A.
    export = export_full(tmp_path / 'a.aiida', state=state_a, backend=backend_a, cursor=None)
    import_delta(
        tmp_path / 'a.aiida',
        state=state_b,
        backend=backend_b,
        extras_mode='local',
        peer='a',
        instant=export.instant,
    )

    # C pulls from A, then from B in the same round, claiming what it just imported.
    import_delta(
        tmp_path / 'a.aiida',
        state=state_c,
        backend=backend_c,
        extras_mode='local',
        peer='a',
        instant=export.instant,
    )
    state_c = CollabState.read(state_c.filepath)
    claim = state_c.imported_uuids_since(None)

    second = export_full(
        tmp_path / 'b.aiida', state=CollabState.read(state_b.filepath), backend=backend_b, cursor=None, claim=claim
    )

    assert second.uuids == []


@pytest.mark.parametrize('reentry', ('relayed', 'touched'))
def test_a_tombstoned_node_that_re_enters_the_delta_is_refused_at_the_diff(tmp_path, peers, reentry):
    """Test that a deleted node the sender's delta reaches again is refused at the diff and cut, with its links.

    The two ways a long-deleted node re-enters a delta whatever the cursor: the sender *imported* it from a third
    peer since the cursor, which no mtime bounds, or something touched it there and moved its mtime past the
    cursor — setting an extra of its own is enough. The claim used to carry every tombstone to keep them out of
    the start set; the receiver refusing them at the manifest diff is bounded by the delta instead of by the whole
    history, and on this graph nothing travels to be thrown away at the import.
    """
    backend, state = peers('sender')
    backend_receiver, state_receiver = peers('receiver')
    calculation = seal_calculation(backend, 'shared')
    output = calculation.base.links.get_outgoing().one().node

    # The receiver holds the input it was run on, and deleted the calculation, which took its output with it.
    export = export_full(tmp_path / 'first.aiida', state=state, backend=backend, cursor=None)
    import_delta(
        tmp_path / 'first.aiida',
        state=state_receiver,
        backend=backend_receiver,
        extras_mode='local',
        peer=PEER,
        instant=export.instant,
    )
    delete_nodes(backend_receiver, [calculation.uuid, output.uuid])
    state_receiver = CollabState.read(state_receiver.filepath)
    state_receiver.tombstones.update({calculation.uuid, output.uuid})
    state_receiver.save()

    cursor = timezone.now()

    if reentry == 'relayed':
        state.events.append(
            CollabEvent(
                time=timezone.now(), direction='pull', peer=PEER, uuids=sorted(linked_uuids(calculation)), size=1
            )
        )
    else:
        calculation.base.extras.set('note', 'edited after the cursor')

    delta = compute_delta(
        state=state, backend=backend, cursor=cursor, claim=state_receiver.imported_uuids_since(cursor)
    )
    missing = set(missing_uuids(backend_receiver, delta.uuids))
    refuse = missing & state_receiver.tombstones
    want = missing - refuse

    assert {calculation.uuid, output.uuid} <= set(delta.uuids), 'the delta reaches the deleted nodes again'
    assert refuse == {calculation.uuid, output.uuid}
    assert want == set()

    export = export_delta(tmp_path / 'second.aiida', delta=delta, backend=backend, want=want, refuse=refuse)

    assert export.uuids == []


def test_a_refused_node_the_wanted_provenance_requires_rides_anyway(tmp_path, peers):
    """Test that the cut closes over a refused node a wanted one needs, and drops the links to the rest.

    Both traps of subtracting a refusal naively, on one graph. The refused *input* of a wanted calculation cannot
    simply go: the receiver's own import re-filter closes over it under the same rules and would import it back,
    so leaving it out would only make the archive link to a node that exists nowhere. The refused *creator* of a
    wanted output genuinely does not travel — and its CREATE link must go with it, or the receiver would refuse
    the whole delta over a boundary endpoint it cannot resolve.
    """
    backend, state = peers('sender')
    producer = seal_calculation(backend, 'producer')
    shared = producer.base.links.get_outgoing().one().node
    consumer = seal_calculation_with(backend, 'consumer', inputs=[shared])
    result = consumer.base.links.get_outgoing().one().node

    delta = compute_delta(state=state, backend=backend, cursor=None)
    refuse = {shared.uuid, producer.uuid}
    want = {consumer.uuid, result.uuid}
    required = required_refused(delta=delta, backend=backend, want=want, refuse=refuse)

    assert required == {shared.uuid}, 'the input of a wanted calculation is required; the creator of an output is not'

    export = export_delta(tmp_path / 'delta.aiida', delta=delta, backend=backend, want=want | required, refuse=refuse)

    assert set(export.uuids) == want | required
    assert _boundary_links(export.filepath) == [], 'the CREATE link of the refused producer has to go with it'


def test_export_claimed_ancestor_still_rides(tmp_path, peers):
    """Test that the claim cannot break provenance closure: a claimed ancestor a new node needs is exported anyway.

    Phase 7 archives stay closed; only whole claimed subgraphs are dropped. Trimming the transfer of required
    ancestors is phase 8.
    """
    backend_a, state_a = peers('a')
    backend_b, state_b = peers('b')
    first = seal_calculation(backend_a, 'first')

    export = export_full(tmp_path / 'a.aiida', state=state_a, backend=backend_a, cursor=None)
    import_delta(
        tmp_path / 'a.aiida',
        state=state_b,
        backend=backend_b,
        extras_mode='local',
        peer='a',
        instant=export.instant,
    )

    # A builds new work on the output B already holds.
    output = first.base.links.get_outgoing().one().node
    second = orm.CalcJobNode(backend=backend_a, label='second')
    second.base.links.add_incoming(output, link_type=LinkType.INPUT_CALC, link_label='input')
    second.store()
    second.seal()

    state_b = CollabState.read(state_b.filepath)
    claim = state_b.imported_uuids_since(None)
    delta = export_full(
        tmp_path / 'a-second.aiida', state=state_a, backend=backend_a, cursor=export.instant, claim=claim
    )
    report = import_delta(
        tmp_path / 'a-second.aiida',
        state=state_b,
        backend=backend_b,
        extras_mode='local',
        peer='a',
        instant=delta.instant,
    )

    assert output.uuid in delta.uuids, 'the claimed input is required by the new calculation, so it must ride'
    assert second.uuid in report.uuids

    imported = load_node(backend_b, second.uuid)
    assert imported.base.links.get_incoming().one().node.uuid == output.uuid


def graph_links(backend):
    """Return every link of ``backend`` as UUID quadruples."""
    query = (
        orm.QueryBuilder(backend=backend)
        .append(orm.Node, tag='incoming', project='uuid')
        .append(orm.Node, with_incoming='incoming', project='uuid', edge_project=['type', 'label'])
    )

    return {tuple(row) for row in query.all()}


def heavy_calculation(backend):
    """Build a calculation with a heavy direct input, whose output a restart will reuse."""
    heavy = orm.Int(1, backend=backend)
    heavy.base.repository.put_object_from_bytes(b'a-heavy-pseudopotential' * 100, 'upf')
    heavy.store()

    first = seal_calculation_with(backend, 'first', inputs=[heavy])

    return heavy, first, first.base.links.get_outgoing().one().node


def restart(backend, heavy, output):
    """Seal the restart: a second calculation reusing the first one's output and its heavy direct input."""
    return seal_calculation_with(backend, 'second', inputs=[heavy, output])


def seal_calculation_with(backend, label, inputs):
    """Store and seal a calculation with the given input nodes and one fresh output."""
    calculation = orm.CalcJobNode(backend=backend, label=label)

    for index, node in enumerate(inputs):
        calculation.base.links.add_incoming(node, link_type=LinkType.INPUT_CALC, link_label=f'input_{index}')

    # Distinct per calculation, since repository objects are content-addressed: two calculations writing the same
    # bytes share one key, and "the wanted node brought its own object" would then be true of the held one's.
    calculation.base.repository.put_object_from_bytes(f'the input of {label}\n'.encode(), 'aiida.in')
    calculation.store()
    outputs = orm.Int(2, backend=backend)
    outputs.base.links.add_incoming(calculation, link_type=LinkType.CREATE, link_label='result')
    outputs.store()
    calculation.seal()

    return calculation


def archive_repo_keys(filepath):
    """Return the repository object keys contained in an archive."""
    from aiida.tools.archive.abstract import get_format

    with get_format().open(filepath, mode='r') as reader:
        return set(orm.Node.get_collection(reader.get_backend()).iter_repo_keys())


def test_vanished_nodes_reports_only_what_is_gone(peers):
    """Test that a deleted node is reported gone and a held one is not.

    Asking by UUID is what keeps SQLite's rowid reuse out of the answer, and no test can pin that: the key-asking
    version took the delta as an argument, so the signature is the guard.
    """
    from aiida.storage.sqlite_zip.models import DbNode
    from aiida.tools.collab.sync import vanished_nodes

    backend, _ = peers('one')
    gone = orm.Int(1, backend=backend).store()
    held = orm.Int(2, backend=backend).store()
    gone_uuid = gone.uuid

    with backend.transaction() as session:
        session.query(DbNode).filter(DbNode.id == gone.pk).delete(synchronize_session=False)

    assert vanished_nodes(backend, {gone_uuid, held.uuid}) == {gone_uuid}


def test_thin_export_ships_only_missing(tmp_path, peers):
    """Test that the second sync of a restart chain transfers neither rows nor repository files already held.

    The second calculation reuses the first one's output and its heavy direct input; both are ancestors of the
    new work, so a provenance-closed archive would re-ship them — the thin one must not.
    """
    backend_one, state_one = peers('one')
    backend_two, state_two = peers('two')
    heavy, _first, output = heavy_calculation(backend_one)

    # First sync: everything travels, including the heavy repository object.
    export = export_full(tmp_path / 'first.aiida', state=state_one, backend=backend_one, cursor=None)
    import_delta(
        tmp_path / 'first.aiida',
        state=state_two,
        backend=backend_two,
        extras_mode='local',
        peer=PEER,
        instant=export.instant,
    )

    heavy_keys = archive_repo_keys(tmp_path / 'first.aiida')
    assert heavy_keys, 'the first sync should carry the heavy repository object'

    # Second sync: the receiver diffs the manifest and requests only what it lacks.
    restart(backend_one, heavy, output)
    delta = compute_delta(state=state_one, backend=backend_one, cursor=None)
    missing = missing_uuids(backend_two, delta.uuids)
    export = export_delta(tmp_path / 'second.aiida', delta=delta, backend=backend_one, want=set(missing))

    assert set(export.uuids) == set(missing)
    assert set(_archive_node_uuids(tmp_path / 'second.aiida')) == set(missing)
    assert heavy.uuid not in export.uuids

    second_keys = archive_repo_keys(tmp_path / 'second.aiida')

    # Both halves, because either alone is satisfied by an archive with no repository objects whatsoever: the
    # thin export has to leave out what the receiver holds *and* carry what the wanted nodes brought with them.
    assert second_keys, 'the restart brought a repository object of its own, which has to travel with it'
    assert second_keys.isdisjoint(heavy_keys)

    report = import_delta(
        tmp_path / 'second.aiida',
        state=state_two,
        backend=backend_two,
        extras_mode='local',
        peer=PEER,
        instant=export.instant,
    )

    assert set(report.uuids) == set(missing)


def _archive_node_uuids(filepath):
    from aiida.tools.collab.sync import _archive_uuids

    return _archive_uuids(filepath)


def test_thin_import_graph_equality(tmp_path, peers):
    """Test that two thin syncs land the same graph — nodes and links — as one full-closure import."""
    backend_one, state_one = peers('one')
    backend_thin, state_thin = peers('thin')
    backend_full, state_full = peers('full')
    heavy, _first, output = heavy_calculation(backend_one)

    # The thin receiver syncs twice, the second time receiving only what it lacks plus boundary links.
    export = export_full(tmp_path / 'one.aiida', state=state_one, backend=backend_one, cursor=None)
    import_delta(
        tmp_path / 'one.aiida',
        state=state_thin,
        backend=backend_thin,
        extras_mode='local',
        peer=PEER,
        instant=export.instant,
    )

    restart(backend_one, heavy, output)
    delta = compute_delta(state=state_one, backend=backend_one, cursor=None)
    missing = missing_uuids(backend_thin, delta.uuids)
    export = export_delta(tmp_path / 'two.aiida', delta=delta, backend=backend_one, want=set(missing))
    import_delta(
        tmp_path / 'two.aiida',
        state=state_thin,
        backend=backend_thin,
        extras_mode='local',
        peer=PEER,
        instant=export.instant,
    )

    # The full receiver imports the whole closure in one archive.
    export = export_delta(tmp_path / 'full.aiida', delta=delta, backend=backend_one)
    import_delta(
        tmp_path / 'full.aiida',
        state=state_full,
        backend=backend_full,
        extras_mode='local',
        peer=PEER,
        instant=export.instant,
    )

    def node_uuids(backend):
        return set(orm.QueryBuilder(backend=backend).append(orm.Node, project='uuid').all(flat=True))

    assert node_uuids(backend_thin) == node_uuids(backend_full)
    assert graph_links(backend_thin) == graph_links(backend_full)


def test_thin_import_missing_endpoint_aborts_and_recovers(tmp_path, peers):
    """Test that a thin delta linking to a node the receiver holds nowhere aborts clean, and the next sync heals."""
    from aiida.common.exceptions import IntegrityError

    backend_one, state_one = peers('one')
    backend_two, state_two = peers('two')
    heavy, _first, output = heavy_calculation(backend_one)
    second = restart(backend_one, heavy, output)

    # A thin delta cut as if the receiver held the first calculation, imported into a profile that does not.
    delta = compute_delta(state=state_one, backend=backend_one, cursor=None)
    want = {second.uuid, second.base.links.get_outgoing().one().node.uuid}
    export = export_delta(tmp_path / 'hole.aiida', delta=delta, backend=backend_one, want=want)

    with pytest.raises(IntegrityError, match='neither in the archive nor in this profile'):
        import_delta(
            tmp_path / 'hole.aiida',
            state=state_two,
            backend=backend_two,
            extras_mode='local',
            peer=PEER,
            instant=export.instant,
        )

    assert node_count(backend_two) == 0, 'nothing should have been imported'
    assert not state_two.filepath.exists(), 'no event or cursor should have been recorded'

    # The next negotiation diffs the manifest against the receiver, whose holes are now part of the request.
    missing = missing_uuids(backend_two, delta.uuids)
    export = export_delta(tmp_path / 'heal.aiida', delta=delta, backend=backend_one, want=set(missing))
    import_delta(
        tmp_path / 'heal.aiida',
        state=state_two,
        backend=backend_two,
        extras_mode='local',
        peer=PEER,
        instant=export.instant,
    )

    assert node_count(backend_two) == len(delta.uuids)
    assert graph_links(backend_two) == graph_links(backend_one)


def test_boundary_link_to_reimported_tombstoned_node(tmp_path, peers):
    """Test that a boundary link is written when its tombstoned endpoint is re-imported by the same delta.

    The receiver deleted the output X of a kept calculation P; the sender then built new work on X, so provenance
    closure re-delivers it (tombstone loses to provenance). The CREATE link P -> X crosses the thin boundary and
    must be restored — a tombstoned endpoint is obsolete only while it is absent.
    """
    backend_one, state_one = peers('one')
    backend_two, state_two = peers('two')
    creator = seal_calculation(backend_one, 'creator')
    deleted = creator.base.links.get_outgoing().one().node

    export = export_full(tmp_path / 'first.aiida', state=state_one, backend=backend_one, cursor=None)
    import_delta(
        tmp_path / 'first.aiida',
        state=state_two,
        backend=backend_two,
        extras_mode='local',
        peer=PEER,
        instant=export.instant,
    )

    # The receiver deletes X and records its tombstone; the creator stays.
    delete_nodes(backend_two, [deleted.uuid])
    state_two = CollabState.read(state_two.filepath)
    state_two.tombstones.add(deleted.uuid)
    state_two.save()

    # The sender builds new work on X, then the receiver syncs, refusing its tombstone at the diff as usual.
    consumer = seal_calculation_with(backend_one, 'consumer', inputs=[deleted])

    cursor = state_two.cursors[PEER]
    claim = state_two.imported_uuids_since(cursor)
    delta = compute_delta(state=state_one, backend=backend_one, cursor=cursor, claim=claim)
    missing = set(missing_uuids(backend_two, delta.uuids))
    refuse = missing & state_two.tombstones
    want = missing - refuse

    assert deleted.uuid in refuse, 'the receiver deleted X, so it does not ask for it'

    required = required_refused(delta=delta, backend=backend_one, want=want, refuse=refuse)

    assert deleted.uuid in required, 'the wanted consumer requires X, so the sender puts it back in the cut'

    export = export_delta(
        tmp_path / 'second.aiida', delta=delta, backend=backend_one, want=want | required, refuse=refuse
    )
    import_delta(
        tmp_path / 'second.aiida',
        state=state_two,
        backend=backend_two,
        extras_mode='local',
        peer=PEER,
        instant=export.instant,
    )

    assert (creator.uuid, deleted.uuid, 'create', 'result') in graph_links(backend_two)
    assert orm.QueryBuilder(backend=backend_two).append(orm.Node, filters={'uuid': consumer.uuid}).count() == 1
    assert CollabState.read(state_two.filepath).pending_links == []


def test_pending_boundary_links_heal_on_next_import(tmp_path, peers, monkeypatch):
    """Test that boundary links journalled before a crashed import are written by the next one."""
    from aiida.tools.collab import sync

    backend_one, state_one = peers('one')
    backend_two, state_two = peers('two')
    heavy, _first, output = heavy_calculation(backend_one)

    export = export_full(tmp_path / 'one.aiida', state=state_one, backend=backend_one, cursor=None)
    import_delta(
        tmp_path / 'one.aiida',
        state=state_two,
        backend=backend_two,
        extras_mode='local',
        peer=PEER,
        instant=export.instant,
    )

    # The crash window: the import of the thin delta lands its nodes, but dies before the boundary links.
    monkeypatch.setattr(sync, '_write_boundary_links', lambda backend, pending, tombstones: [])

    restart(backend_one, heavy, output)
    delta = compute_delta(state=state_one, backend=backend_one, cursor=None)
    missing = missing_uuids(backend_two, delta.uuids)
    export = export_delta(tmp_path / 'two.aiida', delta=delta, backend=backend_one, want=set(missing))
    import_delta(
        tmp_path / 'two.aiida',
        state=state_two,
        backend=backend_two,
        extras_mode='local',
        peer=PEER,
        instant=export.instant,
    )

    monkeypatch.undo()

    assert graph_links(backend_two) != graph_links(backend_one)
    assert CollabState.read(state_two.filepath).pending_links, 'the boundary links should still be journalled'

    # Any following import retries the journal; an empty delta suffices.
    empty = compute_delta(state=state_one, backend=backend_one, cursor=timezone.now())
    export = export_delta(tmp_path / 'empty.aiida', delta=empty, backend=backend_one)
    import_delta(
        tmp_path / 'empty.aiida',
        state=CollabState.read(state_two.filepath),
        backend=backend_two,
        extras_mode='local',
        peer=PEER,
        instant=export.instant,
    )

    assert graph_links(backend_two) == graph_links(backend_one)
    assert CollabState.read(state_two.filepath).pending_links == []


def test_thin_import_sibling_boundary_links_abort(tmp_path, peers):
    """Test that two exclusive boundary links onto the same held node in one delta abort the import.

    Each link alone passes against the local graph — the held node has no creator — so the check must also hold
    the links of a delta against each other, exactly as sequential deltas would be.
    """
    from aiida.common.exceptions import IntegrityError
    from aiida.tools.collab.sync import _write_thin_archive

    backend_one, _state_one = peers('one')
    backend_two, state_two = peers('two')

    orphan = orm.Int(1, backend=backend_two).store()

    impostors = []

    for label in ('impostor-one', 'impostor-two'):
        impostor = orm.CalcJobNode(backend=backend_one, label=label).store()
        impostor.seal()
        impostors.append(impostor)

    _write_thin_archive(
        tmp_path / 'siblings.aiida',
        backend=backend_one,
        node_pks={impostor.pk for impostor in impostors},
        links=[],
        boundary=[[impostor.uuid, orphan.uuid, 'create', 'result'] for impostor in impostors],
        groups_mode='local',
    )

    with pytest.raises(IntegrityError, match='second incoming link'):
        import_delta(
            tmp_path / 'siblings.aiida',
            state=state_two,
            backend=backend_two,
            extras_mode='local',
            peer=PEER,
            instant=timezone.now(),
        )

    assert node_count(backend_two) == 1, 'nothing should have been imported'


def test_thin_import_same_source_relabeled_link_aborts(tmp_path, peers):
    """Test that a second exclusive link from the same source under a different label aborts.

    The exclusive indegree is one full stop — source and label do not matter — so only the identical quadruple
    (an idempotent re-delivery) may pass against an existing link.
    """
    from aiida.common.exceptions import IntegrityError
    from aiida.tools.collab.sync import _write_thin_archive

    backend_one, state_one = peers('one')
    backend_two, state_two = peers('two')
    creator = seal_calculation(backend_one, 'creator')
    created = creator.base.links.get_outgoing().one().node

    export = export_full(tmp_path / 'first.aiida', state=state_one, backend=backend_one, cursor=None)
    import_delta(
        tmp_path / 'first.aiida',
        state=state_two,
        backend=backend_two,
        extras_mode='local',
        peer=PEER,
        instant=export.instant,
    )

    filler = orm.CalcJobNode(backend=backend_one, label='filler').store()
    filler.seal()
    _write_thin_archive(
        tmp_path / 'relabel.aiida',
        backend=backend_one,
        node_pks={filler.pk},
        links=[],
        boundary=[[creator.uuid, created.uuid, 'create', 'result2']],
        groups_mode='local',
    )

    count = node_count(backend_two)

    with pytest.raises(IntegrityError, match='second incoming link'):
        import_delta(
            tmp_path / 'relabel.aiida',
            state=CollabState.read(state_two.filepath),
            backend=backend_two,
            extras_mode='local',
            peer=PEER,
            instant=timezone.now(),
        )

    assert node_count(backend_two) == count, 'nothing should have been imported'


def test_thin_import_self_link_aborts(tmp_path, peers):
    """Test that a boundary link from a held node to itself aborts: no real graph link can produce one."""
    from aiida.common.exceptions import IntegrityError
    from aiida.tools.collab.sync import _write_thin_archive

    backend_one, _state_one = peers('one')
    backend_two, state_two = peers('two')

    held = orm.Int(1, backend=backend_two).store()
    filler = orm.CalcJobNode(backend=backend_one, label='filler').store()
    filler.seal()

    _write_thin_archive(
        tmp_path / 'loop.aiida',
        backend=backend_one,
        node_pks={filler.pk},
        links=[],
        boundary=[[held.uuid, held.uuid, 'create', 'loop']],
        groups_mode='local',
    )

    with pytest.raises(IntegrityError, match='to itself'):
        import_delta(
            tmp_path / 'loop.aiida',
            state=state_two,
            backend=backend_two,
            extras_mode='local',
            peer=PEER,
            instant=timezone.now(),
        )

    assert node_count(backend_two) == 1, 'nothing should have been imported'


def test_thin_import_boundary_invariant_aborts(tmp_path, peers):
    """Test that a boundary link giving a held data node a second creator aborts before anything lands.

    From one coherent sender such a link cannot arise, so one arriving means the sender's graph diverged — a
    hostile or corrupted peer — and the boundary insertion path, which bypasses the archive importer's
    validation, must not write it.
    """
    from aiida.common.exceptions import IntegrityError
    from aiida.tools.collab.sync import _write_thin_archive

    backend_one, state_one = peers('one')
    backend_two, state_two = peers('two')
    creator = seal_calculation(backend_one, 'creator')
    created = creator.base.links.get_outgoing().one().node

    export = export_full(tmp_path / 'first.aiida', state=state_one, backend=backend_one, cursor=None)
    import_delta(
        tmp_path / 'first.aiida',
        state=state_two,
        backend=backend_two,
        extras_mode='local',
        peer=PEER,
        instant=export.instant,
    )

    # A "sender" whose graph diverged: a fresh calculation claiming to have created the already-held node.
    impostor = orm.CalcJobNode(backend=backend_one, label='impostor').store()
    impostor.seal()
    _write_thin_archive(
        tmp_path / 'diverged.aiida',
        backend=backend_one,
        node_pks={impostor.pk},
        links=[],
        boundary=[[impostor.uuid, created.uuid, 'create', 'result']],
        groups_mode='local',
    )

    count = node_count(backend_two)

    with pytest.raises(IntegrityError, match='second incoming link'):
        import_delta(
            tmp_path / 'diverged.aiida',
            state=CollabState.read(state_two.filepath),
            backend=backend_two,
            extras_mode='local',
            peer=PEER,
            instant=timezone.now(),
        )

    assert node_count(backend_two) == count, 'nothing should have been imported'
    assert CollabState.read(state_two.filepath).pending_links == [], 'nothing should have been journalled'


def make_computer(backend, label):
    return orm.Computer(
        label=label, hostname='localhost', transport_type='core.local', scheduler_type='core.direct', backend=backend
    ).store()


def seal_cached_calculation(backend, computer):
    """Return a sealed, finished calculation that is a valid cache source, identical on every call."""
    from aiida.engine import ProcessState

    inputs = orm.Int(1, backend=backend).store()
    calculation = orm.CalcJobNode(
        backend=backend, computer=computer, process_type='aiida.calculations:core.arithmetic.add'
    )
    calculation.base.links.add_incoming(inputs, link_type=LinkType.INPUT_CALC, link_label='term')
    calculation.base.repository.put_object_from_bytes(b'1 + 1', 'aiida.in')
    calculation.set_process_state(ProcessState.FINISHED)
    calculation.set_exit_status(0)
    calculation.store()
    calculation.seal()

    return calculation


def deliver_computer(filepath, *, sender, sender_state, receiver, receiver_state):
    """Import a first, unmapped delta, which is how the computer of the sender arrives in the receiver and is marked.

    Every scenario about a mapped import starts one delta earlier than the mapping does: a mapping may only name a
    computer the receiving profile holds, and an import is the only thing that puts a peer's computer there.

    :returns: the UUIDs the receiver holds afterwards, which is what the next delta is claimed against.
    """
    export = export_full(filepath, state=sender_state, backend=sender, cursor=None)
    import_delta(
        filepath, state=receiver_state, backend=receiver, extras_mode='local', peer=PEER, instant=export.instant
    )

    return set(export.uuids)


def test_a_computer_the_tombstone_refilter_kept_out_is_not_marked(tmp_path, peers):
    """Test that a computer the import never created, because its calculation was tombstoned, is left alone.

    The journal names the computers a delta was *about* to create, which is one more than it created whenever the
    re-filter took the only node carrying one out of the archive. Nothing lands, and the marking has to pass over
    that UUID rather than look it up — after the archive has already committed.
    """
    backend_one, state_one = peers('one')
    backend_two, state_two = peers('two')
    calculation = seal_cached_calculation(backend_one, make_computer(backend_one, 'lumi'))

    filepath = tmp_path / 'delta.aiida'
    export = export_full(filepath, state=state_one, backend=backend_one, cursor=None)
    state_two.tombstones.add(calculation.uuid)

    import_delta(filepath, state=state_two, backend=backend_two, extras_mode='local', peer=PEER, instant=export.instant)

    assert orm.QueryBuilder(backend=backend_two).append(orm.Computer).count() == 0
    assert CollabState.read(state_two.filepath).pending_computers == {}, 'a computer that never landed stays pending'


def test_marking_a_computer_twice_leaves_it_alone(peers):
    """Test that a journal entry outliving the rename it asked for does not collide with the row it renamed.

    The journal is cleared when the state is saved, which is after the renames have committed, so a death or an
    IO error in between leaves an entry naming a row that already carries the marker — as does a user who
    relabels by hand what a crashed import left unmarked. The next delta carrying another `lumi` must be
    deduplicated around that row rather than handed its label, which the unique label column would refuse.
    """
    from aiida.tools.collab.sync import _mark_imported_computers

    backend, _ = peers('one')
    # The pass walks its rows in UUID order, so the labels are assigned by that order rather than at creation:
    # the row wanting the taken label has to be named first for the collision to be reached at all, and a test
    # that leaves that to chance catches the regression it exists for only half the time.
    arrived, marked = sorted((make_computer(backend, 'one'), make_computer(backend, 'two')), key=lambda c: c.uuid)
    arrived.label = 'lumi'
    marked.label = 'lumi@collab'

    _mark_imported_computers(backend, {marked.uuid: 'lumi', arrived.uuid: 'lumi'})

    labels = orm.QueryBuilder(backend=backend).append(orm.Computer, project=['uuid', 'label']).all()

    assert dict(labels) == {marked.uuid: 'lumi@collab', arrived.uuid: 'lumi-2@collab'}


def test_remap_cache_hit(tmp_path, peers):
    """Test that a mapped calculation carries the hash of its local twin and is found by the caching engine."""
    backend_one, state_one = peers('one')
    backend_two, state_two = peers('two')
    lumi = make_computer(backend_one, 'lumi')
    seal_cached_calculation(backend_one, lumi)

    held = deliver_computer(
        tmp_path / 'first.aiida',
        sender=backend_one,
        sender_state=state_one,
        receiver=backend_two,
        receiver_state=state_two,
    )
    calculation = seal_cached_calculation(backend_one, lumi)

    filepath = tmp_path / 'delta.aiida'
    export = export_full(filepath, state=state_one, backend=backend_one, cursor=None, claim=held)

    leonardo = make_computer(backend_two, 'leonardo')
    import_delta(
        filepath,
        state=state_two,
        backend=backend_two,
        extras_mode='local',
        peer=PEER,
        instant=export.instant,
        computer_map={'lumi@collab': 'leonardo'},
    )

    twin = seal_cached_calculation(backend_two, leonardo)
    imported = load_node(backend_two, calculation.uuid)

    assert imported.base.caching.get_hash() == twin.base.caching.compute_hash()
    assert calculation.uuid in {node.uuid for node in twin.base.caching.get_all_same_nodes()}


def test_relabelling_a_computer_leaves_the_hash_of_its_calculations_alone(peers):
    """Test that the hash of a calculation is bound to the UUID of its computer and not to its label.

    The whole mapping feature rests on this: marking an imported computer ``@collab`` would otherwise turn every
    calculation that ran on it into a cache miss, in every collab, silently.
    """
    backend, _ = peers('one')
    computer = make_computer(backend, 'lumi')
    calculation = seal_cached_calculation(backend, computer)
    before = calculation.base.caching.compute_hash()

    computer.label = 'lumi@collab'

    assert load_node(backend, calculation.uuid).base.caching.compute_hash() == before


def test_remap_cache_miss_without_mapping(tmp_path, peers):
    """Test that without a mapping an imported calculation carries no hash and is not a cache hit."""
    backend_one, state_one = peers('one')
    backend_two, state_two = peers('two')
    calculation = seal_cached_calculation(backend_one, make_computer(backend_one, 'lumi'))

    filepath = tmp_path / 'delta.aiida'
    export = export_full(filepath, state=state_one, backend=backend_one, cursor=None)

    leonardo = make_computer(backend_two, 'leonardo')
    import_delta(filepath, state=state_two, backend=backend_two, extras_mode='local', peer=PEER, instant=export.instant)

    twin = seal_cached_calculation(backend_two, leonardo)
    imported = load_node(backend_two, calculation.uuid)

    assert imported.base.caching.get_hash() is None
    assert calculation.uuid not in {node.uuid for node in twin.base.caching.get_all_same_nodes()}


def test_remap_leaves_node_unchanged(tmp_path, peers):
    """Test that remapping writes only the hash extra: UUID, attributes and repository content are as exported."""
    from aiida.orm.nodes.caching import NodeCaching

    backend_one, state_one = peers('one')
    backend_two, state_two = peers('two')
    lumi = make_computer(backend_one, 'lumi')
    seal_cached_calculation(backend_one, lumi)

    held = deliver_computer(
        tmp_path / 'first.aiida',
        sender=backend_one,
        sender_state=state_one,
        receiver=backend_two,
        receiver_state=state_two,
    )
    calculation = seal_cached_calculation(backend_one, lumi)

    filepath = tmp_path / 'delta.aiida'
    export = export_full(filepath, state=state_one, backend=backend_one, cursor=None, claim=held)

    make_computer(backend_two, 'leonardo')
    import_delta(
        filepath,
        state=state_two,
        backend=backend_two,
        extras_mode='local',
        peer=PEER,
        instant=export.instant,
        computer_map={'lumi@collab': 'leonardo'},
    )

    imported = load_node(backend_two, calculation.uuid)

    assert imported.uuid == calculation.uuid
    assert imported.base.attributes.all == calculation.base.attributes.all
    assert imported.base.repository.hash() == calculation.base.repository.hash()
    assert set(imported.base.extras.keys()) == {NodeCaching._HASH_EXTRA_KEY, COLLAB_PEER_KEY}
    # A bumped mtime would re-enter the node into the delta of the next export, echoing it back to the peer.
    assert imported.mtime == calculation.mtime


def test_remap_unknown_local_computer(tmp_path, peers):
    """Test that a mapping to a local computer this profile does not have aborts before anything is imported.

    The peer half of the mapping is deliberately satisfiable — the computer was delivered by the first delta — so
    that what fails is the local half and nothing else.
    """
    from aiida.common.exceptions import ConfigurationError

    backend_one, state_one = peers('one')
    backend_two, state_two = peers('two')
    lumi = make_computer(backend_one, 'lumi')
    seal_cached_calculation(backend_one, lumi)

    held = deliver_computer(
        tmp_path / 'first.aiida',
        sender=backend_one,
        sender_state=state_one,
        receiver=backend_two,
        receiver_state=state_two,
    )
    seal_cached_calculation(backend_one, lumi)

    filepath = tmp_path / 'delta.aiida'
    export = export_full(filepath, state=state_one, backend=backend_one, cursor=None, claim=held)

    with pytest.raises(ConfigurationError, match=r'collab\.computer_map'):
        import_delta(
            filepath,
            state=state_two,
            backend=backend_two,
            extras_mode='local',
            peer=PEER,
            instant=export.instant,
            computer_map={'lumi@collab': 'missing'},
        )

    assert node_count(backend_two) == len(held), 'the import should have been refused before anything landed'
    assert len(CollabState.read(state_two.filepath).events) == 1, 'the refused import recorded an event'


def test_apply_computer_map_retroactively(tmp_path, peers):
    """Test that applying a mapping after the import writes the twin hash onto already-imported calculations."""
    backend_one, state_one = peers('one')
    backend_two, state_two = peers('two')
    calculation = seal_cached_calculation(backend_one, make_computer(backend_one, 'lumi'))

    filepath = tmp_path / 'delta.aiida'
    export = export_full(filepath, state=state_one, backend=backend_one, cursor=None)

    leonardo = make_computer(backend_two, 'leonardo')
    import_delta(filepath, state=state_two, backend=backend_two, extras_mode='local', peer=PEER, instant=export.instant)

    assert load_node(backend_two, calculation.uuid).base.caching.get_hash() is None

    count = apply_computer_map(backend_two, {'lumi@collab': 'leonardo'})
    twin = seal_cached_calculation(backend_two, leonardo)

    assert count == 1
    assert load_node(backend_two, calculation.uuid).base.caching.get_hash() == twin.base.caching.compute_hash()


def sync_pull(
    sender, receiver, filepath, peer, groups_mode='local', receiver_groups_mode=None, receiver_extras_mode='sync'
):
    """Pull from one profile into another as ``verdi collab pull`` does under the ``sync`` extras policy.

    Both sides talk through the same functions the endpoint and the client wire together: the sender offers the
    mtimes of the shared nodes it may have edited and the memberships it gained, the receiver keeps the extras it
    holds an older version of and the memberships it can apply, and only those travel.

    :param groups_mode: the policy of the collab, which both sides run under.
    :param receiver_groups_mode: the receiver's own policy, when the point of the test is that it differs — which
        outside a hand-edited configuration it cannot.
    :param receiver_extras_mode: the same, for extras. The sender always offers, so that what is tested is the
        receiver's gate and not the offer.
    """
    backend_sender, state_sender = sender
    backend_receiver, state_receiver = receiver

    # Re-read, because every import writes the state file behind the object the fixture handed out.
    state_sender = CollabState.read(state_sender.filepath)
    state_receiver = CollabState.read(state_receiver.filepath)
    receiver_groups_mode = receiver_groups_mode or groups_mode

    cursor = state_receiver.cursors.get(peer)
    claim = state_receiver.imported_uuids_since(cursor)
    delta = compute_delta(state=state_sender, backend=backend_sender, cursor=cursor, claim=claim)
    offer = refresh_offer(state=state_sender, backend=backend_sender, cursor=cursor)
    wanted = refresh_wanted(backend_receiver, offer)
    members = (
        membership_offer(state=state_sender, backend=backend_sender, cursor=cursor) if groups_mode == 'grow' else []
    )
    missing = set(missing_uuids(backend_receiver, delta.uuids))
    refuse = missing & state_receiver.tombstones
    want = missing - refuse
    export = export_delta(
        filepath,
        delta=delta,
        backend=backend_sender,
        want=want | required_refused(delta=delta, backend=backend_sender, want=want, refuse=refuse),
        refuse=refuse,
        groups_mode=groups_mode,
    )

    return import_delta(
        export.filepath,
        state=state_receiver,
        backend=backend_receiver,
        extras_mode=receiver_extras_mode,
        peer=peer,
        instant=export.instant,
        refresh=refresh_snapshots(backend_sender, wanted),
        groups_mode=receiver_groups_mode,
        members=members_wanted(backend_receiver, members),
    )


def extras_of(backend, uuid):
    """Return the shared extras of a node: the ``_`` namespace is private to each profile and never compared."""
    return {key: value for key, value in load_node(backend, uuid).base.extras.all.items() if not key.startswith('_')}


def test_refresh_travels_and_the_newest_edit_wins(tmp_path, peers):
    """Test that an extra edited on one peer reaches the other, and that a later edit there wins it back."""
    one, two = peers('one'), peers('two')
    calculation = seal_calculation(one[0], 'sealed')

    # The first exchange in each direction carries the nodes and establishes the cursors the refresh is bounded by.
    sync_pull(one, two, tmp_path / 'one-to-two.aiida', peer='one')
    sync_pull(two, one, tmp_path / 'two-to-one.aiida', peer='two')

    calculation.base.extras.set('note', 'from one')
    report = sync_pull(one, two, tmp_path / 'edit.aiida', peer='one')

    assert report.uuids == [], 'the extras edit must not make any node travel'
    assert report.refreshed == [calculation.uuid]
    assert extras_of(two[0], calculation.uuid) == {'note': 'from one'}

    load_node(two[0], calculation.uuid).base.extras.set('note', 'from two')
    sync_pull(two, one, tmp_path / 'back.aiida', peer='two')

    assert extras_of(one[0], calculation.uuid) == {'note': 'from two'}


def test_refresh_offered_to_a_peer_without_a_cursor_names_every_node(peers):
    """Test that a null cursor is answered with every node's mtime, not with nothing.

    The unit pin of the offer a first contact gets: a peer without a cursor is not a peer holding nothing of this
    profile, so bounding the offer by "nothing" loses the extras of everything it gave this profile.
    """
    backend, state = peers('one')
    calculation = seal_calculation(backend, 'sealed')

    offer = refresh_offer(state=state, backend=backend, cursor=None)

    assert set(offer) == linked_uuids(calculation)
    assert offer[calculation.uuid] == calculation.mtime


def test_refresh_offers_a_node_whose_only_trace_since_the_cursor_is_a_pull(peers):
    """Test that a node imported since the cursor is offered, though nothing refreshed it and its mtime is older.

    The unit pin of the extras edit that arrives baked into a delta: the archive row carries the origin's mtime and
    the import records a ``pull``, so neither the mtime bound nor the refresh journal names the node.
    """
    from datetime import timedelta

    backend, state = peers('one')
    calculation = seal_calculation(backend, 'sealed')
    # Strictly past the node's own mtime, so the mtime leg of the union cannot name it however coarse the clock
    # is. Taking `now()` here instead leaves the two equal on a coarse one, and the `>=` bound then answers with
    # the node by itself — the imported leg this test is about would be doing no work.
    cursor = calculation.mtime + timedelta(seconds=1)
    state.events.append(CollabEvent(time=cursor, direction='pull', peer='two', uuids=[calculation.uuid], size=1))

    offer = refresh_offer(state=state, backend=backend, cursor=cursor)

    assert set(offer) == {calculation.uuid}


def test_refresh_offered_to_a_local_profile_is_not_applied(tmp_path, peers):
    """Test that a profile that keeps its extras local ignores a refresh, however insistently it is offered.

    The mirror of the groups gate: what enters a profile is decided by the profile it enters, so a sender that
    declares ``local`` and serves snapshots anyway — a hand-edited configuration — cannot overwrite extras here.
    """
    one, two = peers('one'), peers('two')
    calculation = seal_calculation(one[0], 'sealed')

    sync_pull(one, two, tmp_path / 'one-to-two.aiida', peer='one')
    load_node(two[0], calculation.uuid).base.extras.set('note', 'mine')

    calculation.base.extras.set('note', 'from one')
    report = sync_pull(one, two, tmp_path / 'edit.aiida', peer='one', receiver_extras_mode='local')

    assert report.refreshed == []
    assert extras_of(two[0], calculation.uuid) == {'note': 'mine'}


def test_refresh_is_not_echoed_back(tmp_path, peers):
    """Test that the side that received a refresh does not offer it back: the sender's mtime travelled with it."""
    one, two = peers('one'), peers('two')
    calculation = seal_calculation(one[0], 'sealed')

    sync_pull(one, two, tmp_path / 'one-to-two.aiida', peer='one')
    sync_pull(two, one, tmp_path / 'two-to-one.aiida', peer='two')

    calculation.base.extras.set('note', 'from one')
    sync_pull(one, two, tmp_path / 'edit.aiida', peer='one')

    report = sync_pull(two, one, tmp_path / 'echo.aiida', peer='two')

    assert report.refreshed == []
    assert load_node(two[0], calculation.uuid).mtime == load_node(one[0], calculation.uuid).mtime


def test_refresh_deletion_propagates(tmp_path, peers):
    """Test that a key deleted on the newer side disappears on the other and does not come back."""
    one, two = peers('one'), peers('two')
    calculation = seal_calculation(one[0], 'sealed')
    calculation.base.extras.set('note', 'from one')

    sync_pull(one, two, tmp_path / 'one-to-two.aiida', peer='one')
    sync_pull(two, one, tmp_path / 'two-to-one.aiida', peer='two')

    assert extras_of(two[0], calculation.uuid) == {'note': 'from one'}

    calculation.base.extras.delete('note')
    sync_pull(one, two, tmp_path / 'delete.aiida', peer='one')

    assert extras_of(two[0], calculation.uuid) == {}

    sync_pull(two, one, tmp_path / 'resurrect.aiida', peer='two')

    assert extras_of(one[0], calculation.uuid) == {}, 'the deleted key must not be restored by the other side'


def test_refresh_relays_through_a_chain(tmp_path, peers):
    """Test that an extras edit made on A reaches C through pairwise pulls alone, relayed by B.

    B's copy keeps A's mtime, which is older than C's cursor for B, so only the refresh event B recorded can put
    the node back into what B offers C.
    """
    one, two, three = peers('one'), peers('two'), peers('three')
    calculation = seal_calculation(one[0], 'sealed')

    sync_pull(one, two, tmp_path / 'one-to-two.aiida', peer='one')
    sync_pull(two, three, tmp_path / 'two-to-three.aiida', peer='two')

    calculation.base.extras.set('note', 'from one')

    # C syncs from B in between, so that its cursor for B is younger than the edit: the mtime B ends up holding
    # cannot put the node back into what B offers C, and only the refresh event B records can.
    sync_pull(two, three, tmp_path / 'in-between.aiida', peer='two')

    sync_pull(one, two, tmp_path / 'edit.aiida', peer='one')
    report = sync_pull(two, three, tmp_path / 'relay.aiida', peer='two')

    assert report.refreshed == [calculation.uuid]
    assert extras_of(three[0], calculation.uuid) == {'note': 'from one'}


def test_refresh_keeps_the_private_namespace(tmp_path, peers):
    """Test that ``_``-prefixed extras neither travel nor are overwritten by an incoming snapshot."""
    one, two = peers('one'), peers('two')
    calculation = seal_calculation(one[0], 'sealed')

    sync_pull(one, two, tmp_path / 'one-to-two.aiida', peer='one')
    sync_pull(two, one, tmp_path / 'two-to-one.aiida', peer='two')

    load_node(two[0], calculation.uuid).base.extras.set('_mine', 'kept')
    calculation.base.extras.set('note', 'from one')
    calculation.base.extras.set('_aiida_hash', 'a-hash-of-the-peer')

    snapshots = refresh_snapshots(one[0], [calculation.uuid])
    sync_pull(one, two, tmp_path / 'edit.aiida', peer='one')

    assert [snapshot.extras for snapshot in snapshots] == [{'note': 'from one'}], 'the private keys must not be sent'
    assert load_node(two[0], calculation.uuid).base.extras.all == {
        'note': 'from one',
        '_mine': 'kept',
        COLLAB_PEER_KEY: 'one',
    }


def test_refresh_survives_compaction(tmp_path, peers, monkeypatch):
    """Test that a relayed extras edit still travels once the event that recorded it was folded by compaction."""
    from aiida.tools.collab import state as state_module

    one, two, three = peers('one'), peers('two'), peers('three')
    calculation = seal_calculation(one[0], 'sealed')

    sync_pull(one, two, tmp_path / 'one-to-two.aiida', peer='one')
    sync_pull(two, three, tmp_path / 'two-to-three.aiida', peer='two')

    calculation.base.extras.set('note', 'from one')

    # As in the relay test: C's cursor for B lands after the edit, so the event B folds is the only thing that can
    # still deliver it.
    sync_pull(two, three, tmp_path / 'in-between.aiida', peer='two')

    sync_pull(one, two, tmp_path / 'edit.aiida', peer='one')

    monkeypatch.setattr(state_module, 'COMPACT_THRESHOLD', 2)
    state_two = CollabState.read(two[1].filepath)
    state_two.events.append(
        CollabEvent(time=timezone.now(), direction='pull', peer='one', uuids=['uuid-padding'], size=1)
    )
    state_two.save()

    folded = CollabState.read(two[1].filepath).events
    assert [event.peer for event in folded if event.direction == 'refresh'] == [state_module.COMPACTED_PEER], (
        'the event recording the refresh should have been folded into the synthetic one'
    )

    report = sync_pull(two, three, tmp_path / 'relay.aiida', peer='two')

    assert report.refreshed == [calculation.uuid]
    assert extras_of(three[0], calculation.uuid) == {'note': 'from one'}


def group_uuid(backend, label):
    """Return the UUID of the group with the given label."""
    return (
        orm.QueryBuilder(backend=backend).append(orm.Group, filters={'label': label}, project='uuid').all(flat=True)[0]
    )


def group_members(backend, label):
    """Return the UUIDs of the nodes in the group with the given label, or ``None`` when there is no such group."""
    query = (
        orm.QueryBuilder(backend=backend)
        .append(orm.Group, filters={'label': label}, tag='group')
        .append(orm.Node, with_group='group', project='uuid')
    )

    if not orm.QueryBuilder(backend=backend).append(orm.Group, filters={'label': label}).count():
        return None

    return set(query.all(flat=True))


def test_groups_grow_carries_curated_groups(tmp_path, peers):
    """Test that ``grow`` delivers the groups a person curated, and never the ones AiiDA generated."""
    one, two = peers('one'), peers('two')
    calculation = seal_calculation(one[0], 'sealed')
    orm.Group(label='curated', backend=one[0]).store().add_nodes([calculation])
    orm.ImportGroup(label='generated', backend=one[0]).store().add_nodes([calculation])

    sync_pull(one, two, tmp_path / 'delta.aiida', peer='one', groups_mode='grow')

    assert group_members(two[0], 'curated') == {calculation.uuid}
    assert group_members(two[0], 'generated') is None


def test_groups_local_carries_none(tmp_path, peers):
    """Test that the default policy leaves groups alone: none travels, and the receiver keeps its own."""
    one, two = peers('one'), peers('two')
    calculation = seal_calculation(one[0], 'sealed')
    orm.Group(label='curated', backend=one[0]).store().add_nodes([calculation])

    sync_pull(one, two, tmp_path / 'delta.aiida', peer='one')

    assert orm.QueryBuilder(backend=two[0]).append(orm.Group).count() == 0


def test_groups_grow_only_adds_members(tmp_path, peers):
    """Test that a node added to a group the receiver already holds joins it, and that a removal does not travel.

    The import writes membership rows only for the groups it creates, so the second sync — whose group already
    exists at the receiver — is the one that would silently drop the new member.
    """
    one, two = peers('one'), peers('two')
    first = seal_calculation(one[0], 'first')
    group = orm.Group(label='curated', backend=one[0]).store()
    group.add_nodes([first])

    sync_pull(one, two, tmp_path / 'first.aiida', peer='one', groups_mode='grow')

    second = seal_calculation(one[0], 'second')
    group.add_nodes([second])
    group.remove_nodes([first])

    sync_pull(one, two, tmp_path / 'second.aiida', peer='one', groups_mode='grow')

    assert group_members(two[0], 'curated') == {first.uuid, second.uuid}


def test_import_migrates_an_older_archive(tmp_path, peers):
    """Test that a delta written by a peer on an older aiida-core is migrated forward instead of refused.

    This is what makes the version gate's "an older peer is no obstacle" true: ``import_archive`` refuses an
    archive that is not at the head format version rather than migrating it itself.
    """
    from pathlib import Path

    from tests.utils.archives import get_archive_file

    backend, state = peers('one')
    filepath = Path(get_archive_file('export_main_0000_simple.aiida', 'export/migrate'))

    report = import_delta(
        filepath, state=state, backend=backend, extras_mode='local', peer=PEER, instant=timezone.now()
    )

    assert report.uuids
    assert node_count(backend) == len(report.uuids)


def curate(profile, group, nodes):
    """Add nodes to a group and journal it, as the ``Group.add_nodes`` hook does under the ``grow`` policy.

    The hook itself is tested where it lives; here the journal is what the exchange is driven by.
    """
    group.add_nodes(nodes)

    state = CollabState.read(profile[1].filepath)
    state.memberships.extend(Membership(time=timezone.now(), group=group.uuid, node=node.uuid) for node in nodes)
    state.save()


def test_groups_curation_of_a_shared_node_travels(tmp_path, peers):
    """Test the headline case: a node the peer already holds is curated, and the membership reaches it anyway.

    Nothing about the node changes, so no delta can carry it — the group and the membership travel beside it or
    not at all.
    """
    one, two = peers('one'), peers('two')
    calculation = seal_calculation(one[0], 'sealed')

    sync_pull(one, two, tmp_path / 'nodes.aiida', peer='one', groups_mode='grow')

    curate(one, orm.Group(label='curated', backend=one[0]).store(), [calculation])
    report = sync_pull(one, two, tmp_path / 'curation.aiida', peer='one', groups_mode='grow')

    assert report.uuids == [], 'the curation must not make any node travel'
    assert report.members == [(group_uuid(one[0], 'curated'), calculation.uuid)]
    assert group_members(two[0], 'curated') == {calculation.uuid}
    assert group_uuid(two[0], 'curated') == group_uuid(one[0], 'curated'), 'one curated group, one UUID everywhere'
    assert CollabState.read(two[1].filepath).cursors['one'], 'a sync that carries only memberships still advances'


def test_groups_curation_relays_through_a_chain(tmp_path, peers):
    """Test that a curation made on A reaches C through pairwise syncs alone, relayed by B.

    C never contacts A, and the node is held by all three, so only what B journalled when it applied A's offer can
    put the membership into what B offers C.
    """
    one, two, three = peers('one'), peers('two'), peers('three')
    calculation = seal_calculation(one[0], 'sealed')

    sync_pull(one, two, tmp_path / 'one-to-two.aiida', peer='one', groups_mode='grow')
    sync_pull(two, three, tmp_path / 'two-to-three.aiida', peer='two', groups_mode='grow')

    curate(one, orm.Group(label='curated', backend=one[0]).store(), [calculation])

    sync_pull(one, two, tmp_path / 'relay-in.aiida', peer='one', groups_mode='grow')
    report = sync_pull(two, three, tmp_path / 'relay-out.aiida', peer='two', groups_mode='grow')

    assert report.uuids == []
    assert group_members(two[0], 'curated') == {calculation.uuid}
    assert group_members(three[0], 'curated') == {calculation.uuid}


def test_groups_membership_of_a_held_group_relays_through_a_chain(tmp_path, peers):
    """Test the same relay for a node added to a group all three already hold."""
    one, two, three = peers('one'), peers('two'), peers('three')
    first = seal_calculation(one[0], 'first')
    group = orm.Group(label='curated', backend=one[0]).store()
    curate(one, group, [first])

    second = seal_calculation(one[0], 'second')

    sync_pull(one, two, tmp_path / 'one-to-two.aiida', peer='one', groups_mode='grow')
    sync_pull(two, three, tmp_path / 'two-to-three.aiida', peer='two', groups_mode='grow')

    assert group_members(three[0], 'curated') == {first.uuid}

    curate(one, group, [second])

    sync_pull(one, two, tmp_path / 'relay-in.aiida', peer='one', groups_mode='grow')
    report = sync_pull(two, three, tmp_path / 'relay-out.aiida', peer='two', groups_mode='grow')

    assert report.uuids == []
    assert group_members(three[0], 'curated') == {first.uuid, second.uuid}


def test_groups_curation_is_not_offered_back(tmp_path, peers):
    """Test that the side that applied a membership does not offer it back to the peer that sent it.

    Only memberships that were new to a profile are journalled, so a pair a peer already holds cannot bounce
    between the two of them forever.
    """
    one, two = peers('one'), peers('two')
    calculation = seal_calculation(one[0], 'sealed')

    sync_pull(one, two, tmp_path / 'nodes.aiida', peer='one', groups_mode='grow')
    sync_pull(two, one, tmp_path / 'back.aiida', peer='two', groups_mode='grow')

    curate(one, orm.Group(label='curated', backend=one[0]).store(), [calculation])
    sync_pull(one, two, tmp_path / 'curation.aiida', peer='one', groups_mode='grow')

    report = sync_pull(two, one, tmp_path / 'echo.aiida', peer='two', groups_mode='grow')

    assert report.members == []


def test_groups_local_exchanges_nothing(tmp_path, peers):
    """Test that a collab that keeps groups local neither offers nor applies membership."""
    one, two = peers('one'), peers('two')
    calculation = seal_calculation(one[0], 'sealed')

    sync_pull(one, two, tmp_path / 'nodes.aiida', peer='one')

    curate(one, orm.Group(label='curated', backend=one[0]).store(), [calculation])
    report = sync_pull(one, two, tmp_path / 'curation.aiida', peer='one')

    assert report.members == []
    assert group_members(two[0], 'curated') is None


def test_groups_offer_to_a_local_profile_imports_nothing(tmp_path, peers):
    """Test that what enters a profile is decided by its own policy, not by what a peer declares or serves.

    A sender that grows groups while the receiver keeps them local can only be a hand-edited configuration, and it
    must not be able to create a group or a membership here — neither with the delta nor beside it.
    """
    one, two = peers('one'), peers('two')
    calculation = seal_calculation(one[0], 'sealed')
    curate(one, orm.Group(label='curated', backend=one[0]).store(), [calculation])

    report = sync_pull(one, two, tmp_path / 'delta.aiida', peer='one', groups_mode='grow', receiver_groups_mode='local')

    assert report.uuids, 'the nodes of the delta still land'
    assert report.members == []
    assert orm.QueryBuilder(backend=two[0]).append(orm.Group).count() == 0


def test_groups_curation_offered_to_a_local_profile_imports_nothing(tmp_path, peers):
    """Test that the same gate holds for a curation offered beside the delta, not only for one riding it.

    This is the half that carries the weight: a pusher can skip ``POST /missing`` entirely, so the import is the
    only place where the receiver's own policy is consulted about an offer.
    """
    one, two = peers('one'), peers('two')
    calculation = seal_calculation(one[0], 'sealed')

    # Shared first, so that the curation has no delta left to ride and can only arrive as an offer.
    sync_pull(one, two, tmp_path / 'nodes.aiida', peer='one', groups_mode='grow')

    curate(one, orm.Group(label='curated', backend=one[0]).store(), [calculation])
    report = sync_pull(
        one, two, tmp_path / 'curation.aiida', peer='one', groups_mode='grow', receiver_groups_mode='local'
    )

    assert report.members == []
    assert group_members(two[0], 'curated') is None
    assert calculation.uuid in {node.uuid for node in orm.QueryBuilder(backend=two[0]).append(orm.Node).all(flat=True)}


def test_groups_survive_the_tombstone_refilter(tmp_path, peers):
    """Test that a curation still lands when a tombstone forces the delta to be re-exported without its groups.

    The re-filter hands ``create_archive`` the nodes alone, which is exactly how the groups are dropped for a
    ``local`` profile — so the memberships that rode the delta have to be able to create their group here after
    the import, or they are lost with no way back: the cursor moves past them and the node never travels again.
    """
    one, two = peers('one'), peers('two')
    calculation = seal_calculation(one[0], 'sealed')
    an_input = calculation.base.links.get_incoming().all()[0].node
    curate(one, orm.Group(label='curated', backend=one[0]).store(), [calculation, an_input])

    # A node of the delta's provenance that this profile deleted: it comes back because the calculation requires
    # it, and the re-filter that drops it from the archive is what strips the group along the way.
    state_two = CollabState.read(two[1].filepath)
    state_two.tombstones.add(an_input.uuid)
    state_two.save()

    report = sync_pull(one, two, tmp_path / 'delta.aiida', peer='one', groups_mode='grow')

    # The tombstoned node is back — provenance of the delta needs it — so it is here to be curated like any other,
    # and what is reported is what was written: a pair claimed but not written would be relayed on to a third peer.
    assert group_members(two[0], 'curated') == {calculation.uuid, an_input.uuid}
    assert report.members == sorted((group_uuid(one[0], 'curated'), uuid) for uuid in (calculation.uuid, an_input.uuid))


def test_groups_generated_by_aiida_are_refused_from_an_offer(tmp_path, peers):
    """Test that a group AiiDA generates for itself is refused however a peer offers it.

    The sender leaves them out, so an offer naming one is a diverged peer — and these groups describe the
    history of the profile that made them, which is nobody else's.
    """
    one, two = peers('one'), peers('two')
    calculation = seal_calculation(one[0], 'sealed')

    sync_pull(one, two, tmp_path / 'nodes.aiida', peer='one', groups_mode='grow')

    offer = [GroupMembers(uuid=str(uuid4()), label='an import', type_string='core.import', nodes=[calculation.uuid])]

    assert apply_members(two[0], offer) == []
    assert orm.QueryBuilder(backend=two[0]).append(orm.Group).count() == 0


def test_groups_offer_naming_a_pair_twice_applies_it_once(tmp_path, peers):
    """Test that an offer repeating a pair is applied once, not attempted twice.

    A membership row is unique, and the offer is wire data: a peer naming a pair twice would otherwise raise out
    of the storage layer, past every handler the sync has, with the archive already committed.
    """
    one, two = peers('one'), peers('two')
    calculation = seal_calculation(one[0], 'sealed')

    sync_pull(one, two, tmp_path / 'nodes.aiida', peer='one', groups_mode='grow')

    uuid = str(uuid4())
    twice = GroupMembers(uuid=uuid, label='curated', type_string='', nodes=[calculation.uuid, calculation.uuid])

    assert apply_members(two[0], [twice, twice]) == [(uuid, calculation.uuid)]
    assert group_members(two[0], 'curated') == {calculation.uuid}


def test_groups_membership_of_an_absent_node_is_dropped(peers):
    """Test that a pair naming a node this profile does not hold is dropped rather than attempted.

    A push asks for what it wants before the delta is uploaded, so the nodes of that very delta are absent when
    the offer is filtered; they come back with it, carrying their memberships as every delta does.
    """
    one, two = peers('one'), peers('two')
    calculation = seal_calculation(one[0], 'sealed')
    curate(one, orm.Group(label='curated', backend=one[0]).store(), [calculation])

    offer = membership_offer(state=CollabState.read(one[1].filepath), backend=one[0], cursor=None)

    assert member_pairs(offer) == [(group_uuid(one[0], 'curated'), calculation.uuid)]
    assert members_wanted(two[0], offer) == []


def test_groups_membership_of_a_tombstoned_node_is_dropped_and_recovered(tmp_path, peers):
    """Test that a pair whose node this profile deleted is dropped, and comes back with the node if it does.

    Dropping is safe precisely because the memberships of a node ride the node: whichever later sync delivers it
    delivers them too. What drops the pair is the node being gone — the tombstone is what keeps it that way.
    """
    one, two = peers('one'), peers('two')
    calculation = seal_calculation(one[0], 'sealed')

    sync_pull(one, two, tmp_path / 'nodes.aiida', peer='one', groups_mode='grow')

    delete_nodes(two[0], [calculation.uuid])
    state_two = CollabState.read(two[1].filepath)
    state_two.tombstones.add(calculation.uuid)
    state_two.save()

    curate(one, orm.Group(label='curated', backend=one[0]).store(), [calculation])
    report = sync_pull(one, two, tmp_path / 'curation.aiida', peer='one', groups_mode='grow')

    assert report.members == []
    assert group_members(two[0], 'curated') is None, 'a group whose only member is tombstoned is not created either'

    # The node is taken back, which is what carries its memberships along: they ride the delta, not the offer.
    delta = compute_delta(state=CollabState.read(one[1].filepath), backend=one[0], cursor=None)
    export = export_delta(tmp_path / 'again.aiida', delta=delta, backend=one[0], groups_mode='grow')
    recovered = import_delta(
        export.filepath,
        state=CollabState.read(two[1].filepath),
        backend=two[0],
        extras_mode='sync',
        peer='one',
        instant=export.instant,
        include_deleted=True,
        groups_mode='grow',
    )

    assert (group_uuid(one[0], 'curated'), calculation.uuid) in recovered.members
    assert group_members(two[0], 'curated') == {calculation.uuid}


def test_groups_membership_survives_compaction(tmp_path, peers, monkeypatch):
    """Test that a curation still travels once the journal entry that recorded it was folded by compaction."""
    from aiida.tools.collab import state as state_module

    one, two = peers('one'), peers('two')
    calculation = seal_calculation(one[0], 'sealed')

    sync_pull(one, two, tmp_path / 'nodes.aiida', peer='one', groups_mode='grow')

    curate(one, orm.Group(label='curated', backend=one[0]).store(), [calculation])

    monkeypatch.setattr(state_module, 'COMPACT_THRESHOLD', 2)
    state_one = CollabState.read(one[1].filepath)
    state_one.memberships.extend(
        Membership(time=timezone.now(), group='uuid-of-padding', node=f'uuid-padding-{index}') for index in range(2)
    )
    state_one.save()

    folded = CollabState.read(one[1].filepath).memberships
    assert len({entry.time for entry in folded}) < 3, 'the older entries should have been folded onto one instant'

    report = sync_pull(one, two, tmp_path / 'curation.aiida', peer='one', groups_mode='grow')

    assert group_members(two[0], 'curated') == {calculation.uuid}
    assert report.members, 'the folded curation must still be offered'


def test_groups_relabels_a_clashing_group(tmp_path, peers):
    """Test that an offered group whose label is taken here is created under a free one, as the import does.

    A UUID cannot collide, a label can: the two profiles curated groups of the same name independently.
    """
    one, two = peers('one'), peers('two')
    calculation = seal_calculation(one[0], 'sealed')
    orm.Group(label='curated', backend=two[0]).store()

    sync_pull(one, two, tmp_path / 'nodes.aiida', peer='one', groups_mode='grow')

    curate(one, orm.Group(label='curated', backend=one[0]).store(), [calculation])
    sync_pull(one, two, tmp_path / 'curation.aiida', peer='one', groups_mode='grow')

    assert group_members(two[0], 'curated') == set(), 'the group that was here keeps its label and its members'
    assert group_members(two[0], 'curated-2') == {calculation.uuid}
