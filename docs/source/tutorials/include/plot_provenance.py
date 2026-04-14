"""Helper to render provenance graphs in tutorial notebooks."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from graphviz import Digraph

    from aiida.orm import ProcessNode


def plot_provenance(node: ProcessNode) -> Digraph:
    """Return a Graphviz digraph for *node* and its connected provenance.

    Traverses ancestors and descendants, including inputs/outputs of
    connected processes, so the full chain is visible.  The graph renders
    as inline SVG in Jupyter notebooks.
    """
    from aiida.tools.visualization import Graph

    graph = Graph()
    graph.recurse_ancestors(node, annotate_links='both', include_process_outputs=True)
    graph.recurse_descendants(node, annotate_links='both', include_process_inputs=True)
    return graph.graphviz
