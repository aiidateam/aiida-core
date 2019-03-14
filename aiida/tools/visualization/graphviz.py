# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Draw the provenance graphs
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import


def is_data_instance(node, plugin_name, allow_fail):
    """ test if a node is an instance of a data class """
    from aiida.orm import DataFactory
    from aiida.common.exceptions import MissingPluginError
    try:
        kls = DataFactory(plugin_name)
    except MissingPluginError:
        if allow_fail:
            return False
        else:
            raise
    return isinstance(node, kls)


def _std_label(node):
    label = "{} ({})".format(
        node.__class__.__name__,
        node.pk
    )
    if hasattr(node, 'label') and node.label:
        label += "\n{}".format(node.label)
    return label


def _style_default(node, override=None):
    style = {'label': _std_label(node)}
    if override:
        style.update(override)
    return style


def _style_calculation(node, override=None):
    style = {}
    if node.get_attribute("process", None):
        label = "{} ({})".format(node.get_attribute("process"), node.pk)
    else:
        label = _std_label(node)
    state = node.get_attribute("state", None)
    # if state:
    #     label += "\n{}".format(state)
    style.update({
        'shape': 'polygon',
        'sides': '4',
        'label': label
    })
    if state == "FINISHED":
        style['style'] = 'filled'
        style['color'] = '#90EE90'
    elif state == "FAILED":
        style['style'] = 'filled'
        style['color'] = 'red'
    if override:
        style.update(override)
    return style


def _style_code(node, override=None):
    style = {
        'shape': 'diamond',
        'color': 'orange',
        'label': _std_label(node)
    }
    if override:
        style.update(override)
    return style


def _style_cif(node, override=None):
    style = {}
    label = _std_label(node)
    formulae = [str(f).replace(" ", "")
                for f in aid.get_attribute(node, 'formulae', []) if f]
    formulae = ", ".join(formulae)
    sg_numbers = [str(s) for s in
                  aid.get_attribute(node, 'spacegroup_numbers', []) if f]
    sg_numbers = ", ".join(sg_numbers)
    if formulae or sg_numbers:
        label += "\n"
    if formulae:
        label += formulae + " "
    if sg_numbers:
        label += "({})".format(sg_numbers)

    style['label'] = label
    style['color'] = 'pink'
    if override:
        style.update(override)
    return style


def _style_basis_set(node, override=None):
    label = "{}\n{}".format(
        _std_label(node),
        node.get_attribute(node, 'element', '')
    )
    style = {
        'label': label,
        'color': 'olive'
    }
    if override:
        style.update(override)
    return style


def _add_graphviz_node(graph, node, override=None, style_func=None):
    from aiida.orm import Code
    from aiida.orm import ProcessNode  

    if style_func is not None:
        node_style = style_func(node, override)
    elif isinstance(node, Code):
        node_style = _style_code(node, override)
    elif isinstance(node, ProcessNode  ):
        node_style = _style_calculation(node, override)
    elif is_data_instance(node, 'cif', allow_fail=True):
        node_style = _style_cif(node, override)
    else:
        node_style = _style_default(node, override)

    return graph.node("N{}".format(node.pk), **node_style)


def _add_graphviz_edge(graph, in_node, out_node, style=None):
    if style is None:
        style = {}
    return graph.edge("N{}".format(in_node.pk),
                      "N{}".format(out_node.pk), **style)


def _get_link_style(link_type):
    from aiida.common.links import LinkType
    if link_type in (LinkType.CREATE.value, LinkType.INPUT.value):
        style = 'solid'  # Solid lines and black colors
        # for CREATE and INPUT (The provenance graph)
        color = "0.0 0.0 0.0"
    elif link_type == LinkType.RETURN.value:
        style = 'solid'  # Dotted  lines of
        color = "blue"  # black color for Returns
    elif link_type == LinkType.CALL.value:
        style = 'bold'  # Bold lines and
        color = "0.0 1.0 1.0"  # Bright red for calls
    else:
        style = 'solid'  # Solid and
        color = "0.0 0.0 0.5"  # grey lines for unspecified links!

    return {
        'style': style,
        'color': color
    }


class Graph(object):
    """ a class to create graphviz graphs of the aiida node provenance """

    def __init__(self, engine=None, graph_attr=None, global_node_style=None):
        """ a class to create graphviz graphs of the aiida node provenance

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

        """
        from graphviz import Digraph

        self._graph = Digraph(engine=engine, graph_attr=graph_attr)
        self._nodes = set()
        self._edges = set()
        self._global_node_style = {}
        if global_node_style:
            self._global_node_style = global_node_style

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
        from aiida.orm import load_node
        if isinstance(node, int):
            return load_node(node)
        else:
            return node

    def add_node(self, node, style=None, overwrite=False):
        """add single node to the graph

        Parameters
        ----------
        node: int or Node
        style=None: dict or None
            graphviz style parameters
        overwrite=False: bool
            whether to overrite an existing node

        """
        node = self._load_node(node)
        style = {} if style is None else style
        style.update(self._global_node_style)
        if node.pk not in self.nodes or overwrite:
            _add_graphviz_node(self._graph, node, style)
            self._nodes.add(node.pk)

    def add_edge(self, in_node, out_node, style=None, overwrite=False):
        """add single node to the graph

        Parameters
        ----------
        in_node: int or Node
        out_node: int or Node
        style=None: dict or None
            graphviz style parameters
        overwrite=False: bool
            whether to overrite an existing node

        """
        in_node = self._load_node(in_node)
        if in_node.pk not in self._nodes:
            raise AssertionError(
                "the in_node must have already been added to the graph")
        out_node = self._load_node(out_node)
        if out_node.pk not in self._nodes:
            raise AssertionError(
                "the out_node must have already been added to the graph")
        style = {} if style is None else style
        if (in_node.pk, out_node.pk) not in self.edges or overwrite:
            self._edges.add((in_node.pk, out_node.pk))
            _add_graphviz_edge(self._graph, in_node, out_node, style)

    def add_inputs(self, node, link_labels=False, return_pks=True):
        from aiida.orm import Node
        from aiida.orm.querybuilder import QueryBuilder
        self.add_node(node)
        input_query = QueryBuilder(**{
            "path": [
                {
                    'cls': node.__class__,
                    "filters": {
                        "id": node.pk
                    },
                    'tag': "target"
                },
                {
                    'cls': Node,
                    'input_of': 'target',
                    'tag': "output",
                    'project': "*",
                    'edge_project': ('id', 'label', 'type')
                }
            ]
        })
        nodes = []
        for (tin_node, link_id, link_label, link_type
             ) in input_query.iterall():
            self.add_node(tin_node)
            style = _get_link_style(link_type)
            if link_labels:
                style['label'] = link_label
            self.add_edge(tin_node, node, style)
            nodes.append(tin_node.pk if return_pks else tin_node)

        return nodes

    def add_outputs(self, node, link_labels=False, return_pks=True):
        from aiida.orm import Node
        from aiida.orm.querybuilder import QueryBuilder

        self.add_node(node)

        output_query = QueryBuilder(**{
            "path": [
                {
                    'cls': node.__class__,
                    "filters": {
                        "id": node.pk
                    },
                    'tag': "target"
                },
                {
                    'cls': Node,
                    'output_of': 'target',
                    'tag': "output",
                    'project': "*",
                    'edge_project': ('id', 'label', 'type')
                }
            ]
        })
        nodes = []
        for (tout_node, link_id, link_label, link_type
             ) in output_query.iterall():
            self.add_node(tout_node)
            style = _get_link_style(link_type)
            if link_labels:
                style['label'] = link_label
            self.add_edge(node, tout_node, style)
            nodes.append(tout_node.pk if return_pks else tout_node)

        return nodes

    def recurse_descendants(self, origin, depth=None,
                            origin_style=(('style', 'filled'),
                                          ('color', 'lightblue')),
                            link_labels=False,
                            include_calculation_inputs=False):
        """add nodes and edges from an origin recursively following outputs

        Parameters
        ----------
        origin: int or class
        depth: None or int
            if not None, stop after travelling a certain depth into the graph
        origin_style: dict
        link_labels: bool
            label edges with the link label

        """
        from aiida.orm.calculation import ProcessNode  
        origin_node = self._load_node(origin)

        self.add_node(origin_node, style=dict(origin_style))

        last_nodes = [origin_node]
        depth = 0
        while last_nodes:
            depth += 1
            # checking of maximum descendant depth is set and applies.
            if depth is not None and depth > depth:
                break
            new_nodes = []
            for node in last_nodes:
                new_nodes.extend(self.add_outputs(
                    node, link_labels=link_labels, return_pks=False))
            last_nodes = new_nodes

            if include_calculation_inputs and isinstance(node, ProcessNode  ):
                self.add_inputs(node, link_labels=link_labels)

    def recurse_ancestors(self, origin, depth=None,
                          origin_style=(('style', 'filled'),
                                        ('color', 'lightblue')),
                          link_labels=False,
                          include_calculation_outputs=False):
        """add nodes and edges from an origin recursively following inputs

        Parameters
        ----------
        origin: int or class
        depth: None or int
            if not None, stop after travelling a certain depth into the graph
        origin_style: dict
        link_labels: bool
            label edges with the link label

        """
        from aiida.orm.calculation import ProcessNode  

        origin_node = self._load_node(origin)

        self.add_node(origin_node, style=dict(origin_style))

        last_nodes = [origin_node]
        depth = 0
        while last_nodes:
            depth += 1
            # checking of maximum descendant depth is set and applies.
            if depth is not None and depth > depth:
                break
            new_nodes = []
            for node in last_nodes:
                new_nodes.extend(self.add_inputs(
                    node, link_labels=link_labels, return_pks=False))
            last_nodes = new_nodes

            if include_calculation_outputs and isinstance(node, ProcessNode  ):
                self.add_outputs(node, link_labels=link_labels)

    def add_origin_to_target(self, origin, target_cls, target_filters=None,
                             include_target_inputs=False,
                             include_target_outputs=False,
                             origin_style=(('style', 'filled'),
                                           ('color', 'lightblue')),
                             link_labels=False):
        """add nodes and edges from an origin node to target nodes

        Parameters
        ----------
        origin: int or class
        target_cls: class
        target_filters=None: dict or None
        include_target_inputs=False: bool
        include_target_outputs=False: bool
        origin_style: dict
        link_labels: bool
            label edges with the link label


        """
        from aiida.orm.querybuilder import QueryBuilder

        origin_node = self._load_node(origin)

        if target_filters is None:
            target_filters = {}

        self.add_node(origin_node, style=dict(origin_style))

        query = QueryBuilder(**{
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
                          {'style': 'dashed', 'color': 'grey'})

            if include_target_inputs:
                self.add_inputs(target_node, link_labels=link_labels)

            if include_target_outputs:
                self.add_outputs(target_node, link_labels=link_labels)

    def add_origins_to_targets(self, origin_cls, target_cls,
                               origin_filters=None,
                               target_filters=None,
                               include_target_inputs=False,
                               include_target_outputs=False,
                               origin_style=(('style', 'filled'),
                                             ('color', 'lightblue')),
                               link_labels=False):
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
        link_labels: bool
            label edges with the link label

        """
        from aiida.orm.querybuilder import QueryBuilder

        if origin_filters is None:
            origin_filters = {}

        query = QueryBuilder(**{
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
                link_labels=link_labels)

