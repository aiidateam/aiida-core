"""Custom parser for the Gray-Scott reaction-diffusion simulation."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from aiida.orm import Float


def parse_gray_scott(dirpath: Path) -> dict[str, Float] | None:
    """Extract structured data from the simulation output.

    :param dirpath: directory containing the retrieved output files.
    :returns: dictionary of AiiDA nodes, or ``None`` if the output file is missing.
    """
    output_file = dirpath / 'results.npz'
    if not output_file.exists():
        return None

    data = np.load(output_file)  # pyright: ignore[reportAny] - np.load returns Any
    variance_v: float = float(data['variance_V'])  # pyright: ignore[reportAny]
    mean_v: float = float(data['mean_V'])  # pyright: ignore[reportAny]
    return {
        'variance_V': Float(variance_v),  # type: ignore[no-untyped-call]
        'mean_V': Float(mean_v),  # type: ignore[no-untyped-call]
    }
