###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Restart loops over declared failures, with attempts as explicit loop state."""

import pytest

from aiida.common.links import LinkType
from aiida.engine.launch import run_get_node
from aiida.engine.processes.graphs.restart import RestartErrors
from aiida.orm import StructureData
from tests.engine.processes.graphs.programs import restart
from tests.engine.processes.graphs.programs.restart import StepErrors

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
    assert node.exit_status == 0
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
