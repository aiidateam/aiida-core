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
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import six
from graphviz import Digraph
from aiida.orm import load_node
from aiida.orm.querybuilder import QueryBuilder
from aiida.plugins import BaseFactory
from aiida.common import LinkType


def default_link_styles(link_type):
    """map link_type to a graphviz edge style

    :param link_type: a LinkType attribute
    :type link_type: One of the members from
        :class:`aiida.common.links.LinkType`
    :rtype: dict

    """
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
    """map a data node to a graphviz node style

    :param node: the node to map
    :type node: aiida.orm.nodes.node.Node
    :rtype: dict

    """
    class_node_type = node.class_node_type
    default = {"shape": "polygon", "sides": "4", "color": "black", "style": "solid"}
    return {"data.code.Code.": {'shape': 'diamond', "color": "orange", "style": "solid"}}.get(class_node_type, default)


def default_data_sublabels(node):
    """function mapping data nodes to a sublabel
    (e.g. specifying some attribute values)

    :param node: the node to map
    :type node: aiida.orm.nodes.node.Node
    :rtype: str

    """
    sublabel = None
    class_node_type = node.class_node_type
    if class_node_type == "data.int.Int.":
        sublabel = "value: {}".format(node.get_attribute("value", ""))
    elif class_node_type == "data.float.Float.":
        sublabel = "value: {}".format(node.get_attribute("value", ""))
    elif class_node_type == "data.code.Code.":
        sublabel = "{}@{}".format(os.path.basename(node.get_execname()), node.get_computer_name())
    elif class_node_type == "data.singlefile.SinglefileData.":
        sublabel = node.filename
    elif class_node_type == "data.remote.RemoteData.":
        sublabel = "@{}".format(node.get_computer_name())
    elif class_node_type == "data.structure.StructureData.":
        sublabel = node.get_formula()
    elif class_node_type == "data.cif.CifData.":
        formulae = [str(f).replace(" ", "") for f in node.get_attribute('formulae', []) if f]
        sg_numbers = [str(s) for s in node.get_attribute('spacegroup_numbers', []) if s]
        sublabel_lines = []
        if formulae:
            sublabel_lines.append(", ".join(formulae))
        if sg_numbers:
            sublabel_lines.append(", ".join(sg_numbers))
        sublabel = "; ".join(sublabel_lines)

    return sublabel


def _add_graphviz_node(graph, node, data_style_func, data_sublabel_func, style_override=None, include_sublabels=True):
    """create a node in the graph

    :param graph: the graphviz.Digraph to add the node to
    :param node: the node to add
    :type node: aiida.orm.nodes.node.Node
    :param data_style_func: callable mapping a node instance to a dictionary for the graphviz node style
    :param data_sublabel_func: callable mapping a node instance to a sub-label for the node text
    :param style_override: style dictionary, whose keys will override the final computed style (Default value = None)
    :type style_override: None or dict
    :param include_sublabels: whether to include the sublabels for nodes (Default value = True)
    :type include_sublabels: bool

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
            node_style = {"shape": "polygon", "sides": "6", "pencolor": "black"}
        else:
            node_style = {'shape': 'ellipse', "pencolor": "black"}

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

        label = [
            "{} ({})".format(node.__class__.__name__ if node.process_label is None else node.process_label, node.pk)
        ]

        if include_sublabels and node.process_state is not None:
            label.append("State: {}".format(node.process_state.value))
        if include_sublabels and node.exit_status is not None:
            label.append("Exit Code: {}".format(node.exit_status))

        node_style["label"] = "\n".join(label)

    if style_override is not None:
        node_style.update(style_override)

    return graph.node("N{}".format(node.pk), **node_style)


def _add_graphviz_edge(graph, in_node, out_node, style=None):
    """add graphviz edge between two nodes

    :param graph: the graphviz.DiGraph to add the edge to
    :param in_node: the head node
    :param out_node: the tail node
    :param style: the graphviz style (Default value = None)
    :type style: dict or None

    """
    if style is None:
        style = {}
    return graph.edge("N{}".format(in_node.pk), "N{}".format(out_node.pk), **style)


class Graph(object):
    """a class to create graphviz graphs of the AiiDA node provenance"""

    # pylint: disable=useless-object-inheritance

    def __init__(self,
                 engine=None,
                 graph_attr=None,
                 global_node_style=None,
                 include_sublabels=True,
                 link_styles=None,
                 data_styles=None,
                 data_sublabels=None):
        """a class to create graphviz graphs of the AiiDA node provenance

        Nodes and edges, are cached, so that they are only created once

        :param engine: the graphviz engine, e.g. dot, circo (Default value = None)
        :type engine: str or None
        :param graph_attr: attributes for the graphviz graph (Default value = None)
        :type graph_attr: dict or None
        :param global_node_style: styles which will be added to all nodes.
            Note this will override any builtin attributes (Default value = None)
        :type global_node_style: dict or None
        :param include_sublabels: if True, the note text will include node dependant sub-labels (Default value = True)
        :type include_sublabels: bool
        :param link_styles: callable mapping LinkType to graphviz style dict;
            link_styles(link_type) -> dict (Default value = None)
        :param data_styles: callable mapping data node to a graphviz style dict;
            data_styles(node) -> dict (Default value = None)
        :param data_sublabels: callable mapping data node to a sublabel (e.g. specifying some attribute values)
            data_sublabels(node) -> str (Default value = None)

        """
        # pylint: disable=too-many-arguments
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
        """return a copy of the graphviz.Digraph"""
        return self._graph.copy()

    @property
    def nodes(self):
        """return a copy of the nodes"""
        return self._nodes.copy()

    @property
    def edges(self):
        """return a copy of the edges"""
        return self._edges.copy()

    @staticmethod
    def _load_node(node):
        """ load a node (if not already loaded)

        :param node: node or node pk
        :type node: int or aiida.orm.nodes.node.Node
        :returns: aiida.orm.nodes.node.Node

        """
        if isinstance(node, int):
            return load_node(node)
        return node

    def add_node(self, node, style_override=None, overwrite=False):
        """add single node to the graph

        :param node: node or node pk
        :type node: int or aiida.orm.nodes.node.Node
        :param style_override: graphviz style parameters that will override default values
        :type style_override: dict or None
        :param overwrite: whether to overrite an existing node (Default value = False)
        :type overwrite: bool

        """
        node = self._load_node(node)
        style = {} if style_override is None else style_override
        style.update(self._global_node_style)
        if node.pk not in self.nodes or overwrite:
            _add_graphviz_node(
                self._graph,
                node,
                self._data_styles,
                self._data_sublabels,
                style_override=style,
                include_sublabels=self._include_sublabels)
            self._nodes.add(node.pk)

    def add_edge(self, in_node, out_node, style=None, overwrite=False):
        """add single node to the graph

        :param in_node: node or node pk
        :type in_node: int or aiida.orm.nodes.node.Node
        :param out_node: node or node pk
        :type out_node: int or aiida.orm.nodes.node.Node
        :param style: graphviz style parameters (Default value = None)
        :type style: dict or None
        :param overwrite: whether to overrite existing edge (Default value = False)
        :type overwrite: bool

        """
        in_node = self._load_node(in_node)
        if in_node.pk not in self._nodes:
            raise AssertionError("the in_node must have already been added to the graph")
        out_node = self._load_node(out_node)
        if out_node.pk not in self._nodes:
            raise AssertionError("the out_node must have already been added to the graph")

        if (in_node.pk, out_node.pk) in self.edges and not overwrite:
            return

        style = {} if style is None else style
        self._edges.add((in_node.pk, out_node.pk))
        _add_graphviz_edge(self._graph, in_node, out_node, style)

    def add_incoming(self, node, link_types=(), annotate_links=False, return_pks=True):
        """add nodes and edges for incoming links to a node

        :param node: node or node pk
        :type node: aiida.orm.nodes.node.Node or int
        :param link_types: filter by link types (Default value = ())
        :type link_types: str or tuple[str] or aiida.common.links.LinkType or tuple[aiida.common.links.LinkType]
        :param annotate_links: label edges with the link 'label', 'type' or 'both' (Default value = False)
        :type annotate_links: bool or str
        :param return_pks: whether to return a list of nodes, or list of node pks (Default value = True)
        :type return_pks: bool
        :returns: list of nodes or node pks

        """
        if annotate_links not in [False, "label", "type", "both"]:
            raise AssertionError('annotate_links must be one of False, "label", "type" or "both"')

        if link_types:
            if isinstance(link_types, six.string_types):
                link_types = [link_types]
            link_types = tuple(
                [getattr(LinkType, l.upper()) if isinstance(l, six.string_types) else l for l in link_types])

        nodes = []
        for link_triple in node.get_incoming(link_type=link_types).link_triples:
            self.add_node(link_triple.node)
            style = self._link_styles(link_triple.link_type)
            if annotate_links == "label":
                style['label'] = link_triple.link_label
            elif annotate_links == "type":
                style['label'] = link_triple.link_type.name
            elif annotate_links == "both":
                style['label'] = "{}\n{}".format(link_triple.link_type.name, link_triple.link_label)
            self.add_edge(link_triple.node, node, style=style)
            nodes.append(link_triple.node.pk if return_pks else link_triple.node)

        return nodes

    def add_outgoing(self, node, link_types=(), annotate_links=False, return_pks=True):
        """add nodes and edges for outgoing links to a node

        :param node: node or node pk
        :type node: aiida.orm.nodes.node.Node or int
        :param link_types: filter by link types (Default value = ())
        :type link_types: str or tuple[str] or aiida.common.links.LinkType or tuple[aiida.common.links.LinkType]
        :param annotate_links: label edges with the link 'label', 'type' or 'both' (Default value = False)
        :type annotate_links: bool or str
        :param return_pks: whether to return a list of nodes, or list of node pks (Default value = True)
        :type return_pks: bool
        :returns: list of nodes or node pks

        """
        if annotate_links not in [False, "label", "type", "both"]:
            raise AssertionError('annotate_links must be one of False, "label", "type" or "both"')

        if link_types:
            if isinstance(link_types, six.string_types):
                link_types = [link_types]
            link_types = tuple(
                [getattr(LinkType, l.upper()) if isinstance(l, six.string_types) else l for l in link_types])

        nodes = []
        for link_triple in node.get_outgoing(link_type=link_types).link_triples:
            self.add_node(link_triple.node)
            style = self._link_styles(link_triple.link_type)
            if annotate_links == "label":
                style['label'] = link_triple.link_label
            elif annotate_links == "type":
                style['label'] = link_triple.link_type.name
            elif annotate_links == "both":
                style['label'] = "{}\n{}".format(link_triple.link_type.name, link_triple.link_label)
            self.add_edge(node, link_triple.node, style=style)
            nodes.append(link_triple.node.pk if return_pks else link_triple.node)

        return nodes

    def recurse_descendants(self,
                            origin,
                            depth=None,
                            link_types=(),
                            annotate_links=False,
                            origin_style=(),
                            include_calculation_inputs=False):
        """add nodes and edges from an origin recursively,
        following outgoing links

        :param origin: node or node pk
        :type origin: aiida.orm.nodes.node.Node or int
        :param depth: if not None, stop after travelling a certain depth into the graph (Default value = None)
        :type depth: None or int
        :param link_types: filter by subset of link types (Default value = ())
        :type link_types: tuple or str
        :param annotate_links: label edges with the link 'label', 'type' or 'both' (Default value = False)
        :type annotate_links: bool or str
        :param origin_style: node style map for origin node (Default value = ())
        :type origin_style: dict or tuple
        :param include_calculation_inputs:  (Default value = False)
        :type include_calculation_inputs: bool

        """
        # pylint: disable=too-many-arguments
        origin_node = self._load_node(origin)

        self.add_node(origin_node, style_override=dict(origin_style))

        last_nodes = [origin_node]
        cur_depth = 0
        while last_nodes:
            cur_depth += 1
            # checking of maximum descendant depth is set and applies.
            if depth is not None and cur_depth > depth:
                break
            new_nodes = []
            for node in last_nodes:
                new_nodes.extend(
                    self.add_outgoing(node, link_types=link_types, annotate_links=annotate_links, return_pks=False))

                if include_calculation_inputs and isinstance(node,
                                                             BaseFactory("aiida.node", "process.calculation.calcjob")):
                    self.add_incoming(node, link_types=link_types, annotate_links=annotate_links)

            last_nodes = new_nodes

    def recurse_ancestors(self,
                          origin,
                          depth=None,
                          link_types=(),
                          annotate_links=False,
                          origin_style=(),
                          include_calculation_outputs=False):
        """add nodes and edges from an origin recursively,
        following incoming links

        :param origin: node or node pk
        :type origin: aiida.orm.nodes.node.Node or int
        :param depth: if not None, stop after travelling a certain depth into the graph (Default value = None)
        :type depth: None or int
        :param link_types: filter by subset of link types (Default value = ())
        :type link_types: tuple or str
        :param annotate_links: label edges with the link 'label', 'type' or 'both' (Default value = False)
        :type annotate_links: bool
        :param origin_style: node style map for origin node (Default value = ())
        :type origin_style: dict or tuple
        :param include_calculation_outputs:  (Default value = False)
        :type include_calculation_outputs: bool

        """
        # pylint: disable=too-many-arguments
        origin_node = self._load_node(origin)

        self.add_node(origin_node, style_override=dict(origin_style))

        last_nodes = [origin_node]
        cur_depth = 0
        while last_nodes:
            cur_depth += 1
            # checking of maximum descendant depth is set and applies.
            if depth is not None and cur_depth > depth:
                break
            new_nodes = []
            for node in last_nodes:
                new_nodes.extend(
                    self.add_incoming(node, link_types=link_types, annotate_links=annotate_links, return_pks=False))

                if include_calculation_outputs and isinstance(node,
                                                              BaseFactory("aiida.node", "process.calculation.calcjob")):
                    self.add_outgoing(node, link_types=link_types, annotate_links=annotate_links)

            last_nodes = new_nodes

    def add_origin_to_target(self,
                             origin,
                             target_cls,
                             target_filters=None,
                             include_target_inputs=False,
                             include_target_outputs=False,
                             origin_style=(),
                             annotate_links=False):
        """add nodes and edges from an origin node to target nodes

        :param origin: node or node pk
        :type origin: aiida.orm.nodes.node.Node or int
        :param target_cls: target node class
        :param target_filters:  (Default value = None)
        :type target_filters: dict or None
        :param include_target_inputs:  (Default value = False)
        :type include_target_inputs: bool
        :param include_target_outputs:  (Default value = False)
        :type include_target_outputs: bool
        :param origin_style: node style map for origin node (Default value = ())
        :type origin_style: dict or tuple
        :param annotate_links: label edges with the link 'label', 'type' or 'both' (Default value = False)
        :type annotate_links: bool

        """
        # pylint: disable=too-many-arguments
        origin_node = self._load_node(origin)

        if target_filters is None:
            target_filters = {}

        self.add_node(origin_node, style_override=dict(origin_style))

        query = QueryBuilder(
            **{
                "path": [{
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
                         }]
            })

        for (target_node,) in query.iterall():
            self.add_node(target_node)
            self.add_edge(origin_node, target_node, style={'style': 'dashed', 'color': 'grey'})

            if include_target_inputs:
                self.add_incoming(target_node, annotate_links=annotate_links)

            if include_target_outputs:
                self.add_outgoing(target_node, annotate_links=annotate_links)

    def add_origins_to_targets(self,
                               origin_cls,
                               target_cls,
                               origin_filters=None,
                               target_filters=None,
                               include_target_inputs=False,
                               include_target_outputs=False,
                               origin_style=(),
                               annotate_links=False):
        """add nodes and edges from multiple origin node to target nodes

        :param origin_cls: origin node class
        :param target_cls: target node class
        :param origin_filters:  (Default value = None)
        :type origin_filters: dict or None
        :param target_filters:  (Default value = None)
        :type target_filters: dict or None
        :param include_target_inputs:  (Default value = False)
        :type include_target_inputs: bool
        :param include_target_outputs:  (Default value = False)
        :type include_target_outputs: bool
        :param origin_style: node style map for origin node (Default value = ())
        :type origin_style: dict or tuple
        :param annotate_links: label edges with the link 'label', 'type' or 'both' (Default value = False)
        :type annotate_links: bool

        """
        # pylint: disable=too-many-arguments
        if origin_filters is None:
            origin_filters = {}

        query = QueryBuilder(
            **{"path": [{
                'cls': origin_cls,
                "filters": origin_filters,
                'tag': "origin",
                'project': "*"
            }]})

        for (node,) in query.iterall():
            self.add_origin_to_target(
                node,
                target_cls,
                target_filters=target_filters,
                include_target_inputs=include_target_inputs,
                include_target_outputs=include_target_outputs,
                origin_style=origin_style,
                annotate_links=annotate_links)
