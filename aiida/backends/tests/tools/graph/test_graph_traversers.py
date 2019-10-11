# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=missing-docstring
# pylint: disable=too-many-locals,too-many-statements
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

#import unittest
from aiida.backends.testbase import AiidaTestCase
from aiida.tools.graph.graph_traversers import exhaustive_traverser


class TestExhaustiveTraverser(AiidaTestCase):

    @staticmethod
    def _create_minimal_graph():
        """
        Creates a minimal graph which has one parent workflow (W2) that calls
        a child workflow (W1) which calls a calculation function (C0). There
        is one input (DI) and one output (DO). It has at least one link of
        each class:

        * CALL_WORK from W2 to W1.
        * CALL_CALC from W1 to C0.
        * INPUT_CALC from DI to C0 and CREATE from C0 to DO.
        * INPUT_WORK from DI to W1 and RETURN from W1 to DO.
        * INPUT_WORK from DI to W2 and RETURN from W2 to DO.

        This graph looks like this::

                  input_work     +----+     return
              +----------------> | W2 | ---------------+
              |                  +----+                |
              |                    |                   |
              |                    | call_work         |
              |                    |                   |
              |                    v                   |
              |     input_work   +----+    return      |
              |  +-------------> | W1 | ------------+  |
              |  |               +----+             |  |
              |  |                 |                |  |
              |  |                 | call_calc      |  |
              |  |                 |                |  |
              |  |                 v                v  v
            +------+ input_calc  +----+  create   +------+
            |  DI  | ----------> | C0 | --------> |  DO  |
            +------+             +----+           +------+
        """
        from aiida.common.links import LinkType
        from aiida import orm

        data_i = orm.Data().store()
        data_o = orm.Data().store()

        calc_0 = orm.CalculationNode()
        work_1 = orm.WorkflowNode()
        work_2 = orm.WorkflowNode()

        calc_0.add_incoming(data_i, link_type=LinkType.INPUT_CALC, link_label='inpcalc')
        work_1.add_incoming(data_i, link_type=LinkType.INPUT_WORK, link_label='inpwork')
        work_2.add_incoming(data_i, link_type=LinkType.INPUT_WORK, link_label='inpwork')
        calc_0.add_incoming(work_1, link_type=LinkType.CALL_CALC, link_label='callcalc')
        work_1.add_incoming(work_2, link_type=LinkType.CALL_WORK, link_label='callwork')

        work_2.store()
        work_1.store()
        calc_0.store()

        data_o.add_incoming(calc_0, link_type=LinkType.CREATE, link_label='create0')
        data_o.add_incoming(work_1, link_type=LinkType.RETURN, link_label='return1')
        data_o.add_incoming(work_2, link_type=LinkType.RETURN, link_label='return2')

        return data_i, data_o, calc_0, work_1, work_2

    def test_traversal_individually(self):
        """
        This will go through all the rules and check one case in graph where it
        can be applied.
        """
        from aiida.common.links import GraphTraversalRules

        # This uses the delete dict because it has the same names as the export dict,
        # which is all this test needs
        traverser_rules = {}
        for name in GraphTraversalRules.DELETE.value:
            traverser_rules[name] = False

        data_i, data_o, calc_0, work_1, work_2 = self._create_minimal_graph()
        pkdi = data_i.pk
        pkdo = data_o.pk
        pkc0 = calc_0.pk
        pkw1 = work_1.pk
        pkw2 = work_2.pk

        test_rule_list = []
        starting_nodes = []
        included_nodes = []

        test_rule_list.append('input_calc_forward')
        starting_nodes.append([pkdi])
        included_nodes.append([pkc0])

        test_rule_list.append('input_calc_backward')
        starting_nodes.append([pkc0])
        included_nodes.append([pkdi])

        test_rule_list.append('create_forward')
        starting_nodes.append([pkc0])
        included_nodes.append([pkdo])

        test_rule_list.append('create_backward')
        starting_nodes.append([pkdo])
        included_nodes.append([pkc0])

        test_rule_list.append('return_forward')
        starting_nodes.append([pkw1])
        included_nodes.append([pkdo])

        test_rule_list.append('return_backward')
        starting_nodes.append([pkdo])
        included_nodes.append([pkw1, pkw2])

        test_rule_list.append('input_work_forward')
        starting_nodes.append([pkdi])
        included_nodes.append([pkw1, pkw2])

        test_rule_list.append('input_work_backward')
        starting_nodes.append([pkw1])
        included_nodes.append([pkdi])

        test_rule_list.append('call_calc_forward')
        starting_nodes.append([pkw1])
        included_nodes.append([pkc0])

        test_rule_list.append('call_calc_backward')
        starting_nodes.append([pkc0])
        included_nodes.append([pkw1])

        test_rule_list.append('call_work_forward')
        starting_nodes.append([pkw2])
        included_nodes.append([pkw1])

        test_rule_list.append('call_work_backward')
        starting_nodes.append([pkw1])
        included_nodes.append([pkw2])

        for idx, test_rule in enumerate(test_rule_list):
            traverser_rules[test_rule] = True
            obtained_nodes = exhaustive_traverser(starting_nodes[idx], **traverser_rules)
            expected_nodes = set(starting_nodes[idx] + included_nodes[idx])
            self.assertEqual(obtained_nodes, expected_nodes)
            traverser_rules[test_rule] = False

    def test_traversal_full_graph(self):
        """
        This will test that the traverser can get the full graph with the minimal traverse
        required keywords.
        """
        from aiida.common.links import GraphTraversalRules

        # This uses the delete dict because it has the same names as the export dict,
        # which is all this test needs
        traverser_rules = {}
        for name in GraphTraversalRules.DELETE.value:
            traverser_rules[name] = False

        data_i, data_o, calc_0, work_1, work_2 = self._create_minimal_graph()
        pkdi = data_i.pk
        pkdo = data_o.pk
        pkc0 = calc_0.pk
        pkw1 = work_1.pk
        pkw2 = work_2.pk

        expected_nodes = set([pkdi, pkdo, pkc0, pkw1, pkw2])

        nodeset_list = []

        nodeset_list.append(
            ([pkdi], ['input_calc_forward', 'call_calc_backward', 'call_work_backward', 'return_forward'])
        )
        nodeset_list.append(([pkdi], ['input_calc_forward', 'create_forward', 'return_backward']))
        nodeset_list.append(([pkdi], ['input_work_forward', 'call_calc_forward', 'create_forward']))

        nodeset_list.append(
            ([pkdo], ['create_backward', 'call_calc_backward', 'call_work_backward', 'input_work_backward'])
        )
        nodeset_list.append(([pkdo], ['create_backward', 'input_calc_backward', 'input_work_forward']))
        nodeset_list.append(([pkdo], ['return_backward', 'call_calc_forward', 'input_calc_backward']))

        nodeset_list.append(
            ([pkc0], ['create_forward', 'call_calc_backward', 'call_work_backward', 'input_calc_backward'])
        )
        nodeset_list.append(([pkc0], ['create_forward', 'return_backward', 'input_work_backward']))
        nodeset_list.append(([pkc0], ['input_calc_backward', 'input_work_forward', 'return_forward']))

        nodeset_list.append(
            ([pkw1], ['input_work_backward', 'return_forward', 'call_work_backward', 'call_calc_forward'])
        )
        nodeset_list.append(
            ([pkw2], ['input_calc_backward', 'create_forward', 'call_work_forward', 'call_calc_forward'])
        )
        nodeset_list.append(([pkw1], ['return_forward', 'create_backward', 'input_calc_backward',
                                      'input_work_forward']))
        nodeset_list.append(([pkw1], ['call_calc_forward', 'create_forward', 'return_backward', 'input_calc_backward']))

        for nodes, minimal_set in nodeset_list:
            for rule in minimal_set:
                traverser_rules[rule] = True
            obtained_nodes = exhaustive_traverser(nodes, **traverser_rules)
            self.assertEqual(obtained_nodes, expected_nodes)
            for rule in minimal_set:
                traverser_rules[rule] = False

    @staticmethod
    def _mini_traverser(node_zero, rule1, rule2, connections):
        """
        For testing purposes, limited functionality of the traverser: will take only
        one node and two rules and obtain all nodes that can be connected to that node
        through a maximum of two links (if they comply with the two rules provided).
        The connections must be provided as a dictionary with the following keys:

        - 'node_i': the incoming node.
        - 'node_o': the outgoing node
        - 'link_f': the link with the forward direction.
        - 'link_b': the link with the backward direction.
        """
        nodes_found = set([node_zero])
        for link1 in connections:

            link1_is_go = False
            zero_is_inp = (node_zero == link1['node_i'])
            zero_is_out = (node_zero == link1['node_o'])
            linkf_is_go = link1['rule_f'] in [rule1, rule2]
            linkb_is_go = link1['rule_b'] in [rule1, rule2]

            if zero_is_inp and linkf_is_go:
                next_node = link1['node_o']
                link1_is_go = True

            if zero_is_out and linkb_is_go:
                next_node = link1['node_i']
                link1_is_go = True

            if link1_is_go:
                nodes_found.add(next_node)
                for link2 in connections:
                    node_is_inp = (next_node == link2['node_i'])
                    node_is_out = (next_node == link2['node_o'])
                    linkf_is_go = link2['rule_f'] in [rule1, rule2]
                    linkb_is_go = link2['rule_b'] in [rule1, rule2]

                    if node_is_inp and linkf_is_go:
                        nodes_found.add(link2['node_o'])

                    if node_is_out and linkb_is_go:
                        nodes_found.add(link2['node_i'])

        return nodes_found

    def test_traversal_concats(self):
        """
        This will go through the possible concatenations of rules.
        """
        from aiida.common.links import GraphTraversalRules

        # This uses the delete dict because it has the same names as the export dict,
        # which is all this test needs
        traverser_rules = {}
        for name in GraphTraversalRules.DELETE.value:
            traverser_rules[name] = False

        data_i, data_o, calc_0, work_1, work_2 = self._create_minimal_graph()
        pkdi = data_i.pk
        pkdo = data_o.pk
        pkc0 = calc_0.pk
        pkw1 = work_1.pk
        pkw2 = work_2.pk

        node_list = [pkdi, pkdo, pkc0, pkw1, pkw2]
        connection_links = []

        newlink = {}
        newlink['node_i'] = pkdi
        newlink['rule_f'] = 'input_work_forward'
        newlink['rule_b'] = 'input_work_backward'
        newlink['node_o'] = pkw2
        connection_links.append(newlink)

        newlink = {}
        newlink['node_i'] = pkdi
        newlink['rule_f'] = 'input_work_forward'
        newlink['rule_b'] = 'input_work_backward'
        newlink['node_o'] = pkw1
        connection_links.append(newlink)

        newlink = {}
        newlink['node_i'] = pkdi
        newlink['rule_f'] = 'input_calc_forward'
        newlink['rule_b'] = 'input_calc_backward'
        newlink['node_o'] = pkc0
        connection_links.append(newlink)

        newlink = {}
        newlink['node_i'] = pkw2
        newlink['rule_f'] = 'return_forward'
        newlink['rule_b'] = 'return_backward'
        newlink['node_o'] = pkdo
        connection_links.append(newlink)

        newlink = {}
        newlink['node_i'] = pkw1
        newlink['rule_f'] = 'return_forward'
        newlink['rule_b'] = 'return_backward'
        newlink['node_o'] = pkdo
        connection_links.append(newlink)

        newlink = {}
        newlink['node_i'] = pkc0
        newlink['rule_f'] = 'create_forward'
        newlink['rule_b'] = 'create_backward'
        newlink['node_o'] = pkdo
        connection_links.append(newlink)

        newlink = {}
        newlink['node_i'] = pkw2
        newlink['rule_f'] = 'call_work_forward'
        newlink['rule_b'] = 'call_work_backward'
        newlink['node_o'] = pkw1
        connection_links.append(newlink)

        newlink = {}
        newlink['node_i'] = pkw1
        newlink['rule_f'] = 'call_calc_forward'
        newlink['rule_b'] = 'call_calc_backward'
        newlink['node_o'] = pkc0
        connection_links.append(newlink)

        rules_list = GraphTraversalRules.DELETE.value.copy()

        for rule1 in list(rules_list):
            rules_list.pop(rule1)
            for rule2 in rules_list:
                for node_zero in node_list:

                    traverser_rules[rule1] = True
                    traverser_rules[rule2] = True
                    expected_nodes = self._mini_traverser(node_zero, rule1, rule2, connection_links)
                    obtained_nodes = exhaustive_traverser([node_zero], **traverser_rules)
                    self.assertEqual(obtained_nodes, expected_nodes)
                    traverser_rules[rule1] = False
                    traverser_rules[rule2] = False

    def test_traversal_cycle(self):
        """
        This will test that cycles don't go into infinite loops by testing a
        graph with two data nodes data_take and data_drop and a work_select
        that takes both as input but returns only data_take
        """
        from aiida.common.links import GraphTraversalRules
        from aiida.common.links import LinkType
        from aiida import orm

        traverser_rules = {}
        for name in GraphTraversalRules.DELETE.value:
            traverser_rules[name] = False

        data_take = orm.Data().store()
        data_drop = orm.Data().store()
        work_select = orm.WorkflowNode()

        work_select.add_incoming(data_take, link_type=LinkType.INPUT_WORK, link_label='input_take')
        work_select.add_incoming(data_drop, link_type=LinkType.INPUT_WORK, link_label='input_drop')
        work_select.store()

        data_take.add_incoming(work_select, link_type=LinkType.RETURN, link_label='return_link')

        data_take = data_take.pk
        data_drop = data_drop.pk
        work_select = work_select.pk

        every_node = [data_take, data_drop, work_select]

        for single_node in every_node:
            expected_nodes = set([single_node])
            obtained_nodes = exhaustive_traverser([single_node], **traverser_rules)
            self.assertEqual(obtained_nodes, expected_nodes)

        traverser_rules['input_work_forward'] = True
        traverser_rules['return_forward'] = True
        obtained_nodes = exhaustive_traverser([data_drop], **traverser_rules)
        expected_nodes = set(every_node)
        self.assertEqual(obtained_nodes, expected_nodes)
        obtained_nodes = exhaustive_traverser([data_take], **traverser_rules)
        expected_nodes = set([work_select, data_take])
        self.assertEqual(obtained_nodes, expected_nodes)
        obtained_nodes = exhaustive_traverser([work_select], **traverser_rules)
        self.assertEqual(obtained_nodes, expected_nodes)
        traverser_rules['input_work_forward'] = False
        traverser_rules['return_forward'] = False

        traverser_rules['input_work_backward'] = True
        traverser_rules['return_backward'] = True
        expected_nodes = set([data_drop])
        obtained_nodes = exhaustive_traverser([data_drop], **traverser_rules)
        self.assertEqual(obtained_nodes, expected_nodes)
        expected_nodes = set(every_node)
        obtained_nodes = exhaustive_traverser([data_take], **traverser_rules)
        self.assertEqual(obtained_nodes, expected_nodes)
        obtained_nodes = exhaustive_traverser([work_select], **traverser_rules)
        self.assertEqual(obtained_nodes, expected_nodes)
        traverser_rules['input_work_backward'] = False
        traverser_rules['return_backward'] = False

    def test_traversal_errors(self):
        """
        This will test the errors of the traversers.
        """
        from aiida.common.links import GraphTraversalRules
        from aiida.common.exceptions import ValidationError, NotExistent

        from aiida import orm

        # This uses the delete dict because it has the same names as the export dict,
        # which is all this test needs
        traverser_rules = {}
        for name in GraphTraversalRules.DELETE.value:
            traverser_rules[name] = False

        test_node = orm.Data().store()

        false_node = -1
        with self.assertRaises(NotExistent):
            exhaustive_traverser([false_node], **traverser_rules)

        del traverser_rules['return_forward']
        with self.assertRaises(ValidationError):
            exhaustive_traverser([test_node], **traverser_rules)
        traverser_rules['return_forward'] = False

        traverser_rules['return_forward'] = 1984
        with self.assertRaises(ValueError):
            exhaustive_traverser([test_node], **traverser_rules)
        traverser_rules['return_forward'] = False

        traverser_rules['false_rule'] = False
        with self.assertRaises(ValidationError):
            exhaustive_traverser([test_node], **traverser_rules)
        del traverser_rules['false_rule']
