###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for functions to traverse AiiDA graphs."""

import sys
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, List, Mapping, Optional, Set, cast

from numpy import inf

from aiida import orm
from aiida.common import exceptions
from aiida.common.links import GraphTraversalRules, LinkType
from aiida.tools.graph.age_entities import Basket
from aiida.tools.graph.age_rules import RuleSaveWalkers, RuleSequence, RuleSetWalkers, UpdateRule

if TYPE_CHECKING:
    from aiida.orm.implementation import StorageBackend
    from aiida.orm.utils.links import LinkQuadruple

if sys.version_info >= (3, 8):
    from typing import TypedDict

    class TraverseGraphOutput(TypedDict, total=False):
        nodes: Set[int]
        links: Optional[Set[LinkQuadruple]]
        rules: Dict[str, bool]
else:
    TraverseGraphOutput = Mapping[str, Any]


def get_nodes_delete(
    starting_pks: Iterable[int],
    get_links: bool = False,
    missing_callback: Optional[Callable[[Iterable[int]], None]] = None,
    backend: Optional['StorageBackend'] = None,
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

    function_output: TraverseGraphOutput = {
        'nodes': traverse_output['nodes'],
        'links': traverse_output['links'],
        'rules': traverse_links['rules_applied'],
    }

    return function_output


def get_nodes_export(
    starting_pks: Iterable[int],
    get_links: bool = False,
    backend: Optional['StorageBackend'] = None,
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

    function_output: TraverseGraphOutput = {
        'nodes': traverse_output['nodes'],
        'links': traverse_output['links'],
        'rules': traverse_links['rules_applied'],
    }

    return function_output


def validate_traversal_rules(
    ruleset: GraphTraversalRules = GraphTraversalRules.DEFAULT, **traversal_rules: bool
) -> dict:
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
        raise TypeError(
            f'ruleset input must be of type aiida.common.links.GraphTraversalRules\ninstead, it is: {type(ruleset)}'
        )

    rules_applied: Dict[str, bool] = {}
    links_forward: List[LinkType] = []
    links_backward: List[LinkType] = []

    for name, rule in ruleset.value.items():
        follow = rule.default

        if name in traversal_rules:
            if not rule.toggleable:
                raise ValueError(f'input rule {name} is not toggleable for ruleset {ruleset}')

            follow = traversal_rules.pop(name)

            if not isinstance(follow, bool):
                raise ValueError(f'the value of rule {name} must be boolean, but it is: {follow}')

        if follow:
            if rule.direction == 'forward':
                links_forward.append(rule.link_type)
            elif rule.direction == 'backward':
                links_backward.append(rule.link_type)
            else:
                raise exceptions.InternalError(f'unrecognized direction `{rule.direction}` for graph traversal rule')

        rules_applied[name] = follow

    if traversal_rules:
        error_message = f"unrecognized keywords: {', '.join(traversal_rules.keys())}"
        raise exceptions.ValidationError(error_message)

    valid_output = {
        'rules_applied': rules_applied,
        'forward': links_forward,
        'backward': links_backward,
    }

    return valid_output


def traverse_graph(
    starting_pks: Iterable[int],
    max_iterations: Optional[int] = None,
    get_links: bool = False,
    links_forward: Iterable[LinkType] = (),
    links_backward: Iterable[LinkType] = (),
    missing_callback: Optional[Callable[[Iterable[int]], None]] = None,
    backend: Optional['StorageBackend'] = None,
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
    """

    if max_iterations is None:
        max_iterations = cast('int', inf)
    elif not (isinstance(max_iterations, int) or max_iterations is inf):  # type: ignore[unreachable]
        raise TypeError('Max_iterations has to be an integer or infinity')

    linktype_list = []
    for linktype in links_forward:
        if not isinstance(linktype, LinkType):
            raise TypeError(f'links_forward should contain links, but one of them is: {type(linktype)}')
        linktype_list.append(linktype.value)
    filters_forwards = {'type': {'in': linktype_list}}

    linktype_list = []
    for linktype in links_backward:
        if not isinstance(linktype, LinkType):
            raise TypeError(f'links_backward should contain links, but one of them is: {type(linktype)}')
        linktype_list.append(linktype.value)
    filters_backwards = {'type': {'in': linktype_list}}

    if not isinstance(starting_pks, Iterable):
        raise TypeError(f'starting_pks must be an iterable\ninstead, it is {type(starting_pks)}')

    if any(not isinstance(pk, int) for pk in starting_pks):
        raise TypeError(f'one of the starting_pks is not of type int:\n {starting_pks}')
    operational_set = set(starting_pks)

    if not operational_set:
        if get_links:
            return {'nodes': set(), 'links': set()}
        return {'nodes': set(), 'links': None}

    query_nodes = orm.QueryBuilder(backend=backend)
    query_nodes.append(orm.Node, project=['id'], filters={'id': {'in': operational_set}})
    existing_pks = set(query_nodes.all(flat=True))

    missing_pks = operational_set.difference(existing_pks)
    if missing_pks and missing_callback is None:
        raise exceptions.NotExistent(
            f'The following pks are not in the database and must be pruned before this call: {missing_pks}'
        )
    elif missing_pks and missing_callback is not None:
        missing_callback(missing_pks)

    rules = []
    basket = Basket(nodes=existing_pks)

    # When max_iterations is finite, the order of traversal may affect the result
    # (its not the same to first go backwards and then forwards than vice-versa)
    # In order to make it order-independent, the result of the first operation needs
    # to be stashed and the second operation must be performed only on the nodes
    # that were already in the set at the begining of the iteration: this way, both
    # rules are applied on the same set of nodes and the order doesn't matter.
    # The way to do this is saving and seting the walkers at the right moments only
    # when both forwards and backwards rules are present.
    if links_forward and links_backward:
        stash = basket.get_template()
        rules += [RuleSaveWalkers(stash)]

    if links_forward:
        query_outgoing = orm.QueryBuilder(backend=backend)
        query_outgoing.append(orm.Node, tag='sources')
        query_outgoing.append(orm.Node, edge_filters=filters_forwards, with_incoming='sources')
        rule_outgoing = UpdateRule(query_outgoing, max_iterations=1, track_edges=get_links)
        rules += [rule_outgoing]

    if links_forward and links_backward:
        rules += [RuleSetWalkers(stash)]

    if links_backward:
        query_incoming = orm.QueryBuilder(backend=backend)
        query_incoming.append(orm.Node, tag='sources')
        query_incoming.append(orm.Node, edge_filters=filters_backwards, with_outgoing='sources')
        rule_incoming = UpdateRule(query_incoming, max_iterations=1, track_edges=get_links)
        rules += [rule_incoming]

    rulesequence = RuleSequence(rules, max_iterations=max_iterations)

    results = rulesequence.run(basket)

    output: TraverseGraphOutput = {}
    output['nodes'] = results.nodes.keyset
    output['links'] = None
    if get_links:
        output['links'] = results['nodes_nodes'].keyset

    return output
