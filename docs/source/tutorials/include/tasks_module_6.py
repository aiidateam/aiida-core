"""Tasks introduced in module 6 to support adaptive workflows.

``fft_peak_wavelength`` (conditional FFT analysis), ``bump_n_steps`` (iterative
convergence), and ``identify_transition_region`` (dynamic construction of a
refined parameter sweep) back the ``If``/``While``/``Map`` examples in modules
6a and 6b.
"""

from typing import Annotated

import numpy as np
from aiida import engine, orm
from aiida_workgraph import dynamic, task


@engine.calcfunction
def fft_peak_wavelength(results_npz: orm.SinglefileData) -> orm.Float:
    """Estimate the dominant pattern wavelength of the V field via a radial FFT.

    Loads the ``V_final`` array from a gsrd ``results.npz``, removes the mean,
    takes a 2D FFT, radially averages the power spectrum and returns
    ``grid_size / k_peak`` (the dominant wavelength in grid cells).

    :param results_npz: the ``results.npz`` SinglefileData produced by a
        ``gsrd`` ShellJob.
    :returns: the dominant pattern wavelength, in grid cells.
    """
    with results_npz.open(mode='rb') as fh:
        data = np.load(fh, allow_pickle=True)
        v_field = data['V_final']

    centred = v_field - v_field.mean()
    power = np.abs(np.fft.fftshift(np.fft.fft2(centred))) ** 2
    cy, cx = (s // 2 for s in power.shape)
    y_idx, x_idx = np.indices(power.shape)
    radii = np.hypot(x_idx - cx, y_idx - cy).astype(int)
    radial = np.bincount(radii.ravel(), power.ravel()) / np.bincount(radii.ravel())
    k_peak = int(np.argmax(radial[1:])) + 1  # skip the DC mode at k=0
    return orm.Float(v_field.shape[0] / k_peak)


@engine.calcfunction
def bump_n_steps(parameters: orm.Dict, increment: orm.Int) -> orm.Dict:
    """Return a copy of *parameters* with ``n_steps`` increased by ``increment``."""
    new_params = parameters.get_dict()
    new_params['n_steps'] = int(new_params['n_steps']) + int(increment.value)
    return orm.Dict(new_params)


@task()
def identify_transition_region(
    variances: Annotated[dict, dynamic(float)],
    base_parameters: dict,
    n_refined: int,
) -> dict:
    """Build a refined ``F``-sweep around the steepest jump in variance(V).

    Given a coarse map of ``{F_label: variance_V}`` (typically the gathered
    output of a ``Map`` zone), locates the two adjacent ``F`` values with the
    largest variance jump and returns ``n_refined`` new parameter sets
    distributed linearly between them.

    :param variances: a dynamic-namespace mapping of coarse-sweep keys (e.g.
        ``F_0_040``) to their measured variance values.
    :param base_parameters: the parameter template to clone for each refined
        point (with ``F`` overwritten).
    :param n_refined: how many refined ``F`` values to generate.
    :returns: a ``{F_<...>: <parameters>}`` dict ready to feed into a ``Map``
        zone as a source.
    """

    def _key_to_f(key: str) -> float:
        _, integer, fractional = key.split('_')
        return float(f'{integer}.{fractional}')

    pairs = sorted((_key_to_f(k), float(v)) for k, v in variances.items())
    f_sorted = [f for f, _ in pairs]
    var_sorted = [v for _, v in pairs]

    jumps = [abs(var_sorted[i + 1] - var_sorted[i]) for i in range(len(var_sorted) - 1)]
    transition_idx = max(range(len(jumps)), key=jumps.__getitem__)
    # Widen the refined window by one coarse-grid step on each side so the
    # transition isn't sitting at the edge of the refined sweep.
    lo_idx = max(0, transition_idx - 1)
    hi_idx = min(len(f_sorted) - 1, transition_idx + 2)
    f_lo, f_hi = f_sorted[lo_idx], f_sorted[hi_idx]

    refined_f_values = np.linspace(f_lo, f_hi, int(n_refined)).tolist()
    refined: dict[str, dict] = {}
    for f_val in refined_f_values:
        key = f'F_{f_val:.4f}'.replace('.', '_')
        refined[key] = {**dict(base_parameters), 'F': float(f_val)}
    return refined
