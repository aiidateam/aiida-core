"""WorkGraph task introduced in module 3b.

``make_transition_plot`` is the reduction step of the parameter-sweep
workflow: it takes the gathered per-iteration variance Floats and renders the
transition curve as a ``SinglefileData`` PNG.
"""

import io
from typing import Annotated

from aiida_workgraph import dynamic, task

from aiida import orm


@task()
def make_transition_plot(variances: Annotated[dict, dynamic(float)]) -> orm.SinglefileData:
    """Plot variance(V) vs feed rate F from gathered sweep results.

    :param variances: dynamic-namespace input mapping sweep keys (e.g.
        ``F_0_038``) to per-iteration variance values.
    :returns: a ``SinglefileData`` PNG of the transition curve.
    """
    import matplotlib.pyplot as plt

    def _key_to_f(key: str) -> float | None:
        """Reverse the `F_0_038` → 0.038 encoding used by `param_sweep`.

        Returns ``None`` for keys that don't follow the 1D `F_<int>_<frac>`
        shape (e.g. multi-parameter sweep keys), so callers can skip them
        instead of crashing.
        """
        parts = key.split('_')
        if len(parts) != 3 or parts[0] != 'F':
            return None
        try:
            return float(f'{parts[1]}.{parts[2]}')
        except ValueError:
            return None

    items = sorted((f, float(v)) for k, v in variances.items() if (f := _key_to_f(k)) is not None)
    f_values = [f for f, _ in items]
    var_values = [v for _, v in items]

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(f_values, var_values, 'o-', color='tab:blue', linewidth=2, markersize=6)
    ax.set_xlabel('Feed rate F')
    ax.set_ylabel('variance(V)')
    ax.set_yscale('log')
    ax.set_title('Pattern transition curve')
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100)
    plt.close(fig)

    return orm.SinglefileData.from_bytes(buf.getvalue(), filename='transition_curve.png')
