###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Explicit success and declared failure contracts for graph tasks."""

from __future__ import annotations

import typing as t
from dataclasses import dataclass
from types import UnionType

from aiida.common.exceptions import GraphLanguageError, GraphTypeCheckError
from aiida.engine.processes.exit_code import ExitCode, ExitCodeEnum

__all__ = ('Err', 'Ok', 'RestartErrors', 'Result', 'catch_error')

T = t.TypeVar('T')
E = t.TypeVar('E')


class Result(t.Generic[T, E]):
    """A task result annotated with its success type and its error enums.

    Return `Ok` for successful outputs or `Err` for a declared failure. Bare graph calls
    expose the success value and propagate failures; use :func:`catch_error` to handle them.
    Error enums must have unique, positive exit codes.
    """


@dataclass(frozen=True)
class Ok(Result[T, E]):
    """Successful task outputs, converted to provenance data nodes as usual."""

    value: T


@dataclass(frozen=True)
class Err(Result[T, E]):
    """A declared error enum member, or its optionally formatted exit code."""

    error: E | ExitCode


def catch_error(invocation: object, /) -> tuple[t.Any, ExitCodeEnum | None]:
    """Expose the optional success and error arms of a direct graph-language call.

    :param invocation: A direct invocation of a fallible task or nested graph in a graph body.
    :return: The success value or the declared error member, with the inactive arm absent.
    :raises GraphLanguageError: If called as ordinary Python rather than lowered in a graph.

    The success arm is typed as `Any`: ordinary Python checkers cannot infer a call's
    declared error and success types from the enclosing intrinsic. Graph build validates both.
    """
    msg = '`catch_error` is only supported in graph bodies as `value, error = catch_error(call(...))`.'
    raise GraphLanguageError(msg)


class RestartErrors(ExitCodeEnum):
    """Failures reported by the restart machinery, not by the retried step."""

    SUB_PROCESS_EXCEPTED = ExitCode(301, 'The sub process excepted.')
    SUB_PROCESS_KILLED = ExitCode(302, 'The sub process was killed.')
    MAXIMUM_ITERATIONS_EXCEEDED = ExitCode(401, 'The maximum number of iterations was exceeded.')
    UNHANDLED_FAILURE = ExitCode(402, 'The process failed with an unhandled failure.')


def _result_contract(annotation: object) -> tuple[object, dict[str, ExitCode]]:
    """Separate successful outputs from the failures declared by a `Result` annotation."""
    if t.get_origin(annotation) is not Result:
        if annotation is Result:
            msg = 'Result requires a success type and an exit-code enum.'
            raise GraphTypeCheckError(msg)
        return annotation, {}
    success, errors = t.get_args(annotation)
    if t.get_origin(success) is Result or success is Result:
        msg = 'nested Result task outputs are not supported.'
        raise GraphTypeCheckError(msg)
    return success, _error_contract(_error_types(errors))


def _error_contract(kinds: tuple[type[ExitCodeEnum], ...]) -> dict[str, ExitCode]:
    """Return the exit codes of the declared error enums, qualifying labels for unions."""
    codes: dict[str, ExitCode] = {}
    statuses: set[int] = set()
    for kind in kinds:
        for name, member in kind.__members__.items():
            label = f'{kind.__name__}_{name}' if len(kinds) > 1 else name
            _register_error_code(codes, statuses, label, member.value)
    return codes


def _register_error_code(codes: dict[str, ExitCode], statuses: set[int], label: str, code: ExitCode) -> None:
    """Register one error code, rejecting duplicate statuses and labels."""
    if code.status in statuses or label in codes:
        msg = f'Result error `{label}` has duplicate exit status {code.status} or label.'
        raise GraphTypeCheckError(msg)
    statuses.add(code.status)
    codes[label] = code


def _error_types(errors: object) -> tuple[type[ExitCodeEnum], ...]:
    """Extract the enum alternatives from an error annotation, one enum or a union of them."""
    kinds = t.get_args(errors) if t.get_origin(errors) in (t.Union, UnionType) else (errors,)
    if (
        not kinds
        or any(not isinstance(kind, type) or not issubclass(kind, ExitCodeEnum) for kind in kinds)
        or any(not kind.__members__ for kind in kinds)
    ):
        msg = 'Result errors must be a non-empty ExitCodeEnum, or a union of these enums.'
        raise GraphTypeCheckError(msg)
    return kinds
