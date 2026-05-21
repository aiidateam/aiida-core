"""Shared constants for tutorial modules."""

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

Values below ≈0.035 trigger the simulation's trivial-state guard
(``gsrd`` reports ``ERR: solution converged to null regime`` on stderr) — V
dies out before any pattern forms — so the sweep starts at 0.038.
"""
