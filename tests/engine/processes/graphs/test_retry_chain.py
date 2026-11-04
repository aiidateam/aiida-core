###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Handler chains: decline by passthrough, priority by call order."""

import typing as t

import pytest

from aiida.engine.launch import run_get_node
from tests.engine.processes.graphs.programs import retry_chain
from tests.engine.processes.graphs.programs.retry_chain import CalculationFailure

pytestmark = pytest.mark.presto


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    'declaration, error, key, expected',
    [
        pytest.param(
            retry_chain.handle_walltime,
            retry_chain.PwCalculationErrors.OUT_OF_WALLTIME,
            'restart_mode',
            'restart',
            id='claims-walltime',
        ),
        pytest.param(
            retry_chain.handle_diagonalization,
            retry_chain.PwCalculationErrors.COMPUTING_CHOLESKY,
            'diagonalization',
            'cg',
            id='claims-diagonalization',
        ),
        pytest.param(
            retry_chain.handle_walltime,
            retry_chain.PwErrors.KNOWN_UNRECOVERABLE_FAILURE,
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
    outputs, node = run_get_node(retry_chain.chained_retry, parameters={}, max_attempts=5)
    assert node.is_finished_ok
    assert node.exit_status == 0
    assert outputs['result'].value == 1.0
