"""Helper to render provenance graphs in tutorial notebooks."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from graphviz import Digraph

    from aiida.orm import ProcessNode


def plot_provenance(node: ProcessNode) -> Digraph:
    """Return a Graphviz digraph showing immediate inputs and outputs of *node*."""
    from aiida.tools.visualization import Graph

    graph = Graph()
    graph.add_incoming(node, annotate_links='both')
    graph.add_outgoing(node, annotate_links='both')
    return graph.graphviz
