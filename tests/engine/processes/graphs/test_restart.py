###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Restart loops over declared failures, with attempts as explicit loop state."""

import typing as t

import pytest

from aiida.common.links import LinkType
from aiida.engine.launch import run_get_node
from aiida.engine.processes.graphs.ir import LoopControl
from aiida.engine.processes.graphs.results import RestartErrors
from aiida.orm import StructureData
from tests.engine.processes.graphs.programs import restart
from tests.engine.processes.graphs.programs.restart import CalculationFailure, StepErrors

pytestmark = pytest.mark.presto


@pytest.fixture
def structure() -> StructureData:
    """An empty structure to carry through the attempts."""
    return StructureData(cell=[[1, 0, 0], [0, 1, 0], [0, 0, 1]])


@pytest.mark.usefixtures('aiida_profile_clean')
def test_restartable_recovers_within_attempts(structure: StructureData) -> None:
    """Two declared failures retry, the third attempt succeeds, the graph exits zero."""
    outputs, node = run_get_node(restart.restartable, structure=structure, max_attempts=5)
    assert node.is_finished_ok
    assert outputs['result'].value == 1.5
    iterations = node.base.links.get_outgoing(link_type=LinkType.CALL_WORK).nested()
    assert len(iterations) == 2
    attempted = [
        iterations[name].base.links.get_outgoing(link_type=LinkType.CALL_CALC).nested()['run_step'].exit_status
        for name in sorted(iterations)
    ]
    assert attempted == [410, 0]


@pytest.mark.usefixtures('aiida_profile_clean')
def test_restartable_fails_without_attempts(structure: StructureData) -> None:
    """No remaining attempt leaves the error unhandled, failing the graph."""
    outputs, node = run_get_node(restart.restartable, structure=structure, max_attempts=0)
    assert node.exit_status == 400
    assert outputs == {}


@pytest.mark.usefixtures('aiida_profile_clean')
def test_absent_arm_resets_between_iterations() -> None:
    """An iteration leaving no value arm reads as `None`, not the previous value."""
    outputs, node = run_get_node(restart.absent_arm_resets)
    assert node.is_finished_ok
    assert outputs['result'].value == 'absent'


@pytest.mark.usefixtures('aiida_profile_clean')
def test_discarded_arm_stays_out_of_loop_state() -> None:
    """A `_` element discards its arm, so the loop carries only the named value arm."""
    spec = restart.discarded_arm.build()
    loop = next(entry for entry in spec.tasks if isinstance(entry, LoopControl))
    assert sorted(loop.body.outputs) == ['attempt', 'retry', 'value']
    outputs, node = run_get_node(restart.discarded_arm)
    assert node.is_finished_ok
    assert outputs['result'].value == 2.0


@pytest.mark.usefixtures('aiida_profile_clean')
def test_report_unhandled_recovers_value() -> None:
    """A recovered value exits cleanly under the shared vocabulary."""
    outputs, node = run_get_node(restart.report_unhandled, value=1.5, error=None)
    assert node.is_finished_ok
    assert outputs['value'].value == 1.5


@pytest.mark.usefixtures('aiida_profile_clean')
def test_report_unhandled_exits_shared_status() -> None:
    """An unrecovered failure exits with the shared `UNHANDLED_FAILURE` status."""
    outputs, node = run_get_node(restart.report_unhandled, value=None, error=StepErrors.UNSTABLE)
    assert node.exit_status == 402
    assert outputs['error'].get_member() is RestartErrors.UNHANDLED_FAILURE


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    'declaration, error, key, expected',
    [
        pytest.param(
            restart.handle_walltime,
            restart.MockScientificCodeErrors.OUT_OF_WALLTIME,
            'restart_mode',
            'restart',
            id='claims-walltime',
        ),
        pytest.param(
            restart.handle_diagonalization,
            restart.MockScientificCodeErrors.COMPUTING_CHOLESKY,
            'diagonalization',
            'cg',
            id='claims-diagonalization',
        ),
        pytest.param(
            restart.handle_walltime,
            restart.MockWorkflowErrors.KNOWN_UNRECOVERABLE_FAILURE,
            'restart_mode',
            None,
            id='declines-unknown',
        ),
    ],
)
def test_handlers_claim_or_decline(
    declaration: t.Any, error: CalculationFailure, key: str, expected: str | None
) -> None:
    """A handler fixes its codes and passes anything else through unchanged."""
    outputs, node = run_get_node(declaration, error=error, parameters={})
    assert node.is_finished_ok
    assert outputs.get(key, None) == expected


@pytest.mark.usefixtures('aiida_profile_clean')
def test_chain_recovers_in_order() -> None:
    """Walltime then diagonalization each claim their code; the third attempt succeeds."""
    outputs, node = run_get_node(restart.chained_retry, parameters={}, max_attempts=5)
    assert node.is_finished_ok
    assert outputs['result'].value == 1.0
