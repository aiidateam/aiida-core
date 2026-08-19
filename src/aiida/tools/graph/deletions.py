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

from plumpy import ProcessState

from aiida.common import exceptions
from aiida.common.links import LinkType
from aiida.common.log import AIIDA_LOGGER
from aiida.manage import get_manager
from aiida.orm import (
    CalculationNode,
    ContractedProcessNode,
    Data,
    Group,
    Node,
    ProcessNode,
    QueryBuilder,
    WorkflowNode,
)
from aiida.orm.implementation import StorageBackend
from aiida.tools.graph.graph_traversers import get_nodes_delete

__all__ = ('delete_group_nodes', 'delete_nodes')

DELETE_LOGGER = AIIDA_LOGGER.getChild('delete')


@dataclass(frozen=True)
class _Link:
    """A link relevant to a replacement plan."""

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
class _ReplacementPlan:
    """Immutable description of a replacement deletion."""

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
    if isinstance(node, ContractedProcessNode):
        return 'contracted_process'
    if isinstance(node, CalculationNode):
        return 'calculation'
    if isinstance(node, WorkflowNode):
        return 'workflow'
    if isinstance(node, ProcessNode):
        return 'process'
    if isinstance(node, Data):
        return 'data'
    return 'node'


def _plan_replacement(pks: Iterable[int], backend: StorageBackend) -> _ReplacementPlan:
    """Construct and validate a replacement deletion plan."""
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
        msg = f'replacement deletion requires terminated and sealed process nodes; offending PKs: {sorted(offending)}'
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
    plan = _ReplacementPlan(
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


def _proposed_pairs(plan: _ReplacementPlan) -> set[tuple[int, int]]:
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


def _validate_no_cycles(plan: _ReplacementPlan, backend: StorageBackend) -> None:
    """Reject a contraction that would create a directed cycle among surviving nodes."""
    builder = QueryBuilder(backend=backend)
    builder.append(Node, tag='source', project='id').append(Node, with_incoming='source', project='id')
    adjacency: dict[int, set[int]] = {}
    for source, target in builder.iterall():
        if source not in plan.selected and target not in plan.selected:
            adjacency.setdefault(source, set()).add(target)

    for source, target in _proposed_pairs(plan):
        if source == target:
            msg = f'replacement deletion would create a cycle through node<{source}>'
            raise exceptions.InvalidOperation(msg)
        pending = [target]
        seen: set[int] = set()
        while pending:
            current = pending.pop()
            if current == source:
                msg = f'replacement deletion would create a cycle between nodes<{source}> and <{target}>'
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


def _log_plan(plan: _ReplacementPlan) -> None:
    """Report a replacement plan without allocating replacement PKs."""
    DELETE_LOGGER.report('Selected nodes: %s', ' '.join(map(str, sorted(plan.selected))) or 'none')
    DELETE_LOGGER.report('Nodes to delete: %s', ' '.join(map(str, sorted(plan.selected))) or 'none')
    DELETE_LOGGER.report('Surviving boundary nodes: %s', ' '.join(map(str, sorted(plan.boundary))) or 'none')
    replacements = [region for region in plan.regions if region.has_process]
    if replacements:
        description = ', '.join(
            f'R{index} ({len(region.nodes)} selected nodes)' for index, region in enumerate(replacements, 1)
        )
    else:
        description = 'none'
    DELETE_LOGGER.report('Replacement processes: %s', description)

    links: list[str] = []
    replacement_index = 0
    for region in plan.regions:
        if region.has_process:
            replacement_index += 1
            links.extend(f'{link.source} -> R{replacement_index}' for link in region.incoming)
            links.extend(f'R{replacement_index} -> {link.target}' for link in region.outgoing)
        else:
            links.extend(f'{source} -> {target}' for source, target in region.direct_pairs)
    DELETE_LOGGER.report('New contracted links: %s', ', '.join(links) or 'none')


def _apply_replacement(plan: _ReplacementPlan, backend: StorageBackend) -> None:
    """Apply a validated replacement plan in the caller's transaction."""
    affected = _load_nodes(plan.selected | plan.boundary, backend)
    if _fingerprint(affected.values()) != plan.fingerprint:
        msg = 'the provenance graph changed after the replacement deletion was planned'
        raise exceptions.InvalidOperation(msg)

    all_nodes = _load_nodes(plan.selected | plan.boundary, backend)

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
            replacement = ContractedProcessNode(backend=backend)
            replacement.base.attributes.set_many(
                {
                    'contraction': {
                        'deleted_at': datetime.now(tz=timezone.utc).isoformat(),
                        'policy': 'replacement-deletion-v1',
                        'initiating_user': replacement.user.pk,
                        'removed_node_count': len(region.nodes),
                        'removed_node_types': dict(region.removed_types),
                        'boundary_links': mappings,
                    },
                    ProcessNode.PROCESS_LABEL_KEY: 'Contracted provenance',
                    ProcessNode.PROCESS_STATE_KEY: ProcessState.FINISHED.value,
                    ProcessNode.EXIT_STATUS_KEY: 0,
                }
            )
            for link in region.incoming:
                replacement.base.links.add_incoming(all_nodes[link.source], LinkType.CONTRACTED, _label('in', (link,)))
            replacement.store()
            for link in region.outgoing:
                all_nodes[link.target].base.links.add_incoming(replacement, LinkType.CONTRACTED, _label('out', (link,)))
            replacement.seal()
        else:
            for source, target in region.direct_pairs:
                related = tuple(
                    link
                    for link in (*region.incoming, *region.outgoing)
                    if link.source == source or link.target == target
                )
                all_nodes[target].base.links.add_incoming(
                    all_nodes[source], LinkType.CONTRACTED, _label('direct', related)
                )

    backend.delete_nodes_and_connections(plan.selected)


def delete_nodes(
    pks: Iterable[int],
    dry_run: bool | Callable[[set[int]], bool] = True,
    backend: StorageBackend | None = None,
    *,
    replace: bool = False,
    **traversal_rules: bool,
) -> tuple[set[int], bool]:
    """Delete nodes, optionally replacing the selected provenance region.

    :param pks: PKs of the nodes to delete.
    :param dry_run: preview, apply, or a confirmation callback receiving the deletion set.
    :param backend: storage backend, or the current profile storage by default.
    :param replace: contract the explicitly selected region instead of expanding it with deletion traversal rules.
    :param traversal_rules: overrides for ordinary traversal deletion. These cannot be combined with ``replace``.
    :returns: the node PKs selected for deletion and whether deletion was performed.
    """
    backend = backend or get_manager().get_profile_storage()

    if replace and traversal_rules:
        msg = '`replace=True` cannot be combined with traversal rule overrides'
        raise ValueError(msg)

    plan: _ReplacementPlan | None = None
    if replace:
        plan = _plan_replacement(pks, backend)
        pks_set_to_delete = set(plan.selected)
        _log_plan(plan)
    else:

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
                DELETE_LOGGER.debug('   %s %s %s %s', uuid, pk, type_string, label)

    if dry_run is True or (callable(dry_run) and dry_run(pks_set_to_delete)):
        DELETE_LOGGER.report('This was a dry run, exiting without deleting anything')
        return pks_set_to_delete, False

    if not pks_set_to_delete:
        return pks_set_to_delete, True

    DELETE_LOGGER.report('Starting node deletion...')
    with backend.transaction():
        if plan is None:
            backend.delete_nodes_and_connections(pks_set_to_delete)
        else:
            _apply_replacement(plan, backend)
    DELETE_LOGGER.report('Deletion of nodes completed.')
    return pks_set_to_delete, True


def delete_group_nodes(
    pks: Iterable[int],
    dry_run: bool | Callable[[set[int]], bool] = True,
    backend: StorageBackend | None = None,
    *,
    replace: bool = False,
    **traversal_rules: bool,
) -> tuple[set[int], bool]:
    """Delete all nodes contained in the specified groups."""
    group_node_query = (
        QueryBuilder(backend=backend)
        .append(Group, filters={'id': {'in': list(pks)}}, tag='groups')
        .append(Node, project='id', with_group='groups')
    )
    group_node_query.distinct()
    node_pks = group_node_query.all(flat=True)
    return delete_nodes(node_pks, dry_run=dry_run, backend=backend, replace=replace, **traversal_rules)
