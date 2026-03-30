import argparse
import json
import sys
from pathlib import Path

import numpy as np
import yaml

# ---------------------------
# Error handling helpers
# ---------------------------


def fail(code, message):
    print(f'ERROR[{code}]: {message}', file=sys.stderr)
    sys.exit(code)


# ---------------------------
# Core solver
# ---------------------------


def laplacian(Z):
    return -4 * Z + np.roll(Z, 1, axis=0) + np.roll(Z, -1, axis=0) + np.roll(Z, 1, axis=1) + np.roll(Z, -1, axis=1)


def simulate(params):
    n = params['grid_size']
    du = params['du']
    dv = params['dv']
    F = params['F']
    k = params['k']
    dt = params['dt']
    steps = params['n_steps']
    seed = params.get('seed', None)

    if du <= 0 or dv <= 0:
        fail(10, 'Diffusion constants must be positive')

    if dt <= 0:
        fail(11, 'Time step must be positive')

    if seed is not None:
        np.random.seed(seed)

    U = np.ones((n, n))
    V = np.zeros((n, n))

    # Small perturbation in the center
    r = n // 10
    c = n // 2
    U[c - r : c + r, c - r : c + r] = 0.50
    V[c - r : c + r, c - r : c + r] = 0.25

    for step in range(steps):
        Lu = laplacian(U)
        Lv = laplacian(V)

        uvv = U * V * V
        U += dt * (du * Lu - uvv + F * (1 - U))
        V += dt * (dv * Lv + uvv - (F + k) * V)

        if not np.isfinite(U).all() or not np.isfinite(V).all():
            fail(20, f'Numerical instability detected at step {step}')

    var_v = float(np.var(V))
    mean_v = float(np.mean(V))

    if var_v < 1e-8:
        fail(30, 'Trivial steady state (no pattern formed)')

    return U, V, var_v, mean_v


# ---------------------------
# CLI
# ---------------------------


def main():
    parser = argparse.ArgumentParser(description='Reaction–diffusion simulation (Gray–Scott model)')
    parser.add_argument('input', help='Input YAML file')
    parser.add_argument('--output', required=True, help='Output .npz file')
    parser.add_argument('--dt', type=float, help='Override time step')
    args = parser.parse_args()

    try:
        with open(args.input) as f:
            params = yaml.safe_load(f)
    except Exception as e:
        fail(1, f'Failed to read input file: {e}')

    if args.dt is not None:
        params['dt'] = args.dt

    required = ['grid_size', 'du', 'dv', 'F', 'k', 'dt', 'n_steps']
    for key in required:
        if key not in params:
            fail(2, f"Missing required parameter '{key}'")

    try:
        U, V, var_v, mean_v = simulate(params)
    except SystemExit:
        raise
    except Exception as e:
        fail(99, f'Unexpected error: {e}')

    out = Path(args.output)
    np.savez(
        out,
        U_final=U,
        V_final=V,
        variance_V=var_v,
        mean_V=mean_v,
        params=json.dumps(params),
    )

    print('JOB DONE')
    sys.exit(0)


if __name__ == '__main__':
    main()
