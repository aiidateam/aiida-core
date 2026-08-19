###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Functions to delete entities from the database, preserving provenance integrity."""

from __future__ import annotations

import hashlib
import logging
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime, timezone

from aiida.common import exceptions
from aiida.common.links import LinkType
from aiida.common.log import AIIDA_LOGGER
from aiida.manage import get_manager
from aiida.orm import (
    CalculationNode,
    Data,
    Group,
    Node,
    ProcessNode,
    QueryBuilder,
    WorkflowNode,
)
from aiida.orm.implementation import StorageBackend
from aiida.orm.nodes.contracted import ContractedNode
from aiida.tools.graph.graph_traversers import get_nodes_delete

__all__ = ('contract_nodes', 'delete_group_nodes', 'delete_nodes')

DELETE_LOGGER = AIIDA_LOGGER.getChild('delete')


@dataclass(frozen=True)
class _Link:
    """A link relevant to a contraction plan."""

    source: int
    target: int
    link_type: LinkType
    label: str


@dataclass(frozen=True)
class _Region:
    """A weakly connected region of selected nodes."""

    nodes: frozenset[int]
    incoming: tuple[_Link, ...]
    outgoing: tuple[_Link, ...]
    has_process: bool
    removed_types: tuple[tuple[str, int], ...]
    direct_pairs: tuple[tuple[int, int], ...] = ()


@dataclass(frozen=True)
class _ContractionPlan:
    """Immutable description of a provenance contraction."""

    selected: frozenset[int]
    boundary: frozenset[int]
    regions: tuple[_Region, ...]
    fingerprint: tuple[tuple[object, ...], ...]


def _load_nodes(pks: Iterable[int], backend: StorageBackend) -> dict[int, Node]:
    """Return stored nodes indexed by PK."""
    pks = set(pks)
    if not pks:
        return {}
    builder = QueryBuilder(backend=backend).append(Node, filters={'id': {'in': pks}}, project=('*', 'id'))
    return {pk: node for node, pk in builder.iterall()}


def _incident_links(nodes: Iterable[Node]) -> set[_Link]:
    """Return all links incident on the given nodes."""
    result: set[_Link] = set()
    for node in nodes:
        assert node.pk is not None
        for triple in node.base.links.get_incoming():
            assert triple.node.pk is not None
            result.add(_Link(triple.node.pk, node.pk, triple.link_type, triple.link_label))
        for triple in node.base.links.get_outgoing():
            assert triple.node.pk is not None
            result.add(_Link(node.pk, triple.node.pk, triple.link_type, triple.link_label))
    return result


def _fingerprint(nodes: Iterable[Node]) -> tuple[tuple[object, ...], ...]:
    """Fingerprint affected nodes and their incident links."""
    nodes = tuple(nodes)
    node_rows = [('node', node.pk, node.uuid, node.mtime.isoformat()) for node in nodes]
    link_rows = [
        ('link', link.source, link.target, link.link_type.value, link.label) for link in _incident_links(nodes)
    ]
    return tuple(sorted((*node_rows, *link_rows)))


def _classify(node: Node) -> str:
    """Return a deliberately broad node class for audit metadata."""
    if isinstance(node, ContractedNode):
        return 'contracted'
    if isinstance(node, CalculationNode):
        return 'calculation'
    if isinstance(node, WorkflowNode):
        return 'workflow'
    if isinstance(node, ProcessNode):
        return 'process'
    if isinstance(node, Data):
        return 'data'
    return 'node'


def _plan_contraction(pks: Iterable[int], backend: StorageBackend) -> _ContractionPlan:
    """Construct and validate a provenance contraction plan."""
    requested = set(pks)
    selected_nodes = _load_nodes(requested, backend)
    for pk in sorted(requested - selected_nodes.keys()):
        DELETE_LOGGER.warning('warning: node with pk<%s> does not exist, skipping', pk)

    selected = frozenset(selected_nodes)
    links = _incident_links(selected_nodes.values())

    offending: list[int] = []
    for node in selected_nodes.values():
        if isinstance(node, ProcessNode) and (not node.is_terminated or not node.is_sealed):
            assert node.pk is not None
            offending.append(node.pk)
    if offending:
        msg = f'provenance contraction requires terminated and sealed process nodes; offending PKs: {sorted(offending)}'
        raise exceptions.InvalidOperation(msg)

    neighbours: dict[int, set[int]] = {pk: set() for pk in selected}
    for link in links:
        if link.source in selected and link.target in selected:
            neighbours[link.source].add(link.target)
            neighbours[link.target].add(link.source)

    components: list[frozenset[int]] = []
    unseen = set(selected)
    while unseen:
        root = min(unseen)
        discovered: set[int] = set()
        pending = [root]
        while pending:
            current = pending.pop()
            if current in discovered:
                continue
            discovered.add(current)
            pending.extend(neighbours[current] - discovered)
        unseen -= discovered
        components.append(frozenset(discovered))

    regions: list[_Region] = []
    boundary: set[int] = set()
    for component in components:
        incoming = tuple(
            sorted((link for link in links if link.target in component and link.source not in selected), key=repr)
        )
        outgoing = tuple(
            sorted((link for link in links if link.source in component and link.target not in selected), key=repr)
        )
        boundary.update(link.source for link in incoming)
        boundary.update(link.target for link in outgoing)
        nodes = [selected_nodes[pk] for pk in component]
        region = _Region(
            nodes=component,
            incoming=incoming,
            outgoing=outgoing,
            has_process=any(isinstance(node, ProcessNode) for node in nodes),
            removed_types=tuple(sorted(Counter(_classify(node) for node in nodes).items())),
        )
        if not region.has_process:
            region = _Region(
                nodes=region.nodes,
                incoming=region.incoming,
                outgoing=region.outgoing,
                has_process=False,
                removed_types=region.removed_types,
                direct_pairs=tuple(sorted(_direct_boundary_pairs(region, links))),
            )
        regions.append(region)

    affected_nodes = _load_nodes(selected | boundary, backend)
    plan = _ContractionPlan(
        selected=selected,
        boundary=frozenset(boundary),
        regions=tuple(sorted(regions, key=lambda region: min(region.nodes))),
        fingerprint=_fingerprint(affected_nodes.values()),
    )
    _validate_no_cycles(plan, backend)
    return plan


def _direct_boundary_pairs(region: _Region, selected_links: set[_Link]) -> set[tuple[int, int]]:
    """Return surviving boundary pairs connected by a directed path through a data region."""
    adjacency: dict[int, set[int]] = {pk: set() for pk in region.nodes}
    for link in selected_links:
        if link.source in region.nodes and link.target in region.nodes:
            adjacency[link.source].add(link.target)

    pairs: set[tuple[int, int]] = set()
    for incoming in region.incoming:
        reachable = {incoming.target}
        pending = [incoming.target]
        while pending:
            current = pending.pop()
            for target in adjacency[current] - reachable:
                reachable.add(target)
                pending.append(target)
        pairs.update((incoming.source, outgoing.target) for outgoing in region.outgoing if outgoing.source in reachable)
    return pairs


def _proposed_pairs(plan: _ContractionPlan) -> set[tuple[int, int]]:
    """Return the surviving node pairs between which contraction creates reachability."""
    pairs: set[tuple[int, int]] = set()
    for region in plan.regions:
        if region.has_process:
            pairs.update(
                (incoming.source, outgoing.target) for incoming in region.incoming for outgoing in region.outgoing
            )
        else:
            pairs.update(region.direct_pairs)
    return pairs


def _validate_no_cycles(plan: _ContractionPlan, backend: StorageBackend) -> None:
    """Reject a contraction that would create a directed cycle among surviving nodes."""
    builder = QueryBuilder(backend=backend)
    builder.append(Node, tag='source', project='id').append(Node, with_incoming='source', project='id')
    adjacency: dict[int, set[int]] = {}
    for source, target in builder.iterall():
        if source not in plan.selected and target not in plan.selected:
            adjacency.setdefault(source, set()).add(target)

    for source, target in _proposed_pairs(plan):
        if source == target:
            msg = f'provenance contraction would create a cycle through node<{source}>'
            raise exceptions.InvalidOperation(msg)
        pending = [target]
        seen: set[int] = set()
        while pending:
            current = pending.pop()
            if current == source:
                msg = f'provenance contraction would create a cycle between nodes<{source}> and <{target}>'
                raise exceptions.InvalidOperation(msg)
            if current not in seen:
                seen.add(current)
                pending.extend(adjacency.get(current, set()) - seen)


def _label(direction: str, links: Iterable[_Link]) -> str:
    """Create a short deterministic contracted link label."""
    value = '|'.join(
        f'{link.source}:{link.target}:{link.link_type.value}:{link.label}' for link in sorted(links, key=repr)
    )
    digest = hashlib.sha256(value.encode()).hexdigest()[:20]
    return f'contracted_{direction}_{digest}'


def _log_plan(plan: _ContractionPlan) -> None:
    """Report a contraction plan without allocating marker PKs."""
    DELETE_LOGGER.report('Selected nodes: %s', ' '.join(map(str, sorted(plan.selected))) or 'none')
    DELETE_LOGGER.report('Nodes to delete: %s', ' '.join(map(str, sorted(plan.selected))) or 'none')
    DELETE_LOGGER.report('Surviving boundary nodes: %s', ' '.join(map(str, sorted(plan.boundary))) or 'none')
    markers = [region for region in plan.regions if region.has_process]
    if markers:
        description = ', '.join(
            f'R{index} ({len(region.nodes)} selected nodes)' for index, region in enumerate(markers, 1)
        )
    else:
        description = 'none'
    DELETE_LOGGER.report('Contraction markers: %s', description)

    links: list[str] = []
    marker_index = 0
    for region in plan.regions:
        if region.has_process:
            marker_index += 1
            links.extend(f'{link.source} -> R{marker_index}' for link in region.incoming)
            links.extend(f'R{marker_index} -> {link.target}' for link in region.outgoing)
        else:
            links.extend(f'{source} -> {target}' for source, target in region.direct_pairs)
    DELETE_LOGGER.report('New contracted links: %s', ', '.join(links) or 'none')


def _apply_contraction(plan: _ContractionPlan, backend: StorageBackend) -> None:
    """Apply a validated contraction plan in the caller's transaction."""
    affected = _load_nodes(plan.selected | plan.boundary, backend)
    if _fingerprint(affected.values()) != plan.fingerprint:
        msg = 'the provenance graph changed after the contraction was planned'
        raise exceptions.InvalidOperation(msg)

    contracted_links: list[tuple[int, int, str]] = []

    for region in plan.regions:
        if region.has_process:
            mappings = [
                {
                    'source': link.source,
                    'target': link.target,
                    'type': link.link_type.value,
                    'label': link.label,
                    'direction': direction,
                    'contracted_label': _label('in' if direction == 'incoming' else 'out', (link,)),
                }
                for direction, links in (('incoming', region.incoming), ('outgoing', region.outgoing))
                for link in links
            ]
            marker = ContractedNode(backend=backend)
            marker.base.attributes.set(
                'contraction',
                {
                    'deleted_at': datetime.now(tz=timezone.utc).isoformat(),
                    'policy': 'contraction-v1',
                    'initiating_user': marker.user.pk,
                    'removed_node_count': len(region.nodes),
                    'removed_node_types': dict(region.removed_types),
                    'boundary_links': mappings,
                },
            )
            marker.store()
            assert marker.pk is not None
            contracted_links.extend((link.source, marker.pk, _label('in', (link,))) for link in region.incoming)
            contracted_links.extend((marker.pk, link.target, _label('out', (link,))) for link in region.outgoing)
        else:
            for source, target in region.direct_pairs:
                related = tuple(
                    link
                    for link in (*region.incoming, *region.outgoing)
                    if link.source == source or link.target == target
                )
                contracted_links.append((source, target, _label('direct', related)))

    backend.replace_nodes_and_connections(plan.selected, contracted_links)


def contract_nodes(
    pks: Iterable[int],
    dry_run: bool | Callable[[set[int]], bool] = True,
    backend: StorageBackend | None = None,
) -> tuple[set[int], bool]:
    """Contract an explicitly selected region of the provenance graph.

    The selected nodes are deleted without traversal expansion. Directed
    reachability across each selected region is preserved with contracted
    links and, for regions containing processes, an internal marker node.

    :param pks: PKs of the nodes to contract.
    :param dry_run: preview, apply, or a confirmation callback receiving the
        selected PKs.
    :param backend: storage backend, or the current profile storage by default.
    :returns: selected node PKs and whether contraction was performed.
    """
    backend = backend or get_manager().get_profile_storage()
    plan = _plan_contraction(pks, backend)
    pks_to_contract = set(plan.selected)
    _log_plan(plan)

    if dry_run is True or (callable(dry_run) and dry_run(pks_to_contract)):
        DELETE_LOGGER.report('This was a dry run, exiting without changing anything')
        return pks_to_contract, False

    if not pks_to_contract:
        return pks_to_contract, True

    DELETE_LOGGER.report('Starting node contraction...')
    with backend.transaction():
        _apply_contraction(plan, backend)
    DELETE_LOGGER.report('Node contraction completed.')
    return pks_to_contract, True


def delete_nodes(
    pks: Iterable[int],
    dry_run: bool | Callable[[set[int]], bool] = True,
    backend: StorageBackend | None = None,
    **traversal_rules: bool,
) -> tuple[set[int], bool]:
    """Delete nodes given a list of "starting" PKs.

    This command will delete not only the specified nodes, but also the ones that are
    linked to these and should be also deleted in order to keep a consistent provenance
    according to the rules explained in the Topics - Provenance section of the documentation.
    In summary:

    1. If a DATA node is deleted, any process nodes linked to it will also be deleted.

    2. If a CALC node is deleted, any incoming WORK node (callers) will be deleted as
    well whereas any incoming DATA node (inputs) will be kept. Outgoing DATA nodes
    (outputs) will be deleted by default but this can be disabled.

    3. If a WORK node is deleted, any incoming WORK node (callers) will be deleted as
    well, but all DATA nodes will be kept. Outgoing WORK or CALC nodes will be kept by
    default, but deletion of either of both kind of connected nodes can be enabled.

    These rules are 'recursive', so if a CALC node is deleted, then its output DATA
    nodes will be deleted as well, and then any CALC node that may have those as
    inputs, and so on.

    :param pks: a list of starting PKs of the nodes to delete
        (the full set will be based on the traversal rules)

    :param dry_run:
        If True, return the pks to delete without deleting anything.
        If False, delete the pks without confirmation
        If callable, a function that return True/False, based on the pks, e.g. ``dry_run=lambda pks: True``

    :param traversal_rules: graph traversal rules.
        See :const:`aiida.common.links.GraphTraversalRules` for what rule names
        are toggleable and what the defaults are.

    :returns: (pks to delete, whether they were deleted)

    """
    backend = backend or get_manager().get_profile_storage()

    def _missing_callback(_pks: Iterable[int]) -> None:
        for _pk in _pks:
            DELETE_LOGGER.warning(f'warning: node with pk<{_pk}> does not exist, skipping')

    pks_set_to_delete = get_nodes_delete(
        pks, get_links=False, missing_callback=_missing_callback, backend=backend, **traversal_rules
    )['nodes']

    DELETE_LOGGER.report('%s Node(s) marked for deletion', len(pks_set_to_delete))

    if pks_set_to_delete and DELETE_LOGGER.level == logging.DEBUG:
        builder = QueryBuilder(backend=backend).append(
            Node, filters={'id': {'in': pks_set_to_delete}}, project=('uuid', 'id', 'node_type', 'label')
        )
        DELETE_LOGGER.debug('Node(s) to delete:')
        for uuid, pk, type_string, label in builder.iterall():
            try:
                short_type_string = type_string.split('.')[-2]
            except IndexError:
                short_type_string = type_string
            DELETE_LOGGER.debug(f'   {uuid} {pk} {short_type_string} {label}')

    if dry_run is True:
        DELETE_LOGGER.report('This was a dry run, exiting without deleting anything')
        return (pks_set_to_delete, False)

    # confirm deletion
    if callable(dry_run) and dry_run(pks_set_to_delete):
        DELETE_LOGGER.report('This was a dry run, exiting without deleting anything')
        return (pks_set_to_delete, False)

    if not pks_set_to_delete:
        return (pks_set_to_delete, True)

    DELETE_LOGGER.report('Starting node deletion...')
    with backend.transaction():
        backend.delete_nodes_and_connections(pks_set_to_delete)
    DELETE_LOGGER.report('Deletion of nodes completed.')

    return (pks_set_to_delete, True)


def delete_group_nodes(
    pks: Iterable[int],
    dry_run: bool | Callable[[set[int]], bool] = True,
    backend: StorageBackend | None = None,
    **traversal_rules: bool,
) -> tuple[set[int], bool]:
    """Delete nodes contained in a list of groups (not the groups themselves!).

    This command will delete not only the nodes, but also the ones that are
    linked to these and should be also deleted in order to keep a consistent provenance
    according to the rules explained in the concepts section of the documentation.
    In summary:

    1. If a DATA node is deleted, any process nodes linked to it will also be deleted.

    2. If a CALC node is deleted, any incoming WORK node (callers) will be deleted as
    well whereas any incoming DATA node (inputs) will be kept. Outgoing DATA nodes
    (outputs) will be deleted by default but this can be disabled.

    3. If a WORK node is deleted, any incoming WORK node (callers) will be deleted as
    well, but all DATA nodes will be kept. Outgoing WORK or CALC nodes will be kept by
    default, but deletion of either of both kind of connected nodes can be enabled.

    These rules are 'recursive', so if a CALC node is deleted, then its output DATA
    nodes will be deleted as well, and then any CALC node that may have those as
    inputs, and so on.

    :param pks: a list of the groups

    :param dry_run:
        If True, return the pks to delete without deleting anything.
        If False, delete the pks without confirmation
        If callable, a function that return True/False, based on the pks, e.g. ``dry_run=lambda pks: True``

    :param traversal_rules: graph traversal rules. See :const:`aiida.common.links.GraphTraversalRules` what rule names
        are toggleable and what the defaults are.

    :returns: (node pks to delete, whether they were deleted)

    """
    group_node_query = (
        QueryBuilder(backend=backend)
        .append(
            Group,
            filters={'id': {'in': list(pks)}},
            tag='groups',
        )
        .append(Node, project='id', with_group='groups')
    )
    group_node_query.distinct()
    node_pks = group_node_query.all(flat=True)
    return delete_nodes(node_pks, dry_run=dry_run, backend=backend, **traversal_rules)
