###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Structured task outputs: model returns, whole bindings, and field selection."""

import typing as t

import pytest

from aiida.common.exceptions import GraphValidationError
from aiida.engine.launch import run_get_node
from tests.engine.processes.graphs.programs import structured_outputs


@pytest.mark.usefixtures('aiida_profile_clean')
def test_plain_port_model_task_stores_fields() -> None:
    """A plain task may return a structured type; each field stores as one output."""
    outputs, node = run_get_node(structured_outputs.make_quotient, numerator=1.0, denominator=2.0)
    assert node.is_finished_ok
    assert outputs['ratio'].value == 0.5


@pytest.mark.usefixtures('aiida_profile_clean')
def test_mapping_return_omits_optional_field() -> None:
    """A mapping return may leave an optional field out; only the returned fields store."""
    outputs, node = run_get_node(structured_outputs.scaled_mapping)
    assert node.is_finished_ok
    assert {name: output.value for name, output in outputs.items()} == {'ratio': 0.5}


@pytest.mark.usefixtures('aiida_profile_clean')
def test_required_output_rejects_none() -> None:
    """A nullable field without a default declares a required output, so `None` fails the task."""
    with pytest.raises(GraphValidationError, match='`value` is a required output'):
        run_get_node(structured_outputs.nullable_none)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_plain_port_model_output_wires_into_input() -> None:
    """A structured task output wires field by field into a structured task input."""
    outputs, node = run_get_node(structured_outputs.quotient_double, numerator=1.0, denominator=2.0)
    assert node.is_finished_ok
    assert outputs['result'].value == 0.5


@pytest.mark.usefixtures('aiida_profile_clean')
def test_nested_namespace_selects_two_levels() -> None:
    """A two-level namespace select wires into a structured task input."""
    outputs, node = run_get_node(structured_outputs.nested_select)
    assert node.is_finished_ok
    assert outputs['result'].value == 0.5


@pytest.mark.usefixtures('aiida_profile_clean')
def test_task_returning_structured_input_stores_fields() -> None:
    """A structured input returned unchanged arrives as a mapping and stores field by field."""
    outputs, node = run_get_node(structured_outputs.nested_passthrough)
    assert node.is_finished_ok
    assert outputs['result'].value == 0.5


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    'flag, expected',
    [
        pytest.param(True, 0.5, id='alias-arm'),
        pytest.param(False, 0.25, id='call-arm'),
    ],
)
def test_dotted_field_alias_in_branch_arm(flag: bool, expected: float) -> None:
    """A branch arm aliasing a two-level field bound before the branch exposes it under the assigned name."""
    outputs, node = run_get_node(structured_outputs.dotted_alias_arm, flag=flag, ratio=0.25)
    assert node.is_finished_ok
    assert outputs['result'].value == expected


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    'declaration, inputs, expected',
    [
        pytest.param(structured_outputs.forward_plain, {'value': 2}, 11, id='forward-namespace'),
        pytest.param(structured_outputs.selected_plain, {'value': 2}, 11, id='select-fields'),
    ],
)
def test_whole_outputs_wire_and_select(declaration: t.Any, inputs: dict[str, int], expected: int) -> None:
    """A whole task outputs namespace wires into a model input, or selects fields after one binding."""
    outputs, node = run_get_node(declaration, **inputs)
    assert node.is_finished_ok
    assert outputs['result'].value == expected
