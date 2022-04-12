# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
""" provides functionality to create graphs of the AiiDa data providence,
*via* graphviz.
"""
import os
from types import MappingProxyType  # pylint: disable=no-name-in-module,useless-suppression
from typing import TYPE_CHECKING, Optional

from graphviz import Digraph

from aiida import orm
from aiida.common import LinkType
from aiida.manage import get_manager
from aiida.orm.utils.links import LinkPair
from aiida.tools.graph.graph_traversers import traverse_graph

if TYPE_CHECKING:
    from aiida.orm.implementation import StorageBackend

__all__ = ('Graph', 'default_link_styles', 'default_node_styles', 'pstate_node_styles', 'default_node_sublabels')


def default_link_styles(link_pair, add_label, add_type):
    # type: (LinkPair, bool, bool) -> dict
    """map link_pair to a graphviz edge style

    :param link_type: a LinkPair attribute
    :type link_type: aiida.orm.utils.links.LinkPair
    :param add_label: include link label
    :type add_label: bool
    :param add_type: include link type
    :type add_type: bool
    :rtype: dict
    """

    style = {
        LinkType.INPUT_CALC: {
            'style': 'solid',
            'color': '#000000'  # black
        },
        LinkType.INPUT_WORK: {
            'style': 'dashed',
            'color': '#000000'  # black
        },
        LinkType.CALL_CALC: {
            'style': 'dotted',
            'color': '#000000'  # black
        },
        LinkType.CALL_WORK: {
            'style': 'dotted',
            'color': '#000000'  # black
        },
        LinkType.CREATE: {
            'style': 'solid',
            'color': '#000000'  # black
        },
        LinkType.RETURN: {
            'style': 'dashed',
            'color': '#000000'  # black
        }
    }[link_pair.link_type]

    if add_label and not add_type:
        style['label'] = link_pair.link_label
    elif add_type and not add_label:
        style['label'] = link_pair.link_type.name
    elif add_label and add_type:
        style['label'] = f'{link_pair.link_type.name}\n{link_pair.link_label}'

    return style


def default_node_styles(node):
    """map a node to a graphviz node style

    :param node: the node to map
    :type node: aiida.orm.nodes.node.Node
    :rtype: dict
    """

    class_node_type = node.class_node_type

    try:
        default = node.get_style_default()
    except AttributeError:
        default = {
            'shape': 'ellipse',
            'style': 'filled',
            'fillcolor': '#8cd499ff',  # green,
            'penwidth': 0
        }

    node_type_map = {
        'data.core.code.Code.': {
            'shape': 'ellipse',
            'style': 'filled',
            'fillcolor': '#4ca4b9aa',  # blue
            'penwidth': 0
        },
        'process.calculation.calcjob.CalcJobNode.': {
            'shape': 'rectangle',
            'style': 'filled',
            'fillcolor': '#de707fff',  # red
            'penwidth': 0
        },
        'process.calculation.calcfunction.CalcFunctionNode.': {
            'shape': 'rectangle',
            'style': 'filled',
            'fillcolor': '#de707f77',  # red
            'penwidth': 0
        },
        'process.workflow.workchain.WorkChainNode.': {
            'shape': 'rectangle',
            'style': 'filled',
            'fillcolor': '#e38851ff',  # orange
            'penwidth': 0
        },
        'process.workflow.workfunction.WorkFunctionNode.': {
            'shape': 'rectangle',
            'style': 'filled',
            'fillcolor': '#e38851ff',  # orange
            'penwidth': 0
        }
    }

    node_style = node_type_map.get(class_node_type, default)

    return node_style


def pstate_node_styles(node):
    """map a process node to a graphviz node style

    :param node: the node to map
    :type node: aiida.orm.nodes.node.Node
    :rtype: dict
    """

    class_node_type = node.class_node_type

    default = {'shape': 'rectangle', 'pencolor': 'black'}

    process_map = {
        'process.calculation.calcjob.CalcJobNode.': {
            'shape': 'ellipse',
            'style': 'filled',
            'penwidth': 0,
            'fillcolor': '#ffffffff'
        },
        'process.calculation.calcfunction.CalcFunctionNode.': {
            'shape': 'ellipse',
            'style': 'filled',
            'penwidth': 0,
            'fillcolor': '#ffffffff'
        },
        'process.workflow.workchain.WorkChainNode.': {
            'shape': 'polygon',
            'sides': '6',
            'style': 'filled',
            'penwidth': 0,
            'fillcolor': '#ffffffff'
        },
        'process.workflow.workfunction.WorkFunctionNode.': {
            'shape': 'polygon',
            'sides': '6',
            'style': 'filled',
            'penwidth': 0,
            'fillcolor': '#ffffffff'
        }
    }

    node_style = process_map.get(class_node_type, default)

    if isinstance(node, orm.ProcessNode):
        # style process node, based on success/failure of process
        if node.is_failed or node.is_excepted or node.is_killed:
            node_style['fillcolor'] = '#de707fff'  # red
        elif node.is_finished_ok:
            node_style['fillcolor'] = '#8cd499ff'  # green
        else:
            # Note: this conditional will hit the states CREATED, WAITING and RUNNING
            node_style['fillcolor'] = '#e38851ff'  # orange

    return node_style


_OVERRIDE_STYLES_DICT = {
    'ignore_node': {
        'color': 'lightgray',
        'fillcolor': 'white',
        'penwidth': 2,
    },
    'origin_node': {
        'color': 'red',
        'penwidth': 6,
    },
}


def default_node_sublabels(node):
    """function mapping nodes to a sublabel
    (e.g. specifying some attribute values)

    :param node: the node to map
    :type node: aiida.orm.nodes.node.Node
    :rtype: str
    """
    # pylint: disable=too-many-branches

    class_node_type = node.class_node_type
    if class_node_type == 'data.core.int.Int.':
        sublabel = f"value: {node.base.attributes.get('value', '')}"
    elif class_node_type == 'data.core.float.Float.':
        sublabel = f"value: {node.base.attributes.get('value', '')}"
    elif class_node_type == 'data.core.str.Str.':
        sublabel = f"{node.base.attributes.get('value', '')}"
    elif class_node_type == 'data.core.bool.Bool.':
        sublabel = f"{node.base.attributes.get('value', '')}"
    elif class_node_type == 'data.core.code.Code.':
        sublabel = f'{os.path.basename(node.get_execname())}@{node.computer.label}'
    elif class_node_type == 'data.core.singlefile.SinglefileData.':
        sublabel = node.filename
    elif class_node_type == 'data.core.remote.RemoteData.':
        sublabel = f'@{node.computer.label}'
    elif class_node_type == 'data.core.structure.StructureData.':
        sublabel = node.get_formula()
    elif class_node_type == 'data.core.cif.CifData.':
        formulae = [str(f).replace(' ', '') for f in node.get_formulae() or []]
        sg_numbers = [str(s) for s in node.get_spacegroup_numbers() or []]
        sublabel_lines = []
        if formulae:
            sublabel_lines.append(', '.join(formulae))
        if sg_numbers:
            sublabel_lines.append(', '.join(sg_numbers))
        sublabel = '; '.join(sublabel_lines)
    elif class_node_type == 'data.core.upf.UpfData.':
        sublabel = f"{node.base.attributes.get('element', '')}"
    elif isinstance(node, orm.ProcessNode):
        sublabel = []
        if node.process_state is not None:
            sublabel.append(f'State: {node.process_state.value}')
        if node.exit_status is not None:
            sublabel.append(f'Exit Code: {node.exit_status}')
        sublabel = '\n'.join(sublabel)
    else:
        sublabel = node.get_description()

    return sublabel


def get_node_id_label(node, id_type):
    """return an identifier str for the node """
    if id_type == 'pk':
        return node.pk
    if id_type == 'uuid':
        return node.uuid.split('-')[0]
    if id_type == 'label':
        return node.label
    raise ValueError(f'node_id_type not recognised: {id_type}')


def _get_node_label(node, id_type='pk'):
    """return a label text of node and the return format is '<NodeType> (<id>)'."""
    if isinstance(node, orm.Data):
        label = f'{node.__class__.__name__} ({get_node_id_label(node, id_type)})'
    elif isinstance(node, orm.ProcessNode):
        label = '{} ({})'.format(
            node.__class__.__name__ if node.process_label is None else node.process_label,
            get_node_id_label(node, id_type)
        )
    else:
        raise TypeError(f'Unknown type: {type(node)}')

    return label


def _add_graphviz_node(
    graph, node, node_style_func, node_sublabel_func, style_override=None, include_sublabels=True, id_type='pk'
):
    """create a node in the graph

    The first line of the node text is always '<node.name> (<node.pk>)'.
    Then, if ``include_sublabels=True``, subsequent lines are added,
    which are node type dependant.

    :param graph: the graphviz.Digraph to add the node to
    :param node: the node to add
    :type node: aiida.orm.nodes.node.Node
    :param node_style_func: callable mapping a node instance to a dictionary defining the graphviz node style
    :param node_sublabel_func: callable mapping a node instance to a sub-label for the node text
    :param style_override: style dictionary, whose keys will override the final computed style
    :type style_override: None or dict
    :param include_sublabels: whether to include the sublabels for nodes
    :type include_sublabels: bool
    :param id_type: the type of identifier to use for node labels ('pk' or 'uuid')
    :type id_type: str

    nodes are styled based on the node type

    For subclasses of Data, the ``class_node_type`` attribute is used
    for mapping to type specific styles

    For subclasses of ProcessNode, we choose styles to distinguish between
    types, and also color the nodes for successful/failed processes
    """
    # pylint: disable=too-many-arguments
    node_style = node_style_func(node)
    label_list = [_get_node_label(node, id_type)]

    if include_sublabels:
        sublabel = node_sublabel_func(node)
        if sublabel:
            label_list.append(sublabel)

    node_style['label'] = '\n'.join(label_list)

    if style_override is not None:
        node_style.update(style_override)

    # coerce node style values to strings, required by graphviz
    node_style = {k: str(v) for k, v in node_style.items()}

    return graph.node(f'N{node.pk}', **node_style)


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

    # coerce node style values to strings
    style = {k: str(v) for k, v in style.items()}

    return graph.edge(f'N{in_node.pk}', f'N{out_node.pk}', **style)


class Graph:
    """a class to create graphviz graphs of the AiiDA node provenance"""

    def __init__(
        self,
        engine=None,
        graph_attr=None,
        global_node_style=None,
        global_edge_style=None,
        include_sublabels=True,
        link_style_fn=None,
        node_style_fn=None,
        node_sublabel_fn=None,
        node_id_type='pk',
        backend: Optional['StorageBackend'] = None
    ):
        """a class to create graphviz graphs of the AiiDA node provenance

        Nodes and edges, are cached, so that they are only created once

        :param engine: the graphviz engine, e.g. dot, circo (Default value = None)
        :type engine: str or None
        :param graph_attr: attributes for the graphviz graph (Default value = None)
        :type graph_attr: dict or None
        :param global_node_style: styles which will be added to all nodes.
            Note this will override any builtin attributes (Default value = None)
        :type global_node_style: dict or None
        :param global_edge_style: styles which will be added to all edges.
            Note this will override any builtin attributes (Default value = None)
        :type global_edge_style: dict or None
        :param include_sublabels: if True, the note text will include node dependant sub-labels (Default value = True)
        :type include_sublabels: bool
        :param link_style_fn: callable mapping LinkType to graphviz style dict;
            link_style_fn(link_type) -> dict (Default value = None)
        :param node_sublabel_fn: callable mapping nodes to a graphviz style dict;
            node_sublabel_fn(node) -> dict (Default value = None)
        :param node_sublabel_fn: callable mapping data node to a sublabel (e.g. specifying some attribute values)
            node_sublabel_fn(node) -> str (Default value = None)
        :param node_id_type: the type of identifier to within the node text ('pk', 'uuid' or 'label')
        :type node_id_type: str
        """
        # pylint: disable=too-many-arguments

        self._graph = Digraph(engine=engine, graph_attr=graph_attr)
        self._nodes = set()
        self._edges = set()
        self._global_node_style = global_node_style or {}
        self._global_edge_style = global_edge_style or {}
        self._include_sublabels = include_sublabels
        self._link_styles = link_style_fn or default_link_styles
        self._node_styles = node_style_fn or default_node_styles
        self._node_sublabels = node_sublabel_fn or default_node_sublabels
        self._node_id_type = node_id_type
        self._backend = backend or get_manager().get_profile_storage()

        self._ignore_node_style = _OVERRIDE_STYLES_DICT['ignore_node']
        self._origin_node_style = _OVERRIDE_STYLES_DICT['origin_node']

    @property
    def backend(self) -> 'StorageBackend':
        """The backend used to create the graph"""
        return self._backend

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

    def _load_node(self, node):
        """ load a node (if not already loaded)

        :param node: node or node pk/uuid
        :type node: int or str or aiida.orm.nodes.node.Node
        :returns: aiida.orm.nodes.node.Node
        """
        if isinstance(node, int):
            return orm.Node.collection(self._backend).get(pk=node)
        if isinstance(node, str):
            return orm.Node.collection(self._backend).get(uuid=node)
        return node

    @staticmethod
    def _default_link_types(link_types):
        """If link_types is empty, it will return all the links_types

        :param links: iterable with the link_types ()
        :returns: list of :py:class:`aiida.common.links.LinkType`
        """
        if not link_types:
            all_link_types = [LinkType.CREATE]
            all_link_types.append(LinkType.RETURN)
            all_link_types.append(LinkType.INPUT_CALC)
            all_link_types.append(LinkType.INPUT_WORK)
            all_link_types.append(LinkType.CALL_CALC)
            all_link_types.append(LinkType.CALL_WORK)
            return all_link_types

        return link_types

    def add_node(self, node, style_override=None, overwrite=False):
        """add single node to the graph

        :param node: node or node pk/uuid
        :type node: int or str or aiida.orm.nodes.node.Node
        :param style_override: graphviz style parameters that will override default values
        :type style_override: dict or None
        :param overwrite: whether to overrite an existing node (Default value = False)
        :type overwrite: bool
        """
        node = self._load_node(node)
        style = {} if style_override is None else dict(style_override)
        style.update(self._global_node_style)
        if node.pk not in self._nodes or overwrite:
            _add_graphviz_node(
                self._graph,
                node,
                node_style_func=self._node_styles,
                node_sublabel_func=self._node_sublabels,
                style_override=style,
                include_sublabels=self._include_sublabels,
                id_type=self._node_id_type
            )
            self._nodes.add(node.pk)
        return node

    def add_edge(self, in_node, out_node, link_pair=None, style=None, overwrite=False):
        """add single node to the graph

        :param in_node: node or node pk/uuid
        :type in_node: int or aiida.orm.nodes.node.Node
        :param out_node: node or node pk/uuid
        :type out_node: int or str or aiida.orm.nodes.node.Node
        :param link_pair: defining the relationship between the nodes
        :type link_pair: None or aiida.orm.utils.links.LinkPair
        :param style: graphviz style parameters (Default value = None)
        :type style: dict or None
        :param overwrite: whether to overrite existing edge (Default value = False)
        :type overwrite: bool
        """
        in_node = self._load_node(in_node)
        if in_node.pk not in self._nodes:
            raise AssertionError(f'in_node pk={in_node.pk} must have already been added to the graph')
        out_node = self._load_node(out_node)
        if out_node.pk not in self._nodes:
            raise AssertionError(f'out_node pk={out_node.pk} must have already been added to the graph')

        if (in_node.pk, out_node.pk, link_pair) in self._edges and not overwrite:
            return

        style = {} if style is None else style
        self._edges.add((in_node.pk, out_node.pk, link_pair))
        style.update(self._global_edge_style)

        _add_graphviz_edge(self._graph, in_node, out_node, style)

    @staticmethod
    def _convert_link_types(link_types):
        """convert link types, which may be strings, to a member of LinkType"""
        if link_types is None:
            return None
        if isinstance(link_types, str):
            link_types = [link_types]
        link_types = tuple(getattr(LinkType, l.upper()) if isinstance(l, str) else l for l in link_types)
        return link_types

    def add_incoming(self, node, link_types=(), annotate_links=None, return_pks=True):
        """add nodes and edges for incoming links to a node

        :param node: node or node pk/uuid
        :type node: aiida.orm.nodes.node.Node or int
        :param link_types: filter by link types (Default value = ())
        :type link_types: str or tuple[str] or aiida.common.links.LinkType or tuple[aiida.common.links.LinkType]
        :param annotate_links: label edges with the link 'label', 'type' or 'both' (Default value = None)
        :type annotate_links: bool or str
        :param return_pks: whether to return a list of nodes, or list of node pks (Default value = True)
        :type return_pks: bool
        :returns: list of nodes or node pks
        """
        if annotate_links not in [None, False, 'label', 'type', 'both']:
            raise ValueError(
                f'annotate_links must be one of False, "label", "type" or "both"\ninstead, it is: {annotate_links}'
            )

        # incoming nodes are found traversing backwards
        node_pk = self._load_node(node).pk
        valid_link_types = self._default_link_types(link_types)
        valid_link_types = self._convert_link_types(valid_link_types)
        traversed_graph = traverse_graph(
            (node_pk,),
            max_iterations=1,
            get_links=True,
            backend=self.backend,
            links_backward=valid_link_types,
        )

        traversed_nodes = orm.QueryBuilder(backend=self.backend).append(
            orm.Node,
            filters={'id': {
                'in': traversed_graph['nodes']
            }},
            project=['id', '*'],
            tag='node',
        )
        traversed_nodes = {query_result[0]: query_result[1] for query_result in traversed_nodes.all()}

        for _, traversed_node in traversed_nodes.items():
            self.add_node(traversed_node, style_override=None)

        for link in traversed_graph['links']:
            source_node = traversed_nodes[link.source_id]
            target_node = traversed_nodes[link.target_id]
            link_pair = LinkPair(self._convert_link_types(link.link_type)[0], link.link_label)
            link_style = self._link_styles(
                link_pair, add_label=annotate_links in ['label', 'both'], add_type=annotate_links in ['type', 'both']
            )
            self.add_edge(source_node, target_node, link_pair, style=link_style)

        if return_pks:
            return list(traversed_nodes.keys())
        # else:
        return list(traversed_nodes.values())

    def add_outgoing(self, node, link_types=(), annotate_links=None, return_pks=True):
        """add nodes and edges for outgoing links to a node

        :param node: node or node pk
        :type node: aiida.orm.nodes.node.Node or int
        :param link_types: filter by link types (Default value = ())
        :type link_types: str or tuple[str] or aiida.common.links.LinkType or tuple[aiida.common.links.LinkType]
        :param annotate_links: label edges with the link 'label', 'type' or 'both' (Default value = None)
        :type annotate_links: bool or str
        :param return_pks: whether to return a list of nodes, or list of node pks (Default value = True)
        :type return_pks: bool
        :returns: list of nodes or node pks
        """
        if annotate_links not in [None, False, 'label', 'type', 'both']:
            raise ValueError(
                f'annotate_links must be one of False, "label", "type" or "both"\ninstead, it is: {annotate_links}'
            )

        # outgoing nodes are found traversing forwards
        node_pk = self._load_node(node).pk
        valid_link_types = self._default_link_types(link_types)
        valid_link_types = self._convert_link_types(valid_link_types)
        traversed_graph = traverse_graph(
            (node_pk,),
            max_iterations=1,
            get_links=True,
            backend=self.backend,
            links_forward=valid_link_types,
        )

        traversed_nodes = orm.QueryBuilder(backend=self.backend).append(
            orm.Node,
            filters={'id': {
                'in': traversed_graph['nodes']
            }},
            project=['id', '*'],
            tag='node',
        )
        traversed_nodes = {query_result[0]: query_result[1] for query_result in traversed_nodes.all()}

        for _, traversed_node in traversed_nodes.items():
            self.add_node(traversed_node, style_override=None)

        for link in traversed_graph['links']:
            source_node = traversed_nodes[link.source_id]
            target_node = traversed_nodes[link.target_id]
            link_pair = LinkPair(self._convert_link_types(link.link_type)[0], link.link_label)
            link_style = self._link_styles(
                link_pair, add_label=annotate_links in ['label', 'both'], add_type=annotate_links in ['type', 'both']
            )
            self.add_edge(source_node, target_node, link_pair, style=link_style)

        if return_pks:
            return list(traversed_nodes.keys())
        # else:
        return list(traversed_nodes.values())

    def recurse_descendants(
        self,
        origin,
        depth=None,
        link_types=(),
        annotate_links=False,
        origin_style=MappingProxyType(_OVERRIDE_STYLES_DICT['origin_node']),
        include_process_inputs=False,
        highlight_classes=None,
    ):
        """add nodes and edges from an origin recursively,
        following outgoing links

        :param origin: node or node pk/uuid
        :type origin: aiida.orm.nodes.node.Node or int
        :param depth: if not None, stop after travelling a certain depth into the graph (Default value = None)
        :type depth: None or int
        :param link_types: filter by subset of link types (Default value = ())
        :type link_types: tuple or str
        :param annotate_links: label edges with the link 'label', 'type' or 'both' (Default value = False)
        :type annotate_links: bool or str
        :param origin_style: node style map for origin node (Default value = None)
        :type origin_style: None or dict
        :param include_calculation_inputs: include incoming links for all processes (Default value = False)
        :type include_calculation_inputs: bool
        :param highlight_classes: target class in exported graph expected to be highlight and
            other nodes are decolorized (Default value = None)
        :typle highlight_classes: tuple of class or class
        """
        # pylint: disable=too-many-arguments,too-many-locals
        # Get graph traversal rules where the given link types and direction are all set to True,
        # and all others are set to False
        origin_pk = self._load_node(origin).pk
        valid_link_types = self._default_link_types(link_types)
        valid_link_types = self._convert_link_types(valid_link_types)
        traversed_graph = traverse_graph(
            (origin_pk,),
            max_iterations=depth,
            get_links=True,
            backend=self.backend,
            links_forward=valid_link_types,
        )

        # Traverse backward along input_work and input_calc links from all nodes traversed in the previous step
        # and join the result with the original traversed graph. This includes calculation inputs in the Graph
        if include_process_inputs:
            traversed_outputs = traverse_graph(
                traversed_graph['nodes'],
                max_iterations=1,
                get_links=True,
                backend=self.backend,
                links_backward=[LinkType.INPUT_WORK, LinkType.INPUT_CALC]
            )
            traversed_graph['nodes'] = traversed_graph['nodes'].union(traversed_outputs['nodes'])
            traversed_graph['links'] = traversed_graph['links'].union(traversed_outputs['links'])

        # Do one central query for all nodes in the Graph and generate a {id: Node} dictionary
        traversed_nodes = orm.QueryBuilder(backend=self.backend).append(
            orm.Node,
            filters={'id': {
                'in': traversed_graph['nodes']
            }},
            project=['id', '*'],
            tag='node',
        )
        traversed_nodes = {query_result[0]: query_result[1] for query_result in traversed_nodes.all()}

        # Pop the origin node and add it to the graph, applying custom styling
        origin_node = traversed_nodes.pop(origin_pk)
        self.add_node(origin_node, style_override=origin_style)

        # Add all traversed nodes to the graph with default styling
        for _, traversed_node in traversed_nodes.items():
            node_label = _get_node_label(traversed_node)
            if highlight_classes and not node_label.split()[0] in highlight_classes:
                self.add_node(traversed_node, style_override=self._ignore_node_style)
            else:
                self.add_node(traversed_node, style_override=None)

        # Add the origin node back into traversed nodes so it can be found for adding edges
        traversed_nodes[origin_pk] = origin_node

        # Add all links to the Graph, using the {id: Node} dictionary for queryless Node retrieval, applying
        # appropriate styling
        for link in traversed_graph['links']:
            source_node = traversed_nodes[link.source_id]
            target_node = traversed_nodes[link.target_id]
            link_pair = LinkPair(self._convert_link_types(link.link_type)[0], link.link_label)
            link_style = self._link_styles(
                link_pair, add_label=annotate_links in ['label', 'both'], add_type=annotate_links in ['type', 'both']
            )
            self.add_edge(source_node, target_node, link_pair, style=link_style)

    def recurse_ancestors(
        self,
        origin,
        depth=None,
        link_types=(),
        annotate_links=False,
        origin_style=MappingProxyType(_OVERRIDE_STYLES_DICT['origin_node']),
        include_process_outputs=False,
        highlight_classes=None,
    ):
        """add nodes and edges from an origin recursively,
        following incoming links

        :param origin: node or node pk/uuid
        :type origin: aiida.orm.nodes.node.Node or int
        :param depth: if not None, stop after travelling a certain depth into the graph (Default value = None)
        :type depth: None or int
        :param link_types: filter by subset of link types (Default value = ())
        :type link_types: tuple or str
        :param annotate_links: label edges with the link 'label', 'type' or 'both' (Default value = False)
        :type annotate_links: bool
        :param origin_style: node style map for origin node (Default value = None)
        :type origin_style: None or dict
        :param include_process_outputs:  include outgoing links for all processes (Default value = False)
        :type include_process_outputs: bool
        :param highlight_classes:  class label (as displayed in the graph, e.g. 'StructureData', 'FolderData', etc.)
            to be highlight and other nodes are decolorized (Default value = None)
        :typle highlight_classes: list or tuple of str
        """
        # pylint: disable=too-many-arguments,too-many-locals
        # Get graph traversal rules where the given link types and direction are all set to True,
        # and all others are set to False
        origin_pk = self._load_node(origin).pk
        valid_link_types = self._default_link_types(link_types)
        valid_link_types = self._convert_link_types(valid_link_types)
        traversed_graph = traverse_graph(
            (origin_pk,),
            max_iterations=depth,
            get_links=True,
            backend=self.backend,
            links_backward=valid_link_types,
        )

        # Traverse forward along input_work and input_calc links from all nodes traversed in the previous step
        # and join the result with the original traversed graph. This includes calculation outputs in the Graph
        if include_process_outputs:
            traversed_outputs = traverse_graph(
                traversed_graph['nodes'],
                max_iterations=1,
                get_links=True,
                backend=self.backend,
                links_forward=[LinkType.CREATE, LinkType.RETURN]
            )
            traversed_graph['nodes'] = traversed_graph['nodes'].union(traversed_outputs['nodes'])
            traversed_graph['links'] = traversed_graph['links'].union(traversed_outputs['links'])

        # Do one central query for all nodes in the Graph and generate a {id: Node} dictionary
        traversed_nodes = orm.QueryBuilder(backend=self.backend).append(
            orm.Node,
            filters={'id': {
                'in': traversed_graph['nodes']
            }},
            project=['id', '*'],
            tag='node',
        )
        traversed_nodes = {query_result[0]: query_result[1] for query_result in traversed_nodes.all()}

        # Pop the origin node and add it to the graph, applying custom styling
        origin_node = traversed_nodes.pop(origin_pk)
        self.add_node(origin_node, style_override=origin_style)

        # Add all traversed nodes to the graph with default styling
        for _, traversed_node in traversed_nodes.items():
            node_label = _get_node_label(traversed_node)
            if highlight_classes and not node_label.split()[0] in highlight_classes:
                self.add_node(traversed_node, style_override=self._ignore_node_style)
            else:
                self.add_node(traversed_node, style_override=None)

        # Add the origin node back into traversed nodes so it can be found for adding edges
        traversed_nodes[origin_pk] = origin_node

        # Add all links to the Graph, using the {id: Node} dictionary for queryless Node retrieval, applying
        # appropriate styling
        for link in traversed_graph['links']:
            source_node = traversed_nodes[link.source_id]
            target_node = traversed_nodes[link.target_id]
            link_pair = LinkPair(self._convert_link_types(link.link_type)[0], link.link_label)
            link_style = self._link_styles(
                link_pair, add_label=annotate_links in ['label', 'both'], add_type=annotate_links in ['type', 'both']
            )
            self.add_edge(source_node, target_node, link_pair, style=link_style)

    def add_origin_to_targets(
        self,
        origin,
        target_cls,
        target_filters=None,
        include_target_inputs=False,
        include_target_outputs=False,
        origin_style=(),
        annotate_links=False
    ):
        """Add nodes and edges from an origin node to all nodes of a target node class.

        :param origin: node or node pk/uuid
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

        query = orm.QueryBuilder(
            backend=self.backend,
            **{
                'path': [{
                    'cls': origin_node.__class__,
                    'filters': {
                        'id': origin_node.pk
                    },
                    'tag': 'origin'
                }, {
                    'cls': target_cls,
                    'filters': target_filters,
                    'with_ancestors': 'origin',
                    'tag': 'target',
                    'project': '*'
                }]
            }
        )

        for (target_node,) in query.iterall():
            self.add_node(target_node)
            self.add_edge(origin_node, target_node, style={'style': 'dashed', 'color': 'grey'})

            if include_target_inputs:
                self.add_incoming(target_node, annotate_links=annotate_links)

            if include_target_outputs:
                self.add_outgoing(target_node, annotate_links=annotate_links)

    def add_origins_to_targets(
        self,
        origin_cls,
        target_cls,
        origin_filters=None,
        target_filters=None,
        include_target_inputs=False,
        include_target_outputs=False,
        origin_style=(),
        annotate_links=False
    ):
        """Add nodes and edges from all nodes of an origin class to all node of a target node class.

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

        query = orm.QueryBuilder(
            backend=self.backend,
            **{'path': [{
                'cls': origin_cls,
                'filters': origin_filters,
                'tag': 'origin',
                'project': '*'
            }]}
        )

        for (node,) in query.iterall():
            self.add_origin_to_targets(
                node,
                target_cls,
                target_filters=target_filters,
                include_target_inputs=include_target_inputs,
                include_target_outputs=include_target_outputs,
                origin_style=origin_style,
                annotate_links=annotate_links
            )
