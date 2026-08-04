###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for creating graphs (using graphviz)"""

import re

import pytest

from aiida import orm
from aiida.common import AttributeDict
from aiida.common.links import LinkType
from aiida.engine import ProcessState
from aiida.orm.utils.links import LinkPair
from aiida.tools.visualization import graph as graph_mod


class TestVisGraph:
    """Tests for verdi graph"""

    @pytest.fixture(autouse=True)
    def init_profile(self, aiida_localhost):
        """Initialize the profile."""
        self.computer = aiida_localhost

    def create_provenance(self):
        """Create an example provenance graph"""
        pd0 = orm.Dict()
        pd0.label = 'pd0'
        pd0.store()

        pd1 = orm.Dict()
        pd1.label = 'pd1'
        pd1.store()

        wc1 = orm.WorkChainNode()
        wc1.set_process_state(ProcessState.RUNNING)
        wc1.base.links.add_incoming(pd0, link_type=LinkType.INPUT_WORK, link_label='input1')
        wc1.base.links.add_incoming(pd1, link_type=LinkType.INPUT_WORK, link_label='input2')
        wc1.store()

        calc1 = orm.CalcJobNode()
        calc1.computer = self.computer
        calc1.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        calc1.label = 'calc1'
        calc1.set_process_state(ProcessState.FINISHED)
        calc1.set_exit_status(0)
        calc1.base.links.add_incoming(pd0, link_type=LinkType.INPUT_CALC, link_label='input1')
        calc1.base.links.add_incoming(pd1, link_type=LinkType.INPUT_CALC, link_label='input2')
        calc1.base.links.add_incoming(wc1, link_type=LinkType.CALL_CALC, link_label='call1')
        calc1.store()

        rd1 = orm.RemoteData()
        rd1.label = 'rd1'
        rd1.set_remote_path('/x/y.py')
        rd1.computer = self.computer
        rd1.store()
        rd1.base.links.add_incoming(calc1, link_type=LinkType.CREATE, link_label='output')

        pd2 = orm.Dict()
        pd2.label = 'pd2'
        pd2.store()

        calcf1 = orm.CalcFunctionNode()
        calcf1.label = 'calcf1'
        calcf1.set_process_state(ProcessState.FINISHED)
        calcf1.set_exit_status(200)
        calcf1.base.links.add_incoming(rd1, link_type=LinkType.INPUT_CALC, link_label='input1')
        calcf1.base.links.add_incoming(pd2, link_type=LinkType.INPUT_CALC, link_label='input2')
        calcf1.base.links.add_incoming(wc1, link_type=LinkType.CALL_CALC, link_label='call2')
        calcf1.store()

        pd3 = orm.Dict()
        pd3.label = 'pd3'

        fd1 = orm.FolderData()
        fd1.label = 'fd1'

        pd3.base.links.add_incoming(calcf1, link_type=LinkType.CREATE, link_label='output1')
        pd3.store()
        fd1.base.links.add_incoming(calcf1, link_type=LinkType.CREATE, link_label='output2')
        fd1.store()

        pd3.base.links.add_incoming(wc1, link_type=LinkType.RETURN, link_label='output1')
        fd1.base.links.add_incoming(wc1, link_type=LinkType.RETURN, link_label='output2')

        return AttributeDict(
            {
                'pd0': pd0,
                'pd1': pd1,
                'calc1': calc1,
                'rd1': rd1,
                'pd2': pd2,
                'calcf1': calcf1,
                'pd3': pd3,
                'fd1': fd1,
                'wc1': wc1,
            }
        )

    def test_graph_init(self):
        """Test initialisation of Graph"""
        graph_mod.Graph()

    def test_graph_add_node(self):
        """Test adding a node to the graph"""
        nodes = self.create_provenance()

        graph = graph_mod.Graph()
        graph.add_node(nodes.pd0)
        assert graph.nodes == set([nodes.pd0.pk])
        assert graph.edges == set()

        # try adding a second time
        graph.add_node(nodes.pd0)
        assert graph.nodes == set([nodes.pd0.pk])

        # add second node
        graph.add_node(nodes.pd1)
        assert graph.nodes == set([nodes.pd0.pk, nodes.pd1.pk])

    def test_graph_add_edge(self):
        """Test adding an edge to the graph"""
        nodes = self.create_provenance()

        graph = graph_mod.Graph()
        graph.add_node(nodes.pd0)
        graph.add_node(nodes.rd1)
        graph.add_edge(nodes.pd0, nodes.rd1)
        assert graph.nodes == set([nodes.pd0.pk, nodes.rd1.pk])
        assert graph.edges == set([(nodes.pd0.pk, nodes.rd1.pk, None)])

    def test_graph_add_incoming(self):
        """Test adding a node and all its incoming nodes to a graph"""
        nodes = self.create_provenance()

        graph = graph_mod.Graph()
        graph.add_incoming(nodes.calc1)

        assert graph.nodes == set([nodes.calc1.pk, nodes.pd0.pk, nodes.pd1.pk, nodes.wc1.pk])
        assert graph.edges == set(
            [
                (nodes.pd0.pk, nodes.calc1.pk, LinkPair(LinkType.INPUT_CALC, 'input1')),
                (nodes.pd1.pk, nodes.calc1.pk, LinkPair(LinkType.INPUT_CALC, 'input2')),
                (nodes.wc1.pk, nodes.calc1.pk, LinkPair(LinkType.CALL_CALC, 'call1')),
            ]
        )

    def test_graph_add_outgoing(self):
        """Test adding a node and all its outgoing nodes to a graph"""
        nodes = self.create_provenance()

        graph = graph_mod.Graph()
        graph.add_outgoing(nodes.calcf1)

        assert graph.nodes == set([nodes.calcf1.pk, nodes.pd3.pk, nodes.fd1.pk])
        assert graph.edges == set(
            [
                (nodes.calcf1.pk, nodes.pd3.pk, LinkPair(LinkType.CREATE, 'output1')),
                (nodes.calcf1.pk, nodes.fd1.pk, LinkPair(LinkType.CREATE, 'output2')),
            ]
        )

    def test_graph_recurse_ancestors(self):
        """Test adding nodes and all its (recursed) incoming nodes to a graph"""
        nodes = self.create_provenance()

        graph = graph_mod.Graph()
        graph.recurse_ancestors(nodes.rd1)

        assert graph.nodes == set([nodes.rd1.pk, nodes.calc1.pk, nodes.pd0.pk, nodes.pd1.pk, nodes.wc1.pk])
        assert graph.edges == set(
            [
                (nodes.calc1.pk, nodes.rd1.pk, LinkPair(LinkType.CREATE, 'output')),
                (nodes.pd0.pk, nodes.calc1.pk, LinkPair(LinkType.INPUT_CALC, 'input1')),
                (nodes.pd1.pk, nodes.calc1.pk, LinkPair(LinkType.INPUT_CALC, 'input2')),
                (nodes.wc1.pk, nodes.calc1.pk, LinkPair(LinkType.CALL_CALC, 'call1')),
                (nodes.pd0.pk, nodes.wc1.pk, LinkPair(LinkType.INPUT_WORK, 'input1')),
                (nodes.pd1.pk, nodes.wc1.pk, LinkPair(LinkType.INPUT_WORK, 'input2')),
            ]
        )

    def test_graph_recurse_spot_highlight_classes(self):
        """Test adding nodes and all its (recursed) incoming nodes to a graph"""
        nodes = self.create_provenance()

        graph = graph_mod.Graph()
        graph.recurse_ancestors(nodes.pd0)
        graph.recurse_descendants(nodes.pd0)

        graph_highlight = graph_mod.Graph()
        graph_highlight.recurse_ancestors(nodes.pd0, highlight_classes=['Dict'])
        graph_highlight.recurse_descendants(nodes.pd0, highlight_classes=['Dict', 'CalcJobNode', 'Dummy'])

        base_lines = set(graph.graphviz.source.splitlines(keepends=True))
        hl_lines = set(graph_highlight.graphviz.source.splitlines(keepends=True))

        added = hl_lines - base_lines
        added_stripped = {line.strip() for line in added}

        expected = {
            'State: running" color=lightgray fillcolor=white penwidth=2 shape=rectangle style=filled]',
            '@localhost" color=lightgray fillcolor=white penwidth=2 shape=ellipse style=filled]',
            'Exit Code: 200" color=lightgray fillcolor=white penwidth=2 shape=rectangle style=filled]',
            f'N{nodes.fd1.pk} [label="FolderData ({nodes.fd1.pk})" color=lightgray fillcolor=white penwidth=2 '
            'shape=ellipse style=filled]',
        }
        assert added_stripped == expected

    def test_graph_recurse_ancestors_filter_links(self):
        """Test adding nodes and all its (recursed) incoming nodes to a graph, but filter link types"""
        nodes = self.create_provenance()

        graph = graph_mod.Graph()
        graph.recurse_ancestors(nodes.rd1, link_types=['create', 'input_calc'])

        assert graph.nodes == set([nodes.rd1.pk, nodes.calc1.pk, nodes.pd0.pk, nodes.pd1.pk])
        assert graph.edges == set(
            [
                (nodes.calc1.pk, nodes.rd1.pk, LinkPair(LinkType.CREATE, 'output')),
                (nodes.pd0.pk, nodes.calc1.pk, LinkPair(LinkType.INPUT_CALC, 'input1')),
                (nodes.pd1.pk, nodes.calc1.pk, LinkPair(LinkType.INPUT_CALC, 'input2')),
            ]
        )

    def test_graph_recurse_descendants(self):
        """Test adding nodes and all its (recursed) incoming nodes to a graph"""
        nodes = self.create_provenance()

        graph = graph_mod.Graph()
        graph.recurse_descendants(nodes.rd1)

        assert graph.nodes == set([nodes.rd1.pk, nodes.calcf1.pk, nodes.pd3.pk, nodes.fd1.pk])
        assert graph.edges == set(
            [
                (nodes.rd1.pk, nodes.calcf1.pk, LinkPair(LinkType.INPUT_CALC, 'input1')),
                (nodes.calcf1.pk, nodes.pd3.pk, LinkPair(LinkType.CREATE, 'output1')),
                (nodes.calcf1.pk, nodes.fd1.pk, LinkPair(LinkType.CREATE, 'output2')),
            ]
        )

    def test_graph_graphviz_source(self):
        """Test the output of graphviz source"""
        nodes = self.create_provenance()

        graph = graph_mod.Graph()
        graph.recurse_descendants(nodes.pd0)

        expected = """\
        digraph {{
                N{pd0} [label="Dict ({pd0})" color=red fillcolor="#8cd499ff" penwidth=6 shape=ellipse style=filled]
                N{calc1} [label="CalcJobNode ({calc1})
                    State: finished
                    Exit Code: 0" fillcolor="#de707fff" penwidth=0 shape=rectangle style=filled]
                N{pd0} -> N{calc1} [color="#000000" style=solid]
                N{wc1} [label="WorkChainNode ({wc1})
                    State: running" fillcolor="#e38851ff" penwidth=0 shape=rectangle style=filled]
                N{pd0} -> N{wc1} [color="#000000" style=dashed]
                N{rd1} [label="RemoteData ({rd1})
                    @localhost" fillcolor="#8cd499ff" penwidth=0 shape=ellipse style=filled]
                N{calc1} -> N{rd1} [color="#000000" style=solid]
                N{fd1} [label="FolderData ({fd1})" fillcolor="#8cd499ff" penwidth=0 shape=ellipse style=filled]
                N{wc1} -> N{fd1} [color="#000000" style=dashed]
                N{pd3} [label="Dict ({pd3})" fillcolor="#8cd499ff" penwidth=0 shape=ellipse style=filled]
                N{wc1} -> N{pd3} [color="#000000" style=dashed]
                N{calcf1} [label="CalcFunctionNode ({calcf1})
                    State: finished
                    Exit Code: 200" fillcolor="#de707f77" penwidth=0 shape=rectangle style=filled]
                N{wc1} -> N{calcf1} [color="#000000" style=dotted]
                N{wc1} -> N{calc1} [color="#000000" style=dotted]
                N{rd1} -> N{calcf1} [color="#000000" style=solid]
                N{calcf1} -> N{fd1} [color="#000000" style=solid]
                N{calcf1} -> N{pd3} [color="#000000" style=solid]
        }}""".format(**{k: v.pk for k, v in nodes.items()})

        # dedent before comparison
        assert sorted([line.strip() for line in graph.graphviz.source.splitlines()]) == sorted(
            [line.strip() for line in expected.splitlines()]
        )

    def test_graph_graphviz_source_pstate(self):
        """Test the output of graphviz source, with the `pstate_node_styles` function"""
        nodes = self.create_provenance()

        graph = graph_mod.Graph(node_style_fn=graph_mod.pstate_node_styles)
        graph.recurse_descendants(nodes.pd0)

        expected = """\
        digraph {{
                N{pd0} [label="Dict ({pd0})" color=red pencolor=black penwidth=6 shape=rectangle]
                N{calc1} [label="CalcJobNode ({calc1})
                    State: finished
                    Exit Code: 0" fillcolor="#8cd499ff" penwidth=0 shape=ellipse style=filled]
                N{pd0} -> N{calc1} [color="#000000" style=solid]
                N{wc1} [label="WorkChainNode ({wc1})
                    State: running" fillcolor="#e38851ff" penwidth=0 shape=polygon sides=6 style=filled]
                N{pd0} -> N{wc1} [color="#000000" style=dashed]
                N{rd1} [label="RemoteData ({rd1})
                    @localhost" pencolor=black shape=rectangle]
                N{calc1} -> N{rd1} [color="#000000" style=solid]
                N{fd1} [label="FolderData ({fd1})" pencolor=black shape=rectangle]
                N{wc1} -> N{fd1} [color="#000000" style=dashed]
                N{pd3} [label="Dict ({pd3})" pencolor=black shape=rectangle]
                N{wc1} -> N{pd3} [color="#000000" style=dashed]
                N{calcf1} [label="CalcFunctionNode ({calcf1})
                    State: finished
                    Exit Code: 200" fillcolor="#de707fff" penwidth=0 shape=ellipse style=filled]
                N{wc1} -> N{calcf1} [color="#000000" style=dotted]
                N{wc1} -> N{calc1} [color="#000000" style=dotted]
                N{rd1} -> N{calcf1} [color="#000000" style=solid]
                N{calcf1} -> N{fd1} [color="#000000" style=solid]
                N{calcf1} -> N{pd3} [color="#000000" style=solid]
        }}""".format(**{k: v.pk for k, v in nodes.items()})

        # dedent before comparison
        assert sorted([line.strip() for line in graph.graphviz.source.splitlines()]) == sorted(
            [line.strip() for line in expected.splitlines()]
        )

    @pytest.mark.parametrize(
        'node_id_type',
        (
            'pk',
            'uuid',
            'label',
            ('pk', 'uuid'),
            ('pk', 'label'),
        ),
    )
    def test_graph_node_identifiers(self, node_id_type, monkeypatch, file_regression):
        """."""
        nodes = self.create_provenance()

        # Monkeypatch the mapping of lambdas that convert return a node's identifier in string form. This is because
        # the pks and uuids of the test nodes will change between each test run and this would fail the file regression.
        node_identifier_to_label = {
            'pk': lambda node: '10',
            'uuid': lambda node: '16739459',
            'label': lambda node: 'some-label',
        }
        monkeypatch.setattr(graph_mod, 'NODE_IDENTIFIER_TO_LABEL', node_identifier_to_label)

        graph = graph_mod.Graph(node_id_type=node_id_type)
        graph.recurse_descendants(nodes.calcf1)

        # The order of certain output lines can be randomly ordered so we split the file in lines, sort, and then join
        # them into a single string again. The node identifiers generated by the engine are of the form ``N{pk}`` and
        # they also clearly vary, so they are replaced with the ``NODE`` placeholder.
        string = graph.graphviz.source
        string = re.sub(r'N\d+', 'NODE', string)
        string = '\n'.join(sorted(string.strip().split('\n')))
        file_regression.check(string)
