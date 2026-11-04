###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Divide/recover programs for declared task failures with a plain float arm."""

from aiida.engine.processes.exit_code import ExitCode, ExitCodeEnum
from aiida.engine.processes.graphs.lowering import graph, task
from aiida.engine.processes.graphs.results import Err, Ok, Result


class DivisionErrors(ExitCodeEnum):
    """Declared failures of the `divide` task."""

    ZERO_DENOMINATOR = ExitCode(410, 'The denominator is zero.', invalidates_cache=True)


@task
def divide(numerator: float, denominator: float) -> Result[float, DivisionErrors]:
    """Divide, declaring the zero-denominator failure instead of raising it."""
    if denominator == 0:
        return Err(DivisionErrors.ZERO_DENOMINATOR)
    return Ok(numerator / denominator)


@task
def recover(error: DivisionErrors) -> float:
    """Recover from a declared division failure."""
    return -float(error.value.status)


@task
def read_ratio(value: float) -> float:
    """Read a successful ratio."""
    return value


@graph
def ratio(numerator: float, denominator: float) -> float:
    """Divide, recovering with `recover` when the denominator is zero."""
    value, error = divide(numerator=numerator, denominator=denominator)
    if error is not None:
        selected = recover(error=error)
    else:
        selected = read_ratio(value=value)
    return selected
