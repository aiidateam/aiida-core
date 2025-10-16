###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""AGE tests"""

import numpy as np
import pytest

from aiida import orm
from aiida.common.links import LinkType
from aiida.tools.graph.age_entities import AiidaEntitySet, Basket, DirectedEdgeSet, GroupNodeEdge
from aiida.tools.graph.age_rules import ReplaceRule, RuleSaveWalkers, RuleSequence, RuleSetWalkers, UpdateRule


def create_tree(max_depth=3, branching=3, starting_cls=orm.Data):
    """Auxiliary function to create a tree with a given depth and a given branching."""
    if starting_cls not in (orm.Data, orm.CalculationNode):
        raise TypeError('The starting_cls has to be either Data or CalculationNode')

    parent = starting_cls().store()
    depth_dict = {}  # saves the descendants, by depth (depth is the key).
    depth_dict[0] = set([parent.pk])

    number_of_nodes = sum(branching**d for d in range(max_depth))
    adjacency = np.zeros((number_of_nodes, number_of_nodes), dtype=int)
    all_instances = np.zeros(number_of_nodes, dtype=int)
    all_instances[0] = parent.pk  # saves all the instances EVER created

    # The previous_class is needed to be able to alternate between Data and CalculationNodes
    # The previous_nodes list stores all the instances created in the previous iteration
    # The previous_indxs list stores where the ids of previous_ins are stored in all_instances
    previous_class = starting_cls
    previous_nodes = [parent]
    previous_indxs = [0]

    counter = 1
    for depth in range(1, max_depth):
        depth_dict[depth] = set()

        current_indxs = []
        current_nodes = []
        current_class = orm.Data if previous_class is orm.CalculationNode else orm.CalculationNode
        current_links = LinkType.CREATE if current_class is orm.Data else LinkType.INPUT_CALC

        # For each previous node, link the requested number of branches
        for previous_node, previous_indx in zip(previous_nodes, previous_indxs):
            for label_id in range(branching):
                new_node = current_class()
                new_node.base.links.add_incoming(previous_node, link_type=current_links, link_label=f'link{label_id}')
                new_node.store()

                current_nodes.append(new_node)
                all_instances[counter] = new_node.pk
                adjacency[previous_indx, counter] = 1
                current_indxs.append(counter)
                depth_dict[depth].add(new_node.pk)

                counter += 1

        previous_nodes = current_nodes
        previous_indxs = current_indxs
        previous_class = current_class

    result = {
        'parent': parent,
        'depth_dict': depth_dict,
        'instances': all_instances,
        'adjacency': adjacency,
    }
    return result


class TestAiidaGraphExplorer:
    """Tests for the AGE"""

    @staticmethod
    def _create_basic_graph():
        """Creates a basic graph which has one parent workflow (work_2) that calls
        a child workflow (work_1) which calls a calculation function (calc_0).
        There is one input (data_i) and one output (data_o). It has at least one
        link of each class:

        * CALL_WORK from work_2 to work_1.
        * CALL_CALC from work_1 to calc_0.
        * INPUT_CALC from data_i to calc_0 and CREATE from calc_0 to data_o.
        * INPUT_WORK from data_i to work_1 and RETURN from work_1 to data_o.
        * INPUT_WORK from data_i to work_2 and RETURN from work_2 to data_o.

        This graph looks like this::

                     input_work      +--------+       return
               +-------------------> | work_2 | --------------------+
               |                     +--------+                     |
               |                         |                          |
               |                         | call_work                |
               |                         |                          |
               |                         v                          |
               |       input_work    +--------+      return         |
               |  +----------------> | work_1 | -----------------+  |
               |  |                  +--------+                  |  |
               |  |                      |                       |  |
               |  |                      | call_calc             |  |
               |  |                      |                       |  |
               |  |                      v                       v  v
            +--------+  input_calc   +--------+    create     +--------+
            | data_i | ------------> | calc_0 | ------------> | data_o |
            +--------+               +--------+               +--------+
        """
        data_i = orm.Data().store()

        work_2 = orm.WorkflowNode()
        work_2.base.links.add_incoming(data_i, link_type=LinkType.INPUT_WORK, link_label='inpwork2')
        work_2.store()

        work_1 = orm.WorkflowNode()
        work_1.base.links.add_incoming(data_i, link_type=LinkType.INPUT_WORK, link_label='inpwork1')
        work_1.base.links.add_incoming(work_2, link_type=LinkType.CALL_WORK, link_label='callwork')
        work_1.store()

        calc_0 = orm.CalculationNode()
        calc_0.base.links.add_incoming(data_i, link_type=LinkType.INPUT_CALC, link_label='inpcalc0')
        calc_0.base.links.add_incoming(work_1, link_type=LinkType.CALL_CALC, link_label='callcalc')
        calc_0.store()

        data_o = orm.Data()
        data_o.base.links.add_incoming(calc_0, link_type=LinkType.CREATE, link_label='create0')
        data_o.store()
        data_o.base.links.add_incoming(work_2, link_type=LinkType.RETURN, link_label='return2')
        data_o.base.links.add_incoming(work_1, link_type=LinkType.RETURN, link_label='return1')

        output_dict = {
            'data_i': data_i,
            'data_o': data_o,
            'calc_0': calc_0,
            'work_1': work_1,
            'work_2': work_2,
        }
        return output_dict

    def test_basic_graph(self):
        """Testing basic operations for the explorer:
        - Selection of ascendants.
        - Selection of descendants.
        - Ascendants and descendants through specific links.
        - Ascendants and descendants of specific type.
        """
        nodes = self._create_basic_graph()
        basket_w1 = Basket(nodes=[nodes['work_1'].pk])
        basket_w2 = Basket(nodes=[nodes['work_2'].pk])

        # Find all the descendants of work_1
        queryb = orm.QueryBuilder()
        queryb.append(orm.Node, tag='nodes_in_set')
        queryb.append(orm.Node, with_incoming='nodes_in_set')
        uprule = UpdateRule(queryb, max_iterations=10)

        obtained = uprule.run(basket_w1.copy())['nodes'].keyset
        expected = set((nodes['work_1'].pk, nodes['calc_0'].pk, nodes['data_o'].pk))
        assert obtained == expected

        # Find all the descendants of work_1 through call_calc (calc_0)
        edge_cacalc = {'type': {'in': [LinkType.CALL_CALC.value]}}
        queryb = orm.QueryBuilder()
        queryb.append(orm.Node, tag='nodes_in_set')
        queryb.append(orm.Node, with_incoming='nodes_in_set', edge_filters=edge_cacalc)
        uprule = UpdateRule(queryb, max_iterations=10)

        obtained = uprule.run(basket_w1.copy())['nodes'].keyset
        expected = set((nodes['work_1'].pk, nodes['calc_0'].pk))
        assert obtained == expected

        # Find all the descendants of work_1 that are data nodes (data_o)
        queryb = orm.QueryBuilder()
        queryb.append(orm.Node, tag='nodes_in_set')
        queryb.append(orm.Data, with_incoming='nodes_in_set')
        uprule = UpdateRule(queryb, max_iterations=10)

        obtained = uprule.run(basket_w1.copy())['nodes'].keyset
        expected = set((nodes['work_1'].pk, nodes['data_o'].pk))
        assert obtained == expected

        # Find all the ascendants of work_1
        queryb = orm.QueryBuilder()
        queryb.append(orm.Node, tag='nodes_in_set')
        queryb.append(orm.Node, with_outgoing='nodes_in_set')
        uprule = UpdateRule(queryb, max_iterations=10)

        obtained = uprule.run(basket_w1.copy())['nodes'].keyset
        expected = set((nodes['work_1'].pk, nodes['work_2'].pk, nodes['data_i'].pk))
        assert obtained == expected

        # Find all the ascendants of work_1 through input_work (data_i)
        edge_inpwork = {'type': {'in': [LinkType.INPUT_WORK.value]}}
        queryb = orm.QueryBuilder()
        queryb.append(orm.Node, tag='nodes_in_set')
        queryb.append(orm.Node, with_outgoing='nodes_in_set', edge_filters=edge_inpwork)
        uprule = UpdateRule(queryb, max_iterations=10)

        obtained = uprule.run(basket_w1.copy())['nodes'].keyset
        expected = set((nodes['work_1'].pk, nodes['data_i'].pk))
        assert obtained == expected

        # Find all the ascendants of work_1 that are workflow nodes (work_2)
        queryb = orm.QueryBuilder()
        queryb.append(orm.Node, tag='nodes_in_set')
        queryb.append(orm.ProcessNode, with_outgoing='nodes_in_set')
        uprule = UpdateRule(queryb, max_iterations=10)

        obtained = uprule.run(basket_w1.copy())['nodes'].keyset
        expected = set((nodes['work_1'].pk, nodes['work_2'].pk))
        assert obtained == expected

        # Only get the descendants that are direct (1st level) (work_1, data_o)
        queryb = orm.QueryBuilder()
        queryb.append(orm.Node, tag='nodes_in_set')
        queryb.append(orm.Node, with_incoming='nodes_in_set')
        rerule = ReplaceRule(queryb, max_iterations=1)

        obtained = rerule.run(basket_w2.copy())['nodes'].keyset
        expected = set((nodes['work_1'].pk, nodes['data_o'].pk))
        assert obtained == expected

        # Only get the descendants of the descendants (2nd level) (calc_0, data_o)
        queryb = orm.QueryBuilder()
        queryb.append(orm.Node, tag='nodes_in_set')
        queryb.append(orm.Node, with_incoming='nodes_in_set')
        rerule = ReplaceRule(queryb, max_iterations=2)

        obtained = rerule.run(basket_w2.copy())['nodes'].keyset
        expected = set((nodes['calc_0'].pk, nodes['data_o'].pk))
        assert obtained == expected

    def test_cycle(self):
        """Testing the case of a cycle (workflow node with a data node that is
        both an input and an output):
        - Update rules with no max iterations should not get stuck.
        - Replace rules should return alternating results.
        """
        data_node = orm.Data().store()
        work_node = orm.WorkflowNode()
        work_node.base.links.add_incoming(data_node, link_type=LinkType.INPUT_WORK, link_label='input_link')
        work_node.store()
        data_node.base.links.add_incoming(work_node, link_type=LinkType.RETURN, link_label='return_link')

        basket = Basket(nodes=[data_node.pk])
        queryb = orm.QueryBuilder()
        queryb.append(orm.Node).append(orm.Node)

        uprule = UpdateRule(queryb, max_iterations=np.inf)
        obtained = uprule.run(basket.copy())['nodes'].keyset
        expected = set([data_node.pk, work_node.pk])
        assert obtained == expected

        rerule1 = ReplaceRule(queryb, max_iterations=1)
        result1 = rerule1.run(basket.copy())['nodes'].keyset
        assert result1 == set([work_node.pk])

        rerule2 = ReplaceRule(queryb, max_iterations=2)
        result2 = rerule2.run(basket.copy())['nodes'].keyset
        assert result2 == set([data_node.pk])

        rerule3 = ReplaceRule(queryb, max_iterations=3)
        result3 = rerule3.run(basket.copy())['nodes'].keyset
        assert result3 == set([work_node.pk])

        rerule4 = ReplaceRule(queryb, max_iterations=4)
        result4 = rerule4.run(basket.copy())['nodes'].keyset
        assert result4 == set([data_node.pk])

    @staticmethod
    def _create_branchy_graph():
        """Creates a basic branchy graph which has two concatenated calculations:

        * calc_1 takes data_0 as an input and returns data_1 and data_o.
        * calc_2 takes data_1 and data_i as inputs and returns data_2.

        This graph looks like this::

                           +--------+                    +--------+
                           | data_o |                    | data_i |
                           +--------+                    +--------+
                               ^                             |
                               |                             v
            +--------+     +--------+     +--------+     +--------+     +--------+
            | data_0 | --> | calc_1 | --> | data_1 | --> | calc_2 | --> | data_2 |
            +--------+     +--------+     +--------+     +--------+     +--------+
        """
        data_0 = orm.Data().store()
        calc_1 = orm.CalculationNode()
        calc_1.base.links.add_incoming(data_0, link_type=LinkType.INPUT_CALC, link_label='inpcalc_data_0')
        calc_1.store()

        data_1 = orm.Data()
        data_o = orm.Data()
        data_1.base.links.add_incoming(calc_1, link_type=LinkType.CREATE, link_label='create_data_1')
        data_o.base.links.add_incoming(calc_1, link_type=LinkType.CREATE, link_label='create_data_o')
        data_1.store()
        data_o.store()

        data_i = orm.Data().store()
        calc_2 = orm.CalculationNode()
        calc_2.base.links.add_incoming(data_1, link_type=LinkType.INPUT_CALC, link_label='inpcalc_data_1')
        calc_2.base.links.add_incoming(data_i, link_type=LinkType.INPUT_CALC, link_label='inpcalc_data_i')
        calc_2.store()

        data_2 = orm.Data()
        data_2.base.links.add_incoming(calc_2, link_type=LinkType.CREATE, link_label='create_data_2')
        data_2.store()

        output_dict = {
            'data_i': data_i,
            'data_0': data_0,
            'data_1': data_1,
            'data_2': data_2,
            'data_o': data_o,
            'calc_1': calc_1,
            'calc_2': calc_2,
        }
        return output_dict

    def test_stash(self):
        """Testing sequencies and 'stashing'

        Testing the dependency on the order of the operations in RuleSequence and the
        'stash' functionality. This will be performed in a graph that has a calculation
        (calc_ca) with two input data nodes (data_i1 and data_i2) and two output data
        nodes (data_o1 and data_o2), and another calculation (calc_cb) which takes both
        one of the inputs and one of the outputs of the first one (data_i2 and data_o2)
        as inputs to produce a final output (data_o3).
        """
        nodes = self._create_branchy_graph()
        basket = Basket(nodes=[nodes['data_1'].pk])

        queryb_inp = orm.QueryBuilder()
        queryb_inp.append(orm.Node, tag='nodes_in_set')
        queryb_inp.append(orm.Node, with_outgoing='nodes_in_set')
        uprule_inp = UpdateRule(queryb_inp)
        queryb_out = orm.QueryBuilder()
        queryb_out.append(orm.Node, tag='nodes_in_set')
        queryb_out.append(orm.Node, with_incoming='nodes_in_set')
        uprule_out = UpdateRule(queryb_out)

        expect_base = set([nodes['calc_1'].pk, nodes['data_1'].pk, nodes['calc_2'].pk])

        # First get outputs, then inputs.
        rule_seq = RuleSequence((uprule_out, uprule_inp))
        obtained = rule_seq.run(basket.copy())['nodes'].keyset
        expected = expect_base.union(set([nodes['data_i'].pk]))
        assert obtained == expected

        # First get inputs, then outputs.
        rule_seq = RuleSequence((uprule_inp, uprule_out))
        obtained = rule_seq.run(basket.copy())['nodes'].keyset
        expected = expect_base.union(set([nodes['data_o'].pk]))
        assert obtained == expected

        # Now using the stash option in either order.
        stash = basket.get_template()
        rule_save = RuleSaveWalkers(stash)
        rule_load = RuleSetWalkers(stash)

        # Checking whether Rule does the right thing
        # (i.e. If I stash the result, the operational sets should be the original,
        # set, whereas the stash contains the same data as the starting point)
        obtained = rule_save.run(basket.copy())
        expected = basket.copy()
        assert obtained == expected
        assert stash == basket

        stash = basket.get_template()
        rule_save = RuleSaveWalkers(stash)
        rule_load = RuleSetWalkers(stash)
        serule_io = RuleSequence((rule_save, uprule_inp, rule_load, uprule_out))
        result_io = serule_io.run(basket.copy())['nodes'].keyset
        assert result_io == expect_base

        stash = basket.get_template()
        rule_save = RuleSaveWalkers(stash)
        rule_load = RuleSetWalkers(stash)
        serule_oi = RuleSequence((rule_save, uprule_out, rule_load, uprule_inp))
        result_oi = serule_oi.run(basket.copy())['nodes'].keyset
        assert result_oi == expect_base

    def test_returns_calls(self):
        """Tests return calls (?)"""
        create_reversed = False
        return_reversed = False

        rules = []
        # linking all processes to input data:
        queryb = orm.QueryBuilder()
        queryb.append(orm.Data, tag='predecessor')
        queryb.append(
            orm.ProcessNode,
            with_incoming='predecessor',
            edge_filters={'type': {'in': [LinkType.INPUT_CALC.value, LinkType.INPUT_WORK.value]}},
        )
        rules.append(UpdateRule(queryb))

        # CREATE/RETURN(ProcessNode, Data) - Forward
        queryb = orm.QueryBuilder()
        queryb.append(orm.ProcessNode, tag='predecessor')
        queryb.append(
            orm.Data,
            with_incoming='predecessor',
            edge_filters={'type': {'in': [LinkType.CREATE.value, LinkType.RETURN.value]}},
        )
        rules.append(UpdateRule(queryb))

        # CALL(ProcessNode, ProcessNode) - Forward
        queryb = orm.QueryBuilder()
        queryb.append(orm.ProcessNode, tag='predecessor')
        queryb.append(
            orm.ProcessNode,
            with_incoming='predecessor',
            edge_filters={'type': {'in': [LinkType.CALL_CALC.value, LinkType.CALL_WORK.value]}},
        )
        rules.append(UpdateRule(queryb))

        # CREATE(ProcessNode, Data) - Reversed
        if create_reversed:
            queryb = orm.QueryBuilder()
            queryb.append(orm.ProcessNode, tag='predecessor', project=['id'])
            queryb.append(orm.Data, with_incoming='predecessor', edge_filters={'type': {'in': [LinkType.CREATE.value]}})
            rules.append(UpdateRule(queryb))

        # Case 3:
        # RETURN(ProcessNode, Data) - Reversed
        if return_reversed:
            queryb = orm.QueryBuilder()
            queryb.append(orm.ProcessNode, tag='predecessor')
            queryb.append(orm.Data, output_of='predecessor', edge_filters={'type': {'in': [LinkType.RETURN.value]}})
            rules.append(UpdateRule(queryb))

        # Test was doing the calculation but not checking the results. Will have to think
        # how to do that now. Temporal replacement:
        new_node = orm.Data().store()
        basket = Basket(nodes=(new_node.pk,))

        ruleseq = RuleSequence(rules, max_iterations=np.inf)
        resulting_set = ruleseq.run(basket.copy())
        expecting_set = resulting_set
        assert expecting_set == resulting_set

    def test_groups(self):
        """Testing connection between (aiida-)groups and (aiida-)nodes, which are treated
        as if they both were (graph-)nodes.
        """
        node1 = orm.Data().store()
        node2 = orm.Data().store()
        node3 = orm.Data().store()
        node4 = orm.Data().store()

        group1 = orm.Group(label='group-01').store()
        group1.add_nodes(node1)

        group2 = orm.Group(label='group-02').store()
        group2.add_nodes(node2)
        group2.add_nodes(node3)

        group3 = orm.Group(label='group-03').store()
        group3.add_nodes(node4)
        group4 = orm.Group(label='group-04').store()
        group4.add_nodes(node4)

        # Rule that only gets nodes connected by the same group
        queryb = orm.QueryBuilder()
        queryb.append(orm.Node, tag='nodes_in_set')
        queryb.append(orm.Group, with_node='nodes_in_set', tag='groups_considered')
        queryb.append(orm.Data, with_group='groups_considered')

        initial_node = [node2.pk]
        basket_inp = Basket(nodes=initial_node)
        tested_rule = UpdateRule(queryb, max_iterations=np.inf)
        basket_out = tested_rule.run(basket_inp.copy())

        obtained = basket_out['nodes'].keyset
        expected = set([node2.pk, node3.pk])
        assert obtained == expected

        obtained = basket_out['groups'].keyset
        expected = set()
        assert obtained == expected

        # But two rules chained should get both nodes and groups...
        queryb = orm.QueryBuilder()
        queryb.append(orm.Node, tag='nodes_in_set')
        queryb.append(orm.Group, with_node='nodes_in_set')
        rule1 = UpdateRule(queryb)

        queryb = orm.QueryBuilder()
        queryb.append(orm.Group, tag='groups_in_set')
        queryb.append(orm.Node, with_group='groups_in_set')
        rule2 = UpdateRule(queryb)

        ruleseq = RuleSequence((rule1, rule2), max_iterations=np.inf)

        # ...both starting with a node
        initial_node = [node2.pk]
        basket_inp = Basket(nodes=initial_node)
        basket_out = ruleseq.run(basket_inp.copy())

        obtained = basket_out['nodes'].keyset
        expected = set([node2.pk, node3.pk])
        assert obtained == expected

        obtained = basket_out['groups'].keyset
        expected = set([group2.pk])
        assert obtained == expected

        # ...and starting with a group
        initial_group = [group3.pk]
        basket_inp = Basket(groups=initial_group)
        basket_out = ruleseq.run(basket_inp.copy())

        obtained = basket_out['nodes'].keyset
        expected = set([node4.pk])
        assert obtained == expected

        obtained = basket_out['groups'].keyset
        expected = set([group3.pk, group4.pk])
        assert obtained == expected

        # Testing a "group chain"
        total_groups = 10

        groups = []
        for idx in range(total_groups):
            new_group = orm.Group(label=f'group-{idx}').store()
            groups.append(new_group)

        nodes = []
        edges = set()
        for idx in range(1, total_groups):
            new_node = orm.Data().store()
            groups[idx].add_nodes(new_node)
            groups[idx - 1].add_nodes(new_node)
            nodes.append(new_node)
            edges.add(GroupNodeEdge(node_id=new_node.pk, group_id=groups[idx].pk))
            edges.add(GroupNodeEdge(node_id=new_node.pk, group_id=groups[idx - 1].pk))

        qb1 = orm.QueryBuilder()
        qb1.append(orm.Node, tag='nodes_in_set')
        qb1.append(orm.Group, with_node='nodes_in_set')
        rule1 = UpdateRule(qb1, track_edges=True)

        qb2 = orm.QueryBuilder()
        qb2.append(orm.Group, tag='groups_in_set')
        qb2.append(orm.Node, with_group='groups_in_set')
        rule2 = UpdateRule(qb2, track_edges=True)

        ruleseq = RuleSequence((rule1, rule2), max_iterations=np.inf)

        initial_node = [nodes[-1].pk]
        basket_inp = Basket(nodes=initial_node)
        basket_out = ruleseq.run(basket_inp.copy())

        obtained = basket_out['nodes'].keyset
        expected = set(n.pk for n in nodes)
        assert obtained == expected

        obtained = basket_out['groups'].keyset
        expected = set(g.pk for g in groups)
        assert obtained == expected

        # testing the edges between groups and nodes:
        result = basket_out['groups_nodes'].keyset
        assert result == edges

    def test_edges(self):
        """Testing how the links are stored during traversal of the graph."""
        nodes = self._create_basic_graph()

        # Forward traversal (check all nodes and all links)
        basket = Basket(nodes=[nodes['data_i'].pk])
        queryb = orm.QueryBuilder()
        queryb.append(orm.Node, tag='nodes_in_set')
        queryb.append(orm.Node, with_incoming='nodes_in_set')
        uprule = UpdateRule(queryb, max_iterations=2, track_edges=True)
        uprule_result = uprule.run(basket.copy())

        obtained = uprule_result['nodes'].keyset
        expected = set(anode.pk for _, anode in nodes.items())
        assert obtained == expected

        obtained = set()
        for data in uprule_result['nodes_nodes'].keyset:
            obtained.add((data[0], data[1]))

        expected = {
            (nodes['data_i'].pk, nodes['calc_0'].pk),
            (nodes['data_i'].pk, nodes['work_1'].pk),
            (nodes['data_i'].pk, nodes['work_2'].pk),
            (nodes['calc_0'].pk, nodes['data_o'].pk),
            (nodes['work_1'].pk, nodes['data_o'].pk),
            (nodes['work_2'].pk, nodes['data_o'].pk),
            (nodes['work_2'].pk, nodes['work_1'].pk),
            (nodes['work_1'].pk, nodes['calc_0'].pk),
        }
        assert obtained == expected

        # Backwards traversal (check partial traversal and link direction)
        basket = Basket(nodes=[nodes['data_o'].pk])
        queryb = orm.QueryBuilder()
        queryb.append(orm.Node, tag='nodes_in_set')
        queryb.append(orm.Node, with_outgoing='nodes_in_set')
        uprule = UpdateRule(queryb, max_iterations=1, track_edges=True)
        uprule_result = uprule.run(basket.copy())

        obtained = uprule_result['nodes'].keyset
        expected = set(anode.pk for _, anode in nodes.items())
        expected = expected.difference(set([nodes['data_i'].pk]))
        assert obtained == expected

        obtained = set()
        for data in uprule_result['nodes_nodes'].keyset:
            obtained.add((data[0], data[1]))

        expected = {
            (nodes['calc_0'].pk, nodes['data_o'].pk),
            (nodes['work_1'].pk, nodes['data_o'].pk),
            (nodes['work_2'].pk, nodes['data_o'].pk),
        }
        assert obtained == expected

    def test_empty_input(self):
        """Testing empty input."""
        basket = Basket(nodes=[])
        queryb = orm.QueryBuilder()
        queryb.append(orm.Node).append(orm.Node)
        uprule = UpdateRule(queryb, max_iterations=np.inf)
        result = uprule.run(basket.copy())['nodes'].keyset
        assert result == set()


class TestAiidaEntitySet:
    """Tests for AiidaEntitySets"""

    def test_class_mismatch(self):
        """Test the case where an AiidaEntitySet is trying to be used in an operation
        with another AiidaEntitySet and they contain mismatched aiida entities, or
        in an operation with a data type other than AiidaEntitySet.
        """
        aes_node = AiidaEntitySet(orm.Node)
        aes_group = AiidaEntitySet(orm.Group)
        des_node_node = DirectedEdgeSet(orm.Node, orm.Node)
        python_set = {1, 2, 3, 4}

        with pytest.raises(TypeError):
            _ = aes_node + aes_group

        with pytest.raises(TypeError):
            _ = aes_node + des_node_node

        with pytest.raises(TypeError):
            _ = aes_group + des_node_node

        with pytest.raises(TypeError):
            _ = aes_node + python_set

    def test_algebra(self):
        """Test simple addition, in-place addition, simple subtraction, in-place subtraction"""
        depth0 = 4
        branching0 = 2
        tree0 = create_tree(max_depth=depth0, branching=branching0)
        basket0 = Basket(nodes=(tree0['parent'].pk,))
        queryb0 = orm.QueryBuilder()
        queryb0.append(orm.Node).append(orm.Node)
        rule0 = UpdateRule(queryb0, max_iterations=depth0)
        res0 = rule0.run(basket0.copy())
        aes0 = res0.nodes

        depth1 = 3
        branching1 = 6
        tree1 = create_tree(max_depth=depth1, branching=branching1)
        basket1 = Basket(nodes=(tree1['parent'].pk,))
        queryb1 = orm.QueryBuilder()
        queryb1.append(orm.Node).append(orm.Node)
        rule1 = UpdateRule(queryb1, max_iterations=depth1)
        res1 = rule1.run(basket1.copy())
        aes1 = res1.nodes

        aes2 = aes0 + aes1
        union01 = aes0.keyset | aes1.keyset
        assert aes2.keyset == union01

        aes0_copy = aes0.copy()
        aes0_copy += aes1
        assert aes0_copy.keyset == union01

        aes3 = aes0_copy - aes1
        assert aes0.keyset == aes3.keyset
        assert aes0 == aes3

        aes0_copy -= aes1
        assert aes0.keyset == aes3.keyset, aes0_copy.keyset
        assert aes0 == aes3, aes0_copy

        aes4 = aes0 - aes0
        assert aes4.keyset == set()

        aes0_copy -= aes0
        assert aes0_copy.keyset == set()
