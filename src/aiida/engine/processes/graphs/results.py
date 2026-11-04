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

from aiida.common.exceptions import GraphTypeCheckError
from aiida.engine.processes.exit_code import ExitCode, ExitCodeEnum

__all__ = ('Err', 'Ok', 'Result')

T = t.TypeVar('T')
E = t.TypeVar('E')


class Result(t.Generic[T, E]):
    """A task result annotated with its success type and its error enums.

    Return `Ok` for successful outputs or `Err` for a declared failure. Graph calls unpack
    into ``(value, error)``, with the absent arm reaching downstream inputs as `None`.
    Error enums must have unique, positive exit codes.
    """


@dataclass(frozen=True)
class Ok(Result[T, E]):
    """Successful task outputs, converted to provenance data nodes as usual."""

    value: T


@dataclass(frozen=True)
class Err(Result[T, E]):
    """A declared error enum member, or its optionally formatted exit code."""

    error: E


def result_contract(annotation: object) -> tuple[object, dict[str, ExitCode]]:
    """Separate successful outputs from the failures declared by a `Result` annotation."""
    if t.get_origin(annotation) is not Result:
        if annotation is Result:
            msg = 'Result requires a success type and an exit-code enum.'
            raise GraphTypeCheckError(msg)
        return annotation, {}
    success, _ = t.get_args(annotation)
    errors = error_types(annotation)
    codes: dict[str, ExitCode] = {}
    statuses: set[int] = set()
    for kind in errors:
        for name, member in kind.__members__.items():
            label = f'{kind.__name__}_{name}' if len(errors) > 1 else name
            code = member.value
            if code.status in statuses or label in codes:
                msg = f'Result error `{label}` has duplicate exit status {code.status} or label.'
                raise GraphTypeCheckError(msg)
            statuses.add(code.status)
            codes[label] = code
    if t.get_origin(success) is Result or success is Result:
        msg = 'nested Result task outputs are not supported.'
        raise GraphTypeCheckError(msg)
    return success, codes


def error_types(annotation: object) -> tuple[type[ExitCodeEnum], ...]:
    """Extract the enum alternatives from a `Result` error annotation."""
    errors = t.get_args(annotation)[1]
    kinds = t.get_args(errors) if t.get_origin(errors) in (t.Union, UnionType) else (errors,)
    if (
        not kinds
        or any(not isinstance(kind, type) or not issubclass(kind, ExitCodeEnum) for kind in kinds)
        or any(not kind.__members__ for kind in kinds)
    ):
        msg = 'Result errors must be a non-empty ExitCodeEnum, or a union of these enums.'
        raise GraphTypeCheckError(msg)
    return kinds
