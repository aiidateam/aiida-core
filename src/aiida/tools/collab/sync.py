###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Export and import the delta of provenance that a profile shares with the peers of its collab."""

from __future__ import annotations

import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from aiida import orm
from aiida.common import timezone
from aiida.common.links import GraphTraversalRules
from aiida.common.log import AIIDA_LOGGER
from aiida.orm.nodes.caching import NodeCaching
from aiida.orm.utils.mixins import Sealable
from aiida.tools.archive import create_archive, import_archive
from aiida.tools.archive.abstract import get_format
from aiida.tools.archive.imports import MergeExtrasType
from aiida.tools.collab.protocol import ExtrasSnapshot
from aiida.tools.collab.state import CollabEvent, CollabState
from aiida.tools.graph.graph_traversers import get_nodes_export, traverse_graph, validate_traversal_rules

if TYPE_CHECKING:
    from aiida.manage.configuration.config import CollabExtrasMode
    from aiida.orm.implementation import StorageBackend

MERGE_EXTRAS: dict[str, MergeExtrasType] = {'local': ('k', 'n', 'l'), 'sync': ('k', 'c', 'u')}

CACHING_EXTRAS = (NodeCaching._HASH_EXTRA_KEY, NodeCaching.CACHED_FROM_KEY)

# Extras whose key starts with this are private to the profile they live in: they never travel in a refresh and an
# incoming snapshot never overwrites them. The caching extras are the ones AiiDA itself keeps there.
PRIVATE_EXTRA_PREFIX = '_'

# Callers are left out: a process that is still running has sealed children but is not sealed itself, and the export
# refuses to write an unsealed process. Their CALL links travel once the caller seals.
TRAVERSAL_RULES: dict[str, Any] = {'call_calc_backward': False, 'call_work_backward': False}

LOGGER = AIIDA_LOGGER.getChild('collab')

# Link types of which a node can have at most one incoming, mapped to the class they are exclusive against:
# a data node has exactly one creator, a process exactly one caller of either call flavour.
EXCLUSIVE_LINKS = {
    'create': ('create',),
    'call_calc': ('call_calc', 'call_work'),
    'call_work': ('call_calc', 'call_work'),
}


def seed_filters(cursor: datetime | None) -> dict[str, Any]:
    """Return the query filters selecting the seeds of a delta: the sealed processes produced since ``cursor``."""
    filters: dict[str, Any] = {f'attributes.{Sealable.SEALED_KEY}': True}

    if cursor is not None:
        filters['mtime'] = {'>=': cursor}

    return filters


def count_seeds(cursor: datetime | None, backend: StorageBackend) -> int:
    """Return the number of seeds a delta bounded by ``cursor`` would start from."""
    return orm.QueryBuilder(backend=backend).append(orm.ProcessNode, filters=seed_filters(cursor)).count()


@dataclass
class Delta:
    """The provenance-closed delta computed for a presented cursor and claim, before any archive is built.

    The manifest — its node UUIDs — is what the negotiation serves; the links are kept so that a later export of a
    subset knows which links cross the subset's boundary.
    """

    uuid_by_pk: dict[int, str]
    links: list[Any]
    instant: datetime
    """The export instant the importer stores as its cursor for this profile once the import succeeds."""

    @property
    def uuids(self) -> list[str]:
        """The manifest: the UUIDs of every node of the closed delta."""
        return sorted(self.uuid_by_pk.values())


@dataclass
class DeltaExport:
    """An archive built from a delta, holding the subset of it that the requester asked for."""

    filepath: Path
    uuids: list[str]
    instant: datetime


@dataclass
class DeltaReport:
    """The outcome of importing a delta."""

    uuids: list[str]
    skipped: list[str]
    size: int
    refreshed: list[str] = field(default_factory=list)
    """The nodes whose extras were replaced by the snapshot that travelled with the delta."""


def compute_delta(
    *,
    state: CollabState,
    backend: StorageBackend,
    cursor: datetime | None,
    claim: frozenset[str] | set[str] = frozenset(),
) -> Delta:
    """Compute everything that entered this profile since the requester's cursor.

    The delta starts from the sealed processes produced since ``cursor`` united with the nodes this profile itself
    imported since then — imported nodes keep their original timestamps, so without the event union provenance
    relayed through this profile would never reach the requester. Nodes the requester claims to hold are dropped
    from that start set; the delta is then closed over inputs, outputs and called processes, so a claimed node
    that the remaining provenance requires is still part of it, which is safe because the requester has it.

    The sender keeps no record of what it served: the requester advances its cursor to the returned instant only
    once it imported a delta.

    :param state: the state of the collab, whose event log supplies the imported nodes.
    :param backend: the storage to compute from.
    :param cursor: the export instant of the last delta the requester imported from this profile, or ``None`` for
        everything. Every instant it is compared against was generated by this profile, so clocks never cross.
    :param claim: UUIDs the requester already holds and does not want re-delivered.
    """
    # Taken before querying, so a process that seals during the computation is picked up by the next one.
    instant = timezone.now()

    seeds = orm.QueryBuilder(backend=backend).append(orm.ProcessNode, filters=seed_filters(cursor)).all(flat=True)
    seed_pks = {node.pk for node in seeds}
    start = {node.pk: node for node in seeds + _imported_nodes(state, cursor, backend)}
    kept = [node for node in start.values() if node.uuid not in claim]
    nodes = _without_unsealed_provenance(kept, backend=backend)

    # A withheld seed has to stay within reach of the next computation, and nothing will touch its mtime when its
    # child seals, so the instant cannot move past it. The seed filter is inclusive for that reason. Imported nodes
    # cannot be withheld: every export rule that could reach a local unsealed process from them is off by default.
    kept_pks = {cast(int, node.pk) for node in nodes}
    withheld = [node for node in kept if node.pk not in kept_pks and node.pk in seed_pks]

    if withheld:
        instant = min(node.mtime for node in withheld)

    traversed = get_nodes_export(starting_pks=kept_pks, get_links=True, backend=backend, **TRAVERSAL_RULES)
    pks = traversed['nodes']
    links = list(traversed['links'] or [])

    uuid_by_pk = {}

    if pks:
        query = orm.QueryBuilder(backend=backend).append(orm.Node, filters={'id': {'in': pks}}, project=['id', 'uuid'])
        uuid_by_pk = dict(query.iterall())

    return Delta(uuid_by_pk=uuid_by_pk, links=links, instant=instant)


def export_delta(
    filepath: Path,
    *,
    delta: Delta,
    backend: StorageBackend,
    want: frozenset[str] | set[str] | None = None,
) -> DeltaExport:
    """Write the requested subset of a delta to an archive.

    The archive is not provenance-closed: it holds exactly the nodes of ``want``, and the links that cross from
    them to nodes the requester already holds travel in the archive metadata as UUID quadruples, to be re-attached
    by the import. This is what keeps already-held ancestors — rows and repository files alike — off the wire;
    closure was already guaranteed when the delta was computed.

    :param filepath: the path to write the archive to.
    :param delta: the computed delta the subset is taken from.
    :param backend: the storage to export from.
    :param want: the UUIDs the requester asked for, or ``None`` for the whole delta.
    """
    want_uuids = set(delta.uuid_by_pk.values()) if want is None else set(want) & set(delta.uuid_by_pk.values())
    want_pks = {pk for pk, uuid in delta.uuid_by_pk.items() if uuid in want_uuids}

    internal = []
    boundary = []

    for link in delta.links:
        in_want = (link.source_id in want_pks) + (link.target_id in want_pks)

        if in_want == 2:
            internal.append(link)
        elif in_want == 1:
            boundary.append(
                [delta.uuid_by_pk[link.source_id], delta.uuid_by_pk[link.target_id], link.link_type, link.link_label]
            )

    _write_thin_archive(filepath, backend=backend, node_pks=want_pks, links=internal, boundary=boundary)

    return DeltaExport(filepath=filepath, uuids=sorted(want_uuids), instant=delta.instant)


def _write_thin_archive(
    filepath: Path,
    *,
    backend: StorageBackend,
    node_pks: set[int],
    links: list[Any],
    boundary: list[list[str]],
) -> None:
    """Write an archive of exactly the given nodes, with the links that leave the set in the metadata.

    Mirrors the streaming of ``create_archive`` — the same rows, checkpoint stripping and repository objects — but
    without its traversal, which would close the set again and pull the already-held ancestors back in. The archive
    is self-consistent (every link row has both endpoints in it), so any reader can open it; only the metadata key
    carries the collab-specific boundary.
    """
    from aiida.common.utils import DEFAULT_BATCH_SIZE, DEFAULT_FILTER_SIZE, batch_iter
    from aiida.orm.entities import EntityTypes
    from aiida.tools.archive.common import entity_type_to_orm
    from aiida.tools.archive.create import _stream_repo_files
    from aiida.tools.archive.implementations.sqlite_zip.main import ArchiveFormatSqlZip

    def related_pks(entity: Any, relationship: str) -> set[int]:
        if not node_pks:
            return set()

        kwargs: dict[str, Any] = {relationship: 'node'}
        query = (
            orm.QueryBuilder(backend=backend)
            .append(orm.Node, filters={'id': {'in': node_pks}}, tag='node')
            .append(entity, project='id', **kwargs)
            .distinct()
        )
        return set(query.all(flat=True))

    entity_pks: dict[EntityTypes, set[int]] = {
        EntityTypes.USER: related_pks(orm.User, 'with_node'),
        EntityTypes.COMPUTER: related_pks(orm.Computer, 'with_node'),
        EntityTypes.NODE: node_pks,
        EntityTypes.COMMENT: related_pks(orm.Comment, 'with_node'),
        EntityTypes.LOG: related_pks(orm.Log, 'with_node'),
    }

    if comment_pks := entity_pks[EntityTypes.COMMENT]:
        query = (
            orm.QueryBuilder(backend=backend)
            .append(orm.Comment, filters={'id': {'in': comment_pks}}, tag='comment')
            .append(orm.User, with_comment='comment', project='id')
            .distinct()
        )
        entity_pks[EntityTypes.USER].update(query.all(flat=True))

    archive_format = ArchiveFormatSqlZip()

    with archive_format.open(filepath, mode='w') as writer:
        writer.update_metadata(
            {
                'ctime': timezone.now().isoformat(),
                'creation_parameters': {'collab_thin_delta': True},
                'collab_boundary_links': boundary,
            }
        )

        def transform(row: dict[str, Any]) -> dict[str, Any]:
            data = row['entity']
            if data.get('node_type', '').startswith('process.'):
                data['attributes'].pop(orm.ProcessNode.CHECKPOINT_KEY, None)
            return data

        for etype, pks in entity_pks.items():
            if not pks:
                continue

            entity_rows = (
                orm.QueryBuilder(backend=backend)
                .append(entity_type_to_orm[etype], filters={'id': {'in': pks}}, tag='entity', project=['**'])
                .iterdict(batch_size=DEFAULT_BATCH_SIZE)
            )

            for _, rows in batch_iter(entity_rows, DEFAULT_BATCH_SIZE, transform):
                writer.bulk_insert(etype, rows)

        link_rows = [
            {'input_id': link.source_id, 'output_id': link.target_id, 'label': link.link_label, 'type': link.link_type}
            for link in links
        ]

        for _, rows in batch_iter(link_rows, DEFAULT_BATCH_SIZE, lambda row: row):
            writer.bulk_insert(EntityTypes.LINK, rows, allow_defaults=True)

        if node_pks:
            _stream_repo_files(
                archive_format.key_format, writer, node_pks, backend, DEFAULT_BATCH_SIZE, DEFAULT_FILTER_SIZE
            )


def missing_uuids(backend: StorageBackend, uuids: list[str]) -> list[str]:
    """Return the subset of ``uuids`` that ``backend`` does not hold: the diff of a manifest against a profile."""
    if not uuids:
        return []

    query = orm.QueryBuilder(backend=backend).append(orm.Node, filters={'uuid': {'in': uuids}}, project='uuid')

    return sorted(set(uuids) - set(query.all(flat=True)))


def refresh_offer(*, state: CollabState, backend: StorageBackend, cursor: datetime | None) -> dict[str, datetime]:
    """Return the mtime of every node whose extras this profile may hold a newer version of than a peer at ``cursor``.

    Under the ``sync`` policy this is what the manifest is for nodes, but for the extras of *shared* ones: the nodes
    edited here since the cursor, united with those refreshed into this profile since then. That union is the same
    one that makes relayed provenance travel, here so that an extras edit relayed A→B→C travels with pairwise pulls
    alone. Only mtimes are offered: the receiver holds the authoritative comparison, its own mtimes, and asks for
    the snapshots it turns out to need.

    A peer without a cursor holds nothing of this profile yet, so everything travels in the delta with its extras
    and there is nothing to refresh.
    """
    if cursor is None:
        return {}

    relayed = sorted(state.refreshed_uuids_since(cursor))
    filters: dict[str, Any] = {'mtime': {'>=': cursor}}

    if relayed:
        filters = {'or': [filters, {'uuid': {'in': relayed}}]}

    query = orm.QueryBuilder(backend=backend).append(orm.Node, filters=filters, project=['uuid', 'mtime'])

    return dict(query.iterall())


def refresh_wanted(backend: StorageBackend, offer: dict[str, datetime], tombstones: set[str]) -> list[str]:
    """Return which of the offered nodes this profile holds an older version of the extras of.

    A node this profile does not hold has no extras to replace — it either travels in the delta with them or is
    not shared at all — and a tombstoned one was deliberately deleted, so both are dropped.
    """
    candidates = {uuid: mtime for uuid, mtime in offer.items() if uuid not in tombstones}

    if not candidates:
        return []

    query = orm.QueryBuilder(backend=backend).append(
        orm.Node, filters={'uuid': {'in': sorted(candidates)}}, project=['uuid', 'mtime']
    )

    return sorted(uuid for uuid, mtime in query.iterall() if candidates[uuid] > mtime)


def refresh_snapshots(backend: StorageBackend, uuids: list[str]) -> list[ExtrasSnapshot]:
    """Return the extras of the requested nodes, as the snapshot a peer replaces its own with."""
    if not uuids:
        return []

    query = orm.QueryBuilder(backend=backend).append(
        orm.Node, filters={'uuid': {'in': uuids}}, project=['uuid', 'mtime', 'extras']
    )

    return [
        ExtrasSnapshot(uuid=uuid, mtime=mtime, extras=_public_extras(extras)) for uuid, mtime, extras in query.iterall()
    ]


def _public_extras(extras: dict[str, Any]) -> dict[str, Any]:
    """Return the extras that are shared with the collab: everything outside the private ``_`` namespace."""
    return {key: value for key, value in extras.items() if not key.startswith(PRIVATE_EXTRA_PREFIX)}


def _apply_refresh(backend: StorageBackend, refresh: list[ExtrasSnapshot], tombstones: set[str]) -> list[str]:
    """Replace the extras of the nodes whose snapshot is the newer one, and return which were written.

    The whole dict is replaced rather than merged, which is what propagates a deletion as absence, except that the
    private ``_`` namespace of this profile — the caching extras among it — is kept and never taken from the peer.
    The snapshot's mtime is written as the node's own, so that this profile does not become the newest side and
    echo the same extras back on the next exchange.
    """
    from aiida.orm.entities import EntityTypes

    wanted = set(refresh_wanted(backend, {snapshot.uuid: snapshot.mtime for snapshot in refresh}, tombstones))

    if not wanted:
        return []

    query = orm.QueryBuilder(backend=backend).append(
        orm.Node, filters={'uuid': {'in': sorted(wanted)}}, project=['uuid', 'id', 'extras']
    )
    local = {uuid: (pk, extras) for uuid, pk, extras in query.iterall()}

    rows = []

    for snapshot in refresh:
        if snapshot.uuid not in wanted:
            continue

        pk, extras = local[snapshot.uuid]
        private = {key: value for key, value in extras.items() if key.startswith(PRIVATE_EXTRA_PREFIX)}
        rows.append({'id': pk, 'extras': {**private, **_public_extras(snapshot.extras)}, 'mtime': snapshot.mtime})

    backend.bulk_update(EntityTypes.NODE, rows)

    return sorted(wanted)


def _imported_nodes(state: CollabState, cursor: datetime | None, backend: StorageBackend) -> list[orm.Node]:
    """Return the nodes this profile imported since ``cursor`` that still exist locally."""
    uuids = state.imported_uuids_since(cursor)

    if not uuids:
        return []

    return orm.QueryBuilder(backend=backend).append(orm.Node, filters={'uuid': {'in': sorted(uuids)}}).all(flat=True)


def import_delta(
    filepath: Path,
    *,
    state: CollabState,
    backend: StorageBackend,
    extras_mode: CollabExtrasMode,
    peer: str,
    instant: datetime,
    include_deleted: bool = False,
    refresh: list[ExtrasSnapshot] | None = None,
) -> DeltaReport:
    """Import a delta received from a peer, advance the cursor for that peer and record the event in the collab log.

    Nodes that were deleted locally are not imported again, unless provenance in the delta depends on them.

    The policy passed here is this profile's own, never the sender's: what enters a profile is decided by the
    profile it enters, so a peer that declares one policy and serves another — which only a hand-edited
    configuration produces — changes nothing here.

    :param filepath: the path of the archive to import.
    :param state: the state of the collab, whose tombstones are honoured and whose log is appended to.
    :param backend: the storage to import into.
    :param extras_mode: how to merge the extras of nodes that already exist locally, and whether an offered
        refresh is applied at all.
    :param refresh: extras snapshots of shared nodes the peer edited more recently, negotiated under the ``sync``
        policy. Applied after the archive, so that the extras of a node that arrives in this very delta are the
        ones the archive carries rather than a snapshot cut before it.
    :param peer: the identity the delta was received under, which keys the cursor: the profile UUID of the peer.
    :param instant: the export instant carried with the delta, which the cursor for ``peer`` advances to.
    :param include_deleted: import nodes that were deleted locally after all, and drop their tombstones.
    :raises ~aiida.common.exceptions.IntegrityError: when the delta links to a node that exists neither in the
        archive nor locally, or a boundary link would violate a link invariant of the local graph; nothing is
        imported in either case.
    """
    size = filepath.stat().st_size

    with tempfile.TemporaryDirectory() as dirpath:
        # A peer on an older aiida-core writes an older archive format, which the importer refuses rather than
        # migrating, so the delta is brought to the head version first — as `verdi archive import` does.
        filepath = _at_head_version(filepath, Path(dirpath) / 'migrated.aiida')

        uuids = _archive_uuids(filepath)
        boundary = _boundary_links(filepath)
        tombstoned = [] if include_deleted else sorted(state.tombstones.intersection(uuids))

        # The caching extras of the peer describe their profile, not this one, so the merge must not be able to
        # carry them over. New nodes are stripped of them by the import itself, existing ones are restored below.
        caching_extras = _get_caching_extras(backend, uuids) if extras_mode == 'sync' else {}

        if tombstoned:
            filepath = _without_nodes(filepath, Path(dirpath) / 'delta.aiida', tombstoned)
            uuids = _archive_uuids(filepath)
            # A boundary link whose archive endpoint was dropped with its tombstone must not be re-attached.
            boundary = [link for link in boundary if link[0] in uuids or link[1] in uuids]

        # Checked before anything lands: a boundary endpoint that exists neither in the archive nor locally would
        # leave the imported nodes permanently disconnected from provenance the sender counted on, and a boundary
        # link that violates a local link invariant must not be plantable by a diverged or hostile sender.
        _check_boundary_resolvable(backend, uuids, boundary)
        _check_boundary_invariants(backend, boundary)

        # The boundary links are journalled before the import, which commits its own transaction: a crash between
        # the two leaves them pending, and the next import retries them instead of losing them.
        if boundary:
            with CollabState.mutate(state.filepath) as fresh:
                fresh.pending_links.extend(link for link in boundary if link not in fresh.pending_links)

        import_archive(
            filepath,
            backend=backend,
            merge_extras=MERGE_EXTRAS[extras_mode],
            create_group=False,
        )

    _set_caching_extras(backend, caching_extras)

    refreshed = _apply_refresh(backend, refresh or [], state.tombstones) if extras_mode == 'sync' else []

    event = CollabEvent(time=timezone.now(), direction='pull', peer=peer, uuids=uuids, size=size)

    # Appended to a freshly read state under the lock instead of saving ``state``: that was read before an import
    # that can take minutes, and writing it back wholesale would erase every tombstone recorded in the meantime.
    with CollabState.mutate(state.filepath) as fresh:
        written = _write_boundary_links(backend, fresh.pending_links, fresh.tombstones)
        fresh.pending_links = [link for link in fresh.pending_links if link not in written]

        if include_deleted:
            fresh.tombstones.difference_update(uuids)

        # A retried push carries the instant of its original export, which can predate a pull that advanced the
        # cursor in the meantime; the cursor means "I hold everything the peer had at T", so it never moves back.
        held = fresh.cursors.get(peer)
        fresh.cursors[peer] = max(held, instant) if held is not None else instant

        fresh.events.append(event)

        # Recorded apart from the import: these nodes were already held, so they are no claim of new provenance,
        # but a peer pulling from here later has to learn that their extras moved on.
        if refreshed:
            fresh.events.append(
                CollabEvent(time=timezone.now(), direction='refresh', peer=peer, uuids=refreshed, size=0)
            )

    return DeltaReport(uuids=uuids, skipped=sorted(set(tombstoned) - set(uuids)), size=size, refreshed=refreshed)


def _boundary_links(filepath: Path) -> list[list[str]]:
    """Return the boundary links of a thin archive, as ``[input_uuid, output_uuid, type, label]``.

    An archive that was not written by ``export_delta``, such as the tombstone re-filter's output, has none.
    """
    with get_format().open(filepath, mode='r') as reader:
        return reader.get_metadata().get('collab_boundary_links', [])


def _check_boundary_resolvable(backend: StorageBackend, uuids: list[str], boundary: list[list[str]]) -> None:
    """Refuse the import when a boundary link endpoint exists neither in the archive nor in this profile."""
    from aiida.common.exceptions import IntegrityError

    archived = set(uuids)
    held = {uuid for link in boundary for uuid in link[:2] if uuid not in archived}

    if not held:
        return

    query = orm.QueryBuilder(backend=backend).append(orm.Node, filters={'uuid': {'in': sorted(held)}}, project='uuid')
    missing = held - set(query.all(flat=True))

    if missing:
        msg = (
            f'refusing to import the delta: it links to node {sorted(missing)[0]}, which is neither in the '
            'archive nor in this profile. Nothing was imported; the next sync will deliver the missing node.'
        )
        raise IntegrityError(msg)


def _check_boundary_invariants(backend: StorageBackend, boundary: list[list[str]]) -> None:
    """Refuse the import when a boundary link would violate a link-uniqueness invariant of the local graph.

    The boundary insertion path bypasses the validation of the archive importer, and from one coherent source
    profile a violation cannot arise — so one arriving means the sender's graph diverged from this profile's,
    and it must not be able to plant a second creator on a data node or a second caller on a process.
    """
    from aiida.common.exceptions import IntegrityError

    # No real graph link connects a node to itself; a self-link in the metadata can only be planted.
    for link in boundary:
        if link[0] == link[1]:
            msg = (
                f'refusing to import the delta: it declares a `{link[2]}` link from node {link[0]} to itself, '
                'which cannot exist in a provenance graph. Nothing was imported.'
            )
            raise IntegrityError(msg)

    checks = [link for link in boundary if link[2] in EXCLUSIVE_LINKS]

    if not checks:
        return

    query = (
        orm.QueryBuilder(backend=backend)
        .append(orm.Node, filters={'uuid': {'in': sorted({link[1] for link in checks})}}, tag='target', project='uuid')
        .append(
            orm.Node,
            with_outgoing='target',
            project='uuid',
            edge_filters={'type': {'in': sorted(EXCLUSIVE_LINKS)}},
            edge_project=['type', 'label'],
        )
    )

    existing: dict[str, list[tuple[str, str, str]]] = {}

    for target_uuid, input_uuid, link_type, label in query.all():
        existing.setdefault(target_uuid, []).append((input_uuid, link_type, label))

    for input_uuid, output_uuid, link_type, label in checks:
        # The indegree of the exclusive classes is one full stop — source and label do not matter — so anything
        # short of the identical quadruple (an idempotent re-delivery) is a second link and refused.
        conflicts = [
            other
            for other in existing.get(output_uuid, [])
            if other[1] in EXCLUSIVE_LINKS[link_type] and other != (input_uuid, link_type, label)
        ]

        if conflicts:
            msg = (
                f'refusing to import the delta: its `{link_type}` link from {input_uuid} to {output_uuid} would '
                f'give the target a second incoming link of that kind (it has one from {conflicts[0][0]}). The '
                'graph of the sender has diverged from this profile; nothing was imported.'
            )
            raise IntegrityError(msg)

        # A sibling link later in this same delta must be held against this one, exactly as it would be against
        # the local graph had the two arrived in separate deltas.
        existing.setdefault(output_uuid, []).append((input_uuid, link_type, label))


def _write_boundary_links(backend: StorageBackend, pending: list[list[str]], tombstones: set[str]) -> list[list[str]]:
    """Write the pending boundary links whose endpoints both exist, and return the ones written or obsolete.

    A link is obsolete when an endpoint was tombstoned: the node was deliberately deleted, so the link died with
    it. A link whose endpoint simply has not arrived yet stays pending until a later sync delivers the node.
    """
    from aiida.orm.entities import EntityTypes

    if not pending:
        return []

    uuids = sorted({uuid for link in pending for uuid in link[:2]})
    query = orm.QueryBuilder(backend=backend).append(orm.Node, filters={'uuid': {'in': uuids}}, project=['uuid', 'id'])
    pk_by_uuid = dict(query.iterall())

    resolved = []
    writable = []

    for link in pending:
        input_uuid, output_uuid, link_type, label = link

        # A journalled self-link predates the pre-check that now refuses them; dropped, never written.
        if input_uuid == output_uuid:
            resolved.append(link)
        # Existence wins over the tombstone: a tombstoned endpoint that provenance closure re-imported in this
        # very delta is held again, and its link must be restored — only a tombstoned *absent* node is obsolete.
        elif input_uuid in pk_by_uuid and output_uuid in pk_by_uuid:
            resolved.append(link)
            writable.append(link)
        elif input_uuid in tombstones or output_uuid in tombstones:
            resolved.append(link)

    if not writable:
        return resolved

    outputs = sorted({pk_by_uuid[link[1]] for link in writable})
    existing = {
        tuple(row)
        for row in orm.QueryBuilder(backend=backend)
        .append(
            entity_type='link',
            filters={'output_id': {'in': outputs}},
            project=['input_id', 'output_id', 'type', 'label'],
        )
        .all()
    }

    rows = []

    for link in writable:
        row = (pk_by_uuid[link[0]], pk_by_uuid[link[1]], link[2], link[3])

        if row in existing:
            continue

        # The invariants were checked when the link was journalled, but the graph can have changed since a
        # crash-recovered entry was written; a link that would violate them now is dropped, not retried forever.
        # The exclusive indegree is one regardless of source and label, so any non-identical link conflicts.
        if link[2] in EXCLUSIVE_LINKS and any(
            output_id == row[1]
            and link_type in EXCLUSIVE_LINKS[link[2]]
            and (input_id, link_type, label) != (row[0], row[2], row[3])
            for input_id, output_id, link_type, label in existing
        ):
            LOGGER.warning('dropping journalled link %s: it now violates a link invariant of this profile', link)
            continue

        rows.append({'input_id': row[0], 'output_id': row[1], 'type': row[2], 'label': row[3]})
        # Later pending links are held against this one too, not only against what the query returned.
        existing.add(row)

    if rows:
        backend.bulk_insert(EntityTypes.LINK, rows)

    return resolved


def _without_unsealed_provenance(nodes: list[orm.Node], *, backend: StorageBackend) -> list[orm.Node]:
    """Return the start nodes whose provenance does not reach a process that is still running.

    A process that excepted is sealed even though a process it called can still be running, and the export refuses to
    write an unsealed process. Since the rules that pull in called processes cannot be turned off, such a seed has to
    be left out entirely; it travels once its child seals.
    """
    if not nodes:
        return nodes

    nodes_by_pk = {cast(int, node.pk): node for node in nodes}
    unsealed = _unsealed_pks(backend, get_nodes_export(nodes_by_pk.keys(), backend=backend, **TRAVERSAL_RULES)['nodes'])

    if not unsealed:
        return nodes

    # Which seeds reach an unsealed process is answered by walking the export in reverse from the unsealed ones, so
    # that it costs one traversal rather than one per seed.
    rules = validate_traversal_rules(GraphTraversalRules.EXPORT, **TRAVERSAL_RULES)
    reaching = traverse_graph(
        unsealed, backend=backend, links_forward=rules['backward'], links_backward=rules['forward']
    )['nodes']

    return [node for pk, node in nodes_by_pk.items() if pk not in reaching]


def _unsealed_pks(backend: StorageBackend, pks: set[int]) -> set[int]:
    """Return the primary keys of the processes among ``pks`` that are not sealed."""

    def query(**filters: Any) -> set[int]:
        return set(
            orm.QueryBuilder(backend=backend)
            .append(orm.ProcessNode, filters={'id': {'in': list(pks)}, **filters}, project='id')
            .all(flat=True)
        )

    # Queried as the complement of the sealed processes, because an unsealed one has no ``sealed`` attribute at all.
    return query() - query(**{f'attributes.{Sealable.SEALED_KEY}': True})


def _get_caching_extras(backend: StorageBackend, uuids: list[str]) -> dict[str, dict[str, Any]]:
    """Return the caching extras of the nodes of a delta that already exist in ``backend``, keyed by UUID."""
    if not uuids:
        return {}

    query = orm.QueryBuilder(backend=backend).append(
        orm.Node, filters={'uuid': {'in': uuids}}, project=['uuid', 'extras']
    )

    return {uuid: {key: extras[key] for key in CACHING_EXTRAS if key in extras} for uuid, extras in query.iterall()}


def _set_caching_extras(backend: StorageBackend, caching_extras: dict[str, dict[str, Any]]) -> None:
    """Restore the caching extras of nodes, dropping the ones they did not have before.

    In one transaction, so that an interruption cannot leave the extras of the peer on some of the nodes and the local
    ones on the rest.
    """
    if not caching_extras:
        return

    query = orm.QueryBuilder(backend=backend).append(orm.Node, filters={'uuid': {'in': list(caching_extras)}})

    with backend.transaction():
        for (node,) in query.iterall():
            extras = {key: value for key, value in node.base.extras.all.items() if key not in CACHING_EXTRAS}
            extras.update(caching_extras[node.uuid])
            node.base.extras.reset(extras)


def _at_head_version(filepath: Path, filepath_migrated: Path) -> Path:
    """Return the archive at the head format version, migrating a copy of it when a peer wrote an older one.

    Peers whose archive format is *newer* are refused at the handshake, before anything is exported or transferred;
    an older one is no obstacle, and this is what makes that true — the importer refuses an archive that is not at
    head rather than migrating it itself.
    """
    archive_format = get_format()

    if archive_format.read_version(filepath) == archive_format.latest_version:
        return filepath

    archive_format.migrate(filepath, filepath_migrated, archive_format.latest_version, compression=0)

    return filepath_migrated


def _archive_uuids(filepath: Path) -> list[str]:
    """Return the UUIDs of the nodes in an archive."""
    with get_format().open(filepath, mode='r') as reader:
        return orm.QueryBuilder(backend=reader.get_backend()).append(orm.Node, project='uuid').all(flat=True)


def _without_nodes(filepath: Path, filepath_filtered: Path, uuids: list[str]) -> Path:
    """Write a copy of an archive from which the given nodes are left out.

    Provenance is kept closed, so a node is still included if one that is kept requires it as an input or an output.
    """
    with get_format().open(filepath, mode='r') as reader:
        archive_backend = reader.get_backend()
        nodes = (
            orm.QueryBuilder(backend=archive_backend).append(orm.Node, filters={'uuid': {'!in': uuids}}).all(flat=True)
        )
        # Every kept node is already a starting entity here, so walking CREATE backwards can only add back a node that
        # was left out on purpose. The export needs that rule to close over ancestry; this re-filter does not.
        create_archive(
            nodes, filename=filepath_filtered, backend=archive_backend, create_backward=False, **TRAVERSAL_RULES
        )

    return filepath_filtered
