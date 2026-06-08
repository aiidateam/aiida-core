# pyright: reportUnknownMemberType=false
# ^^^ matplotlib stubs are incomplete; this suppresses upstream typing noise
"""Plotting helpers used across the tutorial notebooks.

Independent helpers, grouped here so the notebooks can ``import``
rather than ``%run -i`` each script:

* :func:`plot_provenance` — render the provenance graph of a process node.
* :func:`plot_transition_curve` — variance(V) as a function of feed rate F.
* :func:`plot_uv_fields` — side-by-side imshow of the U and V fields.
* :func:`plot_2d_variance_heatmap` — variance(V) over a 2D (F, k) parameter grid.
* :func:`plot_fft_spectrum` — 2D power spectrum + radial profile for a V field.
* :func:`plot_adaptive_sweep` — coarse + refined transition curves on one axis.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    import numpy as np
    from graphviz import Digraph
    from numpy.typing import NDArray

    from aiida.orm import Float, ProcessNode, SinglefileData


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


def plot_2d_variance_heatmap(
    variances: Mapping[str, Float],
    param_sweep: Mapping[str, Mapping[str, float]],
    f_grid: Sequence[float],
    k_grid: Sequence[float],
    dead_threshold: float = 1e-6,
) -> None:
    """Render gathered ``variance(V)`` as a log-scale 2D heatmap over ``(F, k)``.

    :param variances: mapping from sweep key (e.g. ``F_0_045_k_0_060``) to an
        ``orm.Float`` carrying the per-iteration ``variance(V)``. Typically
        obtained from ``wg.outputs.variance_V._value`` after a 2D ``Map`` run.
    :param param_sweep: the sweep dict used to build the workflow; provides
        the ``(F, k)`` lookup for each key without having to parse the key.
    :param f_grid: feed-rate axis values, in the order to display on the y-axis.
    :param k_grid: kill-rate axis values, in the order to display on the x-axis.
    :param dead_threshold: variance values below this floor are treated as
        "dead zone" (no pattern). Clamps the log-norm so the colour scale
        focuses on the physically meaningful ``[dead_threshold, max]`` range
        instead of spanning hundreds of orders of magnitude down to numerical
        underflow.
    """
    import numpy as np
    from matplotlib.colors import LogNorm

    grid = np.full((len(f_grid), len(k_grid)), np.nan)
    for key, value in variances.items():
        params = param_sweep[key]
        f_idx = list(f_grid).index(params['F'])
        k_idx = list(k_grid).index(params['k'])
        grid[f_idx, k_idx] = float(value.value)

    positive = grid[grid > 0]
    if positive.size == 0:
        msg = (
            'No positive variance values to plot. '
            'Did the workflow gather succeed? '
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


def plot_fft_spectrum(results_npz: SinglefileData) -> None:
    """Show the 2D power spectrum and radial profile of a Gray-Scott V field.

    Loads ``V_final`` from a gsrd ``results.npz``, computes the 2D FFT, and
    renders two panels side by side:

    * the log-scale 2D power spectrum, centred on the DC mode
    * the radially-averaged power profile, with the peak (the dominant
      pattern wavelength) marked

    :param results_npz: the ``results.npz`` SinglefileData produced by a
        ``gsrd`` ShellJob.
    """
    import numpy as np

    with results_npz.open(mode='rb') as fh:
        data = np.load(fh, allow_pickle=True)
        v_field = data['V_final']

    centred = v_field - v_field.mean()
    power = np.abs(np.fft.fftshift(np.fft.fft2(centred))) ** 2
    cy, cx = (s // 2 for s in power.shape)
    y_idx, x_idx = np.indices(power.shape)
    radii = np.hypot(x_idx - cx, y_idx - cy).astype(int)
    counts = np.bincount(radii.ravel())
    radial = np.bincount(radii.ravel(), power.ravel()) / np.maximum(counts, 1)
    k_peak = int(np.argmax(radial[1:])) + 1  # skip the DC mode at k=0
    wavelength = v_field.shape[0] / k_peak

    fig: Figure
    fig, ax_array = plt.subplots(nrows=1, ncols=2, figsize=(10, 4))
    ax_2d: Axes = ax_array[0]
    ax_radial: Axes = ax_array[1]

    ax_2d.imshow(np.log1p(power), origin='lower', cmap='magma')
    ax_2d.set_title('2D power spectrum (log scale)')
    ax_2d.set_xlabel('k_x')
    ax_2d.set_ylabel('k_y')

    ax_radial.plot(radial, color='tab:blue')
    ax_radial.axvline(
        k_peak, color='tab:red', linestyle='--', label=f'peak at k={k_peak}  →  λ ≈ {wavelength:.1f} cells'
    )
    ax_radial.set_xlabel('radial wavenumber k')
    ax_radial.set_ylabel('radially-averaged power')
    ax_radial.set_yscale('log')
    ax_radial.set_xlim(0, len(radial))
    ax_radial.set_title('Radial profile')
    ax_radial.legend()
    ax_radial.grid(True, alpha=0.3)

    fig.tight_layout()
    plt.show()


def plot_adaptive_sweep(
    coarse_variances: Mapping[str, Float],
    refined_variances: Mapping[str, Float],
) -> None:
    """Plot a coarse and a refined variance(V)-vs-F sweep on the same log axes.

    Reverses the ``F_<int>_<frac>`` key encoding used by Module 6's adaptive
    sweep, sorts each series by F, and renders both on a single figure.

    :param coarse_variances: mapping from sweep key (e.g. ``F_0_038``) to
        the coarse-iteration ``variance(V)`` value.
    :param refined_variances: mapping with the same key shape from the
        refined iteration.
    """

    def _key_to_f(key: str) -> float:
        _, integer, fractional = key.split('_')
        return float(f'{integer}.{fractional}')

    coarse = {_key_to_f(k): float(v) for k, v in coarse_variances.items()}
    refined = {_key_to_f(k): float(v) for k, v in refined_variances.items()}

    fig: Figure
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(sorted(coarse), [coarse[f] for f in sorted(coarse)], 'o-', color='tab:blue', label='coarse sweep')
    ax.plot(sorted(refined), [refined[f] for f in sorted(refined)], 's-', color='tab:orange', label='refined sweep')
    ax.set_xlabel('Feed rate F')
    ax.set_ylabel('variance(V)')
    ax.set_yscale('log')
    ax.set_title('Adaptive Gray-Scott sweep')
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    plt.show()
