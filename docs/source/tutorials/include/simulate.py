# ruff: noqa: N803, N806 - uppercase variable names follow standard mathematical notation
# pyright: reportConstantRedefinition=false
"""In-process Gray-Scott reaction-diffusion simulation.

A pure-Python function that runs the simulation and returns the results
as a dictionary. Used in Module 1 where we treat it as a black-box code.
"""

from __future__ import annotations

from typing import NotRequired, TypedDict

import numpy as np
from numpy.typing import NDArray


class SimParams(TypedDict):
    """Typed dictionary for simulation parameters."""

    grid_size: int
    du: float
    dv: float
    F: float
    k: float
    dt: float
    n_steps: int
    seed: NotRequired[int]


def _laplacian(Z: NDArray[np.floating]) -> NDArray[np.floating]:
    """Compute the discrete Laplacian with periodic boundary conditions."""
    return -4 * Z + np.roll(Z, 1, axis=0) + np.roll(Z, -1, axis=0) + np.roll(Z, 1, axis=1) + np.roll(Z, -1, axis=1)


def simulate(params: SimParams) -> dict[str, NDArray[np.floating] | float]:
    """Run a Gray-Scott reaction-diffusion simulation.

    :param params: typed dictionary with simulation parameters.
    :returns: dictionary with ``U_final``, ``V_final``, ``variance_V``, ``mean_V``.
    """
    n: int = params['grid_size']
    du: float = params['du']
    dv: float = params['dv']
    F: float = params['F']
    k: float = params['k']
    dt: float = params['dt']
    steps: int = params['n_steps']

    _rng: np.random.Generator = np.random.default_rng(params.get('seed'))

    U: NDArray[np.floating] = np.ones((n, n))
    V: NDArray[np.floating] = np.zeros((n, n))
    r: int = n // 10
    c: int = n // 2
    U[c - r : c + r, c - r : c + r] = 0.50
    V[c - r : c + r, c - r : c + r] = 0.25

    for _ in range(steps):
        Lu: NDArray[np.floating] = _laplacian(U)
        Lv: NDArray[np.floating] = _laplacian(V)
        uvv: NDArray[np.floating] = U * V * V
        U += dt * (du * Lu - uvv + F * (1 - U))
        V += dt * (dv * Lv + uvv - (F + k) * V)

    return {
        'U_final': U,
        'V_final': V,
        'variance_V': float(np.var(V)),
        'mean_V': float(np.mean(V)),
    }
