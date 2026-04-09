"""Helper to render provenance graphs in tutorial notebooks."""

from __future__ import annotations

import base64
from typing import TYPE_CHECKING

from IPython.display import HTML, SVG, display

if TYPE_CHECKING:
    from aiida.orm import ProcessNode


def plot_provenance(
    node: ProcessNode,
    *,
    link_text: str = 'Open full-size graph',
) -> None:
    """Display a provenance graph as inline SVG with a link to open it full-size.

    The link uses a JavaScript blob URL so it works regardless of the
    Sphinx build output location.

    :param node: AiiDA process node to visualize.
    :param link_text: text for the "open in new tab" link.
    """
    from aiida.tools.visualization import Graph

    graph = Graph()
    graph.add_incoming(node, annotate_links='both')
    graph.add_outgoing(node, annotate_links='both')

    svg_bytes: bytes = graph.graphviz.pipe(format='svg')
    svg_b64: str = base64.b64encode(svg_bytes).decode()

    display(SVG(svg_bytes))
    display(
        HTML(
            '<a href="#" onclick="'
            f"var b=new Blob([atob('{svg_b64}')],{{type:'image/svg+xml'}}); "
            "window.open(URL.createObjectURL(b),'_blank'); return false;"
            f'">{link_text}</a>'
        )
    )
