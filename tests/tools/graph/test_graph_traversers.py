###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for aiida.tools.graph.graph_traversers"""

import pytest

from aiida.common.links import LinkType
from aiida.tools.graph.graph_traversers import get_nodes_delete, traverse_graph


def create_minimal_graph():
    """Creates a minimal graph which has one parent workflow (W2) that calls
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
    from aiida import orm

    data_i = orm.Data().store()
    data_o = orm.Data().store()

    calc_0 = orm.CalculationNode()
    work_1 = orm.WorkflowNode()
    work_2 = orm.WorkflowNode()

    calc_0.base.links.add_incoming(data_i, link_type=LinkType.INPUT_CALC, link_label='inpcalc')
    work_1.base.links.add_incoming(data_i, link_type=LinkType.INPUT_WORK, link_label='inpwork')
    work_2.base.links.add_incoming(data_i, link_type=LinkType.INPUT_WORK, link_label='inpwork')

    calc_0.base.links.add_incoming(work_1, link_type=LinkType.CALL_CALC, link_label='callcalc')
    work_1.base.links.add_incoming(work_2, link_type=LinkType.CALL_WORK, link_label='callwork')

    work_2.store()
    work_1.store()
    calc_0.store()

    data_o.base.links.add_incoming(calc_0, link_type=LinkType.CREATE, link_label='create0')
    data_o.base.links.add_incoming(work_1, link_type=LinkType.RETURN, link_label='return1')
    data_o.base.links.add_incoming(work_2, link_type=LinkType.RETURN, link_label='return2')

    output_dict = {
        'data_i': data_i,
        'data_o': data_o,
        'calc_0': calc_0,
        'work_1': work_1,
        'work_2': work_2,
    }

    return output_dict


class TestTraverseGraph:
    """Test class for traverse_graph"""

    def _single_test(self, starting_nodes=(), expanded_nodes=(), links_forward=(), links_backward=()):
        """Auxiliary method to perform a single test run and assertion"""
        obtained_nodes = traverse_graph(
            starting_nodes,
            links_forward=links_forward,
            links_backward=links_backward,
        )['nodes']
        expected_nodes = set(starting_nodes + expanded_nodes)
        assert obtained_nodes == expected_nodes

    def test_traversal_individually(self):
        """This will go through all the rules and check one case in the graph
        where it can be applied.
        """
        nodes_dict = create_minimal_graph()

        self._single_test(
            starting_nodes=[nodes_dict['data_i'].pk],
            expanded_nodes=[nodes_dict['calc_0'].pk],
            links_forward=[LinkType.INPUT_CALC],
        )

        self._single_test(
            starting_nodes=[nodes_dict['calc_0'].pk],
            expanded_nodes=[nodes_dict['data_i'].pk],
            links_backward=[LinkType.INPUT_CALC],
        )

        self._single_test(
            starting_nodes=[nodes_dict['calc_0'].pk],
            expanded_nodes=[nodes_dict['data_o'].pk],
            links_forward=[LinkType.CREATE],
        )

        self._single_test(
            starting_nodes=[nodes_dict['data_o'].pk],
            expanded_nodes=[nodes_dict['calc_0'].pk],
            links_backward=[LinkType.CREATE],
        )

        self._single_test(
            starting_nodes=[nodes_dict['work_1'].pk],
            expanded_nodes=[nodes_dict['data_o'].pk],
            links_forward=[LinkType.RETURN],
        )

        self._single_test(
            starting_nodes=[nodes_dict['data_o'].pk],
            expanded_nodes=[nodes_dict['work_1'].pk, nodes_dict['work_2'].pk],
            links_backward=[LinkType.RETURN],
        )

        self._single_test(
            starting_nodes=[nodes_dict['data_i'].pk],
            expanded_nodes=[nodes_dict['work_1'].pk, nodes_dict['work_2'].pk],
            links_forward=[LinkType.INPUT_WORK],
        )

        self._single_test(
            starting_nodes=[nodes_dict['work_1'].pk],
            expanded_nodes=[nodes_dict['data_i'].pk],
            links_backward=[LinkType.INPUT_WORK],
        )

        self._single_test(
            starting_nodes=[nodes_dict['work_1'].pk],
            expanded_nodes=[nodes_dict['calc_0'].pk],
            links_forward=[LinkType.CALL_CALC],
        )

        self._single_test(
            starting_nodes=[nodes_dict['calc_0'].pk],
            expanded_nodes=[nodes_dict['work_1'].pk],
            links_backward=[LinkType.CALL_CALC],
        )

        self._single_test(
            starting_nodes=[nodes_dict['work_2'].pk],
            expanded_nodes=[nodes_dict['work_1'].pk],
            links_forward=[LinkType.CALL_WORK],
        )

        self._single_test(
            starting_nodes=[nodes_dict['work_1'].pk],
            expanded_nodes=[nodes_dict['work_2'].pk],
            links_backward=[LinkType.CALL_WORK],
        )

    def test_traversal_full_graph(self):
        """This will test that the traverser can get the full graph with the minimal traverse
        required keywords.
        """
        nodes_dict = create_minimal_graph()

        expected_nodes = [value.pk for value in nodes_dict.values()]

        self._single_test(
            starting_nodes=[nodes_dict['data_i'].pk],
            expanded_nodes=expected_nodes,
            links_backward=[LinkType.CALL_CALC, LinkType.CALL_WORK],
            links_forward=[LinkType.INPUT_CALC, LinkType.RETURN],
        )

        self._single_test(
            starting_nodes=[nodes_dict['data_i'].pk],
            expanded_nodes=expected_nodes,
            links_backward=[LinkType.RETURN],
            links_forward=[LinkType.INPUT_CALC, LinkType.CREATE],
        )

        self._single_test(
            starting_nodes=[nodes_dict['data_i'].pk],
            expanded_nodes=expected_nodes,
            links_backward=[],
            links_forward=[LinkType.INPUT_WORK, LinkType.CALL_CALC, LinkType.CREATE],
        )

        self._single_test(
            starting_nodes=[nodes_dict['data_o'].pk],
            expanded_nodes=expected_nodes,
            links_backward=[LinkType.CREATE, LinkType.CALL_CALC, LinkType.INPUT_WORK, LinkType.CALL_WORK],
            links_forward=[],
        )

        self._single_test(
            starting_nodes=[nodes_dict['data_o'].pk],
            expanded_nodes=expected_nodes,
            links_backward=[LinkType.CREATE, LinkType.INPUT_CALC],
            links_forward=[LinkType.INPUT_WORK],
        )

        self._single_test(
            starting_nodes=[nodes_dict['data_o'].pk],
            expanded_nodes=expected_nodes,
            links_backward=[LinkType.RETURN, LinkType.INPUT_CALC],
            links_forward=[LinkType.CALL_CALC],
        )

        self._single_test(
            starting_nodes=[nodes_dict['calc_0'].pk],
            expanded_nodes=expected_nodes,
            links_backward=[LinkType.INPUT_CALC, LinkType.CALL_CALC, LinkType.CALL_WORK],
            links_forward=[LinkType.CREATE],
        )

        self._single_test(
            starting_nodes=[nodes_dict['calc_0'].pk],
            expanded_nodes=expected_nodes,
            links_backward=[LinkType.RETURN, LinkType.INPUT_WORK],
            links_forward=[LinkType.CREATE],
        )

        self._single_test(
            starting_nodes=[nodes_dict['calc_0'].pk],
            expanded_nodes=expected_nodes,
            links_backward=[LinkType.INPUT_CALC],
            links_forward=[LinkType.RETURN, LinkType.INPUT_WORK],
        )

        self._single_test(
            starting_nodes=[nodes_dict['work_1'].pk],
            expanded_nodes=expected_nodes,
            links_backward=[LinkType.INPUT_WORK, LinkType.CALL_WORK],
            links_forward=[LinkType.RETURN, LinkType.CALL_CALC],
        )

        self._single_test(
            starting_nodes=[nodes_dict['work_2'].pk],
            expanded_nodes=expected_nodes,
            links_backward=[LinkType.INPUT_CALC],
            links_forward=[LinkType.CREATE, LinkType.CALL_CALC, LinkType.CALL_WORK],
        )

        self._single_test(
            starting_nodes=[nodes_dict['work_1'].pk],
            expanded_nodes=expected_nodes,
            links_backward=[LinkType.CREATE, LinkType.INPUT_CALC],
            links_forward=[LinkType.RETURN, LinkType.INPUT_WORK],
        )

        self._single_test(
            starting_nodes=[nodes_dict['work_1'].pk],
            expanded_nodes=expected_nodes,
            links_backward=[LinkType.INPUT_CALC, LinkType.RETURN],
            links_forward=[LinkType.CREATE, LinkType.CALL_CALC],
        )

    def test_traversal_cycle(self):
        """This will test that cycles don't go into infinite loops by testing a
        graph with two data nodes data_take and data_drop and a work_select
        that takes both as input but returns only data_take
        """
        from aiida import orm

        data_take = orm.Data().store()
        data_drop = orm.Data().store()
        work_select = orm.WorkflowNode()

        work_select.base.links.add_incoming(data_take, link_type=LinkType.INPUT_WORK, link_label='input_take')
        work_select.base.links.add_incoming(data_drop, link_type=LinkType.INPUT_WORK, link_label='input_drop')
        work_select.store()

        data_take.base.links.add_incoming(work_select, link_type=LinkType.RETURN, link_label='return_link')

        data_take = data_take.pk
        data_drop = data_drop.pk
        work_select = work_select.pk

        every_node = [data_take, data_drop, work_select]

        for single_node in every_node:
            expected_nodes = set([single_node])
            obtained_nodes = traverse_graph([single_node])['nodes']
            assert obtained_nodes == expected_nodes

        links_forward = [LinkType.INPUT_WORK, LinkType.RETURN]
        links_backward = []

        # Forward: data_drop to (input) work_select to (return) data_take
        obtained_nodes = traverse_graph([data_drop], links_forward=links_forward, links_backward=links_backward)[
            'nodes'
        ]
        expected_nodes = set(every_node)
        assert obtained_nodes == expected_nodes

        # Forward: data_take to (input) work_select (data_drop is not returned)
        obtained_nodes = traverse_graph([data_take], links_forward=links_forward, links_backward=links_backward)[
            'nodes'
        ]
        expected_nodes = set([work_select, data_take])
        assert obtained_nodes == expected_nodes

        # Forward: work_select to (return) data_take (data_drop is not returned)
        obtained_nodes = traverse_graph([work_select], links_forward=links_forward, links_backward=links_backward)[
            'nodes'
        ]
        assert obtained_nodes == expected_nodes

        links_forward = []
        links_backward = [LinkType.INPUT_WORK, LinkType.RETURN]

        # Backward: data_drop is not returned so it has no backward link
        expected_nodes = set([data_drop])
        obtained_nodes = traverse_graph([data_drop], links_forward=links_forward, links_backward=links_backward)[
            'nodes'
        ]
        assert obtained_nodes == expected_nodes

        # Backward: data_take to (return) work_select to (input) data_drop
        expected_nodes = set(every_node)
        obtained_nodes = traverse_graph([data_take], links_forward=links_forward, links_backward=links_backward)[
            'nodes'
        ]
        assert obtained_nodes == expected_nodes

        # Backward: work_select to (input) data_take and data_drop
        obtained_nodes = traverse_graph([work_select], links_forward=links_forward, links_backward=links_backward)[
            'nodes'
        ]
        assert obtained_nodes == expected_nodes

    def test_traversal_errors(self):
        """This will test the errors of the traversers."""
        from aiida import orm
        from aiida.common.exceptions import NotExistent

        test_node = orm.Data().store()
        false_node = -1

        with pytest.raises(NotExistent):
            _ = traverse_graph([false_node])

        with pytest.raises(TypeError):
            _ = traverse_graph(['not a node'])

        with pytest.raises(TypeError):
            _ = traverse_graph('not a list')

        with pytest.raises(TypeError):
            _ = traverse_graph([test_node], links_forward=1984)

        with pytest.raises(TypeError):
            _ = traverse_graph([test_node], links_backward=['not a link'])

    def test_empty_input(self):
        """Testing empty input."""
        all_links = [
            LinkType.INPUT_CALC,
            LinkType.CALL_CALC,
            LinkType.CREATE,
            LinkType.INPUT_WORK,
            LinkType.CALL_WORK,
            LinkType.RETURN,
        ]

        obtained_results = traverse_graph([], links_forward=all_links, links_backward=all_links)
        assert obtained_results['nodes'] == set()
        assert obtained_results['links'] is None

        obtained_results = traverse_graph([], get_links=True, links_forward=all_links, links_backward=all_links)
        assert obtained_results['nodes'] == set()
        assert obtained_results['links'] == set()

    def test_delete_aux(self):
        """Tests for the get_nodes_delete function"""
        nodes_dict = create_minimal_graph()
        nodes_pklist = [value.pk for value in nodes_dict.values()]

        obtained_nodes = get_nodes_delete([nodes_dict['data_i'].pk])['nodes']
        expected_nodes = set(nodes_pklist)
        assert obtained_nodes == expected_nodes

        obtained_nodes = get_nodes_delete([nodes_dict['data_o'].pk])['nodes']
        expected_nodes = set(nodes_pklist).difference(set([nodes_dict['data_i'].pk]))
        assert obtained_nodes == expected_nodes

        obtained_nodes = get_nodes_delete([nodes_dict['work_1'].pk], call_calc_forward=False)['nodes']
        expected_nodes = set([nodes_dict['work_1'].pk, nodes_dict['work_2'].pk])
        assert obtained_nodes == expected_nodes

        obtained_nodes = get_nodes_delete([nodes_dict['work_2'].pk], call_work_forward=False)['nodes']
        expected_nodes = set([nodes_dict['work_2'].pk])
        assert obtained_nodes == expected_nodes

        obtained_nodes = get_nodes_delete([nodes_dict['calc_0'].pk], create_forward=False)['nodes']
        expected_nodes = set([nodes_dict['calc_0'].pk, nodes_dict['work_1'].pk, nodes_dict['work_2'].pk])
        assert obtained_nodes == expected_nodes

        with pytest.raises(ValueError):
            _ = get_nodes_delete([nodes_dict['data_o'].pk], create_backward=False)
