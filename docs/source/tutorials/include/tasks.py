"""Shared tasks for tutorial modules 2 and 3.

``prepare_input`` and ``parse_output`` are plain AiiDA calcfunctions (also
shown inline in module 2). ``make_transition_plot`` is a WorkGraph task that
takes the gathered per-iteration variance Floats and renders the transition
curve as a ``SinglefileData`` PNG.
"""

import io
from typing import Annotated, TypedDict

import yaml
from aiida_workgraph import dynamic, task

from aiida import engine, orm


class ParseOutputs(TypedDict):
    """Named outputs produced by :func:`parse_output`."""

    variance_V: float
    mean_V: float


@engine.calcfunction
def prepare_input(parameters: orm.Dict) -> orm.SinglefileData:
    """Convert a Dict of parameters into a SinglefileData YAML file."""
    content = yaml.dump(parameters.get_dict())
    return orm.SinglefileData(io.BytesIO(content.encode()), filename='input.yaml')


@engine.calcfunction
def parse_output(output_file: orm.SinglefileData) -> ParseOutputs:
    """Extract variance_V and mean_V from a SinglefileData YAML results file."""
    with output_file.open(mode='r') as f:
        data = yaml.safe_load(f)
        return {
            'variance_V': orm.Float(data['variance_V']),
            'mean_V': orm.Float(data['mean_V']),
        }


@task()
def make_transition_plot(variances: Annotated[dict, dynamic(float)]) -> orm.SinglefileData:
    """Plot variance(V) vs feed rate F from gathered sweep results.

    :param variances: dynamic-namespace input mapping sweep keys (e.g.
        ``F_0_038``) to per-iteration variance values.
    :returns: a ``SinglefileData`` PNG of the transition curve.
    """
    import matplotlib.pyplot as plt

    def _key_to_f(key: str) -> float:
        """Reverse the `F_0_038` → 0.038 encoding used by `param_sweep`."""
        _, integer, fractional = key.split('_')
        return float(f'{integer}.{fractional}')

    items = sorted((_key_to_f(k), float(v)) for k, v in variances.items())
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
    buf.seek(0)

    return orm.SinglefileData(io.BytesIO(buf.getvalue()), filename='transition_curve.png')
