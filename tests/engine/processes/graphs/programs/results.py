###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Divide/recover programs for declared task failures with a plain float arm."""

from aiida.engine import PortModel
from aiida.engine.processes.exit_code import ExitCode, ExitCodeEnum
from aiida.engine.processes.graphs.lowering import graph, task
from aiida.engine.processes.graphs.results import Err, Ok, Result
from tests.engine.processes.graphs.programs.structured import Quotient, read_quotient


class DivisionErrors(ExitCodeEnum):
    """Declared failures of the `divide` task."""

    ZERO_DENOMINATOR = ExitCode(410, 'The denominator is zero.', invalidates_cache=True)


class InputErrors(ExitCodeEnum):
    """A second error enum for union contracts."""

    NEGATIVE_NUMERATOR = ExitCode(411, 'Negative numerator: {value}')


@task
def divide(numerator: float, denominator: float) -> Result[float, DivisionErrors]:
    """Divide, declaring the zero-denominator failure instead of raising it."""
    if denominator == 0:
        return Err(DivisionErrors.ZERO_DENOMINATOR)
    return Ok(numerator / denominator)


@task
def recover_zero(error: DivisionErrors) -> float:
    """Recover from a zero denominator with a neutral fallback."""
    return 0.0


@task
def recover_negative(numerator: float, error: InputErrors) -> float:
    """Recover from a negative numerator with its absolute value."""
    return abs(numerator)


@task
def divide_signed(numerator: float, denominator: float) -> Result[float, DivisionErrors | InputErrors]:
    """Divide, declaring failures from two error enums."""
    if denominator == 0:
        return Err(DivisionErrors.ZERO_DENOMINATOR)
    if numerator < 0:
        return Err(InputErrors.NEGATIVE_NUMERATOR)
    return Ok(numerator / denominator)


@task
def union_fallback(error: DivisionErrors | InputErrors) -> float:
    """Recover from a failure declared by either error enum."""
    return 0.0


# rejected at runtime: task exit codes must be declared in a Result return annotation.
@task
def stray_ok(value: int) -> int:
    """Return `Ok` without a `Result` annotation."""
    return Ok(value)  # type: ignore[return-value] - misuse: Ok without Result


@task
def legacy_exit(value: int) -> ExitCode:
    """Return a bare `ExitCode`, preserved from before `Result` existed."""
    return ExitCode(500, 'Legacy failure.')


# rejected at runtime: task errors must come from the declared exit-code enum.
@task
def undeclared_error(value: int) -> Result[int, DivisionErrors]:
    """Return an exit code outside the declared enum."""
    return Err(ExitCode(999, 'Not declared'))  # type: ignore[arg-type] - misuse: code outside the enum


# rejected at runtime: Result tasks return Ok outputs or Err errors.
@task
def missing_result_wrapper(value: int) -> Result[int, DivisionErrors]:
    """Return bare outputs where a `Result` wrapper is required."""
    return value  # type: ignore[return-value] - misuse: bare Result return


@graph
def ratio_signed(numerator: float, denominator: float) -> float:
    """Divide, routing each declared failure to its own handler."""
    value, error = divide_signed(numerator=numerator, denominator=denominator)
    if error is None:
        selected = value
    elif error is DivisionErrors.ZERO_DENOMINATOR:
        selected = recover_zero(error=error)
    else:
        selected = recover_negative(numerator=numerator, error=error)
    return selected


@graph
def ratio_fallback(numerator: float, denominator: float) -> float:
    """Divide, recovering failures from either error enum."""
    value, error = divide_signed(numerator=numerator, denominator=denominator)
    if error is not None:
        selected = union_fallback(error=error)
    else:
        selected = value
    return selected


@graph
def matched_signed(numerator: float, denominator: float) -> float:
    """Branch on one declared member; a union handler takes the rest."""
    value, error = divide_signed(numerator=numerator, denominator=denominator)
    if error is None:
        selected = value
    elif error is DivisionErrors.ZERO_DENOMINATOR:
        selected = recover_zero(error=error)
    else:
        selected = union_fallback(error=error)
    return selected


@graph
def matched_negated(numerator: float, denominator: float) -> float:
    """Branch away from one declared member; a union handler takes the rest."""
    value, error = divide_signed(numerator=numerator, denominator=denominator)
    if error is None:
        selected = value
    elif error is not DivisionErrors.ZERO_DENOMINATOR:
        selected = union_fallback(error=error)
    else:
        selected = recover_zero(error=error)
    return selected


class AliasErrors(ExitCodeEnum):
    """A distinct enum reusing the zero-denominator status."""

    ALSO_ZERO = ExitCode(410, 'Same status, different enum.')


@task
def recover_alias(error: AliasErrors) -> float:
    """Recover from the alias enum's same-status failure."""
    return -1.0


@graph
def matched_distinct_enum(numerator: float, denominator: float) -> float:
    """Branch against a same-valued member of another enum; identity decides."""
    value, error = divide(numerator=numerator, denominator=denominator)
    if error is None:
        selected = value
    elif error is AliasErrors.ALSO_ZERO:
        selected = recover_alias(error=error)
    else:
        selected = recover_zero(error=error)
    return selected


# rejected at lowering: conditions test enum members with is, not ==.
@graph
def matched_equality(value: float) -> float:
    """Compare an error arm for equality; only `is` tests members."""
    outcome, error = divide(numerator=value, denominator=0.0)
    if error == 1:
        selected = recover_zero(error=error)
    else:
        selected = outcome
    return selected


# rejected at lowering: conditions compare against declared enum members.
@graph
def matched_unknown_member(value: float) -> float:
    """Test an unknown name; the compared member must exist."""
    outcome, error = divide(numerator=value, denominator=0.0)
    if error is MISSING:  # noqa: F821 - the unknown member is rejected
        selected = recover_zero(error=error)
    else:
        selected = outcome
    return selected


# rejected at lowering: compared members must exist on the enum.
@graph
def matched_member_typo(value: float) -> float:
    """Test a misspelled member of a known enum; the member must exist."""
    outcome, error = divide(numerator=value, denominator=0.0)
    if error is DivisionErrors.ZERO_DENOMINATORR:
        selected = recover_zero(error=error)
    else:
        selected = outcome
    return selected


@task
def divide_quotient(numerator: float, denominator: float) -> Result[Quotient, DivisionErrors]:
    """Divide, declaring a structured success instead of a leaf."""
    if denominator == 0:
        return Err(DivisionErrors.ZERO_DENOMINATOR)
    return Ok(Quotient(ratio=numerator / denominator))


@graph
def selected_ratio(numerator: float, denominator: float) -> float:
    """Bind the whole result, then select arms and fields from it."""
    outcome = divide_quotient(numerator=numerator, denominator=denominator)
    if outcome.error is None:
        selected = read_quotient(value=outcome.value)
    else:
        selected = recover_zero(error=outcome.error)
    return selected


@graph
def field_ratio(numerator: float, denominator: float) -> float:
    """Select a structured field without a call on one arm; recover on the other."""
    outcome = divide_quotient(numerator=numerator, denominator=denominator)
    if outcome.error is None:
        selected = outcome.value.ratio
    else:
        selected = recover_zero(error=outcome.error)
    return selected


@task
def noop() -> Result[None, DivisionErrors]:
    """Validate without producing a value; the success arm stays empty."""
    return Ok(None)


# rejected at runtime: structured successes reject undeclared fields.
@task
def extra_field(value: float) -> Result[Quotient, DivisionErrors]:
    """Return a structured success with an undeclared field."""
    return Ok({'ratio': value, 'typo': value})  # type: ignore[arg-type] - misuse: field outside Quotient


@graph
def quotient_ratio(numerator: float, denominator: float) -> float:
    """Divide, recovering with zero on any declared failure."""
    value, error = divide_quotient(numerator=numerator, denominator=denominator)
    if error is not None:
        selected = recover_zero(error=error)
    else:
        selected = read_quotient(value=value)
    return selected


@task
def divide_reported(numerator: float, denominator: float) -> Result[float, InputErrors]:
    """Divide, formatting the declared message with the offending input."""
    if numerator < 0:
        return Err(InputErrors.NEGATIVE_NUMERATOR.value.format(value=str(numerator)))
    return Ok(numerator / denominator)


class MaybeQuotient(PortModel):
    """A structured success with a nullable field."""

    ratio: float | None = None


@task
def divide_maybe(numerator: float, denominator: float) -> Result[MaybeQuotient, DivisionErrors]:
    """Divide, leaving the ratio empty when there is nothing to report."""
    if denominator == 0:
        return Err(DivisionErrors.ZERO_DENOMINATOR)
    if numerator == 0:
        return Ok(MaybeQuotient(ratio=None))
    return Ok(MaybeQuotient(ratio=numerator / denominator))


@graph
def direct_arm(numerator: float, denominator: float) -> float:
    """Return the success arm itself; the graph output is absent on failure."""
    value, _error = divide(numerator=numerator, denominator=denominator)
    return value


# rejected at decoration: Result requires a success type.
def bare_result(value: int) -> Result:
    """Reject an unparameterized `Result` at decoration."""
    return value  # type: ignore[return-value] - misuse: bare Result


# rejected at decoration: task results do not nest.
def nested_result(value: int) -> Result[Result[int, DivisionErrors], DivisionErrors]:
    """Reject a nested `Result` success type at decoration."""
    return Ok(Ok(value))


def structured_success(value: int) -> Result[Quotient, DivisionErrors]:
    """Accept a structured success type at decoration."""
    return Ok(Quotient(ratio=value))


# rejected at decoration: name multiple task outputs instead of a tuple.
def tuple_success(value: int) -> Result[tuple[int, int], DivisionErrors]:
    """Reject a tuple success type at decoration."""
    return Ok((value, value))


class ClashStatus(ExitCodeEnum):
    """An error enum reusing a reserved engine status."""

    CUSTOM = ExitCode(1, 'reserved status')


class ClashLabel(ExitCodeEnum):
    """An error enum reusing a reserved engine label."""

    ERROR_UNSPECIFIED = ExitCode(410, 'reserved label')


# rejected at decoration: error codes must not clash with engine codes.
def engine_clash_status() -> Result[int, ClashStatus]:
    """Reject a declared status that collides with an engine exit status."""
    raise AssertionError('building must not execute the body')


# rejected at decoration: error codes must not clash with engine codes.
def engine_clash_label() -> Result[int, ClashLabel]:
    """Reject a declared label that collides with an engine exit code."""
    raise AssertionError('building must not execute the body')
