# pyright: reportUnknownMemberType=false
# pyright: reportAny=false
# ^^^ matplotlib stubs are incomplete; these suppress upstream typing noise
"""Plot a transition curve (variance_V vs F) from a parameter sweep."""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

if TYPE_CHECKING:
    from collections.abc import Sequence


def plot_transition_curve(f_values: Sequence[float], variances: Sequence[float]) -> None:
    """Plot variance_V as a function of feed rate F.

    :param f_values: sequence of F values scanned.
    :param variances: corresponding variance_V values.
    """
    fig: Figure
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(f_values, variances, 'o-', color='tab:blue', linewidth=2, markersize=6)
    ax.set_xlabel('Feed rate F')
    ax.set_ylabel('variance(V)')
    ax.set_title('Pattern transition curve')
    ax.set_yscale('log')
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    plt.show()
