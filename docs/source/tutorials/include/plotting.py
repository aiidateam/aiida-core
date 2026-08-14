###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Plotting helpers shared across the tutorial notebooks.

Grouped here so the notebooks can ``import`` a figure helper rather than
redefine it in every cell. Only the provenance-graph helper is AiiDA-specific.
The gsrd-output plots (pattern gallery, variance heatmap) live in
:mod:`gsrd.plotting`; the wrappers here just unwrap the AiiDA nodes into the
plain arrays/floats those functions expect.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from graphviz import Digraph

    from aiida.orm import Float, ProcessNode, SinglefileData


def plot_provenance(node: ProcessNode) -> Digraph:
    """Return a Graphviz digraph for *node* and its connected provenance.

    Traverses ancestors and descendants, including inputs/outputs of
    connected processes, so the full chain is visible. Renders as inline SVG
    in Jupyter notebooks.
    """
    from aiida.tools.visualization import Graph

    graph = Graph()
    graph.recurse_ancestors(node, annotate_links='both', include_process_outputs=True)
    graph.recurse_descendants(node, annotate_links='both', include_process_inputs=True)
    return graph.graphviz


def plot_pattern_gallery(runs: Mapping[str, SinglefileData]) -> None:
    """Plot the final V field of several gsrd runs side by side, each labelled.

    :param runs: mapping from a label (e.g. ``'labyrinth'``) to the
        ``results.npz`` SinglefileData produced by that run's ``gsrd`` ShellJob.
    """
    import matplotlib.pyplot as plt
    import numpy as np
    from gsrd.plotting import plot_field_gallery

    fields = {}
    for label, results_npz in runs.items():
        with results_npz.open(mode='rb') as fh:
            fields[label] = np.load(fh, allow_pickle=True)['V_final']
    plot_field_gallery(fields)
    plt.show()


def plot_2d_variance_heatmap(
    variances: Mapping[str, Float],
    param_sweep: Mapping[str, Mapping[str, float]],
    f_grid: Sequence[float],
    k_grid: Sequence[float],
    dead_threshold: float = 1e-6,
) -> None:
    """Render gathered ``variance(V)`` as a log-scale 2D heatmap over ``(F, k)``.

    :param variances: mapping from sweep key (e.g. ``F_0_045_k_0_060``) to an
        ``orm.Float`` carrying the per-iteration ``variance(V)``.
    :param param_sweep: the sweep dict used to build the workflow; provides the
        ``(F, k)`` lookup for each key without having to parse the key.
    :param f_grid: feed-rate axis values, in display order on the y-axis.
    :param k_grid: kill-rate axis values, in display order on the x-axis.
    :param dead_threshold: variance values below this floor are clamped, so the
        log colour scale focuses on the physical range rather than spanning down
        to numerical underflow.
    """
    import matplotlib.pyplot as plt
    import numpy as np
    from gsrd.plotting import plot_variance_heatmap

    grid = np.full((len(f_grid), len(k_grid)), np.nan)
    for key, value in variances.items():
        params = param_sweep[key]
        f_idx = list(f_grid).index(params['F'])
        k_idx = list(k_grid).index(params['k'])
        grid[f_idx, k_idx] = float(value.value)

    # A more informative error than gsrd's generic one: the usual cause here is a
    # failed WorkGraph ``Map`` gather, which drops all entries.
    if grid[grid > 0].size == 0:
        msg = (
            'No positive variance values to plot. Did the workflow gather succeed? '
            "WorkGraph's `Map` drops all gathered entries when any iteration fails."
        )
        raise ValueError(msg)

    plot_variance_heatmap(grid, f_grid, k_grid, dead_threshold=dead_threshold)
    plt.show()
