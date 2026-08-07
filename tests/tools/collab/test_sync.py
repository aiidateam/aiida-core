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

import pytest

from aiida import orm
from aiida.common import timezone
from aiida.common.links import LinkType
from aiida.storage.sqlite_temp import SqliteTempBackend
from aiida.tools.collab.state import CollabEvent, CollabState
from aiida.tools.collab.sync import (
    compute_delta,
    export_delta,
    import_delta,
    missing_uuids,
    refresh_offer,
    refresh_snapshots,
    refresh_wanted,
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

    assert load_node(backend_two, calculation.uuid).base.extras.all == {}


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
    claim = state_c.imported_uuids_since(None) | state_c.tombstones

    second = export_full(
        tmp_path / 'b.aiida', state=CollabState.read(state_b.filepath), backend=backend_b, cursor=None, claim=claim
    )

    assert second.uuids == []


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


def test_thin_export_ships_only_missing(tmp_path, peers):
    """Test that the second sync of a restart chain transfers neither rows nor repository files already held.

    The second calculation reuses the first one's output and its heavy direct input; both are ancestors of the
    new work, so a provenance-closed archive would re-ship them — the thin one must not.
    """
    backend_one, state_one = peers('one')
    backend_two, state_two = peers('two')
    heavy, first, output = heavy_calculation(backend_one)

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
    assert archive_repo_keys(tmp_path / 'second.aiida').isdisjoint(heavy_keys)

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
    heavy, first, output = heavy_calculation(backend_one)

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
    heavy, first, output = heavy_calculation(backend_one)
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

    # The receiver deletes X and records its tombstone; the creator stays. Deleted through raw rows, because
    # ``SqliteTempBackend`` does not implement ``delete_nodes_and_connections``.
    from aiida.storage.sqlite_zip.models import DbLink, DbNode

    pk = orm.QueryBuilder(backend=backend_two).append(orm.Node, filters={'uuid': deleted.uuid}, project='id').one()[0]

    with backend_two.transaction() as session:
        session.query(DbLink).filter((DbLink.input_id == pk) | (DbLink.output_id == pk)).delete(
            synchronize_session=False
        )
        session.query(DbNode).filter(DbNode.id == pk).delete(synchronize_session=False)

    state_two = CollabState.read(state_two.filepath)
    state_two.tombstones.add(deleted.uuid)
    state_two.save()

    # The sender builds new work on X, then the receiver syncs, claiming its tombstone as usual.
    consumer = seal_calculation_with(backend_one, 'consumer', inputs=[deleted])

    cursor = state_two.cursors[PEER]
    claim = state_two.imported_uuids_since(cursor) | state_two.tombstones
    delta = compute_delta(state=state_one, backend=backend_one, cursor=cursor, claim=claim)
    want = set(missing_uuids(backend_two, delta.uuids))

    assert deleted.uuid in want, 'closure requires X, and the receiver does not hold it'

    export = export_delta(tmp_path / 'second.aiida', delta=delta, backend=backend_one, want=want)
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
    heavy, first, output = heavy_calculation(backend_one)

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

    backend_one, state_one = peers('one')
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

    backend_one, state_one = peers('one')
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


def sync_pull(sender, receiver, filepath, peer, receiver_extras_mode='sync'):
    """Pull from one profile into another as ``verdi collab pull`` does under the ``sync`` extras policy.

    Both sides talk through the same functions the endpoint and the client wire together: the sender offers the
    mtimes of the shared nodes it may have edited, the receiver keeps the extras it holds an older version of, and
    only those travel.

    :param receiver_extras_mode: the receiver's own policy, when the point of the test is that it differs. The
        sender always offers, so that what is tested is the receiver's gate and not the offer.
    """
    backend_sender, state_sender = sender
    backend_receiver, state_receiver = receiver

    # Re-read, because every import writes the state file behind the object the fixture handed out.
    state_sender = CollabState.read(state_sender.filepath)
    state_receiver = CollabState.read(state_receiver.filepath)

    cursor = state_receiver.cursors.get(peer)
    claim = state_receiver.imported_uuids_since(cursor) | state_receiver.tombstones
    delta = compute_delta(state=state_sender, backend=backend_sender, cursor=cursor, claim=claim)
    offer = refresh_offer(state=state_sender, backend=backend_sender, cursor=cursor)
    wanted = refresh_wanted(backend_receiver, offer, state_receiver.tombstones)
    export = export_delta(
        filepath, delta=delta, backend=backend_sender, want=set(missing_uuids(backend_receiver, delta.uuids))
    )

    return import_delta(
        export.filepath,
        state=state_receiver,
        backend=backend_receiver,
        extras_mode=receiver_extras_mode,
        peer=peer,
        instant=export.instant,
        refresh=refresh_snapshots(backend_sender, wanted),
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


def test_refresh_offered_to_a_local_profile_is_not_applied(tmp_path, peers):
    """Test that a profile that keeps its extras local ignores a refresh, however insistently it is offered.

    What enters a profile is decided by the profile it enters, so a sender that declares ``local`` and serves
    snapshots anyway — a hand-edited configuration — cannot overwrite extras here.
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
    assert load_node(two[0], calculation.uuid).base.extras.all == {'note': 'from one', '_mine': 'kept'}


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
