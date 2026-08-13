###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Reusable WorkGraph definitions shared across the tutorial modules.

Promoting these out of the per-module notebooks lets later modules import the
same pipeline module 3 builds instead of redefining it. Each notebook runs in
its own kernel, so a file on disk is the only way to share definitions.
"""

from __future__ import annotations

from typing import TypedDict

from aiida_workgraph import shelljob, task
from include.tasks import parse_output, prepare_input

from aiida import orm

# WorkGraph-wrapped variants of the Module 2 calcfunctions. Defined once
# here so any workflow in this module can plug them into a graph without
# re-wrapping at every call site.
prepare_input_task = task()(prepare_input)
parse_output_task = task()(parse_output)


class GrayScottOutputs(TypedDict):
    """Outputs of :func:`gray_scott_pipeline`.

    :ivar variance_V: variance of the V field after the simulation.
    :ivar mean_V: mean of the V field after the simulation.
    :ivar results_npz: the full ``results.npz`` file produced by ``gsrd``, kept
        so downstream tasks can read the V and U fields directly (module 3a's
        pattern gallery does this).
    """

    variance_V: orm.Float
    mean_V: orm.Float
    results_npz: orm.SinglefileData


@task.graph()
def gray_scott_pipeline(
    parameters: orm.Dict,
    command: orm.InstalledCode,
) -> GrayScottOutputs:
    """Run one gsrd simulation and parse its results (variance_V, mean_V, results_npz)."""

    prepared = prepare_input_task(parameters=parameters)

    simulation = shelljob(
        command=command,
        arguments=['{input}'],
        nodes={'input': prepared.result},
        outputs=['results.npz'],
    )

    parsed = parse_output_task(stdout=simulation.stdout)

    return {
        'variance_V': parsed.variance_V,
        'mean_V': parsed.mean_V,
        'results_npz': simulation.results_npz,
    }
