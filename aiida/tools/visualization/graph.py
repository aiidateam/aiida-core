# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
""" provides functionality to create graphs of the AiiDa data providence,
*via* graphviz.
"""
import os
import six
from graphviz import Digraph
from aiida.orm import load_node
from aiida.orm.querybuilder import QueryBuilder
from aiida.plugins import BaseFactory
from aiida.common import LinkType


def default_link_styles(link_type):
    """return a dictionary for the graphviz edge style """
    return {
        LinkType.INPUT_CALC: {
            "style": "solid",
            "color": "black"
        },
        LinkType.INPUT_WORK: {
            "style": "solid",
            "color": "black"
        },
        LinkType.CREATE: {
            "style": "solid",
            "color": "#006400"
        },
        LinkType.CALL_CALC: {
            "style": "dotted",
            "color": "blue"
        },
        LinkType.CALL_WORK: {
            "style": "dotted",
            "color": "blue"
        },
        LinkType.RETURN: {
            "style": "dashed",
            "color": "#006400"
        }
    }[link_type]


def default_data_styles(node):
    """return a dictionary for the graphviz node style """
    class_node_type = node.class_node_type
    default = {
        "shape": "polygon",
        "sides": "4",
        "color": "black",
        "style": "solid"
    }
    return {
        "data.code.Code.": {
            'shape': 'diamond',
            "color": "orange",
            "style": "solid"
        }
    }.get(class_node_type, default)


def default_data_sublabels(node):
    """ function mapping data nodes to a sublabel
    (e.g. specifying some attribute values)
    """
    class_node_type = node.class_node_type
    if class_node_type == "data.int.Int.":
        return "value: {}".format(node.get_attribute("value", ""))
    if class_node_type == "data.float.Float.":
        return "value: {}".format(node.get_attribute("value", ""))
    if class_node_type == "data.code.Code.":
        return "{}@{}".format(os.path.basename(node.get_execname()),
                              node.get_computer_name())
    if class_node_type == "data.singlefile.SinglefileData.":
        return node.filename
    if class_node_type == "data.remote.RemoteData.":
        return "@{}".format(node.get_computer_name())
    if class_node_type == "data.structure.StructureData.":
        return node.get_formula()
    if class_node_type == "data.cif.CifData.":
        formulae = [str(f).replace(" ", "")
                    for f in node.get_attribute('formulae', []) if f]
        sg_numbers = [str(s) for s in
                      node.get_attribute('spacegroup_numbers', []) if s]
        sublabel = []
        if formulae:
            sublabel.append(", ".join(formulae))
        if sg_numbers:
            sublabel.append(", ".join(sg_numbers))
        return "; ".join(sublabel)

    return None


def _add_graphviz_node(graph, node, data_style_func, data_sublabel_func, 
                       style_override=None, include_sublabels=True):
    """create a node in the graph

    Parameters
    ----------
    graph: graphviz.Digraph
    node: aiida.orm.nodes.node.Node
    data_style_func: func
        maps a node instance to a dictionary for the graphviz node style
    data_sublabel_func: func
        maps a node instance to a sub-label for the node text
    style_override=None: None or dict
        style dictionary, whose keys will override the final computed style
    include_sublabels=True: bool
        whether to include the sublabels for nodes

    Notes
    -----

    nodes are styled based on the node type

    For subclasses of Data, the ``class_node_type`` attribute is used
    for mapping to type specific styles

    For subclasses of ProcessNode, we choose styles to distinguish between
    workflows (4 sides) and calculations (6 sides), and also color the nodes
    green/red for successful/failed processes

    The first line of the node text is always '<node.name> (<node.pk>)'.
    Then, if ``include_sublabels=True``, subsequent lines are added,
    which are node type dependant.

    """
    node_style = {}
    if isinstance(node, BaseFactory("aiida.node", "data")):

        node_style = data_style_func(node)
        label = ["{} ({})".format(node.__class__.__name__, node.pk)]
        if include_sublabels:
            sublabel = data_sublabel_func(node)
            if sublabel:
                label.append(sublabel)
        node_style["label"] = "\n".join(label)

    elif isinstance(node, BaseFactory("aiida.node", "process")):
        # style process nodes, based on type

        if isinstance(node, BaseFactory("aiida.node", "process.workflow")):
            node_style = {
                "shape": "polygon",
                "sides": "6",
                "pencolor": "black"
            }
        else:
            node_style = {
                'shape': 'ellipse',
                "pencolor": "black"
            }

        if isinstance(node, (BaseFactory("aiida.node", "process.calculation.calcfunction"),
                             BaseFactory("aiida.node", "process.workflow.workfunction"))):
            node_style["pencolor"] = "#FFF0F5"

        # style process node, based on success/failure of process
        if node.is_failed:
            node_style['style'] = 'filled'
            node_style['fillcolor'] = 'red'
        elif node.is_finished_ok:
            node_style['style'] = 'filled'
            node_style['fillcolor'] = '#90EE90'

        label = ["{} ({})".format(
            node.__class__.__name__ if node.process_label is None else node.process_label,
            node.pk)]

        if include_sublabels:
            if node.process_state is not None:
                label.append("State: {}".format(node.process_state.value))
            if node.exit_status is not None:
                label.append("Exit Code: {}".format(node.exit_status))

        node_style["label"] = "\n".join(label)

    if style_override is not None:
        node_style.update(style_override)

    return graph.node("N{}".format(node.pk), **node_style)


def _add_graphviz_edge(graph, in_node, out_node, style=None):
    """ add graphviz edge between two nodes"""
    if style is None:
        style = {}
    return graph.edge("N{}".format(in_node.pk),
                      "N{}".format(out_node.pk), **style)


class Graph(object):

    def __init__(self, engine=None, graph_attr=None,
                 global_node_style=None,
                 include_sublabels=True,
                 link_styles=None, data_styles=None, data_sublabels=None):
        """ a class to create graphviz graphs off the aiida node provenance

        Nodes and edges, are cached, so that they are only created once

        Parameters
        ----------
        engine=None: str or None
            the graphviz engine, e.g. dot, circo
        graph_attr=None: dict or None
            attributes for the graphviz graph
        global_node_style=None: dict or None
            styles which will be added to all nodes.
            Note this will override any builtin attributes
        include_sublabels: bool
            if True, the note text will include node dependant sub-labels
        link_styles: func or None
            function mapping LinkType to graphviz style dict;
            link_styles(link_type) -> dict
        data_styles: func or None
            function mapping data node to a graphviz style dict;
            data_styles(node) -> dict
        data_sublabels: func or None
            function mapping data node to a sublabel
            (e.g. specifying some attribute values);
            data_sublabels(node) -> str

        """
        self._graph = Digraph(engine=engine, graph_attr=graph_attr)
        self._nodes = set()
        self._edges = set()
        self._global_node_style = {}
        if global_node_style:
            self._global_node_style = global_node_style
        self._include_sublabels = include_sublabels
        if link_styles is not None:
            self._link_styles = link_styles
        else:
            self._link_styles = default_link_styles
        if data_styles is not None:
            self._data_styles = data_styles
        else:
            self._data_styles = default_data_styles
        if data_sublabels is not None:
            self._data_sublabels = data_sublabels
        else:
            self._data_sublabels = default_data_sublabels

    @property
    def graphviz(self):
        return self._graph.copy()

    @property
    def nodes(self):
        return self._nodes.copy()

    @property
    def edges(self):
        return self._edges.copy()

    def _load_node(self, node):
        if isinstance(node, int):
            return load_node(node)
        else:
            return node

    def add_node(self, node, style_override=None, overwrite=False):
        """add single node to the graph

        Parameters
        ----------
        node: int or aiida.orm.nodes.node.Node
            node or node pk
        style_override=None: dict or None
            graphviz style parameters that will override default values
        overwrite=False: bool
            whether to overrite an existing node

        """
        node = self._load_node(node)
        style = {} if style_override is None else style_override
        style.update(self._global_node_style)
        if node.pk not in self.nodes or overwrite:
            _add_graphviz_node(self._graph, node,
                               self._data_styles, self._data_sublabels,
                               style_override=style,
                               include_sublabels=self._include_sublabels)
            self._nodes.add(node.pk)

    def add_edge(self, in_node, out_node, style=None, overwrite=False):
        """add single node to the graph

        Parameters
        ----------
        in_node: int or aiida.orm.nodes.node.Node
            node or node pk
        out_node: int or aiida.orm.nodes.node.Node
            node or node pk
        override_style=None: dict or None
            graphviz style parameters
        overwrite=False: bool
            whether to overrite existing edge

        """
        in_node = self._load_node(in_node)
        if in_node.pk not in self._nodes:
            raise AssertionError(
                "the in_node must have already been added to the graph")
        out_node = self._load_node(out_node)
        if out_node.pk not in self._nodes:
            raise AssertionError(
                "the out_node must have already been added to the graph")

        if (in_node.pk, out_node.pk) in self.edges and not overwrite:
            return

        style = {} if style is None else style
        self._edges.add((in_node.pk, out_node.pk))
        _add_graphviz_edge(self._graph, in_node, out_node, style)

    def add_incoming(self, node, link_types=(), annotate_links=False, return_pks=True):
        """add nodes and edges for incoming links to a node

        Parameters
        ----------
        node: aiida.orm.nodes.node.Node or int
            node or node pk
        link_types: str or tuple[str] or LinkType or tuple[LinkType]
            filter by link types
        annotate_links: bool or str
            label edges with the link 'label', 'type' or 'both'
        return_pks=True: bool
            whether to return a list of nodes, or list of node pks

        Returns
        -------
        list:
            list of nodes or node pks

        """
        if annotate_links not in [False, "label", "type", "both"]:
            raise AssertionError(
                'annotate_links must be one of False, "label", "type" or "both"')

        if link_types:
            if isinstance(link_types, six.string_types):
                link_types = [link_types]
            link_types = tuple(
                [getattr(LinkType, l.upper())
                 if isinstance(l, six.string_types) else l for l in link_types])

        nodes = []
        for link_triple in node.get_incoming(link_type=link_types).link_triples:
            self.add_node(link_triple.node)
            style = self._link_styles(link_triple.link_type)
            if annotate_links == "label":
                style['label'] = link_triple.link_label
            elif annotate_links == "type":
                style['label'] = link_triple.link_type.name
            elif annotate_links == "both":
                style['label'] = "{}\n{}".format(
                    link_triple.link_type.name, link_triple.link_label)
            self.add_edge(link_triple.node, node, style=style)
            nodes.append(
                link_triple.node.pk if return_pks else link_triple.node)

        return nodes

    def add_outgoing(self, node, link_types=(), annotate_links=False, return_pks=True):
        """add nodes and edges for outgoing links to a node

        Parameters
        ----------
        node: aiida.orm.nodes.node.Node or int
            node or node pk
        link_types: str or tuple[str] or LinkType or tuple[LinkType]
            filter by link types
        annotate_links: bool or str
            label edges with the link 'label', 'type' or 'both'
        return_pks=True: bool
            whether to return a list of nodes, or list of node pks

        Returns
        -------
        list:
            list of nodes or node pks

        """
        if annotate_links not in [False, "label", "type", "both"]:
            raise AssertionError(
                'annotate_links must be one of False, "label", "type" or "both"')

        if link_types:
            if isinstance(link_types, six.string_types):
                link_types = [link_types]
            link_types = tuple(
                [getattr(LinkType, l.upper())
                 if isinstance(l, six.string_types) else l for l in link_types])

        nodes = []
        for link_triple in node.get_outgoing(link_type=link_types).link_triples:
            self.add_node(link_triple.node)
            style = self._link_styles(link_triple.link_type)
            if annotate_links == "label":
                style['label'] = link_triple.link_label
            elif annotate_links == "type":
                style['label'] = link_triple.link_type.name
            elif annotate_links == "both":
                style['label'] = "{}\n{}".format(
                    link_triple.link_type.name, link_triple.link_label)
            self.add_edge(node, link_triple.node, style=style)
            nodes.append(
                link_triple.node.pk if return_pks else link_triple.node)

        return nodes

    def recurse_descendants(self, origin, depth=None, link_types=(),
                            annotate_links=False,
                            origin_style=(('style', 'filled'),
                                          ('color', 'lightblue')),
                            include_calculation_inputs=False):
        """add nodes and edges from an origin recursively,
        following outgoing links

        Parameters
        ----------
        origin: aiida.orm.nodes.node.Node or int
            node or node pk
        depth: None or int
            if not None, stop after travelling a certain depth into the graph
        link_type: tuple or str
            filter by subset of link types
        annotate_links: bool or str
            label edges with the link 'label', 'type' or 'both'
        origin_style: dict

        """
        Calculation = BaseFactory("aiida.node", "process.calculation.calcjob")
        origin_node = self._load_node(origin)

        self.add_node(origin_node, style_override=dict(origin_style))

        last_nodes = [origin_node]
        depth = 0
        while last_nodes:
            depth += 1
            # checking of maximum descendant depth is set and applies.
            if depth is not None and depth > depth:
                break
            new_nodes = []
            for node in last_nodes:
                new_nodes.extend(self.add_outgoing(
                    node, link_types=link_types,
                    annotate_links=annotate_links, return_pks=False))
            last_nodes = new_nodes

            if include_calculation_inputs and isinstance(node, Calculation):
                self.add_incoming(
                    node, link_types=link_types, annotate_links=annotate_links)

    def recurse_ancestors(self, origin, depth=None, link_types=(),
                          annotate_links=False,
                          origin_style=(),
                          include_calculation_outputs=False):
        """add nodes and edges from an origin recursively,
        following incoming links

        Parameters
        ----------
        origin: aiida.orm.nodes.node.Node or int
            node or node pk
        depth: None or int
            if not None, stop after travelling a certain depth into the graph
        link_type: tuple or str
            filter by subset of link types
        annotate_links: bool
            label edges with the link 'label', 'type' or 'both'
        origin_style: dict

        """
        Calculation = BaseFactory("aiida.node", "process.calculation.calcjob")

        origin_node = self._load_node(origin)

        self.add_node(origin_node, style_override=dict(origin_style))

        last_nodes = [origin_node]
        depth = 0
        while last_nodes:
            depth += 1
            # checking of maximum descendant depth is set and applies.
            if depth is not None and depth > depth:
                break
            new_nodes = []
            for node in last_nodes:
                new_nodes.extend(self.add_incoming(
                    node, link_types=link_types,
                    annotate_links=annotate_links, return_pks=False))
            last_nodes = new_nodes

            if include_calculation_outputs and isinstance(node, Calculation):
                self.add_outgoing(
                    node, link_types=link_types, annotate_links=annotate_links)

    def add_origin_to_target(self, origin, target_cls, target_filters=None,
                             include_target_inputs=False,
                             include_target_outputs=False,
                             origin_style=(),
                             annotate_links=False):
        """add nodes and edges from an origin node to target nodes

        Parameters
        ----------
        origin: aiida.orm.nodes.node.Node or int
            node or node pk
        target_cls: class
        target_filters=None: dict or None
        include_target_inputs=False: bool
        include_target_outputs=False: bool
        origin_style: dict
        annotate_links: bool
            label edges with the link 'label', 'type' or 'both'


        """
        origin_node = self._load_node(origin)

        if target_filters is None:
            target_filters = {}

        self.add_node(origin_node, style_override=dict(origin_style))

        query = QueryBuilder()(**{
            "path": [
                {
                    'cls': origin_node.__class__,
                    "filters": {
                        "id": origin_node.pk
                    },
                    'tag': "origin"
                },
                {
                    'cls': target_cls,
                    'filters': target_filters,
                    'descendant_of': 'origin',
                    'tag': "target",
                    'project': "*"
                }
            ]
        })

        for (target_node,) in query.iterall():
            self.add_node(target_node)
            self.add_edge(origin_node, target_node,
                          style={'style': 'dashed', 'color': 'grey'})

            if include_target_inputs:
                self.add_incoming(target_node, annotate_links=annotate_links)

            if include_target_outputs:
                self.add_outgoing(target_node, annotate_links=annotate_links)

    def add_origins_to_targets(self, origin_cls,
                               target_cls,
                               origin_filters=None,
                               target_filters=None,
                               include_target_inputs=False,
                               include_target_outputs=False,
                               origin_style=(),
                               annotate_links=False):
        """add nodes and edges from multiple origin node to target nodes

        Parameters
        ----------
        origin_cls: class
        target_cls: class
        origin_filters=None: dict or None
        target_filters=None: dict or None
        include_target_inputs=False: bool
        include_target_outputs=False: bool
        origin_style: dict
        annotate_links: bool
            label edges with the link 'label', 'type' or 'both'

        """
        if origin_filters is None:
            origin_filters = {}

        query = QueryBuilder()(**{
            "path": [
                {
                    'cls': origin_cls,
                    "filters": origin_filters,
                    'tag': "origin",
                    'project': "*"
                }
            ]
        })

        for (node,) in query.iterall():
            self.add_origin_to_target(
                node, target_cls, target_filters=target_filters,
                include_target_inputs=include_target_inputs,
                include_target_outputs=include_target_outputs,
                origin_style=origin_style,
                annotate_links=annotate_links)
