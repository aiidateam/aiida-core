# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for functions to traverse AiiDA graphs."""

from numpy import inf
from aiida.common.links import GraphTraversalRules, LinkType


def get_nodes_delete(starting_pks, get_links=False, **kwargs):
    """
    This function will return the set of all nodes that can be connected
    to a list of initial nodes through any sequence of specified authorized
    links and directions for deletion.

    :type starting_pks: list or tuple or set
    :param starting_pks: Contains the (valid) pks of the starting nodes.

    :param bool get_links:
        Pass True to also return the links between all nodes (found + initial).

    :param bool create_forward: will traverse CREATE links in the forward direction.
    :param bool call_calc_forward: will traverse CALL_CALC links in the forward direction.
    :param bool call_work_forward: will traverse CALL_WORK links in the forward direction.
    """
    traverse_links = validate_traversal_rules(GraphTraversalRules.DELETE, **kwargs)

    traverse_output = traverse_graph(
        starting_pks,
        get_links=get_links,
        links_forward=traverse_links['forward'],
        links_backward=traverse_links['backward']
    )

    function_output = {
        'nodes': traverse_output['nodes'],
        'links': traverse_output['links'],
        'rules': traverse_links['rules_applied']
    }

    return function_output


def get_nodes_export(starting_pks, get_links=False, **kwargs):
    """
    This function will return the set of all nodes that can be connected
    to a list of initial nodes through any sequence of specified authorized
    links and directions for export. This will also return the links and
    the traversal rules parsed.

    :type starting_pks: list or tuple or set
    :param starting_pks: Contains the (valid) pks of the starting nodes.

    :param bool get_links:
        Pass True to also return the links between all nodes (found + initial).

    :param bool input_calc_forward: will traverse INPUT_CALC links in the forward direction.
    :param bool create_backward: will traverse CREATE links in the backward direction.
    :param bool return_backward: will traverse RETURN links in the backward direction.
    :param bool input_work_forward: will traverse INPUT_WORK links in the forward direction.
    :param bool call_calc_backward: will traverse CALL_CALC links in the backward direction.
    :param bool call_work_backward: will traverse CALL_WORK links in the backward direction.
    """
    traverse_links = validate_traversal_rules(GraphTraversalRules.EXPORT, **kwargs)

    traverse_output = traverse_graph(
        starting_pks,
        get_links=get_links,
        links_forward=traverse_links['forward'],
        links_backward=traverse_links['backward']
    )

    function_output = {
        'nodes': traverse_output['nodes'],
        'links': traverse_output['links'],
        'rules': traverse_links['rules_applied']
    }

    return function_output


def validate_traversal_rules(ruleset=GraphTraversalRules.DEFAULT, **kwargs):
    """
    Validates the keywords with a ruleset template and returns a parsed dictionary
    ready to be used.

    :type ruleset: :py:class:`aiida.common.links.GraphTraversalRules`
    :param ruleset: Ruleset template used to validate the set of rules.
    :param bool input_calc_forward: will traverse INPUT_CALC links in the forward direction.
    :param bool input_calc_backward: will traverse INPUT_CALC links in the backward direction.
    :param bool create_forward: will traverse CREATE links in the forward direction.
    :param bool create_backward: will traverse CREATE links in the backward direction.
    :param bool return_forward: will traverse RETURN links in the forward direction.
    :param bool return_backward: will traverse RETURN links in the backward direction.
    :param bool input_work_forward: will traverse INPUT_WORK links in the forward direction.
    :param bool input_work_backward: will traverse INPUT_WORK links in the backward direction.
    :param bool call_calc_forward: will traverse CALL_CALC links in the forward direction.
    :param bool call_calc_backward: will traverse CALL_CALC links in the backward direction.
    :param bool call_work_forward: will traverse CALL_WORK links in the forward direction.
    :param bool call_work_backward: will traverse CALL_WORK links in the backward direction.
    """
    from aiida.common import exceptions

    if not isinstance(ruleset, GraphTraversalRules):
        raise TypeError(
            f'ruleset input must be of type aiida.common.links.GraphTraversalRules\ninstead, it is: {type(ruleset)}'
        )

    rules_applied = {}
    links_forward = []
    links_backward = []

    for name, rule in ruleset.value.items():

        follow = rule.default

        if name in kwargs:

            if not rule.toggleable:
                raise ValueError(f'input rule {name} is not toggleable for ruleset {ruleset}')

            follow = kwargs.pop(name)

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

    if kwargs:
        error_message = f"unrecognized keywords: {', '.join(kwargs.keys())}"
        raise exceptions.ValidationError(error_message)

    valid_output = {
        'rules_applied': rules_applied,
        'forward': links_forward,
        'backward': links_backward,
    }

    return valid_output


def traverse_graph(starting_pks, max_iterations=None, get_links=False, links_forward=(), links_backward=()):
    """
    This function will return the set of all nodes that can be connected
    to a list of initial nodes through any sequence of specified links.
    Optionally, it may also return the links that connect these nodes.

    :type starting_pks: list or tuple or set
    :param starting_pks: Contains the (valid) pks of the starting nodes.

    :type max_iterations: int or None
    :param max_iterations:
        The number of iterations to apply the set of rules (a value of 'None' will
        iterate until no new nodes are added).

    :param bool get_links:
        Pass True to also return the links between all nodes (found + initial).

    :type links_forward: aiida.common.links.LinkType
    :param links_forward:
        List with all the links that should be traversed in the forward direction.

    :type links_backward: aiida.common.links.LinkType
    :param links_backward:
        List with all the links that should be traversed in the backward direction.
    """
    # pylint: disable=too-many-locals,too-many-statements,too-many-branches
    from aiida import orm
    from aiida.tools.graph.age_entities import Basket
    from aiida.tools.graph.age_rules import UpdateRule, RuleSequence, RuleSaveWalkers, RuleSetWalkers
    from aiida.common import exceptions

    if max_iterations is None:
        max_iterations = inf
    elif not (isinstance(max_iterations, int) or max_iterations is inf):
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

    if not isinstance(starting_pks, (list, set, tuple)):
        raise TypeError(f'starting_pks must be of type list, set or tuple\ninstead, it is {type(starting_pks)}')

    if not starting_pks:
        if get_links:
            output = {'nodes': set(), 'links': set()}
        else:
            output = {'nodes': set(), 'links': None}
        return output

    if any([not isinstance(pk, int) for pk in starting_pks]):
        raise TypeError(f'one of the starting_pks is not of type int:\n {starting_pks}')
    operational_set = set(starting_pks)

    query_nodes = orm.QueryBuilder()
    query_nodes.append(orm.Node, project=['id'], filters={'id': {'in': operational_set}})
    existing_pks = set(query_nodes.all(flat=True))
    missing_pks = operational_set.difference(existing_pks)
    if missing_pks:
        raise exceptions.NotExistent(
            f'The following pks are not in the database and must be pruned before this   call: {missing_pks}'
        )

    rules = []
    basket = Basket(nodes=operational_set)

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
        query_outgoing = orm.QueryBuilder()
        query_outgoing.append(orm.Node, tag='sources')
        query_outgoing.append(orm.Node, edge_filters=filters_forwards, with_incoming='sources')
        rule_outgoing = UpdateRule(query_outgoing, max_iterations=1, track_edges=get_links)
        rules += [rule_outgoing]

    if links_forward and links_backward:
        rules += [RuleSetWalkers(stash)]

    if links_backward:
        query_incoming = orm.QueryBuilder()
        query_incoming.append(orm.Node, tag='sources')
        query_incoming.append(orm.Node, edge_filters=filters_backwards, with_outgoing='sources')
        rule_incoming = UpdateRule(query_incoming, max_iterations=1, track_edges=get_links)
        rules += [rule_incoming]

    rulesequence = RuleSequence(rules, max_iterations=max_iterations)

    results = rulesequence.run(basket)

    output = {}
    output['nodes'] = results.nodes.keyset
    output['links'] = None
    if get_links:
        output['links'] = results['nodes_nodes'].keyset

    return output
