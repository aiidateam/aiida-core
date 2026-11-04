###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Declared task failures in source contracts and process runs."""

import pytest

from aiida.common.exceptions import GraphTypeCheckError
from aiida.engine import Err, ExitCode, ExitCodeEnum, Ok, Result
from aiida.engine.processes.graphs.results import error_types, result_contract
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
