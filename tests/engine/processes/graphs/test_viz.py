###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file       #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for Mermaid rendering of `aiida.engine.processes.graphs.viz`."""

import pytest

from aiida.engine.processes.graphs.viz import to_mermaid
from tests.engine.processes.graphs.programs import calls

pytestmark = pytest.mark.presto


def test_diamond_renders_inputs_and_wirings() -> None:
    """One graph input fans out to both placements with dependency edges."""
    chart = to_mermaid(calls.diamond.lower())
    assert chart.startswith('flowchart TD\n')
    assert 'in__x{{x}}' in chart
    assert 'in__x -->|x| add' in chart
    assert 'in__x -->|x| add_2' in chart
    assert 'add -->|result -> x| add_3' in chart
    assert 'add_2 -->|result -> y| add_3' in chart
    assert 'add_3 -->|result| out__result' in chart


def test_nested_graph_renders_pathed_placements() -> None:
    """Nested placements render flat with path-prefixed ids under their control."""
    chart = to_mermaid(calls.nested_multiply_add.lower())
    assert 'multiply_add["multiply_add"]' in chart
    assert 'multiply_add__multiply["multiply_add/multiply"]' in chart
    assert 'multiply_add -.-> multiply_add__in__x' in chart
    assert 'multiply_add -->|result -> x| add' in chart
