###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for functions to traverse AiiDA graphs."""

from __future__ import annotations

import typing as t
from collections.abc import Callable, Iterable

from typing_extensions import TypedDict

from aiida import orm
from aiida.common import exceptions
from aiida.common.links import GraphTraversalRules, LinkType
from aiida.common.progress_reporter import get_progress_reporter
from aiida.tools.graph.age_entities import Basket
from aiida.tools.graph.age_rules import Operation, RuleSaveWalkers, RuleSequence, RuleSetWalkers, UpdateRule

if t.TYPE_CHECKING:
    from aiida.orm.implementation import StorageBackend
    from aiida.orm.utils.links import LinkQuadruple


class MembershipEdge(t.NamedTuple):
    """One ownership membership edge, always oriented owner -> child.

    :param owner_id: pk of the owner container node.
    :param child_id: pk of the owned child node.
    :param position: persisted iteration ordinal of the child within the owner.
    :param key: dictionary key of the child, ``None`` for list members.
    """

    owner_id: int
    child_id: int
    position: int
    key: str | None


class TraverseGraphOutput(TypedDict, total=False, closed=True):
    nodes: set[int]
    links: set[LinkQuadruple] | None
    memberships: set[MembershipEdge]
    rules: dict[str, bool]


class _MembershipRule(Operation):
    """Batched one-hop ownership traversal in a single direction.

    Forward follows ``with_members`` (owner -> child), backward follows ``with_owner``
    (child -> owner). Each :meth:`run` performs a single batched frontier query; visited
    termination is handled by the enclosing :class:`RuleSequence`. Collected edges are always
    oriented owner -> child and accumulated in :attr:`memberships`, separate from the
    provenance :class:`Basket` edge schema.
    """

    def __init__(self, backend: StorageBackend | None, *, forward: bool, track_edges: bool) -> None:
        super().__init__(max_iterations=1, track_edges=track_edges)
        self._forward = forward
        self._backend = backend
        self.memberships: set[MembershipEdge] = set()

    def run(self, operational_set: Basket) -> Basket:
        """Add the one-hop ownership neighbours of the walkers to a copy and return it."""
        result = operational_set.copy()
        frontier = operational_set.nodes.keyset
        if not frontier:
            return result

        query = orm.QueryBuilder(backend=self._backend)
        query.append(orm.Node, tag='source', filters={'id': {'in': frontier}}, project='id')
        edge_project = ['position', 'key'] if self._track_edges else []
        if self._forward:
            query.append(orm.Node, with_members='source', project='id', edge_project=edge_project)
        else:
            query.append(orm.Node, with_owner='source', project='id', edge_project=edge_project)

        new_ids: set[int] = set()
        for source, target, *edge in query.iterall():
            new_ids.add(target)
            if self._track_edges:
                owner, child = (source, target) if self._forward else (target, source)
                position, key = edge
                self.memberships.add(MembershipEdge(owner, child, position, key))

        result.nodes.add_entities(new_ids)
        return result


def get_nodes_delete(
    starting_pks: Iterable[int],
    get_links: bool = False,
    missing_callback: Callable[[Iterable[int]], None] | None = None,
    backend: StorageBackend | None = None,
    **traversal_rules: bool,
) -> TraverseGraphOutput:
    """This function will return the set of all nodes that can be connected
    to a list of initial nodes through any sequence of specified authorized
    links and directions for deletion.

    :param starting_pks: Contains the (valid) pks of the starting nodes.

    :param get_links:
        Pass True to also return the links between all nodes (found + initial).

    :param missing_callback: A callback to handle missing starting_pks or if None raise NotExistent
        For example to ignore them: ``missing_callback=lambda missing_pks: None``

    :param traversal_rules: graph traversal rules. See :const:`aiida.common.links.GraphTraversalRules` what rule names
        are toggleable and what the defaults are.

    """
    traverse_links = validate_traversal_rules(GraphTraversalRules.DELETE, **traversal_rules)

    traverse_output = traverse_graph(
        starting_pks,
        get_links=get_links,
        backend=backend,
        links_forward=traverse_links['forward'],
        links_backward=traverse_links['backward'],
        missing_callback=missing_callback,
    )

    return TraverseGraphOutput(
        nodes=traverse_output['nodes'],
        links=traverse_output['links'],
        rules=traverse_links['rules_applied'],
    )


def get_nodes_export(
    starting_pks: Iterable[int],
    get_links: bool = False,
    backend: StorageBackend | None = None,
    **traversal_rules: bool,
) -> TraverseGraphOutput:
    """This function will return the set of all nodes that can be connected
    to a list of initial nodes through any sequence of specified authorized
    links and directions for export. This will also return the links and
    the traversal rules parsed.

    :param starting_pks: Contains the (valid) pks of the starting nodes.

    :param get_links:
        Pass True to also return the links between all nodes (found + initial).

    :param input_calc_forward: will traverse INPUT_CALC links in the forward direction.
    :param create_backward: will traverse CREATE links in the backward direction.
    :param return_backward: will traverse RETURN links in the backward direction.
    :param input_work_forward: will traverse INPUT_WORK links in the forward direction.
    :param call_calc_backward: will traverse CALL_CALC links in the backward direction.
    :param call_work_backward: will traverse CALL_WORK links in the backward direction.
    """
    traverse_links = validate_traversal_rules(GraphTraversalRules.EXPORT, **traversal_rules)

    traverse_output = traverse_graph(
        starting_pks,
        get_links=get_links,
        backend=backend,
        links_forward=traverse_links['forward'],
        links_backward=traverse_links['backward'],
    )

    return TraverseGraphOutput(
        nodes=traverse_output['nodes'],
        links=traverse_output['links'],
        rules=traverse_links['rules_applied'],
    )


def validate_traversal_rules(
    ruleset: GraphTraversalRules = GraphTraversalRules.DEFAULT, **traversal_rules: bool
) -> dict[str, t.Any]:
    """Validates the keywords with a ruleset template and returns a parsed dictionary
    ready to be used.

    :param ruleset: Ruleset template used to validate the set of rules.
    :param input_calc_forward: will traverse INPUT_CALC links in the forward direction.
    :param input_calc_backward: will traverse INPUT_CALC links in the backward direction.
    :param create_forward: will traverse CREATE links in the forward direction.
    :param create_backward: will traverse CREATE links in the backward direction.
    :param return_forward: will traverse RETURN links in the forward direction.
    :param return_backward: will traverse RETURN links in the backward direction.
    :param input_work_forward: will traverse INPUT_WORK links in the forward direction.
    :param input_work_backward: will traverse INPUT_WORK links in the backward direction.
    :param call_calc_forward: will traverse CALL_CALC links in the forward direction.
    :param call_calc_backward: will traverse CALL_CALC links in the backward direction.
    :param call_work_forward: will traverse CALL_WORK links in the forward direction.
    :param call_work_backward: will traverse CALL_WORK links in the backward direction.
    """
    if not isinstance(ruleset, GraphTraversalRules):
        msg = f'ruleset input must be of type aiida.common.links.GraphTraversalRules\ninstead, it is: {type(ruleset)}'  # type: ignore[unreachable]
        raise TypeError(msg)

    rules_applied: dict[str, bool] = {}
    links_forward: list[LinkType] = []
    links_backward: list[LinkType] = []

    for name, rule in ruleset.value.items():
        follow = rule.default

        if name in traversal_rules:
            if not rule.toggleable:
                msg = f'input rule {name} is not toggleable for ruleset {ruleset}'
                raise ValueError(msg)

            follow = traversal_rules.pop(name)

            if not isinstance(follow, bool):
                msg = f'the value of rule {name} must be boolean, but it is: {follow}'  # type: ignore[unreachable]
                raise ValueError(msg)

        if follow:
            if rule.direction == 'forward':
                links_forward.append(rule.link_type)
            elif rule.direction == 'backward':
                links_backward.append(rule.link_type)
            else:
                msg = f'unrecognized direction `{rule.direction}` for graph traversal rule'
                raise exceptions.InternalError(msg)

        rules_applied[name] = follow

    if traversal_rules:
        error_message = f'unrecognized keywords: {", ".join(traversal_rules.keys())}'
        raise exceptions.ValidationError(error_message)

    valid_output = {
        'rules_applied': rules_applied,
        'forward': links_forward,
        'backward': links_backward,
    }

    return valid_output


def traverse_graph(
    starting_pks: Iterable[int],
    max_iterations: int | None = None,
    get_links: bool = False,
    links_forward: Iterable[LinkType] = (),
    links_backward: Iterable[LinkType] = (),
    missing_callback: Callable[[Iterable[int]], None] | None = None,
    backend: StorageBackend | None = None,
) -> TraverseGraphOutput:
    """This function will return the set of all nodes that can be connected
    to a list of initial nodes through any sequence of specified links.
    Optionally, it may also return the links that connect these nodes.

    :param starting_pks: Contains the (valid) pks of the starting nodes.

    :param max_iterations:
        The number of iterations to apply the set of rules (a value of 'None' will
        iterate until no new nodes are added).

    :param get_links: Pass True to also return the links between all nodes (found + initial).

    :param links_forward: List with all the links that should be traversed in the forward direction.
    :param links_backward: List with all the links that should be traversed in the backward direction.

    :param missing_callback: A callback to handle missing starting_pks or if None raise NotExistent

    ``LinkType.CONTAINS`` may be passed in ``links_forward`` (owner -> child via
    ``with_members``) and/or ``links_backward`` (child -> owner via ``with_owner``).
    When ``get_links`` is ``True`` and ``CONTAINS`` is requested, the result also contains
    ``memberships``, the set of traversed :class:`MembershipEdge` (always oriented
    owner -> child), even if empty. Otherwise the key is omitted and the result keeps
    its previous shape. Provenance links are reported separately under ``links``.
    """
    from numpy import inf

    if max_iterations is None:
        max_iterations = t.cast('int', inf)
    elif not (isinstance(max_iterations, int) or max_iterations is inf):  # type: ignore[unreachable]
        raise TypeError('Max_iterations has to be an integer or infinity')

    links_forward = list(links_forward)
    links_backward = list(links_backward)

    for linktype in links_forward:
        if not isinstance(linktype, LinkType):
            msg = f'links_forward should contain links, but one of them is: {type(linktype)}'  # type: ignore[unreachable]
            raise TypeError(msg)
    for linktype in links_backward:
        if not isinstance(linktype, LinkType):
            msg = f'links_backward should contain links, but one of them is: {type(linktype)}'  # type: ignore[unreachable]
            raise TypeError(msg)

    provenance_forward = [linktype.value for linktype in links_forward if linktype is not LinkType.CONTAINS]
    provenance_backward = [linktype.value for linktype in links_backward if linktype is not LinkType.CONTAINS]
    membership_forward = LinkType.CONTAINS in links_forward
    membership_backward = LinkType.CONTAINS in links_backward

    if not isinstance(starting_pks, Iterable):
        msg = f'starting_pks must be an iterable\ninstead, it is {type(starting_pks)}'  # type: ignore[unreachable]
        raise TypeError(msg)

    if any(not isinstance(pk, int) for pk in starting_pks):
        msg = f'one of the starting_pks is not of type int:\n {starting_pks}'
        raise TypeError(msg)
    operational_set = set(starting_pks)

    if not operational_set:
        if get_links:
            output: TraverseGraphOutput = {'nodes': set(), 'links': set()}
            if membership_forward or membership_backward:
                output['memberships'] = set()
            return output
        return {'nodes': set(), 'links': None}

    query_nodes = orm.QueryBuilder(backend=backend)
    query_nodes.append(orm.Node, project=['id'], filters={'id': {'in': operational_set}})
    existing_pks = set(query_nodes.all(flat=True))

    missing_pks = operational_set.difference(existing_pks)
    if missing_pks and missing_callback is None:
        msg = f'The following pks are not in the database and must be pruned before this call: {missing_pks}'
        raise exceptions.NotExistent(msg)
    elif missing_pks and missing_callback is not None:
        missing_callback(missing_pks)

    rules: list[Operation] = []
    basket = Basket(nodes=existing_pks)

    directional_rules: list[Operation] = []
    membership_rules: list[_MembershipRule] = []

    if provenance_forward:
        query_outgoing = orm.QueryBuilder(backend=backend)
        query_outgoing.append(orm.Node, tag='sources')
        query_outgoing.append(orm.Node, edge_filters={'type': {'in': provenance_forward}}, with_incoming='sources')
        rule_outgoing = UpdateRule(query_outgoing, max_iterations=1, track_edges=get_links)
        directional_rules.append(rule_outgoing)

    if provenance_backward:
        query_incoming = orm.QueryBuilder(backend=backend)
        query_incoming.append(orm.Node, tag='sources')
        query_incoming.append(orm.Node, edge_filters={'type': {'in': provenance_backward}}, with_outgoing='sources')
        rule_incoming = UpdateRule(query_incoming, max_iterations=1, track_edges=get_links)
        directional_rules.append(rule_incoming)

    for forward, enabled in [(True, membership_forward), (False, membership_backward)]:
        if enabled:
            rule = _MembershipRule(backend, forward=forward, track_edges=get_links)
            membership_rules.append(rule)
            directional_rules.append(rule)

    # Every rule must start from the same frontier: otherwise adding another rule
    # could advance the walk more than one hop per iteration.
    if len(directional_rules) > 1:
        stash = basket.get_template()
        rules.append(RuleSaveWalkers(stash))
        for index, directional_rule in enumerate(directional_rules):
            if index > 0:
                rules.append(RuleSetWalkers(stash))
            rules.append(directional_rule)
    else:
        rules.extend(directional_rules)

    # Without a total the project bar format's percentage sits frozen at 0%, so `bar_format=None`
    # falls back to tqdm's plain counter. `unit` is set because tqdm's default renders the count as
    # `251000it`, which beside a description ending in "(iteration 3)" reads as a count of iterations.
    description = 'Traversing provenance graph'
    with get_progress_reporter()(total=None, desc=description, unit=' nodes', bar_format=None) as progress:
        # The starting nodes already count as visited. `update` alone is throttled and the next
        # tick is the long first query itself, so the description write is what forces the redraw.
        progress.update(len(basket.nodes.keyset))
        progress.set_description_str(description, refresh=True)

        def update_progress(iterations_done: int, nodes_visited: int) -> None:
            # refresh=False: the throttled `update` below redraws anyway, and refreshing here on
            # every level would flood non-TTY output such as CI logs.
            progress.set_description_str(f'{description} (iteration {iterations_done})', refresh=False)
            progress.update(nodes_visited - progress.n)

        rulesequence = RuleSequence(rules, max_iterations=max_iterations, iteration_callback=update_progress)
        results = rulesequence.run(basket)

    traverse_output = TraverseGraphOutput(
        nodes=results.nodes.keyset,
        links=results['nodes_nodes'].keyset if get_links else None,
    )
    if get_links and membership_rules:
        collected: set[MembershipEdge] = set()
        for membership_rule in membership_rules:
            collected |= membership_rule.memberships
        traverse_output['memberships'] = collected
    return traverse_output
