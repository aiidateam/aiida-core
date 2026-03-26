# ruff: noqa: N803, N806 - uppercase variable names (U, V, F, Lu, Lv) follow standard mathematical notation
# pyright: reportConstantRedefinition=false
"""Reaction-diffusion simulation (Gray-Scott model).

A standalone CLI script that reads a YAML input file, runs a 2D Gray-Scott
reaction-diffusion simulation, and writes the results to a ``.npz`` file.

Exit codes:
    0  -- success
    1  -- failed to read input file
    2  -- missing required parameter
    10 -- diffusion constants not positive
    11 -- time step not positive
    20 -- numerical instability (NaN/Inf detected)
    30 -- trivial steady state (no pattern formed)
    99 -- unexpected error
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import NoReturn, NotRequired, TypedDict, cast

import numpy as np
import yaml
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


REQUIRED_KEYS: list[str] = ['grid_size', 'du', 'dv', 'F', 'k', 'dt', 'n_steps']


def fail(code: int, message: str) -> NoReturn:
    """Print an error message to stderr and exit with the given code."""
    print(f'ERROR[{code}]: {message}', file=sys.stderr)
    sys.exit(code)


def laplacian(Z: NDArray[np.floating]) -> NDArray[np.floating]:
    """Compute the discrete Laplacian of a 2D field using periodic boundary conditions."""
    return -4 * Z + np.roll(Z, 1, axis=0) + np.roll(Z, -1, axis=0) + np.roll(Z, 1, axis=1) + np.roll(Z, -1, axis=1)


def simulate(params: SimParams) -> tuple[NDArray[np.floating], NDArray[np.floating], float, float]:
    """Run the Gray-Scott simulation and return final fields and diagnostics.

    :param params: typed dictionary with simulation parameters.
    :returns: tuple of ``(U, V, variance_V, mean_V)``.
    """
    n: int = params['grid_size']
    du: float = params['du']
    dv: float = params['dv']
    F: float = params['F']
    k: float = params['k']
    dt: float = params['dt']
    steps: int = params['n_steps']
    seed: int | None = params.get('seed', None)

    if du <= 0 or dv <= 0:
        fail(code=10, message='Diffusion constants must be positive')

    if dt <= 0:
        fail(code=11, message='Time step must be positive')

    if seed is not None:
        np.random.seed(seed)

    U: NDArray[np.floating] = np.ones((n, n))
    V: NDArray[np.floating] = np.zeros((n, n))

    # Small perturbation in the center
    r: int = n // 10
    c: int = n // 2
    U[c - r : c + r, c - r : c + r] = 0.50
    V[c - r : c + r, c - r : c + r] = 0.25

    for step in range(steps):
        Lu: NDArray[np.floating] = laplacian(U)
        Lv: NDArray[np.floating] = laplacian(V)

        uvv: NDArray[np.floating] = U * V * V
        U += dt * (du * Lu - uvv + F * (1 - U))
        V += dt * (dv * Lv + uvv - (F + k) * V)

        if not np.all(np.isfinite(U)) or not np.all(np.isfinite(V)):
            fail(code=20, message=f'Numerical instability detected at step {step}')

    var_v: float = float(np.var(V))
    mean_v: float = float(np.mean(V))

    if var_v < 1e-8:
        fail(code=30, message='Trivial steady state (no pattern formed)')

    return U, V, var_v, mean_v


def main() -> None:
    """CLI entry point: parse arguments, run simulation, write output."""
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description='Reaction-diffusion simulation (Gray-Scott model)',
    )
    _ = parser.add_argument('input', help='Input YAML file')
    _ = parser.add_argument('--output', required=True, help='Output .npz file')
    _ = parser.add_argument('--dt', type=float, help='Override time step')
    args: argparse.Namespace = parser.parse_args()

    input_path: str = cast(str, args.input)
    output_path: str = cast(str, args.output)
    dt_override: float | None = cast(float | None, args.dt)

    try:
        with open(input_path) as f:
            raw_params: dict[str, object] = cast(dict[str, object], yaml.safe_load(f))
    except Exception as e:
        fail(code=1, message=f'Failed to read input file: {e}')

    if dt_override is not None:
        raw_params['dt'] = dt_override

    for key in REQUIRED_KEYS:
        if key not in raw_params:
            fail(code=2, message=f"Missing required parameter '{key}'")

    # raw_params is validated above; cast via object for basedpyright compatibility
    params: SimParams = cast(SimParams, cast(object, raw_params))

    try:
        U, V, var_v, mean_v = simulate(params=params)
    except SystemExit:
        raise
    except Exception as e:
        fail(code=99, message=f'Unexpected error: {e}')

    np.savez(
        Path(output_path),
        U_final=U,
        V_final=V,
        variance_V=var_v,
        mean_V=mean_v,
        params=json.dumps(raw_params),
    )

    print('JOB DONE')
    sys.exit(0)


if __name__ == '__main__':
    main()
