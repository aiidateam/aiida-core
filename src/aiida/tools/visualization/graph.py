###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""provides functionality to create graphs of the AiiDa data providence,
*via* graphviz.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, Callable, Literal, Mapping, Protocol, Sequence

from graphviz import Digraph

from aiida import orm
from aiida.common import LinkType
from aiida.common.utils import DEFAULT_FILTER_SIZE, batch_iter
from aiida.manage import get_manager
from aiida.orm.utils.links import LinkPair
from aiida.tools.graph.graph_traversers import traverse_graph

if TYPE_CHECKING:
    from aiida.orm.implementation import StorageBackend

__all__ = ('Graph', 'default_link_styles', 'default_node_styles', 'default_node_sublabels', 'pstate_node_styles')

LinkAnnotateType = Literal[None, 'label', 'type', 'both']
IdentifierType = Literal['pk', 'uuid', 'label']


class LinkStyleFunc(Protocol):
    """Protocol for a link style function"""

    def __call__(self, link_pair: LinkPair, add_label: bool, add_type: bool) -> dict: ...


def default_link_styles(link_pair: LinkPair, add_label: bool, add_type: bool) -> dict:
    """Map link_pair to a graphviz edge style

    :param link_type: a LinkPair attribute
    :param add_label: include link label
    :param add_type: include link type
    """
    style = {
        LinkType.INPUT_CALC: {
            'style': 'solid',
            'color': '#000000',  # black
        },
        LinkType.INPUT_WORK: {
            'style': 'dashed',
            'color': '#000000',  # black
        },
        LinkType.CALL_CALC: {
            'style': 'dotted',
            'color': '#000000',  # black
        },
        LinkType.CALL_WORK: {
            'style': 'dotted',
            'color': '#000000',  # black
        },
        LinkType.CREATE: {
            'style': 'solid',
            'color': '#000000',  # black
        },
        LinkType.RETURN: {
            'style': 'dashed',
            'color': '#000000',  # black
        },
    }[link_pair.link_type]

    if add_label and not add_type:
        style['label'] = link_pair.link_label
    elif add_type and not add_label:
        style['label'] = link_pair.link_type.name
    elif add_label and add_type:
        style['label'] = f'{link_pair.link_type.name}\n{link_pair.link_label}'

    return style


def default_node_styles(node: orm.Node) -> dict:
    """Map a node to a graphviz node style

    :param node: the node to map
    """
    class_node_type = node.class_node_type

    try:
        default = node.get_style_default()
    except AttributeError:
        default = {
            'shape': 'ellipse',
            'style': 'filled',
            'fillcolor': '#8cd499ff',  # green,
            'penwidth': 0,
        }

    node_type_map = {
        'data.core.code.Code.': {
            'shape': 'ellipse',
            'style': 'filled',
            'fillcolor': '#4ca4b9aa',  # blue
            'penwidth': 0,
        },
        'process.calculation.calcjob.CalcJobNode.': {
            'shape': 'rectangle',
            'style': 'filled',
            'fillcolor': '#de707fff',  # red
            'penwidth': 0,
        },
        'process.calculation.calcfunction.CalcFunctionNode.': {
            'shape': 'rectangle',
            'style': 'filled',
            'fillcolor': '#de707f77',  # red
            'penwidth': 0,
        },
        'process.workflow.workchain.WorkChainNode.': {
            'shape': 'rectangle',
            'style': 'filled',
            'fillcolor': '#e38851ff',  # orange
            'penwidth': 0,
        },
        'process.workflow.workfunction.WorkFunctionNode.': {
            'shape': 'rectangle',
            'style': 'filled',
            'fillcolor': '#e38851ff',  # orange
            'penwidth': 0,
        },
    }

    node_style = node_type_map.get(class_node_type, default)

    return node_style


def pstate_node_styles(node: orm.Node) -> dict:
    """Map a process node to a graphviz node style

    :param node: the node to map
    """
    class_node_type = node.class_node_type

    default = {'shape': 'rectangle', 'pencolor': 'black'}

    process_map = {
        'process.calculation.calcjob.CalcJobNode.': {
            'shape': 'ellipse',
            'style': 'filled',
            'penwidth': 0,
            'fillcolor': '#ffffffff',
        },
        'process.calculation.calcfunction.CalcFunctionNode.': {
            'shape': 'ellipse',
            'style': 'filled',
            'penwidth': 0,
            'fillcolor': '#ffffffff',
        },
        'process.workflow.workchain.WorkChainNode.': {
            'shape': 'polygon',
            'sides': '6',
            'style': 'filled',
            'penwidth': 0,
            'fillcolor': '#ffffffff',
        },
        'process.workflow.workfunction.WorkFunctionNode.': {
            'shape': 'polygon',
            'sides': '6',
            'style': 'filled',
            'penwidth': 0,
            'fillcolor': '#ffffffff',
        },
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


def _default_ignore_node_styles() -> dict:
    """Return the default style for ignored nodes."""
    return {
        'color': 'lightgray',
        'fillcolor': 'white',
        'penwidth': 2,
    }


def _default_origin_node_styles() -> dict:
    """Return the default style for origin nodes."""
    return {
        'color': 'red',
        'penwidth': 6,
    }


def default_node_sublabels(node: orm.Node) -> str:
    """Function mapping nodes to a sub-label
    (e.g. specifying some attribute values)

    :param node: the node to map
    """
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
        label = '?' if node.computer is None else node.computer.label
        sublabel = f'{os.path.basename(node.get_execname())}@{label}'
    elif class_node_type == 'data.core.singlefile.SinglefileData.':
        sublabel = node.filename
    elif class_node_type == 'data.core.remote.RemoteData.':
        sublabel = f'@{node.computer.label}' if node.computer is not None else '@?'
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
        sublabel_list = []
        if node.process_state is not None:
            sublabel_list.append(f'State: {node.process_state.value}')
        if node.exit_status is not None:
            sublabel_list.append(f'Exit Code: {node.exit_status}')
        sublabel = '\n'.join(sublabel_list)
    else:
        sublabel = node.get_description()

    return sublabel


NODE_IDENTIFIER_TO_LABEL = {
    'pk': lambda node: str(node.pk),
    'uuid': lambda node: node.uuid.split('-')[0],
    'label': lambda node: node.label,
}


def get_node_id_label(node: orm.Node, id_type: IdentifierType | list[IdentifierType]) -> str:
    """Return an identifier str for the node"""

    id_types = id_type if isinstance(id_type, (list, tuple)) else [id_type]

    try:
        return '|'.join(NODE_IDENTIFIER_TO_LABEL[key](node) for key in id_types)
    except KeyError as exception:
        raise ValueError(f'`{id_type}` is not a valid `node_id_type`, choose from: pk, uuid, label') from exception


def _get_node_label(node: orm.Node, id_type: IdentifierType | list[IdentifierType] = 'pk') -> str:
    """Return a label text of node and the return format is '<NodeType> (<id>)'."""
    if isinstance(node, orm.Data):
        label = f'{node.__class__.__name__} ({get_node_id_label(node, id_type)})'
    elif isinstance(node, orm.ProcessNode):
        label = '{} ({})'.format(
            node.__class__.__name__ if node.process_label is None else node.process_label,
            get_node_id_label(node, id_type),
        )
    else:
        raise TypeError(f'Unknown type: {type(node)}')

    return label


def _add_graphviz_node(
    graph: Digraph,
    node: orm.Node,
    node_style_func,
    node_sublabel_func,
    style_override: None | dict = None,
    include_sublabels: bool = True,
    id_type: IdentifierType | list[IdentifierType] = 'pk',
):
    """Create a node in the graph

    The first line of the node text is always '<node.name> (<node.pk>)'.
    Then, if ``include_sublabels=True``, subsequent lines are added,
    which are node type dependant.

    :param graph: the graphviz.Digraph to add the node to
    :param node: the node to add
    :param node_style_func: callable mapping a node instance to a dictionary defining the graphviz node style
    :param node_sublabel_func: callable mapping a node instance to a sub-label for the node text
    :param style_override: style dictionary, whose keys will override the final computed style
    :param include_sublabels: whether to include the sublabels for nodes
    :param id_type: the type of identifier to use for node labels

    Nodes are styled based on the node type

    For subclasses of Data, the ``class_node_type`` attribute is used
    for mapping to type specific styles

    For subclasses of ProcessNode, we choose styles to distinguish between
    types, and also color the nodes for successful/failed processes
    """
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


def _add_graphviz_edge(graph: Digraph, in_node: orm.Node, out_node: orm.Node, style: dict | None = None) -> dict:
    """Add graphviz edge between two nodes

    :param graph: the graphviz.DiGraph to add the edge to
    :param in_node: the head node
    :param out_node: the tail node
    :param style: the graphviz style
    """
    if style is None:
        style = {}

    # coerce node style values to strings
    style = {k: str(v) for k, v in style.items()}

    return graph.edge(f'N{in_node.pk}', f'N{out_node.pk}', **style)


class Graph:
    """A class to create graphviz graphs of the AiiDA node provenance."""

    def __init__(
        self,
        engine: str | None = None,
        graph_attr: dict | None = None,
        global_node_style: dict | None = None,
        global_edge_style: dict | None = None,
        include_sublabels: bool = True,
        link_style_fn: LinkStyleFunc | None = None,
        node_style_fn: Callable[[orm.Node], dict] | None = None,
        node_sublabel_fn: Callable[[orm.Node], str] | None = None,
        node_id_type: IdentifierType | list[IdentifierType] = 'pk',
        backend: StorageBackend | None = None,
    ):
        """A class to create graphviz graphs of the AiiDA node provenance

        Nodes and edges, are cached, so that they are only created once

        :param engine: the graphviz engine, e.g. dot, circo
        :param graph_attr: attributes for the graphviz graph
        :param global_node_style: styles which will be added to all nodes.
            Note this will override any builtin attributes
        :param global_edge_style: styles which will be added to all edges.
            Note this will override any builtin attributes
        :param include_sublabels: if True, the note text will include node dependant sub-labels
        :param link_style_fn: callable mapping LinkType to graphviz style dict;
            link_style_fn(link_type, add_label, add_type) -> dict
        :param node_sublabel_fn: callable mapping nodes to a graphviz style dict;
            node_sublabel_fn(node) -> dict
        :param node_sublabel_fn: callable mapping data node to a sublabel (e.g. specifying some attribute values)
            node_sublabel_fn(node) -> str
        :param node_id_type: the type of identifier to within the node text
        """
        self._graph = Digraph(engine=engine, graph_attr=graph_attr)
        self._nodes: set[int] = set()
        self._edges: set[tuple[int, int, None | LinkPair]] = set()
        self._global_node_style = global_node_style or {}
        self._global_edge_style = global_edge_style or {}
        self._include_sublabels = include_sublabels
        self._link_styles = link_style_fn or default_link_styles
        self._node_styles = node_style_fn or default_node_styles
        self._node_sublabels = node_sublabel_fn or default_node_sublabels
        self._node_id_type = node_id_type
        self._backend = backend or get_manager().get_profile_storage()

        self._ignore_node_style = _default_ignore_node_styles()
        self._origin_node_style = _default_origin_node_styles()

    @property
    def backend(self) -> StorageBackend:
        """The backend used to create the graph"""
        return self._backend

    @property
    def graphviz(self) -> Digraph:
        """Return a copy of the graphviz.Digraph"""
        return self._graph.copy()

    @property
    def nodes(self) -> set[int]:
        """Return a copy of the nodes"""
        return self._nodes.copy()

    @property
    def edges(self) -> set[tuple[int, int, None | LinkPair]]:
        """Return a copy of the edges"""
        return self._edges.copy()

    def _load_node(self, node: int | str | orm.Node) -> orm.Node:
        """Load a node (if not already loaded)

        :param node: node or node pk/uuid
        """
        if isinstance(node, int):
            return orm.Node.get_collection(self._backend).get(pk=node)
        if isinstance(node, str):
            return orm.Node.get_collection(self._backend).get(uuid=node)
        return node

    def add_node(
        self, node: int | str | orm.Node, style_override: dict | None = None, overwrite: bool = False
    ) -> orm.Node:
        """Add single node to the graph

        :param node: node or node pk/uuid
        :param style_override: graphviz style parameters that will override default values
        :param overwrite: whether to overwrite an existing node
        """
        node = self._load_node(node)
        style = {} if style_override is None else dict(style_override)
        style.update(self._global_node_style)
        if node.pk not in self._nodes or overwrite:
            assert node.pk is not None
            _add_graphviz_node(
                self._graph,
                node,
                node_style_func=self._node_styles,
                node_sublabel_func=self._node_sublabels,
                style_override=style,
                include_sublabels=self._include_sublabels,
                id_type=self._node_id_type,
            )
            self._nodes.add(node.pk)
        return node

    def add_edge(
        self,
        in_node: int | str | orm.Node,
        out_node: int | str | orm.Node,
        link_pair: LinkPair | None = None,
        style: dict | None = None,
        overwrite: bool = False,
    ) -> None:
        """Add single node to the graph

        :param in_node: node or node pk/uuid
        :param out_node: node or node pk/uuid
        :param link_pair: defining the relationship between the nodes
        :param style: graphviz style parameters
        :param overwrite: whether to overwrite existing edge
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
    def _convert_link_types(
        link_types: None | str | LinkType | Sequence[str] | Sequence[LinkType],
    ) -> tuple[LinkType, ...]:
        """Convert link types, which may be strings, to a member of LinkType"""
        link_types_list: Sequence[LinkType] | Sequence[str]
        if not link_types:
            link_types_list = [
                LinkType.CREATE,
                LinkType.RETURN,
                LinkType.INPUT_CALC,
                LinkType.INPUT_WORK,
                LinkType.CALL_CALC,
                LinkType.CALL_WORK,
            ]
        elif isinstance(link_types, (str, LinkType)):
            link_types_list = [link_types]  # type: ignore[assignment]
        else:
            link_types_list = link_types
        return tuple(getattr(LinkType, link.upper()) if isinstance(link, str) else link for link in link_types_list)

    def add_incoming(
        self,
        node: int | str | orm.Node,
        link_types: None | str | Sequence[str] | LinkType | Sequence[LinkType] = None,
        annotate_links: LinkAnnotateType = None,
        return_pks: bool = True,
    ) -> list[int] | list[orm.Node]:
        """Add nodes and edges for incoming links to a node

        :param node: node or node pk/uuid
        :param link_types: filter by link types
        :param annotate_links: label edges with the link 'label', 'type' or 'both'
        :param return_pks: whether to return a list of nodes, or list of node pks
        :returns: list of nodes or node pks
        """
        if annotate_links not in [None, False, 'label', 'type', 'both']:
            raise ValueError(
                f'annotate_links must be one of False, "label", "type" or "both"\ninstead, it is: {annotate_links}'
            )

        # incoming nodes are found traversing backwards
        node_pk = self._load_node(node).pk
        assert node_pk is not None
        valid_link_types = self._convert_link_types(link_types)
        traversed_graph = traverse_graph(
            (node_pk,),
            max_iterations=1,
            get_links=True,
            backend=self.backend,
            links_backward=valid_link_types,
        )

        # Batch the query to avoid database parameter limits
        traversed_nodes = {}
        for _, node_batch_ids in batch_iter(traversed_graph['nodes'], DEFAULT_FILTER_SIZE):
            query = orm.QueryBuilder(backend=self.backend).append(
                orm.Node,
                filters={'id': {'in': node_batch_ids}},
                project=['id', '*'],
                tag='node',
            )
            traversed_nodes.update({query_result[0]: query_result[1] for query_result in query.all()})

        for _, traversed_node in traversed_nodes.items():
            self.add_node(traversed_node, style_override=None)

        for link in traversed_graph['links'] or []:
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

    def add_outgoing(
        self,
        node: int | str | orm.Node,
        link_types: None | str | Sequence[str] | LinkType | Sequence[LinkType] = None,
        annotate_links: LinkAnnotateType = None,
        return_pks: bool = True,
    ) -> list[int] | list[orm.Node]:
        """Add nodes and edges for outgoing links to a node

        :param node: node or node pk
        :param link_types: filter by link types
        :param annotate_links: label edges with the link 'label', 'type' or 'both'
        :param return_pks: whether to return a list of nodes, or list of node pks
        :returns: list of nodes or node pks
        """
        if annotate_links not in [None, False, 'label', 'type', 'both']:
            raise ValueError(
                f'annotate_links must be one of False, "label", "type" or "both"\ninstead, it is: {annotate_links}'
            )

        # outgoing nodes are found traversing forwards
        node_pk = self._load_node(node).pk
        assert node_pk is not None
        valid_link_types = self._convert_link_types(link_types)
        traversed_graph = traverse_graph(
            (node_pk,),
            max_iterations=1,
            get_links=True,
            backend=self.backend,
            links_forward=valid_link_types,
        )

        # Batch the query to avoid database parameter limits
        traversed_nodes = {}
        for _, node_batch_ids in batch_iter(traversed_graph['nodes'], DEFAULT_FILTER_SIZE):
            query = orm.QueryBuilder(backend=self.backend).append(
                orm.Node,
                filters={'id': {'in': node_batch_ids}},
                project=['id', '*'],
                tag='node',
            )
            traversed_nodes.update({query_result[0]: query_result[1] for query_result in query.all()})

        for _, traversed_node in traversed_nodes.items():
            self.add_node(traversed_node, style_override=None)

        for link in traversed_graph['links'] or []:
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
        origin: int | str | orm.Node,
        depth: int | None = None,
        link_types: None | str | Sequence[str] | LinkType | Sequence[LinkType] = None,
        annotate_links: LinkAnnotateType = None,
        origin_style: dict | None = None,
        include_process_inputs: bool = False,
        highlight_classes: None | Sequence[str] = None,
    ) -> None:
        """Add nodes and edges from an origin recursively,
        following outgoing links

        :param origin: node or node pk/uuid
        :param depth: if not None, stop after travelling a certain depth into the graph
        :param link_types: filter by subset of link types
        :param annotate_links: label edges with the link 'label', 'type' or 'both'
        :param origin_style: node style map for origin node
        :param include_calculation_inputs: include incoming links for all processes
        :param highlight_classes: target class in exported graph expected to be highlight and
            other nodes are decolorized
        """
        # Get graph traversal rules where the given link types and direction are all set to True,
        # and all others are set to False
        origin_pk = self._load_node(origin).pk
        assert origin_pk is not None
        valid_link_types = self._convert_link_types(link_types)
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
                links_backward=[LinkType.INPUT_WORK, LinkType.INPUT_CALC],
            )
            traversed_graph['nodes'] = traversed_graph['nodes'].union(traversed_outputs['nodes'])
            traversed_graph['links'] = (traversed_graph['links'] or set()).union(traversed_outputs['links'] or set())

        # Do one central query for all nodes in the Graph and generate a {id: Node} dictionary
        # Batch the query to avoid database parameter limits
        traversed_nodes = {}
        for _, node_batch_ids in batch_iter(traversed_graph['nodes'], DEFAULT_FILTER_SIZE):
            query = orm.QueryBuilder(backend=self.backend).append(
                orm.Node,
                filters={'id': {'in': node_batch_ids}},
                project=['id', '*'],
                tag='node',
            )
            traversed_nodes.update({query_result[0]: query_result[1] for query_result in query.all()})

        # Pop the origin node and add it to the graph, applying custom styling
        origin_node = traversed_nodes.pop(origin_pk)
        self.add_node(origin_node, style_override=origin_style or _default_origin_node_styles())

        # Add all traversed nodes to the graph with default styling
        for _, traversed_node in traversed_nodes.items():
            node_label = _get_node_label(traversed_node)
            if highlight_classes and node_label.split()[0] not in highlight_classes:
                self.add_node(traversed_node, style_override=self._ignore_node_style)
            else:
                self.add_node(traversed_node, style_override=None)

        # Add the origin node back into traversed nodes so it can be found for adding edges
        traversed_nodes[origin_pk] = origin_node

        # Add all links to the Graph, using the {id: Node} dictionary for queryless Node retrieval, applying
        # appropriate styling
        for link in traversed_graph['links'] or []:
            source_node = traversed_nodes[link.source_id]
            target_node = traversed_nodes[link.target_id]
            link_pair = LinkPair(self._convert_link_types(link.link_type)[0], link.link_label)
            link_style = self._link_styles(
                link_pair, add_label=annotate_links in ['label', 'both'], add_type=annotate_links in ['type', 'both']
            )
            self.add_edge(source_node, target_node, link_pair, style=link_style)

    def recurse_ancestors(
        self,
        origin: int | str | orm.Node,
        depth: int | None = None,
        link_types: None | str | Sequence[str] | LinkType | Sequence[LinkType] = None,
        annotate_links: LinkAnnotateType = None,
        origin_style: dict | None = None,
        include_process_outputs: bool = False,
        highlight_classes: None | Sequence[str] = None,
    ) -> None:
        """Add nodes and edges from an origin recursively,
        following incoming links

        :param origin: node or node pk/uuid
        :param depth: if not None, stop after travelling a certain depth into the graph
        :param link_types: filter by subset of link types
        :param annotate_links: label edges with the link 'label', 'type' or 'both'
        :param origin_style: node style map for origin node
        :param include_process_outputs: include outgoing links for all processes
        :param highlight_classes:  class label (as displayed in the graph, e.g. 'StructureData', 'FolderData', etc.)
            to be highlight and other nodes are decolorized
        """
        # Get graph traversal rules where the given link types and direction are all set to True,
        # and all others are set to False
        origin_pk = self._load_node(origin).pk
        assert origin_pk is not None
        valid_link_types = self._convert_link_types(link_types)
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
                links_forward=[LinkType.CREATE, LinkType.RETURN],
            )
            traversed_graph['nodes'] = traversed_graph['nodes'].union(traversed_outputs['nodes'])
            traversed_graph['links'] = (traversed_graph['links'] or set()).union(traversed_outputs['links'] or set())

        # Do one central query for all nodes in the Graph and generate a {id: Node} dictionary
        # Batch the query to avoid database parameter limits
        traversed_nodes = {}
        for _, node_batch_ids in batch_iter(traversed_graph['nodes'], DEFAULT_FILTER_SIZE):
            query = orm.QueryBuilder(backend=self.backend).append(
                orm.Node,
                filters={'id': {'in': node_batch_ids}},
                project=['id', '*'],
                tag='node',
            )
            traversed_nodes.update({query_result[0]: query_result[1] for query_result in query.all()})

        # Pop the origin node and add it to the graph, applying custom styling
        origin_node = traversed_nodes.pop(origin_pk)
        self.add_node(origin_node, style_override=(origin_style or _default_origin_node_styles()))

        # Add all traversed nodes to the graph with default styling
        for _, traversed_node in traversed_nodes.items():
            node_label = _get_node_label(traversed_node)
            if highlight_classes and node_label.split()[0] not in highlight_classes:
                self.add_node(traversed_node, style_override=self._ignore_node_style)
            else:
                self.add_node(traversed_node, style_override=None)

        # Add the origin node back into traversed nodes so it can be found for adding edges
        traversed_nodes[origin_pk] = origin_node

        # Add all links to the Graph, using the {id: Node} dictionary for queryless Node retrieval, applying
        # appropriate styling
        for link in traversed_graph['links'] or []:
            source_node = traversed_nodes[link.source_id]
            target_node = traversed_nodes[link.target_id]
            link_pair = LinkPair(self._convert_link_types(link.link_type)[0], link.link_label)
            link_style = self._link_styles(
                link_pair, add_label=annotate_links in ['label', 'both'], add_type=annotate_links in ['type', 'both']
            )
            self.add_edge(source_node, target_node, link_pair, style=link_style)

    def add_origin_to_targets(
        self,
        origin: int | str | orm.Node,
        target_cls: type[orm.Node],
        target_filters: dict | None = None,
        include_target_inputs: bool = False,
        include_target_outputs: bool = False,
        origin_style: Mapping[str, Any] | None = None,
        annotate_links: LinkAnnotateType = None,
    ) -> None:
        """Add nodes and edges from an origin node to all nodes of a target node class.

        :param origin: node or node pk/uuid
        :param target_cls: target node class
        :param target_filters: filters for query of target nodes
        :param include_target_inputs: Include incoming links for all target nodes
        :param include_target_outputs: Include outgoing links for all target nodes
        :param origin_style: node style map for origin node
        :param annotate_links: label edges with the link 'label', 'type' or 'both'
        """
        origin_node = self._load_node(origin)

        if target_filters is None:
            target_filters = {}

        self.add_node(origin_node, style_override=dict(origin_style or {}))

        query = orm.QueryBuilder(
            backend=self.backend,
            path=[
                {'cls': origin_node.__class__, 'filters': {'id': origin_node.pk}, 'tag': 'origin'},
                {
                    'cls': target_cls,
                    'filters': target_filters,
                    'with_ancestors': 'origin',
                    'tag': 'target',
                    'project': '*',
                },
            ],
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
        origin_cls: type[orm.Node],
        target_cls: type[orm.Node],
        origin_filters: dict | None = None,
        target_filters: dict | None = None,
        include_target_inputs: bool = False,
        include_target_outputs: bool = False,
        origin_style: Mapping[str, Any] | None = None,
        annotate_links: LinkAnnotateType = None,
    ) -> None:
        """Add nodes and edges from all nodes of an origin class to all node of a target node class.

        :param origin_cls: origin node class
        :param target_cls: target node class
        :param origin_filters: filters for origin nodes
        :param target_filters: filters for target nodes
        :param include_target_inputs: Include incoming links for all target nodes
        :param include_target_outputs: Include outgoing links for all target nodes
        :param origin_style: node style map for origin node
        :param annotate_links: label edges with the link 'label', 'type' or 'both'
        """
        if origin_filters is None:
            origin_filters = {}

        query = orm.QueryBuilder(
            backend=self.backend, path=[{'cls': origin_cls, 'filters': origin_filters, 'tag': 'origin', 'project': '*'}]
        )

        for (node,) in query.iterall():
            self.add_origin_to_targets(
                node,
                target_cls,
                target_filters=target_filters,
                include_target_inputs=include_target_inputs,
                include_target_outputs=include_target_outputs,
                origin_style=origin_style,
                annotate_links=annotate_links,
            )
