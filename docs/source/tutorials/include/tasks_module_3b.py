###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
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
    """Plot variance(V) vs feed rate F from the gathered sweep results.

    :param variances: dynamic-namespace input mapping sweep keys (e.g.
        ``F_0_038``) to per-iteration variance values.
    :returns: a ``SinglefileData`` PNG of the transition curve.
    """
    import matplotlib.pyplot as plt

    # Sweep keys encode the feed rate as `F_0_038` (= 0.038). Keys from a
    # multi-parameter sweep (e.g. `F_0_040_k_0_060`) don't fit that 1D shape,
    # so we skip them and plot only the points that sit on a single F axis.
    points = {}
    for key, value in variances.items():
        parts = key.split('_')
        if len(parts) == 3 and parts[0] == 'F':
            points[float(f'{parts[1]}.{parts[2]}')] = float(value)

    f_values = sorted(points)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(f_values, [points[f] for f in f_values], 'o-')
    ax.set_xlabel('Feed rate F')
    ax.set_ylabel('variance(V)')
    ax.set_yscale('log')
    ax.set_title('Pattern transition curve')

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100)
    plt.close(fig)

    return orm.SinglefileData.from_bytes(buf.getvalue(), filename='transition_curve.png')
