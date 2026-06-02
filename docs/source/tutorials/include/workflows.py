"""Reusable WorkGraph definitions used across the tutorial modules.

Promoting these out of the per-module notebooks lets Module 6 and Module 7
import the same pipeline Module 3 builds, instead of redefining it. Each
notebook runs in its own kernel, so the only way to share definitions is
through a file on disk.
"""

from __future__ import annotations

from typing import TypedDict

from aiida_workgraph import shelljob, task
from include.tasks import parse_output, prepare_input

from aiida import orm

# WorkGraph-wrapped variants of the Module 2 calcfunctions. Defined once
# here so any workflow in this module can plug them into a graph without
# re-wrapping at every call site.
prepare_input_task = task(prepare_input)
parse_output_task = task(parse_output)


class GrayScottOutputs(TypedDict):
    """Outputs of :func:`gray_scott_pipeline`.

    :ivar variance_V: variance of the V field after the simulation.
    :ivar mean_V: mean of the V field after the simulation.
    :ivar results_npz: the full ``results.npz`` file produced by ``gsrd``,
        kept around so downstream tasks (e.g. an FFT-based diagnostic in
        Module 6) can read the V and U fields directly.
    """

    variance_V: orm.Float
    mean_V: orm.Float
    results_npz: orm.SinglefileData


@task.graph()
def gray_scott_pipeline(
    parameters: orm.Dict,
    command: orm.AbstractCode,
) -> GrayScottOutputs:
    """Run a single ``gsrd`` simulation and parse its scalar diagnostics.

    Three-step graph: ``prepare_input`` (calcfunction) builds the YAML input
    file, ``ShellJob`` runs the ``gsrd`` binary against it, ``parse_output``
    (calcfunction) recovers the diagnostics from stdout. The graph exposes
    ``variance_V``, ``mean_V``, and the raw ``results.npz`` file so callers
    can pick what they need.

    :param parameters: ``Dict`` of Gray-Scott parameters (``F``, ``k``,
        ``grid_size``, ``n_steps``, ...).
    :param command: the ``gsrd`` ``InstalledCode`` to run on.
    """
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
