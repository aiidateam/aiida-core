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

import dataclasses
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
from aiida.tools.collab.config import COLLAB_PEER_KEY, GENERATED_GROUP_TYPES
from aiida.tools.collab.protocol import ExtrasSnapshot, GroupMembers
from aiida.tools.collab.state import CollabEvent, CollabState, Membership
from aiida.tools.graph.graph_traversers import get_nodes_export, traverse_graph, validate_traversal_rules

if TYPE_CHECKING:
    from aiida.manage.configuration.config import CollabExtrasMode, CollabGroupsMode
    from aiida.orm.implementation import StorageBackend

MERGE_EXTRAS: dict[str, MergeExtrasType] = {'local': ('k', 'n', 'l'), 'sync': ('k', 'c', 'u')}

CACHING_EXTRAS = (NodeCaching._HASH_EXTRA_KEY, NodeCaching.CACHED_FROM_KEY)

# Extras whose key starts with this are private to the profile they live in: they never travel in a refresh and an
# incoming snapshot never overwrites them. The caching extras are the ones AiiDA itself keeps there.
PRIVATE_EXTRA_PREFIX = '_'

# Appended to the label of every computer an import creates, so that a machine that arrived through the collab is
# recognizable as one and a mapping can name it. Neutral rather than the peer's name: a nickname is local and never
# travels, and on a relay it would name the wrong member anyway.
COMPUTER_MARKER = '@collab'

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


def withheld_seeds(backend: StorageBackend) -> list[datetime]:
    """Return the mtimes of the sealed processes that no delta of this profile can carry.

    A seed whose provenance reaches a process that is still running is left out of every delta until that child
    seals, and nothing brings it back when the child never does — a workchain that excepted over a calculation the
    daemon never finished holds its subgraph back for good. The only symptom is a peer that never receives it,
    which is why ``verdi status`` reports the count.
    """
    unsealed = _unsealed_pks(backend)

    if not unsealed:
        return []

    query = orm.QueryBuilder(backend=backend).append(
        orm.ProcessNode,
        filters={'id': {'in': list(_reaching_unsealed(backend, unsealed))}, **seed_filters(None)},
        project='mtime',
    )

    return query.all(flat=True)


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

    computed: datetime
    """When the computation started, which is what a cache of it has to be measured against.

    Distinct from the export instant because a withheld seed pulls that one back to its own mtime, which the seed
    then satisfies for as long as it is withheld: staleness measured against it would be permanent.
    """

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

    computed: datetime | None = None
    """The computation these bytes were cut from, which says whether they are still the ones on offer. The export
    instant will not do: a withheld seed pins it across recomputations."""


@dataclass
class DeltaReport:
    """The outcome of importing a delta."""

    uuids: list[str]
    skipped: list[str]
    size: int
    refreshed: list[str] = field(default_factory=list)
    """The nodes whose extras were replaced by the snapshot that travelled with the delta."""

    members: list[tuple[str, str]] = field(default_factory=list)
    """The ``(group, node)`` memberships written, whether they rode the delta or the membership offer beside it."""


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
    computed = timezone.now()

    seeds = orm.QueryBuilder(backend=backend).append(orm.ProcessNode, filters=seed_filters(cursor)).all(flat=True)
    seed_pks = {node.pk for node in seeds}
    start = {node.pk: node for node in seeds + _imported_nodes(state, cursor, backend)}
    kept = [node for node in start.values() if node.uuid not in claim]
    nodes = _without_unsealed_provenance(kept, backend=backend)

    # A withheld seed has to stay within reach of the next computation, and nothing will touch its mtime when its
    # child seals, so the export instant cannot move past it. The seed filter is inclusive for that reason. Imported
    # nodes cannot be withheld: every export rule that could reach a local unsealed process from them is off by
    # default. The instant the computation was taken at is kept beside it, because that pull-back is what a peer is
    # owed and not a statement about when this delta was computed.
    kept_pks = {cast(int, node.pk) for node in nodes}
    withheld = [node for node in kept if node.pk not in kept_pks and node.pk in seed_pks]
    instant = min(node.mtime for node in withheld) if withheld else computed

    traversed = get_nodes_export(starting_pks=kept_pks, get_links=True, backend=backend, **TRAVERSAL_RULES)
    pks = traversed['nodes']
    links = list(traversed['links'] or [])

    uuid_by_pk = {}

    if pks:
        query = orm.QueryBuilder(backend=backend).append(orm.Node, filters={'id': {'in': pks}}, project=['id', 'uuid'])
        uuid_by_pk = dict(query.iterall())

    return Delta(uuid_by_pk=uuid_by_pk, links=links, instant=instant, computed=computed)


def required_refused(
    *, delta: Delta, backend: StorageBackend, want: frozenset[str] | set[str], refuse: frozenset[str] | set[str]
) -> set[str]:
    """Return the refused nodes the wanted provenance requires, which therefore travel despite the refusal.

    A requester refuses the nodes it deleted, but provenance is never delivered with holes in it: a wanted
    calculation still needs the input it consumed. The import re-filters what it receives under its own rules and
    closes over such a node anyway, so the cut is taken under those very rules — ``create_backward`` off, since an
    output does not need its creator — and what they reach is put back into the want here, where the archive can
    still be built to hold it.
    """
    refused_pks = {pk for pk, uuid in delta.uuid_by_pk.items() if uuid in refuse}

    if not refused_pks:
        return set()

    want_pks = {pk for pk, uuid in delta.uuid_by_pk.items() if uuid in want}
    reached = get_nodes_export(
        starting_pks=want_pks, get_links=False, backend=backend, create_backward=False, **TRAVERSAL_RULES
    )['nodes']

    return {delta.uuid_by_pk[pk] for pk in refused_pks & set(reached)}


def export_delta(
    filepath: Path,
    *,
    delta: Delta,
    backend: StorageBackend,
    want: frozenset[str] | set[str] | None = None,
    refuse: frozenset[str] | set[str] = frozenset(),
    groups_mode: CollabGroupsMode = 'local',
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
    :param refuse: the UUIDs the requester deleted and will not take. A link between the cut and one of them is
        dropped rather than carried as a boundary link, because that endpoint exists neither in the archive nor on
        the requester and the import would refuse the whole delta over it. Whatever the wanted provenance requires
        belongs in ``want`` instead, see ``required_refused``.
    :param groups_mode: under ``grow``, the curated groups of the exported nodes travel with their memberships.
    """
    want_uuids = set(delta.uuid_by_pk.values()) if want is None else set(want) & set(delta.uuid_by_pk.values())
    want_pks = {pk for pk, uuid in delta.uuid_by_pk.items() if uuid in want_uuids}
    refused_pks = {pk for pk, uuid in delta.uuid_by_pk.items() if uuid in refuse} - want_pks

    internal = []
    boundary = []

    for link in delta.links:
        in_want = (link.source_id in want_pks) + (link.target_id in want_pks)

        if in_want == 2:
            internal.append(link)
        elif in_want == 1 and not {link.source_id, link.target_id} & refused_pks:
            boundary.append(
                [delta.uuid_by_pk[link.source_id], delta.uuid_by_pk[link.target_id], link.link_type, link.link_label]
            )

    _write_thin_archive(
        filepath,
        backend=backend,
        node_pks=want_pks,
        links=internal,
        boundary=boundary,
        groups_mode=groups_mode,
    )

    return DeltaExport(filepath=filepath, uuids=sorted(want_uuids), instant=delta.instant, computed=delta.computed)


def _write_thin_archive(
    filepath: Path,
    *,
    backend: StorageBackend,
    node_pks: set[int],
    links: list[Any],
    boundary: list[list[str]],
    groups_mode: CollabGroupsMode,
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

    def related_pks(entity: Any, relationship: str, filters: dict[str, Any] | None = None) -> set[int]:
        if not node_pks:
            return set()

        kwargs: dict[str, Any] = {relationship: 'node'}
        query = (
            orm.QueryBuilder(backend=backend)
            .append(orm.Node, filters={'id': {'in': node_pks}}, tag='node')
            .append(entity, project='id', filters=filters, **kwargs)
            .distinct()
        )
        return set(query.all(flat=True))

    group_pks = (
        related_pks(orm.Group, 'with_node', {'type_string': {'!in': list(GENERATED_GROUP_TYPES)}})
        if groups_mode == 'grow'
        else set()
    )

    entity_pks: dict[EntityTypes, set[int]] = {
        EntityTypes.USER: related_pks(orm.User, 'with_node'),
        EntityTypes.COMPUTER: related_pks(orm.Computer, 'with_node'),
        EntityTypes.GROUP: group_pks,
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

    if group_pks:
        query = (
            orm.QueryBuilder(backend=backend)
            .append(orm.Group, filters={'id': {'in': group_pks}}, tag='group')
            .append(orm.User, with_group='group', project='id')
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

        if group_pks:
            # Restricted to the exported nodes: a group holds members the requester is not entitled to in this
            # delta, and a membership row naming an absent node would be an unresolvable reference.
            membership = (
                orm.QueryBuilder(backend=backend)
                .append(orm.Group, filters={'id': {'in': group_pks}}, tag='group', project='id')
                .append(orm.Node, with_group='group', filters={'id': {'in': node_pks}}, project='id')
            )
            member_rows = [{'dbgroup_id': group_pk, 'dbnode_id': node_pk} for group_pk, node_pk in membership.all()]

            for _, rows in batch_iter(member_rows, DEFAULT_BATCH_SIZE, lambda row: row):
                writer.bulk_insert(EntityTypes.GROUP_NODE, rows, allow_defaults=True)

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


def vanished_nodes(backend: StorageBackend, uuids: set[str] | frozenset[str]) -> set[str]:
    """Return which of the given nodes the profile no longer holds.

    A delta is computed once and cached, and a ``verdi node delete`` here is no staleness signal for that cache —
    it moves no seal and records no import. The cut taken from it would name rows that are gone: the node is
    silently missing from the archive while the links to it still travel, so the requester either refuses the whole
    delta or attaches a link to a node that exists nowhere.

    Asked by UUID and not by the key the delta holds these under: SQLite reuses a freed rowid, and the cut goes
    by key, so a replacement would be shipped under a manifest that never named it.
    """
    asked = sorted(uuids)

    if not asked:
        return set()

    query = orm.QueryBuilder(backend=backend).append(orm.Node, filters={'uuid': {'in': asked}}, project='uuid')

    return set(asked) - set(query.all(flat=True))


def refresh_offer(*, state: CollabState, backend: StorageBackend, cursor: datetime | None) -> dict[str, datetime]:
    """Return the mtime of every node whose extras this profile may hold a newer version of than a peer at ``cursor``.

    Under the ``sync`` policy this is what the manifest is for nodes, but for the extras of *shared* ones: the nodes
    edited here since the cursor, united with everything that entered this profile since then — refreshed as a
    snapshot or imported as a node. That union is the same one that makes relayed provenance travel, here so that an
    extras edit relayed A→B→C travels with pairwise pulls alone. The imported leg is what covers the edit that
    arrived *inside* a delta: a peer receiving the node for the first time after the edit gets the new extras in the
    archive row, under the origin's mtime, so neither the mtime bound nor the refresh log names it. Only mtimes are
    offered: the receiver holds the authoritative comparison, its own mtimes, and asks for the snapshots it turns
    out to need.

    A peer without a cursor is offered every node, because it is not true that such a peer holds nothing of this
    profile: it holds whatever it gave this profile in the first place, and those extras are in no delta. The offer
    is only mtimes, and a null-cursor negotiation already ships a manifest of the whole shareable graph, so the
    unbounded offer costs a payload of the order of one already being sent.
    """
    filters: dict[str, Any] = {}

    if cursor is not None:
        relayed = sorted(state.refreshed_uuids_since(cursor) | state.imported_uuids_since(cursor))
        filters = {'mtime': {'>=': cursor}}

        if relayed:
            filters = {'or': [filters, {'uuid': {'in': relayed}}]}

    query = orm.QueryBuilder(backend=backend).append(orm.Node, filters=filters, project=['uuid', 'mtime'])

    return dict(query.iterall())


def refresh_wanted(backend: StorageBackend, offer: dict[str, datetime]) -> list[str]:
    """Return which of the offered nodes this profile holds an older version of the extras of.

    A node this profile does not hold has no extras to replace — it either travels in the delta with them or is
    not shared at all — and being held is the whole condition: a tombstone gates delivery, not participation, so a
    node this profile deleted and provenance later brought back takes part in the extras exchange again. One that
    is merely deleted has no mtime row and falls out here on its own.
    """
    if not offer:
        return []

    query = orm.QueryBuilder(backend=backend).append(
        orm.Node, filters={'uuid': {'in': sorted(offer)}}, project=['uuid', 'mtime']
    )

    return sorted(uuid for uuid, mtime in query.iterall() if offer[uuid] > mtime)


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


def membership_offer(*, state: CollabState, backend: StorageBackend, cursor: datetime | None) -> list[GroupMembers]:
    """Return the group memberships this profile gained since ``cursor``, with the identity of their groups.

    Under the ``grow`` policy this is to curation what the delta is to provenance: a ``GROUP_NODE`` row has no
    timestamp of its own, so the journal — which records a person curating here and a peer's addition applied here
    alike — is the only answer to "what changed since T". That union is what makes a curation made on A reach C
    through B by pairwise syncs, exactly as the event union does for relayed provenance and extras.

    Only memberships are offered, never removals: under ``grow`` the set of members grows and nothing else. A group
    that no longer exists here is dropped, since there is no label left to create it under on the other side.
    """
    pairs = state.memberships_since(cursor)

    if not pairs:
        return []

    query = orm.QueryBuilder(backend=backend).append(
        orm.Group,
        filters={'uuid': {'in': sorted({group for group, _ in pairs})}},
        project=['uuid', 'label', 'type_string'],
    )
    groups = {uuid: (label, type_string) for uuid, label, type_string in query.iterall()}
    nodes: dict[str, list[str]] = {}

    for group, node in sorted(pairs):
        if group in groups:
            nodes.setdefault(group, []).append(node)

    return [
        GroupMembers(uuid=group, label=groups[group][0], type_string=groups[group][1], nodes=members)
        for group, members in nodes.items()
    ]


def members_wanted(backend: StorageBackend, offer: list[GroupMembers]) -> list[GroupMembers]:
    """Return the offered memberships this profile can apply and does not hold yet.

    A pair whose node is not here — never shared, or deleted — is dropped rather than kept pending: the
    memberships of a node travel with the node, so whichever later sync delivers it delivers them too. Being held
    is the whole condition, tombstone or not: a node this profile deleted and provenance later brought back is
    curated again like any other, since a tombstone gates delivery rather than participation. The groups
    AiiDA generates for itself are refused whatever a peer offers: they describe the history of the profile that
    made them, and this profile decides what enters it.

    The offer is wire data, so it is folded first: a group row and a membership row are both unique, and a peer
    naming a group twice or a node twice within one entry would otherwise raise out of the storage layer, past
    every handler the sync has and with the archive already committed.
    """
    folded: dict[str, GroupMembers] = {}

    for group in offer:
        if group.type_string not in GENERATED_GROUP_TYPES:
            folded.setdefault(group.uuid, dataclasses.replace(group, nodes=[])).nodes.extend(group.nodes)

    candidates = [dataclasses.replace(group, nodes=list(dict.fromkeys(group.nodes))) for group in folded.values()]
    wanted_nodes = {node for group in candidates for node in group.nodes}

    if not wanted_nodes:
        return []

    query = orm.QueryBuilder(backend=backend).append(
        orm.Node, filters={'uuid': {'in': sorted(wanted_nodes)}}, project='uuid'
    )
    held_nodes = set(query.all(flat=True))

    if not held_nodes:
        return []

    membership = (
        orm.QueryBuilder(backend=backend)
        .append(
            orm.Group,
            filters={'uuid': {'in': sorted({group.uuid for group in candidates})}},
            tag='group',
            project='uuid',
        )
        .append(orm.Node, with_group='group', filters={'uuid': {'in': sorted(held_nodes)}}, project='uuid')
    )
    held = {(group, node) for group, node in membership.all()}

    wanted = [
        dataclasses.replace(
            group, nodes=[node for node in group.nodes if node in held_nodes and (group.uuid, node) not in held]
        )
        for group in candidates
    ]

    return [group for group in wanted if group.nodes]


def apply_members(backend: StorageBackend, offer: list[GroupMembers]) -> list[tuple[str, str]]:
    """Insert the offered memberships this profile lacks, creating the groups it does not hold, and return them.

    A group is created under the offered UUID, so that every member of the collab holds one group where one group
    was curated, however many hops the offer took to arrive. Its label is deduplicated against the labels in use
    here, as the archive import does, because a label collides where a UUID cannot.
    """
    from aiida.orm.entities import EntityTypes

    wanted = members_wanted(backend, offer)

    if not wanted:
        return []

    query = orm.QueryBuilder(backend=backend).append(
        orm.Group, filters={'uuid': {'in': sorted({group.uuid for group in wanted})}}, project=['uuid', 'id']
    )
    group_pks = dict(query.iterall())
    missing = [group for group in wanted if group.uuid not in group_pks]

    if missing:
        # Keyed by type string, because that is what the uniqueness constraint on a group label is keyed by.
        taken: dict[str, set[str]] = {}
        query = orm.QueryBuilder(backend=backend).append(orm.Group, project=['label', 'type_string'])

        for label, type_string in query.all():
            taken.setdefault(type_string, set()).add(label)

        rows = []

        for group in missing:
            in_use = taken.setdefault(group.type_string, set())
            label = _unique_label(group.label, in_use)
            in_use.add(label)
            rows.append(
                {
                    'uuid': group.uuid,
                    'label': label,
                    'type_string': group.type_string,
                    'user_id': cast(orm.User, backend.default_user).pk,
                }
            )

        pks = backend.bulk_insert(EntityTypes.GROUP, rows, allow_defaults=True)
        group_pks.update(zip([group.uuid for group in missing], pks))

    query = orm.QueryBuilder(backend=backend).append(
        orm.Node,
        filters={'uuid': {'in': sorted({node for group in wanted for node in group.nodes})}},
        project=['uuid', 'id'],
    )
    node_pks = dict(query.iterall())
    applied = [(group.uuid, node) for group in wanted for node in group.nodes]

    backend.bulk_insert(
        EntityTypes.GROUP_NODE,
        [{'dbgroup_id': group_pks[group], 'dbnode_id': node_pks[node]} for group, node in applied],
    )

    return applied


def _unique_label(stem: str, taken: set[str], suffix: str = '') -> str:
    """Return ``stem`` with ``suffix`` appended, deduplicated against ``taken`` by an index kept before the suffix.

    The index goes before the suffix so that a marked label ends in its marker whatever the dedup did to it:
    ``lumi-2@collab``, never ``lumi@collab-2``, which the next hop would no longer recognize as marked.
    """
    if f'{stem}{suffix}' not in taken:
        return f'{stem}{suffix}'

    index = 2

    while f'{stem}-{index}{suffix}' in taken:
        index += 1

    return f'{stem}-{index}{suffix}'


def _public_extras(extras: dict[str, Any]) -> dict[str, Any]:
    """Return the extras that are shared with the collab: everything outside the private ``_`` namespace."""
    return {key: value for key, value in extras.items() if not key.startswith(PRIVATE_EXTRA_PREFIX)}


def _apply_refresh(backend: StorageBackend, refresh: list[ExtrasSnapshot]) -> list[str]:
    """Replace the extras of the nodes whose snapshot is the newer one, and return which were written.

    The whole dict is replaced rather than merged, which is what propagates a deletion as absence, except that the
    private ``_`` namespace of this profile — the caching extras among it — is kept and never taken from the peer.
    The snapshot's mtime is written as the node's own, so that this profile does not become the newest side and
    echo the same extras back on the next exchange.
    """
    from aiida.orm.entities import EntityTypes

    wanted = set(refresh_wanted(backend, {snapshot.uuid: snapshot.mtime for snapshot in refresh}))

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
    computer_map: dict[str, str] | None = None,
    refresh: list[ExtrasSnapshot] | None = None,
    groups_mode: CollabGroupsMode = 'local',
    members: list[GroupMembers] | None = None,
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
    :param groups_mode: under ``grow``, the groups of the delta and the offered memberships are applied and every
        membership written here is journalled, so that it travels on to the peers of this profile.
    :param members: memberships of nodes this profile already holds, offered beside the delta. They are what makes
        a node curated after it was shared reach anybody: no delta can carry it, since the node itself never
        travels again.
    :param peer: the identity the delta was received under, which keys the cursor: the profile UUID of the peer.
    :param instant: the export instant carried with the delta, which the cursor for ``peer`` advances to.
    :param include_deleted: import nodes that were deleted locally after all, and drop their tombstones.
    :param computer_map: peer computer label to local computer label; imported calculations that ran on a mapped
        computer get the hash they would have on the local one, so they can be cache hits (see ``_remap_hashes``).
    :raises ~aiida.common.exceptions.IntegrityError: when the delta links to a node that exists neither in the
        archive nor locally, or a boundary link would violate a link invariant of the local graph; nothing is
        imported in either case.
    """
    size = filepath.stat().st_size

    with tempfile.TemporaryDirectory() as dirpath:
        # A peer on an older aiida-core writes an older archive format, which the importer refuses rather than
        # migrating, so the delta is brought to the head version first — as `verdi archive import` does.
        filepath = _at_head_version(filepath, Path(dirpath) / 'migrated.aiida')

        uuids, delivered, computers = _archive_contents(filepath)
        boundary = _boundary_links(filepath)
        tombstoned = [] if include_deleted else sorted(state.tombstones.intersection(uuids))

        if delivered and groups_mode != 'grow':
            # This profile keeps its groups to itself, so the delta's have to go before it lands — a sender that
            # declares `local` and serves group rows anyway is the whole reason the gate sits on this side.
            filepath = _without_groups(filepath, Path(dirpath) / 'ungrouped.aiida')
            delivered = []

        # Which groups were held before is what tells apart the memberships the import writes by itself — it
        # creates the rows of a group it creates — from the ones that were already here. The same question is
        # asked of the computers, whose answer decides which of them the import is about to create.
        held_groups = _held_uuids(backend, orm.Group, [group.uuid for group in delivered])
        held_computers = _held_uuids(backend, orm.Computer, list(computers))
        arriving = {uuid: label for uuid, label in computers.items() if uuid not in held_computers}
        imported_groups = delivered

        # Resolved before anything lands, so that a stale mapping aborts the import instead of crashing after it,
        # half-done and unlogged.
        computer_uuids = resolve_computer_map(backend, computer_map) if computer_map else {}

        # The caching extras of the peer describe their profile, not this one, so the merge must not be able to
        # carry them over. New nodes are stripped of them by the import itself, existing ones are restored below.
        caching_extras = _get_caching_extras(backend, uuids) if extras_mode == 'sync' else {}

        if tombstoned:
            filepath = _without_nodes(filepath, Path(dirpath) / 'delta.aiida', tombstoned)
            uuids = _archive_uuids(filepath)
            # Re-exporting the surviving nodes alone is exactly how the groups are dropped for a `local` profile,
            # so the archive that lands now carries none: the import writes no membership of its own, and every
            # pair that still applies has to be written after it.
            imported_groups = []
            # A boundary link whose archive endpoint was dropped with its tombstone must not be re-attached.
            boundary = [link for link in boundary if link[0] in uuids or link[1] in uuids]

        # Checked before anything lands: a boundary endpoint that exists neither in the archive nor locally would
        # leave the imported nodes permanently disconnected from provenance the sender counted on, and a boundary
        # link that violates a local link invariant must not be plantable by a diverged or hostile sender.
        _check_boundary_resolvable(backend, uuids, boundary)
        _check_boundary_invariants(backend, boundary)

        # The boundary links and the computers about to be created are journalled before the import, which commits
        # its own transaction: a crash between the two leaves both pending, and the next import finishes them
        # instead of losing them. Neither can be re-derived afterwards — by then the links look written and the
        # computers look like this profile's own.
        if boundary or arriving:
            with CollabState.mutate(state.filepath) as fresh:
                fresh.pending_links.extend(link for link in boundary if link not in fresh.pending_links)
                fresh.pending_computers.update(arriving)

        import_archive(
            filepath,
            backend=backend,
            merge_extras=MERGE_EXTRAS[extras_mode],
            create_group=False,
        )

    _set_caching_extras(backend, caching_extras)

    if computer_uuids:
        _remap_hashes(backend, uuids, computer_uuids)

    refreshed = _apply_refresh(backend, refresh or []) if extras_mode == 'sync' else []

    # Last of the extras writes of this import, so that none of the others has to carry the key through its own
    # read-modify-write of the same dict.
    _set_peer_extra(backend, uuids, peer)

    # Both ways a membership arrives go through the same apply, which is what lets a pair whose group the archive
    # lost still create it here. A tombstone speaks for what this import leaves deleted and nothing more: a node
    # the delta brings back anyway — because provenance of it depends on the node, or because `--include-deleted`
    # asked for it — is here afterwards, and the apply's own held-check is what tells the two apart. Only what was
    # written is journalled — a pair sent back to the peer that already has it would otherwise bounce between the
    # two forever, and a pair claimed but not written would be relayed to a third peer this profile cannot back up.
    archived = set(uuids)
    applied = sorted(
        {
            *apply_members(backend, delivered),
            # What the import wrote by itself, which is the memberships of a group that was not here before it
            # ran — and nothing at all once the re-filter has taken that group out of the archive.
            *(
                (group.uuid, node)
                for group in imported_groups
                if group.uuid not in held_groups
                for node in group.nodes
                if node in archived
            ),
            *(apply_members(backend, members or []) if groups_mode == 'grow' else []),
        }
    )
    # Appended to a freshly read state under the lock instead of saving ``state``: that was read before an import
    # that can take minutes, and writing it back wholesale would erase every tombstone recorded in the meantime.
    with CollabState.mutate(state.filepath) as fresh:
        written = _write_boundary_links(backend, fresh.pending_links, fresh.tombstones)
        fresh.pending_links = [link for link in fresh.pending_links if link not in written]

        # Emptied whether or not every computer of it was there to be marked: one the delta no longer carries was
        # never created here, and if a later delta does create it, that import journals it again.
        _mark_imported_computers(backend, fresh.pending_computers)
        fresh.pending_computers.clear()

        if include_deleted:
            fresh.tombstones.difference_update(uuids)

        # A retried push carries the instant of its original export, which can predate a pull that advanced the
        # cursor in the meantime; the cursor means "I hold everything the peer had at T", so it never moves back.
        held = fresh.cursors.get(peer)
        fresh.cursors[peer] = max(held, instant) if held is not None else instant

        # Stamped under the lock, not before waiting for it, as the membership journal is: a negotiation served in
        # the window between the two reads a state without the event and stamps its computation after its time, so
        # no later negotiation unions these nodes either — the imported provenance becomes invisible for good.
        fresh.events.append(CollabEvent(time=timezone.now(), direction='pull', peer=peer, uuids=uuids, size=size))

        # Recorded apart from the import: these nodes were already held, so they are no claim of new provenance,
        # but a peer pulling from here later has to learn that their extras moved on.
        if refreshed:
            fresh.events.append(
                CollabEvent(time=timezone.now(), direction='refresh', peer=peer, uuids=refreshed, size=0)
            )

        # Journalled as if curated here, which for the peers of this profile is exactly what it is: they hold no
        # cursor of the peer this delta came from, and only the journal makes a membership relay A→B→C.
        stamped = timezone.now()
        fresh.memberships.extend(Membership(time=stamped, group=group, node=node) for group, node in applied)

    return DeltaReport(
        uuids=uuids, skipped=sorted(set(tombstoned) - set(uuids)), size=size, refreshed=refreshed, members=applied
    )


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


def _held_uuids(backend: StorageBackend, entity: type[orm.Entity], uuids: list[str]) -> set[str]:
    """Return which of the given entities this profile already holds, which is what an import cannot have created."""
    if not uuids:
        return set()

    query = orm.QueryBuilder(backend=backend).append(entity, filters={'uuid': {'in': sorted(uuids)}}, project='uuid')

    return set(query.all(flat=True))


def _mark_imported_computers(backend: StorageBackend, computers: dict[str, str]) -> None:
    """Label every computer an import created for what it is: a machine that arrived through the collab.

    ``lumi@collab`` says which computers a mapping could name, in ``verdi computer list`` and in the refusal of
    one that names something else. It is idempotent — a label that already carries the marker keeps it — so the
    second hop of a relay renames nothing and every member but the originator holds one machine under one label.
    The originator keeps its plain ``lumi``: the importer matches an existing computer by UUID and never renames
    it, which is also why a computer that circles the collab back to its owner creates no second row.

    :param computers: the journalled computers an import created and has not named yet, keyed by UUID and
        labelled as the *sender* labels them, which is what the marker is derived from — the importer may already
        have renamed the row here on a label clash.
    """
    # Intersected with what the profile holds, because a computer of the archive whose nodes the tombstone
    # re-filter dropped never reached it.
    current = dict(orm.QueryBuilder(backend=backend).append(orm.Computer, project=['uuid', 'label']).all())
    created = set(computers).intersection(current)

    if not created:
        return

    # A row already carrying the marker is left alone, which is the idempotence: the second hop of a relay, and
    # a row an earlier pass renamed whose journal entry outlived it — a lost state save, or a hand relabel after
    # a crash in the window the journal exists for. Every row that is renamed therefore carries a label without
    # the marker and is given one with it, while `taken` holds every label in use, so no update can land on a
    # label another row still holds however the arbitrary order comes out — and the label column is unique.
    keeps = {uuid for uuid in created if current[uuid].endswith(COMPUTER_MARKER)}
    taken = set(current.values())
    collection = orm.Computer.get_collection(backend)

    for uuid in sorted(created - keeps):
        label = _unique_label(computers[uuid].removesuffix(COMPUTER_MARKER), taken, COMPUTER_MARKER)
        taken.add(label)
        collection.get(uuid=uuid).label = label


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

    reaching = _reaching_unsealed(backend, unsealed)

    return [node for pk, node in nodes_by_pk.items() if pk not in reaching]


def _reaching_unsealed(backend: StorageBackend, unsealed: set[int]) -> set[int]:
    """Return the primary keys of the nodes whose export closure holds one of the given unsealed processes.

    Answered by walking the export in reverse from the unsealed ones, so that it costs one traversal rather than
    one per node.
    """
    rules = validate_traversal_rules(GraphTraversalRules.EXPORT, **TRAVERSAL_RULES)

    return traverse_graph(unsealed, backend=backend, links_forward=rules['backward'], links_backward=rules['forward'])[
        'nodes'
    ]


def _unsealed_pks(backend: StorageBackend, pks: set[int] | None = None) -> set[int]:
    """Return the primary keys of the processes that are not sealed, among ``pks`` when one is given.

    Asked as the absence of the attribute, because ``seal()`` is its only writer and only ever writes ``True``: a
    process without the key is exactly an unsealed one. The complement of the sealed processes answers the same,
    but only after materialising every process in the profile, which the unbounded caller cannot afford.
    """
    filters: dict[str, Any] = {'attributes': {'!has_key': Sealable.SEALED_KEY}}

    if pks is not None:
        filters['id'] = {'in': list(pks)}

    return set(orm.QueryBuilder(backend=backend).append(orm.ProcessNode, filters=filters, project='id').all(flat=True))


def apply_computer_map(backend: StorageBackend, computer_map: dict[str, str]) -> int:
    """Write remapped hashes onto every calculation that ran on a mapped computer.

    Run when the mapping changes, so that calculations imported before it was declared become cache sources
    too; every import applies the same remap to its own delta.

    :returns: the number of calculations whose hash was written.
    """
    return _remap_hashes(backend, None, resolve_computer_map(backend, computer_map))


def resolve_computer_map(backend: StorageBackend, computer_map: dict[str, str]) -> dict[str, str]:
    """Return peer computer label to local computer UUID, refusing the whole mapping when a pair cannot be honoured.

    Both halves must name a computer this profile holds. The local one is what the remapped hash is computed for;
    the peer one is the condition ``_remap_hashes`` silently imposes anyway, since it finds the calculations to
    remap by querying *this* profile for that label — so a mapping naming a computer that has never arrived here
    used to remap nothing and say nothing. It must also carry the marker every arrived computer is labelled with:
    a pair written the natural way round, ``lumi=lumi@collab``, otherwise passes every check and writes remapped
    hashes onto the calculations of this profile's own ``lumi``, breaking local caching for good. A pair whose
    halves resolve to the same computer is refused for that same reason, and is what the marker rule generalizes.

    Every unusable pair of the call is named at once, since the mapping is a single option and applying the good
    half of it leaves a set of equivalences that is harder to reason about than none.

    :raises ~aiida.common.exceptions.ConfigurationError: when any pair names a computer this profile does not hold,
        maps one onto itself, or names as the peer half a computer that did not arrive through the collab.
    """
    from aiida.common.exceptions import ConfigurationError

    uuids = dict(orm.QueryBuilder(backend=backend).append(orm.Computer, project=['label', 'uuid']).all())
    unknown_peer = sorted(label for label in computer_map if label not in uuids)
    unknown_local = sorted({label for label in computer_map.values() if label not in uuids})
    unmarked = {peer: local for peer, local in computer_map.items() if not peer.endswith(COMPUTER_MARKER)}
    reflexive = sorted(
        f'`{peer}`=`{local}`'
        for peer, local in computer_map.items()
        if peer in uuids and local in uuids and uuids[peer] == uuids[local]
    )
    problems = []

    if unknown_peer:
        listed = ', '.join(f'`{label}`' for label in unknown_peer)
        known = ', '.join(sorted(label for label in uuids if label.endswith(COMPUTER_MARKER)))
        problems.append(
            f'{listed} is not a computer known to this profile — pull from a peer that holds it first.'
            if len(unknown_peer) == 1
            else f'{listed} are not computers known to this profile — pull from a peer that holds them first.'
        )
        problems.append(f'Known peer computers: {known}' if known else 'No peer computer has arrived here yet.')

    if unknown_local:
        listed = ', '.join(f'`{label}`' for label in unknown_local)
        problems.append(f'no local computer of this profile is labelled {listed}.')

    if unmarked:
        listed = ', '.join(f'`{label}`' for label in sorted(unmarked))
        problems.append(
            f'{listed} did not arrive through the collab: a computer that did is labelled '
            f'`<label>{COMPUTER_MARKER}`, and the peer half of a mapping is that computer.'
        )
        # Offered only for a pair that would actually validate the other way round: both halves have to be
        # computers this profile holds, or the suggestion is one this same function would refuse in turn.
        swapped = sorted(
            f'`{local}={peer}`'
            for peer, local in unmarked.items()
            if local.endswith(COMPUTER_MARKER) and local in uuids and peer in uuids
        )

        if swapped:
            problems.append(f'The halves look the wrong way round; did you mean {", ".join(swapped)}?')

    if reflexive:
        problems.append(f'{", ".join(reflexive)}: the two halves are one and the same computer.')

    if problems:
        msg = '\n'.join(['the `collab.computer_map` option cannot be applied to this profile:', *problems])
        raise ConfigurationError(msg)

    return {peer_label: uuids[local_label] for peer_label, local_label in computer_map.items()}


def _remap_hashes(backend: StorageBackend, uuids: list[str] | None, computer_uuids: dict[str, str]) -> int:
    """Write onto each mapped calculation the hash it would have on the local computer.

    The hash of a calculation includes the UUID of its computer, which differs between the profiles of a collab,
    so an imported calculation can never be a cache hit for a local submission on its own. Where the user declared
    a peer computer equivalent to a local one, the hash is recomputed with the local computer's UUID substituted;
    everything else about the node, including which computer it actually ran on, stays untouched.

    :param uuids: the nodes of the delta being imported, or ``None`` for every mapped calculation.
    :param computer_uuids: peer computer label to local computer UUID, from ``resolve_computer_map``.
    :returns: the number of calculations whose hash was written.
    """
    from aiida.common.exceptions import HashingError
    from aiida.common.hashing import make_hash
    from aiida.orm.entities import EntityTypes

    filters: dict[str, Any] = {'uuid': {'in': uuids}} if uuids is not None else {}

    query = (
        orm.QueryBuilder(backend=backend)
        .append(orm.Computer, filters={'label': {'in': list(computer_uuids)}}, project='label', tag='computer')
        .append(orm.CalcJobNode, with_computer='computer', filters=filters, project='*')
    )

    rows = []

    for label, node in query.iterall():
        objects = node.base.caching.get_objects_to_hash()
        objects['computer_uuid'] = computer_uuids[label]

        try:
            remapped = make_hash(objects)
        except HashingError:
            node.logger.exception('remapping the hash failed, the node stays a cache miss')
            continue

        # Written through a bulk update with the mtime passed explicitly, because a regular extras write fires
        # the ``mtime`` ``onupdate``, and a freshly stamped node re-enters the delta of the next export — the
        # peer would be echoed the whole subgraph it just sent, on every sync, forever.
        extras = dict(node.base.extras.all)
        extras[NodeCaching._HASH_EXTRA_KEY] = remapped
        rows.append({'id': node.pk, 'extras': extras, 'mtime': node.mtime})

    if rows:
        backend.bulk_update(EntityTypes.NODE, rows)

    return len(rows)


def _set_peer_extra(backend: StorageBackend, uuids: list[str], peer: str) -> None:
    """Record on each node of the delta which peer this profile took it from.

    A relayed node names the relay rather than the author: this answers "who did I get it from", which is the
    question the node's own provenance cannot answer and the only one this profile has evidence for.

    Written through a bulk update with the mtime passed explicitly, for the reason ``_remap_hashes`` gives: an
    ordinary extras write fires the ``mtime`` ``onupdate``, and every node just imported would re-enter the next
    delta this profile serves — the peer would be echoed the subgraph it just sent, on every sync, forever.
    """
    from aiida.orm.entities import EntityTypes

    if not uuids:
        return

    query = orm.QueryBuilder(backend=backend).append(
        orm.Node, filters={'uuid': {'in': uuids}}, project=['id', 'extras', 'mtime']
    )

    rows = [
        {'id': pk, 'extras': {**extras, COLLAB_PEER_KEY: peer}, 'mtime': mtime} for pk, extras, mtime in query.iterall()
    ]

    backend.bulk_update(EntityTypes.NODE, rows)


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


def _archive_contents(filepath: Path) -> tuple[list[str], list[GroupMembers], dict[str, str]]:
    """Return the UUIDs of the nodes in an archive, the groups it carries with their members, and its computers.

    All in one read: opening an archive extracts its database to a temporary file, so the import path asks for
    everything it needs from a single open. The groups are empty unless the sender exported under ``grow``, and
    are described exactly as an offer describes them, so that both ways a membership can arrive are applied by
    the same function. A group with no members is reported too, since it is still a group row to gate on.

    The computers are keyed by UUID and carry the label the *sender* holds them under, which is what the marking
    of an imported computer needs: the importer may already have renamed the row here on a label clash.
    """
    with get_format().open(filepath, mode='r') as reader:
        backend = reader.get_backend()
        uuids = orm.QueryBuilder(backend=backend).append(orm.Node, project='uuid').all(flat=True)
        computers = dict(orm.QueryBuilder(backend=backend).append(orm.Computer, project=['uuid', 'label']).all())
        rows = (
            orm.QueryBuilder(backend=backend)
            .append(orm.Group, tag='group', project=['uuid', 'label', 'type_string'])
            .append(orm.Node, with_group='group', project='uuid', outerjoin=True)
            .all()
        )

    groups: dict[str, GroupMembers] = {}

    for group_uuid, label, type_string, node_uuid in rows:
        group = groups.setdefault(
            group_uuid, GroupMembers(uuid=group_uuid, label=label, type_string=type_string, nodes=[])
        )

        if node_uuid is not None:
            group.nodes.append(node_uuid)

    return uuids, [groups[uuid] for uuid in sorted(groups)], computers


def _archive_uuids(filepath: Path) -> list[str]:
    """Return the UUIDs of the nodes in an archive."""
    return _archive_contents(filepath)[0]


def _without_groups(filepath: Path, filepath_filtered: Path) -> Path:
    """Write a copy of an archive from which the groups and their memberships are left out.

    ``create_archive`` carries only the groups it is handed as entities, so re-exporting the nodes alone is all it
    takes to drop them.
    """
    return _without_nodes(filepath, filepath_filtered, [])


def _without_nodes(filepath: Path, filepath_filtered: Path, uuids: list[str]) -> Path:
    """Write a copy of an archive from which the given nodes are left out.

    Provenance is kept closed, so a node is still included if one that is kept requires it as an input or an output.
    """
    with get_format().open(filepath, mode='r') as reader:
        archive_backend = reader.get_backend()
        # An empty exclusion keeps every node — which is how the groups are dropped and nothing else with them —
        # and has to be spelled as no filter at all, since an empty `!in` is not a query.
        filters = {'uuid': {'!in': uuids}} if uuids else {}
        nodes = orm.QueryBuilder(backend=archive_backend).append(orm.Node, filters=filters).all(flat=True)
        # Every kept node is already a starting entity here, so walking CREATE backwards can only add back a node that
        # was left out on purpose. The export needs that rule to close over ancestry; this re-filter does not.
        create_archive(
            nodes, filename=filepath_filtered, backend=archive_backend, create_backward=False, **TRAVERSAL_RULES
        )

    return filepath_filtered
