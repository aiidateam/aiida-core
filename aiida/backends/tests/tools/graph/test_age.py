# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=too-many-locals
"""AGE tests"""

from __future__ import absolute_import
from __future__ import print_function
import numpy as np
from six.moves import range
from six.moves import zip

from aiida.tools.graph.age_entities import get_basket
from aiida.tools.graph.age_rules import (UpdateRule, RuleSequence, MODES, RuleSaveWalkers, RuleSetWalkers)

from aiida.backends.testbase import AiidaTestCase
from aiida.common.links import LinkType
from aiida.orm import Group, Node, Data, CalculationNode, WorkflowNode, ProcessNode
from aiida.orm.querybuilder import QueryBuilder


def create_tree(max_depth=3, branching=3, starting_cls=Data, draw=False):
    """
    Auxiliary function to create a tree with a given depth and a given branching.
    """
    if starting_cls not in (Data, CalculationNode):
        raise TypeError('The starting_cls has to be either Data or Calculation')

    # The number of nodes I will create:
    number_of_nodes = sum([branching**d for d in range(max_depth)])

    # This is the ancestor of every Node I create later
    parent = starting_cls().store()

    # This where I save the descendants, by depth (depth is the key).
    # I'm including original node as a descendant of depth 0.
    depth_dict = {}
    depth_dict[0] = set([parent.id])

    # The previous_cls is needed to be able to alternate between Data and Calculations
    # If previous_cls is Data, add calculations, and vice versa
    # The previous_ins list stores all the instance created in the previous iteration
    # The previous_indicies list stores where the ids of previous_ins are
    # stored in all_instances:
    previous_cls = starting_cls
    previous_ins = [parent]
    previous_indices = [0]

    # all_instances saves all the instances EVER created"
    all_instances = np.zeros(number_of_nodes, dtype=int)
    all_instances[0] = parent.id
    adjacency = np.zeros((number_of_nodes, number_of_nodes), dtype=int)

    # Iterating over the depth of the tree
    counter = 1
    for depth in range(1, max_depth):
        # I'm at new depth, create new set:
        depth_dict[depth] = set()

        # Here I decide what class to create this level of descendants, and what the
        # link type is:
        cls = Data if previous_cls is CalculationNode else CalculationNode
        ltype = LinkType.CREATE if cls is Data else LinkType.INPUT_CALC

        # The new instances I create are saved in this list:
        new_ins = []
        new_indices = []

        # Iterating over previous instances
        for (pins, pins_idx) in zip(previous_ins, previous_indices):
            # every previous instances gets a certain number of children:
            for ioutgoing in range(branching):
                new = cls()
                new.add_incoming(pins, link_type=ltype, link_label='link{}'.format(ioutgoing))
                new.store()
                #new.add_link_from(pins, link_type=ltype, label='{}'.format(ioutgoing))
                new_ins.append(new)
                all_instances[counter] = new.id
                adjacency[pins_idx, counter] = 1
                new_indices.append(counter)

                depth_dict[depth].add(new.id)
                counter += 1
        # Everything done, loading new instances to previous instances, and previous class
        # to this class:
        previous_ins = new_ins
        previous_indices = new_indices
        previous_cls = cls

    if draw:
        print('Function disabled.')
    #    from aiida.cmdline.utils.ascii_vis import draw_children
    #    print('\n\n\n The tree created:')
    #    print(draw_children(parent, dist=max_depth+1))
    # ~ follow_links_of_type=(LinkType.INPUT_CALC, LinkType.CREATE)))
    # ~ follow_links_of_type=(LinkType.INPUT, LinkType.CREATE)))
    #    print('\n\n\n')

    result = {}
    result['parent'] = parent
    result['depth_dict'] = depth_dict
    result['instances'] = all_instances
    result['adjacency'] = adjacency
    return result


class TestNodes(AiidaTestCase):
    """Tests for the AGE"""
    # Hardcoding here how deep I go and the branching at every level
    # i.e. the number of children per parent Node.
    DEPTH = 4
    NUMBER_OF_CHILDREN = 2

    def test_data_provenance(self):
        """
        Creating a parent (Data) node.
        Attaching a sequence of Calculation/Data to create a "provenance".
        """

        created_dict = create_tree(self.DEPTH, self.NUMBER_OF_CHILDREN)
        parent = created_dict['parent']
        desc_dict = created_dict['depth_dict']

        # Created all the nodes, tree.
        # Now testing whether I find all the descendants
        # Using the utility function to create the starting entity set:
        basket0 = get_basket(node_ids=(parent.id,))
        queryb0 = QueryBuilder().append(Node).append(Node)

        for depth in range(0, self.DEPTH):
            #print('At depth {}'.format(depth))

            rule = UpdateRule(queryb0, mode=MODES.REPLACE, max_iterations=depth)
            res = rule.run(basket0.copy())['nodes'].get_keys()
            #print('   Replace-mode results: {}'.format(', '.join(map(str, sorted(res)))))
            should_set = desc_dict[depth]
            self.assertTrue(not (res.difference(should_set) or should_set.difference(res)))

            rule = UpdateRule(queryb0, mode=MODES.APPEND, max_iterations=depth)
            res = rule.run(basket0.copy())['nodes'].get_keys()
            #print('   Append-mode  results: {}'.format(', '.join(map(str, sorted(res)))))
            should_set = set()
            for this_depth in range(depth + 1):
                for node_id in desc_dict[this_depth]:
                    should_set.add(node_id)

            self.assertTrue(not (res.difference(should_set) or should_set.difference(res)))

    def test_cycle(self):
        """
        Creating a cycle: A data-instance is both input to and returned by a WorkFlowNode
        """
        data_node = Data().store()
        work_node = WorkflowNode()
        work_node.add_incoming(data_node, link_type=LinkType.INPUT_WORK, link_label='input_link')
        work_node.store()
        data_node.add_incoming(work_node, link_type=LinkType.RETURN, link_label='return_link')

        queryb0 = QueryBuilder().append(Node).append(Node)
        rule = UpdateRule(queryb0, max_iterations=np.inf)
        basket0 = get_basket(node_ids=(data_node.id,))
        res = rule.run(basket0.copy())
        self.assertEqual(res['nodes'].get_keys(), set([data_node.id, work_node.id]))

    def test_stash(self):
        """
        Testing the 'stash' functionality
        """
        # This will be tested with a graph that has a calculation (calc_ca) with two
        # input data nodes (data_i1 and data_i2) and two output data nodes (data_o1
        # and data_o2), and another calculation (calc_cb) which takes both one of
        # the inputs and one of the outputs of the first one (data_i2 and data_o2)
        # as inputs to produce a final output (data_o3).

        calc_ca = CalculationNode()

        data_i1 = Data().store()
        data_i2 = Data().store()
        calc_ca.add_incoming(data_i1, link_type=LinkType.INPUT_CALC, link_label='link_ai1')
        calc_ca.add_incoming(data_i2, link_type=LinkType.INPUT_CALC, link_label='link_ai2')
        calc_ca.store()

        data_o1 = Data().store()
        data_o2 = Data().store()
        data_o1.add_incoming(calc_ca, link_type=LinkType.CREATE, link_label='link_ao1')
        data_o2.add_incoming(calc_ca, link_type=LinkType.CREATE, link_label='link_ao2')

        dins = set()
        dins.add(data_i1.id)
        dins.add(data_i2.id)
        douts = set()
        douts.add(data_o1.id)
        douts.add(data_o2.id)

        calc_cb = CalculationNode()
        calc_cb.add_incoming(data_i2, link_type=LinkType.INPUT_CALC, link_label='link_bi2')
        calc_cb.add_incoming(data_o2, link_type=LinkType.INPUT_CALC, link_label='link_bo2')
        calc_cb.store()
        data_o3 = Data().store()
        data_o3.add_incoming(calc_cb, link_type=LinkType.CREATE, link_label='link_bo3')

        # ALso here starting with a set that only contains the starting the calculation:
        basket0 = get_basket(node_ids=(calc_ca.id,))

        # Creating the rule for getting input nodes:
        queryb1 = QueryBuilder().append(Node, tag='n').append(Node, with_outgoing='n')
        rule_in = UpdateRule(queryb1)

        # Creating the rule for getting output nodes
        queryb2 = QueryBuilder().append(Node, tag='n').append(Node, with_incoming='n')
        rule_out = UpdateRule(queryb2)

        # I'm testing the input rule. Since I'm updating, I should
        # have the input and the calculation itself:
        is_set = rule_in.run(basket0.copy())['nodes'].get_keys()
        self.assertEqual(is_set, dins.union({calc_ca.id}))

        # Testing the output rule, also here, output + calculation c is expected:
        is_set = rule_out.run(basket0.copy())['nodes'].get_keys()
        self.assertEqual(is_set, douts.union({calc_ca.id}))

        # Now I'm  testing the rule sequence.
        # I first apply the rule to get outputs, than the rule to get inputs
        rs1 = RuleSequence((rule_out, rule_in))
        is_set = rs1.run(basket0.copy())['nodes'].get_keys()

        # I expect the union of inputs, outputs, and the calculation:
        self.assertEqual(is_set, douts.union(dins).union({calc_ca.id}))

        # If the order of the rules is exchanged, I end up of also attaching c2 to the results.
        # This is because c and c2 share one data-input:
        rs2 = RuleSequence((rule_in, rule_out))
        is_set = rs2.run(basket0.copy())['nodes'].get_keys()
        self.assertEqual(is_set, douts.union(dins).union({calc_ca.id, calc_cb.id}))

        # Testing similar rule, but with the possibility to stash the results:
        stash = basket0.copy(with_data=False)
        rsave = RuleSaveWalkers(stash)

        # Checking whether Rule does the right thing i.e If I stash the result,
        # the active walkers should be an empty set:
        self.assertEqual(rsave.run(basket0.copy()), basket0.copy(with_data=False))

        # Whereas the stash contains the same data as the starting point:
        self.assertEqual(stash, basket0)
        rs2 = RuleSequence((RuleSaveWalkers(stash), rule_in, RuleSetWalkers(stash), rule_out))
        is_set = rs2.run(basket0.copy())['nodes'].get_keys()

        # NOw I test whether the stash does the right thing,
        # namely not including c2 in the results:
        self.assertEqual(is_set, douts.union(dins).union({calc_ca.id}))

    def test_returns_calls(self):
        """Tests return calls (?)"""
        create_reversed = False
        return_reversed = False

        rules = []
        # linking all processes to input data:
        queryb0 = QueryBuilder()
        queryb0.append(Data, tag='predecessor')
        queryb0.append(
            ProcessNode,
            with_incoming='predecessor',
            edge_filters={'type': {
                'in': [LinkType.INPUT_CALC.value, LinkType.INPUT_WORK.value]
            }}
        )
        rules.append(UpdateRule(queryb0))

        # CREATE/RETURN(ProcessNode, Data) - Forward
        queryb0 = QueryBuilder()
        queryb0.append(ProcessNode, tag='predecessor')
        queryb0.append(
            Data,
            with_incoming='predecessor',
            edge_filters={'type': {
                'in': [LinkType.CREATE.value, LinkType.RETURN.value]
            }}
        )
        rules.append(UpdateRule(queryb0))

        # CALL(ProcessNode, ProcessNode) - Forward
        queryb0 = QueryBuilder()
        queryb0.append(ProcessNode, tag='predecessor')
        queryb0.append(
            ProcessNode,
            with_incoming='predecessor',
            edge_filters={'type': {
                'in': [LinkType.CALL_CALC.value, LinkType.CALL_WORK.value]
            }}
        )
        rules.append(UpdateRule(queryb0))

        # CREATE(ProcessNode, Data) - Reversed
        if create_reversed:
            queryb0 = QueryBuilder()
            queryb0.append(ProcessNode, tag='predecessor', project=['id'])
            queryb0.append(Data, with_incoming='predecessor', edge_filters={'type': {'in': [LinkType.CREATE.value]}})
            rules.append(UpdateRule(queryb0))

        # Case 3:
        # RETURN(ProcessNode, Data) - Reversed
        if return_reversed:
            queryb0 = QueryBuilder()
            queryb0.append(ProcessNode, tag='predecessor')
            queryb0.append(Data, output_of='predecessor', edge_filters={'type': {'in': [LinkType.RETURN.value]}})
            rules.append(UpdateRule(queryb0))

        # Test was doing the calculation but not checking the results. Will have to think
        # how to do that now. Temporal replacement:
        new_node = Data().store()
        basket0 = get_basket(node_ids=(new_node.id,))

        ruleseq = RuleSequence(rules, max_iterations=np.inf)
        resulting_set = ruleseq.run(basket0.copy())
        expecting_set = resulting_set
        self.assertEqual(expecting_set, resulting_set)

    def test_groups(self):
        """
        Testing whether groups and nodes can be traversed with the Graph explorer:
        """
        total_groups = 10

        # I create a certain number of groups and save them in this list:
        groups = []
        for idx in range(total_groups):
            new_group = Group(label='group-{}'.format(idx))
            new_group.store()
            groups.append(new_group)

        # Same with nodes: Create 1 node less than I have groups, each node will
        # be added to the group with the same index and the group of index-1
        nodes = []
        for idx in range(1, total_groups):
            new_node = Data().store()
            groups[idx].add_nodes(new_node)
            groups[idx - 1].add_nodes(new_node)
            nodes.append(new_node)

        # Creating sets for the test:
        nodes_set = {n.id for n in nodes}
        groups_set = {g.id for g in groups}

        # Now I want rule that gives me all the data starting from the last node,
        # with links, belonging to the same group:
        qb0 = QueryBuilder()
        qb0.append(Data, tag='d')
        #qb0.append(Group, with_node='d', tag='g', filters={'type_string':''} )
        qb0.append(Group, with_node='d', tag='g')
        # The filter here is there for avoiding problems with autogrouping.
        # Depending how the test exactly is run, nodes can be put into autogroups.
        qb0.append(Data, with_group='g')

        initial_node = nodes[-1]
        expecting_set = nodes_set
        basket_inp = get_basket(node_ids=(initial_node.id,))
        tested_rule = UpdateRule(qb0, max_iterations=np.inf)
        basket_out = tested_rule.run(basket_inp.copy())
        resulting_set = basket_out['nodes'].get_keys()

        # checking whether this updateRule above really visits all the nodes I created:
        self.assertEqual(expecting_set, resulting_set)

        # The visits:
        self.assertEqual(tested_rule.get_visits()['nodes'].get_keys(), resulting_set)

        # I can do the same with 2 rules chained into a RuleSequence:
        qb1 = QueryBuilder()
        qb1.append(Node, tag='n')
        qb1.append(Group, with_node='n')
        #        qb1.append(Group, with_node='n', filters={'type_string':''})

        qb2 = QueryBuilder()
        qb2.append(Group, tag='n')
        qb2.append(Node, with_group='n')

        rule1 = UpdateRule(qb1)
        rule2 = UpdateRule(qb2)
        seq = RuleSequence((rule1, rule2), max_iterations=np.inf)
        res = seq.run(basket_inp.copy())
        for should_set, is_set in ((nodes_set.copy(), res['nodes'].get_keys()), (groups_set, res['groups'].get_keys())):
            self.assertEqual(is_set, should_set)

    def test_edges(self):
        """
        Testing whether nodes (and nodes) can be traversed with the Graph explorer,
        with the links being stored
        """

        # I create a certain number of groups and save them in this list:
        # (draw was true but changed it until the function is re-stablished)
        created_dict = create_tree(self.DEPTH, self.NUMBER_OF_CHILDREN, draw=False)
        instances = created_dict['instances']
        adjacency = created_dict['adjacency']

        basket0 = get_basket(node_ids=(created_dict['parent'].id,))

        queryb0 = QueryBuilder().append(Node).append(Node)

        rule = UpdateRule(queryb0, mode=MODES.APPEND, max_iterations=self.DEPTH - 1, track_edges=True)
        res = rule.run(basket0.copy())

        should_set = set()
        for this_depth in range(self.DEPTH):
            for node_id in created_dict['depth_dict'][this_depth]:
                should_set.add(node_id)

        self.assertEqual(res['nodes'].get_keys(), should_set)

        touples_should = set()
        for i, j in zip(*np.where(adjacency)):
            touples_should.add((instances[i], instances[j]))

        touples_are = set()
        for data_touple in res['nodes_nodes'].get_keys():
            touples_are.add((data_touple[0], data_touple[1]))

        self.assertEqual(touples_are, touples_should)

        rule = UpdateRule(queryb0, mode=MODES.REPLACE, max_iterations=self.DEPTH - 1, track_edges=True)
        res = rule.run(basket0.copy())

        # Since I apply the replace rule, the last set of links should appear:
        instances = created_dict['instances']
        adjacency = created_dict['adjacency']

        touples_should = set()
        for idx1, pk1 in enumerate(instances):
            for idx2, pk2 in enumerate(instances):
                are_adjacent = (adjacency[idx1, idx2] == 1)
                depth1_ok = pk1 in created_dict['depth_dict'][self.DEPTH - 2]
                depth2_ok = pk2 in created_dict['depth_dict'][self.DEPTH - 1]
                if are_adjacent and depth1_ok and depth2_ok:
                    touples_should.add((pk1, pk2))

        #[
        #    touples_should.add((pk1, pk2))
        #    for idx1, pk1 in enumerate(instances)
        #    for idx2, pk2 in enumerate(instances)
        #    if adjacency[idx1, idx2] and pk1 in created_dict['depth_dict'][self.DEPTH - 2] and
        #    pk2 in created_dict['depth_dict'][self.DEPTH - 1]
        #]

        touples_are = set()
        for data_touple in res['nodes_nodes'].get_keys():
            touples_are.add((data_touple[0], data_touple[1]))

        self.assertEqual(touples_are, touples_should)
