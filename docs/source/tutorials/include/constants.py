"""Shared constants for tutorial modules."""

import re

VARIANCE_RE = re.compile(r'Variance of V field\s*:\s*([\d.eE+-]+)')
"""Regex matching the ``Variance of V field : <value>`` diagnostic in ``gsrd`` stdout."""

MEAN_RE = re.compile(r'Mean\s+of V field\s*=\s*([\d.eE+-]+)')
"""Regex matching the ``Mean of V field = <value>`` diagnostic in ``gsrd`` stdout."""

BASE_PARAMS: dict = {
    'grid_size': 64,
    'du': 0.16,
    'dv': 0.08,
    'F': 0.04,
    'k': 0.065,
    'dt': 1.0,
    'n_steps': 3000,
    'seed': 42,
}

F_VALUES: list[float] = [0.038, 0.040, 0.042, 0.044, 0.046, 0.050, 0.055, 0.060]
"""Feed rate scan: denser around the F ≈ 0.043 phase transition.

Stays at F ≥ 0.038 so that, with the default ``k = 0.065``, every sweep
point lands inside the pattern-forming region of Gray-Scott parameter
space. ``gsrd`` will happily run outside that region too (it just reports
a near-zero ``variance(V)``), but a 1D transition curve is easiest to
read when every point is in the band.
"""
