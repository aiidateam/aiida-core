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

from __future__ import absolute_import
from numpy import inf


def exhaustive_traverser(starting_pks, **kwargs):
    """
    This function will return the set of all nodes that can be connected
    to a list of initial nodes through any sequence of specified authorized
    links and directions.

    :param starting_pks:
        A list with the (valid) pks of all starting nodes.
    :param traverse_links:
        A dictionary asigning a boolean value to each of the graph traversal
        rules.
    """
    # pylint: disable=too-many-locals,too-many-statements,too-many-branches
    from aiida.orm import Node
    from aiida.orm.querybuilder import QueryBuilder
    from aiida.tools.graph.age_entities import get_basket
    from age_rules import UpdateRule, RuleSequence, RuleSaveWalkers, RuleSetWalkers, MODES
    from aiida.common import exceptions
    from aiida.common.links import GraphTraversalRules

    follow_backwards = []
    follow_forwards = []

    # Create the dictionary with graph traversal rules to be applied
    # (This uses the delete dict because it has the same names and directions
    #  as the export dict, which is all this function needs)
    for name, rule in GraphTraversalRules.DELETE.value.items():

        # Check that all rules are explicitly provided
        if name not in kwargs:
            raise exceptions.ValidationError('traversal rule {} was not provided'.format(name))

        follow = kwargs.pop(name)
        if not isinstance(follow, bool):
            raise ValueError('the value of rule {} must be boolean, but it is: {}'.format(name, follow))

        if follow:
            if rule.direction == 'forward':
                follow_forwards.append(rule.link_type.value)
            elif rule.direction == 'backward':
                follow_backwards.append(rule.link_type.value)
            else:
                raise exceptions.InternalError(
                    'unrecognized direction `{}` for graph traversal rule'.format(rule.direction)
                )

    if kwargs:
        raise exceptions.ValidationError('unrecognized keywords: {}'.format(', '.join(kwargs.keys())))

    links_backwards = {'type': {'in': follow_backwards}}
    links_forwards = {'type': {'in': follow_forwards}}

    operational_set = set(starting_pks)
    query_nodes = QueryBuilder()
    query_nodes.append(Node, project=['id'], filters={'id': {'in': operational_set}})
    existing_pks = {pk[0] for pk in query_nodes.all()}
    missing_pks = operational_set.difference(existing_pks)
    if missing_pks:
        raise exceptions.NotExistent(
            'The following pks are not in the database and must be pruned before this call: {}'.format(missing_pks)
        )

    basket = get_basket(node_ids=operational_set)
    rules = []
    if follow_forwards and follow_backwards:
        stash = basket.get_template()
        rules += [RuleSaveWalkers(stash)]
    if follow_forwards:
        query_outgoing = QueryBuilder()
        query_outgoing.append(Node, tag='sources')
        query_outgoing.append(Node, edge_filters=links_forwards, with_incoming='sources')
        rule_outgoing = UpdateRule(query_outgoing, mode=MODES.APPEND, max_iterations=1, track_edges=False)
        rules += [rule_outgoing]
    if follow_forwards and follow_backwards:
        rules += [RuleSetWalkers(stash)]
    if follow_backwards:
        query_incomong = QueryBuilder()
        query_incomong.append(Node, tag='sources')
        query_incomong.append(Node, edge_filters=links_backwards, with_outgoing='sources')
        rule_incoming = UpdateRule(query_incomong, mode=MODES.APPEND, max_iterations=1, track_edges=False)
        rules += [rule_incoming]
    rulesequence = RuleSequence(rules, max_iterations=inf)
    results = rulesequence.run(basket)
    # ~ accumulator_set = operational_set.copy()
    # ~ while operational_set:
    # ~ new_pks_set = set()

    # ~ if follow_forwards:
    # ~ query_nodes = QueryBuilder()
    # ~ query_nodes.append(Node, filters={'id': {'in': operational_set}}, tag='sources')
    # ~ query_nodes.append(Node, edge_filters=links_forwards, with_incoming='sources', project='id')
    # ~ new_pks_set = new_pks_set.union(set(pk for pk, in query_nodes.iterall()))

    # ~ if follow_backwards:
    # ~ query_nodes = QueryBuilder()
    # ~ query_nodes.append(Node, filters={'id': {'in': operational_set}}, tag='sources')
    # ~ query_nodes.append(Node, edge_filters=links_backwards, with_outgoing='sources', project='id')
    # ~ new_pks_set = new_pks_set.union(set(pk for pk, in query_nodes.iterall()))

    # ~ operational_set = new_pks_set.difference(accumulator_set)
    # ~ accumulator_set = new_pks_set.union(accumulator_set)

    # ~ if accumulator_set == results.nodes.get_keys():
    # ~ pass
    # ~ else:
    # ~ print(1, accumulator_set)
    # ~ print(2, results.nodes.get_keys())
    # ~ print('forwards', links_forwards)
    # ~ print('backward', links_backwards)
    # ~ print('origin', starting_pks)
    # ~ input()
    return results.nodes.get_keys()
