"""Shared tasks for the tutorial modules.

``prepare_input`` and ``parse_output`` are plain AiiDA calcfunctions (also
shown inline in module 2). ``make_transition_plot`` is a WorkGraph task that
takes the gathered per-iteration variance Floats and renders the transition
curve as a ``SinglefileData`` PNG.

``fft_peak_wavelength``, ``bump_n_steps`` and ``identify_transition_region``
are introduced in module 6 to support adaptive workflows (conditional FFT
analysis, iterative convergence, and dynamic construction of a refined
parameter sweep, respectively).
"""

import io
from typing import Annotated, TypedDict

import numpy as np
import yaml
from aiida_workgraph import dynamic, task
from include.constants import MEAN_RE, VARIANCE_RE

from aiida import engine, orm


class ParseOutputs(TypedDict):
    """Named outputs produced by :func:`parse_output`."""

    variance_V: float
    mean_V: float


@engine.calcfunction
def prepare_input(parameters: orm.Dict) -> orm.SinglefileData:
    """Convert a Dict of parameters into a SinglefileData YAML file."""
    content = yaml.dump(parameters.get_dict())
    return orm.SinglefileData(io.BytesIO(content.encode()), filename='input.yaml')


@engine.calcfunction
def parse_output(stdout: orm.SinglefileData) -> ParseOutputs:
    """Extract variance_V and mean_V scalars from the ``gsrd`` stdout log.

    :param stdout: captured stdout of a ``gsrd`` run (as produced by
        ``aiida-shell``). ``gsrd`` prints the headline diagnostics only to
        stdout, so we recover them with a simple regex.
    """
    with stdout.open(mode='r') as f:
        text = f.read()
    variance_match = VARIANCE_RE.search(text)
    mean_match = MEAN_RE.search(text)
    if variance_match is None or mean_match is None:
        msg = "gsrd stdout did not contain 'Variance of V field' / 'Mean of V field' diagnostics"
        raise ValueError(msg)
    return {
        'variance_V': orm.Float(float(variance_match.group(1))),
        'mean_V': orm.Float(float(mean_match.group(1))),
    }


@task()
def make_transition_plot(variances: Annotated[dict, dynamic(float)]) -> orm.SinglefileData:
    """Plot variance(V) vs feed rate F from gathered sweep results.

    :param variances: dynamic-namespace input mapping sweep keys (e.g.
        ``F_0_038``) to per-iteration variance values.
    :returns: a ``SinglefileData`` PNG of the transition curve.
    """
    import matplotlib.pyplot as plt

    def _key_to_f(key: str) -> float | None:
        """Reverse the `F_0_038` → 0.038 encoding used by `param_sweep`.

        Returns ``None`` for keys that don't follow the 1D `F_<int>_<frac>`
        shape (e.g. multi-parameter sweep keys), so callers can skip them
        instead of crashing.
        """
        parts = key.split('_')
        if len(parts) != 3 or parts[0] != 'F':
            return None
        try:
            return float(f'{parts[1]}.{parts[2]}')
        except ValueError:
            return None

    items = sorted((f, float(v)) for k, v in variances.items() if (f := _key_to_f(k)) is not None)
    f_values = [f for f, _ in items]
    var_values = [v for _, v in items]

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(f_values, var_values, 'o-', color='tab:blue', linewidth=2, markersize=6)
    ax.set_xlabel('Feed rate F')
    ax.set_ylabel('variance(V)')
    ax.set_yscale('log')
    ax.set_title('Pattern transition curve')
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100)
    plt.close(fig)
    buf.seek(0)

    return orm.SinglefileData(io.BytesIO(buf.getvalue()), filename='transition_curve.png')


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
