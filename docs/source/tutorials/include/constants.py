"""Shared constants for tutorial modules."""

from pathlib import Path

SCRIPT_PATH: Path = Path(__file__).resolve().parent / 'reaction-diffusion.py'

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
(``reaction-diffusion.py`` exit code 30: ``var(V) < 1e-8``) — V dies out
before any pattern forms — so the sweep starts at 0.038.
"""
