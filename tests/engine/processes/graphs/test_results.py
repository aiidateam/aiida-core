###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Declared task failures in source contracts, IR and process runs."""

import json
import typing as t

import pytest

from aiida.common.exceptions import GraphTypeCheckError, GraphValidationError
from aiida.common.links import LinkType
from aiida.engine import Err, ExitCode, ExitCodeEnum, Ok, Result, task
from aiida.engine.launch import run_get_node
from aiida.engine.processes.graphs.ir import BranchControl, GraphIR, ProcessTask, TaskIR
from aiida.engine.processes.graphs.restart import RestartErrors
from aiida.engine.processes.graphs.results import error_types, result_contract
from tests.engine.processes.graphs.programs import results
from tests.engine.processes.graphs.programs.results import DivisionErrors, InputErrors

pytestmark = pytest.mark.presto


@pytest.mark.parametrize(
    'annotation, success, labels',
    [
        pytest.param(Result[float, DivisionErrors], float, {'ZERO_DENOMINATOR'}, id='single-enum'),
        pytest.param(
            Result[float, DivisionErrors | InputErrors],
            float,
            {'DivisionErrors_ZERO_DENOMINATOR', 'InputErrors_NEGATIVE_NUMERATOR'},
            id='union-enums',
        ),
    ],
)
def test_result_contract_supported(annotation: t.Any, success: t.Any, labels: set[str]) -> None:
    """A `Result` annotation declares its success type and its exit codes."""
    resolved, codes = result_contract(annotation)
    assert resolved is success
    assert set(codes) == labels


def test_result_union_qualifies_shared_member_names() -> None:
    """Union alternatives keep their enum name, so shared member names stay distinct."""
    assert error_types(Result[float, DivisionErrors | InputErrors]) == (DivisionErrors, InputErrors)


class DuplicateFirst(ExitCodeEnum):
    """First enum with a status shared with `DuplicateSecond`."""

    FAILURE = ExitCode(410, 'first')


class DuplicateSecond(ExitCodeEnum):
    """Second enum with a status shared with `DuplicateFirst`."""

    FAILURE = ExitCode(410, 'second')


class EmptyErrors(ExitCodeEnum):
    """An enum without members declares no failure."""


_BAD_CACHE: t.Any = {'invalidates_cache': 'yes'}


@pytest.mark.parametrize(
    'annotation, match',
    [
        pytest.param(Result, 'requires a success type', id='bare-result'),
        pytest.param(Result[Result[float, DivisionErrors], DivisionErrors], 'nested Result', id='nested-result'),
        pytest.param(Result[float, DivisionErrors | int], 'non-empty ExitCodeEnum', id='int-alternative'),
        pytest.param(Result[float, DivisionErrors | None], 'non-empty ExitCodeEnum', id='none-alternative'),
        pytest.param(Result[float, EmptyErrors], 'non-empty ExitCodeEnum', id='empty-enum'),
        pytest.param(Result[float, DuplicateFirst | DuplicateSecond], 'duplicate exit status', id='shared-status'),
    ],
)
def test_result_contract_rejected(annotation: t.Any, match: str) -> None:
    """Error types outside non-empty `ExitCodeEnum` alternatives fail the contract."""
    with pytest.raises(GraphTypeCheckError, match=match):
        result_contract(annotation)


def test_restart_errors_contract() -> None:
    """The shared machinery vocabulary declares the `BaseRestartWorkChain` statuses."""
    success, codes = result_contract(Result[float, RestartErrors])
    assert success is float
    assert set(codes) == {
        'SUB_PROCESS_EXCEPTED',
        'SUB_PROCESS_KILLED',
        'MAXIMUM_ITERATIONS_EXCEEDED',
        'UNHANDLED_FAILURE',
    }
    assert codes['UNHANDLED_FAILURE'].status == 402


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
        pytest.param(ExitCode(400, 'ok', **_BAD_CACHE), 'boolean cache flag', id='cache-flag'),
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


@pytest.mark.parametrize(
    'declaration, match',
    [
        pytest.param(results.bare_result, 'requires a success type', id='bare-result'),
        pytest.param(results.nested_result, 'nested Result', id='nested-result'),
        pytest.param(results.structured_success, 'output namespaces are not supported', id='port-model-success'),
        pytest.param(results.named_success, 'single leaves', id='typed-dict-success'),
        pytest.param(results.tuple_success, 'single leaves', id='tuple-success'),
    ],
)
def test_result_declaration_rejected(declaration: t.Any, match: str) -> None:
    """Success types outside single leaves fail at decoration."""
    with pytest.raises(GraphTypeCheckError, match=match):
        task(declaration)


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    'declaration, labels',
    [
        pytest.param(results.divide, {'ZERO_DENOMINATOR'}, id='single-enum'),
        pytest.param(
            results.divide_signed,
            {'DivisionErrors_ZERO_DENOMINATOR', 'InputErrors_NEGATIVE_NUMERATOR'},
            id='union-enums',
        ),
    ],
)
def test_result_task_declares_value_and_error_ports(declaration: t.Any, labels: set[str]) -> None:
    """A `Result` task stores its arms under `value` and `error`, registering each exit code."""
    spec = declaration.spec()
    assert set(spec.outputs) == {'value', 'error'}
    assert not spec.outputs['value'].required
    assert not spec.outputs['error'].required
    assert labels <= set(spec.exit_codes)


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    'declaration, inputs, expected',
    [
        pytest.param(results.divide, {'numerator': 1.0, 'denominator': 2.0}, 0.5, id='value-arm'),
        pytest.param(results.divide_signed, {'numerator': 3.0, 'denominator': 2.0}, 1.5, id='union-value-arm'),
    ],
)
def test_ok_result_stores_value_arm(declaration: t.Any, inputs: dict[str, t.Any], expected: float) -> None:
    """A declared success exits cleanly with its value output."""
    outputs, node = run_get_node(declaration, **inputs)
    assert node.is_finished_ok
    assert outputs['value'].value == expected


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    'declaration, inputs, status, member',
    [
        pytest.param(
            results.divide,
            {'numerator': 1.0, 'denominator': 0.0},
            410,
            DivisionErrors.ZERO_DENOMINATOR,
            id='declared-member',
        ),
        pytest.param(
            results.divide_signed,
            {'numerator': -1.0, 'denominator': 2.0},
            411,
            InputErrors.NEGATIVE_NUMERATOR,
            id='union-member',
        ),
    ],
)
def test_err_result_stores_error_arm(
    declaration: t.Any, inputs: dict[str, t.Any], status: int, member: ExitCodeEnum
) -> None:
    """A declared failure exits with its status and stores the error member."""
    outputs, node = run_get_node(declaration, **inputs)
    assert node.exit_status == status
    assert node.exit_message == member.value.message
    assert outputs['error'].get_member() is member
    assert set(node.outputs) == {'error'}


@pytest.mark.usefixtures('aiida_profile_clean')
def test_error_member_feeds_recovery_input() -> None:
    """The stored error member arrives at the recovery task unwrapped."""
    outputs, node = run_get_node(results.recover, error=DivisionErrors.ZERO_DENOMINATOR)
    assert node.is_finished_ok
    assert t.cast(t.Any, outputs).value == -410.0


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    'declaration, inputs, match',
    [
        pytest.param(results.undeclared_error, {'value': 1}, 'undeclared exit code', id='undeclared-enum'),
        pytest.param(results.missing_result_wrapper, {'value': 1}, 'must return `Ok`', id='bare-return'),
        pytest.param(results.stray_ok, {'value': 1}, 'must be declared', id='stray-ok'),
    ],
)
def test_result_task_misuse_fails_task(declaration: t.Any, inputs: dict[str, t.Any], match: str) -> None:
    """Undeclared errors and unwrapped returns fail the task itself."""
    with pytest.raises(GraphValidationError, match=match):
        run_get_node(declaration, **inputs)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_legacy_exit_code_preserved() -> None:
    """A task without `Result` keeps exiting with a returned `ExitCode`."""
    _, node = run_get_node(results.legacy_exit, value=1)
    assert node.exit_status == 500


@pytest.mark.parametrize(
    'declaration, handle, labels',
    [
        pytest.param(results.ratio, results.divide, {'ZERO_DENOMINATOR'}, id='ratio'),
        pytest.param(results.ratio_is_none, results.divide, {'ZERO_DENOMINATOR'}, id='ratio-is-none'),
        pytest.param(
            results.signed_ratio,
            results.divide_signed,
            {'DivisionErrors_ZERO_DENOMINATOR', 'InputErrors_NEGATIVE_NUMERATOR'},
            id='signed-ratio',
        ),
    ],
)
def test_result_contract_in_ir(declaration: t.Any, handle: t.Any, labels: set[str]) -> None:
    """The declared exit codes and the presence test survive an IR round trip."""
    spec = declaration.build()
    placed = next(entry for entry in spec.tasks if isinstance(entry, ProcessTask))
    assert isinstance(placed, ProcessTask)
    assert isinstance(placed.spec, TaskIR)
    assert set(placed.spec.exit_codes) == labels
    assert placed.spec.exit_codes == {label: handle.spec().exit_codes[label] for label in labels}
    branch = next(entry for entry in spec.tasks if isinstance(entry, BranchControl))
    assert isinstance(branch, BranchControl)
    assert branch.condition_test in ('is_none', 'is_not_none')
    assert GraphIR.from_dict(json.loads(json.dumps(spec.to_dict()))).to_dict() == spec.to_dict()


def test_legacy_task_ir_without_exit_codes() -> None:
    """Task declarations stored before exit codes default to no declared failures."""
    divide = results.ratio.build().task('divide')
    assert isinstance(divide, ProcessTask)
    data = divide.spec.to_dict()
    data.pop('exit_codes')
    assert TaskIR.from_dict(data).exit_codes == {}


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    'declaration, inputs, expected, task_status, task_arm, branch_child',
    [
        pytest.param(
            results.ratio,
            {'numerator': 1.0, 'denominator': 0.0},
            -410.0,
            410,
            'error',
            'recover',
            id='ratio-zero-denominator',
        ),
        pytest.param(
            results.ratio, {'numerator': 1.0, 'denominator': 2.0}, 0.5, 0, 'value', 'read_ratio', id='ratio-ok'
        ),
        pytest.param(
            results.ratio_is_none,
            {'numerator': 1.0, 'denominator': 0.0},
            -410.0,
            410,
            'error',
            'recover',
            id='is-none-zero-denominator',
        ),
        pytest.param(
            results.ratio_is_none,
            {'numerator': 1.0, 'denominator': 2.0},
            0.5,
            0,
            'value',
            'read_ratio',
            id='is-none-ok',
        ),
        pytest.param(
            results.signed_ratio,
            {'numerator': 1.0, 'denominator': 0.0},
            -410.0,
            410,
            'error',
            'union_fallback',
            id='signed-zero-denominator',
        ),
        pytest.param(
            results.signed_ratio,
            {'numerator': -1.0, 'denominator': 2.0},
            -411.0,
            411,
            'error',
            'union_fallback',
            id='signed-negative-numerator',
        ),
        pytest.param(
            results.signed_ratio,
            {'numerator': 1.0, 'denominator': 2.0},
            0.5,
            0,
            'value',
            'read_ratio',
            id='signed-ok',
        ),
    ],
)
def test_declared_failure_branches(
    declaration: t.Any,
    inputs: dict[str, t.Any],
    expected: float,
    task_status: int,
    task_arm: str,
    branch_child: str,
) -> None:
    """A declared failure branches to recovery with exit zero; a success reads the value arm."""
    outputs, node = run_get_node(declaration, **inputs)
    assert node.is_finished_ok
    assert node.exit_status == 0
    assert outputs['result'].value == expected
    calls = node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).nested()
    assert len(calls) == 1
    (fallible,) = calls.values()
    assert fallible.exit_status == task_status
    assert set(fallible.outputs) == {task_arm}
    branches = node.base.links.get_outgoing(link_type=LinkType.CALL_WORK).nested()
    assert len(branches) == 1
    (branch,) = branches.values()
    assert branch.is_finished_ok
    assert set(branch.base.links.get_outgoing(link_type=LinkType.CALL_CALC).nested()) == {branch_child}
