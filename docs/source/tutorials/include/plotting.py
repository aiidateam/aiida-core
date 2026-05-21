# pyright: reportUnknownMemberType=false
# ^^^ matplotlib stubs are incomplete; this suppresses upstream typing noise
"""Plotting helpers used across the tutorial notebooks.

Three independent helpers, grouped here so the notebooks can ``import``
rather than ``%run -i`` each script:

* :func:`plot_provenance` — render the provenance graph of a process node.
* :func:`plot_transition_curve` — variance(V) as a function of feed rate F.
* :func:`plot_uv_fields` — side-by-side imshow of the U and V fields.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

if TYPE_CHECKING:
    from collections.abc import Sequence

    import numpy as np
    from graphviz import Digraph
    from numpy.typing import NDArray

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


def plot_transition_curve(f_values: Sequence[float], variances: Sequence[float]) -> None:
    """Plot variance_V as a function of feed rate F.

    :param f_values: sequence of F values scanned.
    :param variances: corresponding variance_V values.
    """
    fig: Figure
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(f_values, variances, 'o-', color='tab:blue', linewidth=2, markersize=6)
    ax.set_xlabel('Feed rate F')
    ax.set_ylabel('variance(V)')
    ax.set_title('Pattern transition curve')
    ax.set_yscale('log')
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    plt.show()


def plot_uv_fields(u_field: NDArray[np.floating], v_field: NDArray[np.floating]) -> None:
    """Plot U (substrate) and V (activator) fields side by side.

    :param u_field: 2D array of U values.
    :param v_field: 2D array of V values.
    """
    fig: Figure
    fig, ax_array = plt.subplots(nrows=1, ncols=2, figsize=(8, 4))
    ax_u: Axes = ax_array[0]
    ax_v: Axes = ax_array[1]

    _ = ax_u.imshow(u_field, cmap='viridis', origin='lower')
    _ = ax_u.set_title('U (substrate)')
    _ = ax_u.axis('off')
    _ = ax_v.imshow(v_field, cmap='inferno', origin='lower')
    _ = ax_v.set_title('V (activator)')
    _ = ax_v.axis('off')
    fig.tight_layout()
    plt.show()
