# pyright: reportUnknownMemberType=false
# pyright: reportAny=false
# ^^^ matplotlib stubs are incomplete; these suppress upstream typing noise
"""Plot the U and V fields from a Gray-Scott simulation result."""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray


def plot_uv_fields(u_field: NDArray[np.floating], v_field: NDArray[np.floating]) -> None:
    """Plot U (substrate) and V (activator) fields side by side.

    :param u_field: 2D array of U values.
    :param v_field: 2D array of V values.
    """
    fig: Figure
    fig, ax_array = plt.subplots(nrows=1, ncols=2, figsize=(8, 4))
    ax_u: Axes = ax_array[0]
    ax_v: Axes = ax_array[1]

    _ = ax_u.imshow(u_field, cmap='viridis', origin='lower')
    _ = ax_u.set_title('U (substrate)')
    _ = ax_u.axis('off')
    _ = ax_v.imshow(v_field, cmap='inferno', origin='lower')
    _ = ax_v.set_title('V (activator)')
    _ = ax_v.axis('off')
    fig.tight_layout()
    plt.show()
