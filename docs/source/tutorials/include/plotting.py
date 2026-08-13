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
redefine it in every cell.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

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
    import numpy as np

    fig: Figure
    fig, ax_array = plt.subplots(nrows=1, ncols=len(runs), figsize=(4 * len(runs), 4))
    axes = np.atleast_1d(ax_array)
    for ax, (label, results_npz) in zip(axes, runs.items()):
        with results_npz.open(mode='rb') as fh:
            v_field = np.load(fh, allow_pickle=True)['V_final']
        _ = ax.imshow(v_field, cmap='magma', origin='lower')
        _ = ax.set_title(label)
        _ = ax.axis('off')
    fig.tight_layout()
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
    import numpy as np
    from matplotlib.colors import LogNorm

    grid = np.full((len(f_grid), len(k_grid)), np.nan)
    for key, value in variances.items():
        params = param_sweep[key]
        f_idx = list(f_grid).index(params['F'])
        k_idx = list(k_grid).index(params['k'])
        grid[f_idx, k_idx] = float(value.value)

    if grid[grid > 0].size == 0:
        msg = (
            'No positive variance values to plot. Did the workflow gather succeed? '
            "WorkGraph's `Map` drops all gathered entries when any iteration fails."
        )
        raise ValueError(msg)

    vmin = dead_threshold
    vmax = float(np.nanmax(grid))
    grid_for_plot = np.where(grid >= vmin, grid, vmin)

    fig: Figure
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax_typed: Axes = ax
    im = ax_typed.imshow(
        grid_for_plot,
        origin='lower',
        aspect='auto',
        extent=(min(k_grid), max(k_grid), min(f_grid), max(f_grid)),
        norm=LogNorm(vmin=vmin, vmax=vmax),
        cmap='viridis',
    )
    ax_typed.set_xlabel('Kill rate k')
    ax_typed.set_ylabel('Feed rate F')
    ax_typed.set_title(f'Gray-Scott pattern strength: variance(V) on a {len(f_grid)}x{len(k_grid)} F-by-k grid')
    ax_typed.set_xticks(list(k_grid))
    ax_typed.set_yticks(list(f_grid))
    fig.colorbar(im, ax=ax_typed, label='variance(V)')
    fig.tight_layout()
    plt.show()
