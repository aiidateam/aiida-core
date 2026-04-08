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

F_VALUES: list[float] = [round(0.04 + i * 0.002, 3) for i in range(11)]
"""Feed rate scan: 0.040, 0.042, ..., 0.060."""
