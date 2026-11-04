###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Declared task failures in source contracts and process runs."""

import json

import pytest

from aiida.common.exceptions import GraphTypeCheckError, GraphValidationError
from aiida.common.links import LinkType
from aiida.engine import Err, ExitCode, ExitCodeEnum, Ok, Result
from aiida.engine.launch import run_get_node
from aiida.engine.processes.graphs.ir import BranchControl, GraphIR, TaskIR
from aiida.engine.processes.graphs.results import error_types, result_contract
from tests.engine.processes.graphs.programs import results
from tests.engine.processes.graphs.programs.results import DivisionErrors

pytestmark = pytest.mark.presto


class InputErrors(ExitCodeEnum):
    """A second error enum for union contracts, with a shared member name."""

    ZERO_DENOMINATOR = ExitCode(412, 'Empty input.')


def test_result_contract_separates_success_from_failures() -> None:
    """A `Result` annotation declares its success type and its exit codes."""
    success, codes = result_contract(Result[float, DivisionErrors])
    assert success is float
    assert codes == {'ZERO_DENOMINATOR': DivisionErrors.ZERO_DENOMINATOR.value}
    assert error_types(Result[float, DivisionErrors]) == (DivisionErrors,)


def test_result_union_qualifies_shared_member_names() -> None:
    """Union alternatives keep their enum name, so shared member names stay distinct."""
    success, codes = result_contract(Result[float, DivisionErrors | InputErrors])
    assert success is float
    assert set(codes) == {'DivisionErrors_ZERO_DENOMINATOR', 'InputErrors_ZERO_DENOMINATOR'}
    assert error_types(Result[float, DivisionErrors | InputErrors]) == (DivisionErrors, InputErrors)


def test_bare_result_requires_arguments() -> None:
    """An unparameterized `Result` declares no contract."""
    with pytest.raises(GraphTypeCheckError, match='requires a success type'):
        result_contract(Result)


def test_nested_result_rejected() -> None:
    """A `Result` success type cannot itself be a `Result`."""
    with pytest.raises(GraphTypeCheckError, match='nested Result'):
        result_contract(Result[Result[float, DivisionErrors], DivisionErrors])


def test_union_requires_only_error_enums() -> None:
    """Error alternatives must be non-empty `ExitCodeEnum` subclasses."""
    with pytest.raises(GraphTypeCheckError, match='non-empty ExitCodeEnum'):
        result_contract(Result[float, DivisionErrors | int])
    with pytest.raises(GraphTypeCheckError, match='non-empty ExitCodeEnum'):
        result_contract(Result[float, DivisionErrors | None])


def test_union_rejects_duplicate_statuses() -> None:
    """Alternatives sharing an exit status cannot be told apart at runtime."""
    first = ExitCodeEnum('First', {'FAILURE': ExitCode(410, 'first')})
    second = ExitCodeEnum('Second', {'FAILURE': ExitCode(410, 'second')})
    with pytest.raises(GraphTypeCheckError, match='duplicate exit status'):
        result_contract(Result[float, first | second])


def test_empty_error_enum_rejected() -> None:
    """An enum without members declares no failure."""
    errors = ExitCodeEnum('Errors', {})
    with pytest.raises(GraphTypeCheckError, match='non-empty ExitCodeEnum'):
        result_contract(Result[float, errors])


def test_plain_annotation_has_no_contract() -> None:
    """A task without `Result` declares no failures."""
    assert result_contract(float) == (float, {})


@pytest.mark.parametrize(
    'value, message',
    [
        pytest.param(400, 'must be `ExitCode` values', id='int'),
        pytest.param(ExitCode(0, 'success'), 'positive exit status', id='zero'),
        pytest.param(ExitCode(-1, 'negative'), 'positive exit status', id='negative'),
        pytest.param(ExitCode(400), 'string message', id='missing-message'),
        pytest.param(ExitCode(400, 'ok', invalidates_cache='yes'), 'boolean cache flag', id='cache-flag'),
    ],
)
def test_invalid_error_values_rejected_at_definition(value: object, message: str) -> None:
    """Invalid enum members fail when the enum class is defined."""
    with pytest.raises((TypeError, ValueError), match=message):
        ExitCodeEnum('Errors', {'BAD': value})


def test_ok_err_carry_declared_values() -> None:
    """`Ok` holds outputs and `Err` holds a member or a formatted exit code."""
    assert Ok(0.5).value == 0.5
    assert Err(DivisionErrors.ZERO_DENOMINATOR).error is DivisionErrors.ZERO_DENOMINATOR
    code = DivisionErrors.ZERO_DENOMINATOR.value.format()
    assert Err(code).error == code


@pytest.mark.usefixtures('aiida_profile_clean')
def test_result_task_declares_value_and_error_ports() -> None:
    """A `Result` task stores its arms under `value` and `error`, registering each exit code."""
    spec = results.divide.spec()
    assert set(spec.outputs) == {'value', 'error'}
    assert not spec.outputs['value'].required
    assert not spec.outputs['error'].required
    assert spec.exit_codes['ZERO_DENOMINATOR'] == DivisionErrors.ZERO_DENOMINATOR.value


@pytest.mark.usefixtures('aiida_profile_clean')
def test_ok_result_stores_value_arm() -> None:
    """A declared success exits cleanly with its value output."""
    outputs, node = run_get_node(results.divide, numerator=1.0, denominator=2.0)
    assert node.is_finished_ok
    assert outputs['value'].value == 0.5


@pytest.mark.usefixtures('aiida_profile_clean')
def test_err_result_stores_error_arm() -> None:
    """A declared failure exits with its status and stores the error member."""
    outputs, node = run_get_node(results.divide, numerator=1.0, denominator=0.0)
    assert node.exit_status == 410
    assert node.exit_message == 'The denominator is zero.'
    assert outputs['error'].get_member() is DivisionErrors.ZERO_DENOMINATOR


@pytest.mark.usefixtures('aiida_profile_clean')
def test_error_member_feeds_recovery_input() -> None:
    """The stored error member arrives at the recovery task unwrapped."""
    outputs, node = run_get_node(results.recover, error=DivisionErrors.ZERO_DENOMINATOR)
    assert node.is_finished_ok
    assert outputs.value == -410.0


@pytest.mark.usefixtures('aiida_profile_clean')
def test_undeclared_err_fails_task() -> None:
    """An `Err` outside the declared enum fails the task itself."""
    with pytest.raises(GraphValidationError, match='undeclared exit code'):
        run_get_node(results.undeclared_error, value=1)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_bare_result_return_fails_task() -> None:
    """A `Result` task must wrap its outputs in `Ok` or `Err`."""
    with pytest.raises(GraphValidationError, match='must return `Ok`'):
        run_get_node(results.missing_result_wrapper, value=1)


def test_result_contract_in_ir() -> None:
    """The declared exit codes and the presence test survive an IR round trip."""
    spec = results.ratio.build()
    task = spec.task('divide').spec
    assert isinstance(task, TaskIR)
    assert task.exit_codes == {'ZERO_DENOMINATOR': DivisionErrors.ZERO_DENOMINATOR.value}
    assert task.outputs['value'].valid_type is not None
    assert task.outputs['error'].valid_type is not None
    branch = next(task for task in spec.tasks if isinstance(task, BranchControl))
    assert branch.condition_test == 'is_not_none'
    assert GraphIR.from_dict(json.loads(json.dumps(spec.to_dict()))).to_dict() == spec.to_dict()


def test_legacy_task_ir_without_exit_codes() -> None:
    """Task declarations stored before exit codes default to no declared failures."""
    data = results.ratio.build().task('divide').spec.to_dict()
    data.pop('exit_codes')
    assert TaskIR.from_dict(data).exit_codes == {}


@pytest.mark.usefixtures('aiida_profile_clean')
def test_zero_denominator_recovers_with_exit_zero() -> None:
    """A declared failure branches to recovery instead of failing the graph."""
    outputs, node = run_get_node(results.ratio, numerator=1.0, denominator=0.0)
    assert node.is_finished_ok
    assert node.exit_status == 0
    assert outputs['result'].value == -410.0
    calls = node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).nested()
    assert set(calls) == {'divide'}
    divided = calls['divide']
    assert divided.exit_status == 410
    assert divided.exit_message == 'The denominator is zero.'
    assert set(divided.outputs) == {'error'}
    branches = node.base.links.get_outgoing(link_type=LinkType.CALL_WORK).nested()
    assert set(branches) == {'branch_2'}
    recovered = branches['branch_2'].base.links.get_outgoing(link_type=LinkType.CALL_CALC).nested()
    assert set(recovered) == {'recover'}
    assert recovered['recover'].is_finished_ok


@pytest.mark.usefixtures('aiida_profile_clean')
def test_nonzero_denominator_reads_ratio() -> None:
    """A declared success branches past recovery and reads the value arm."""
    outputs, node = run_get_node(results.ratio, numerator=1.0, denominator=2.0)
    assert node.is_finished_ok
    assert node.exit_status == 0
    assert outputs['result'].value == 0.5
    calls = node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).nested()
    assert set(calls) == {'divide'}
    assert calls['divide'].is_finished_ok
    assert set(calls['divide'].outputs) == {'value'}
    branches = node.base.links.get_outgoing(link_type=LinkType.CALL_WORK).nested()
    assert set(branches) == {'branch_2'}
    read = branches['branch_2'].base.links.get_outgoing(link_type=LinkType.CALL_CALC).nested()
    assert set(read) == {'read_ratio'}
    assert read['read_ratio'].is_finished_ok
