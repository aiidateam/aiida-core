###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Schema dataclasses and validator registry for data nodes."""

from __future__ import annotations

import typing as t
from dataclasses import dataclass


def _non_empty(value: str) -> str:
    if not value:
        msg = 'value may not be empty'
        raise ValueError(msg)
    return value


def _positive_int(value: int) -> int:
    if value <= 0:
        msg = f'value must be positive, got {value}'
        raise ValueError(msg)
    return value


VALIDATORS: dict[str, t.Callable[[t.Any], t.Any]] = {
    'non_empty': _non_empty,
    'positive_int': _positive_int,
}

PYTHON_TYPES: dict[int, t.Any] = {
    0: str,
    1: int,
    2: float,
    3: bool,
    4: list[str],
}


def validate_values(schema: 'SchemaSpec', values: dict[str, t.Any]) -> dict[str, t.Any]:
    """Validate a payload against a persisted data-node schema."""
    validated = dict(values)

    for field in schema.fields:
        value = validated.get(field.name)
        if field.required and value in ('', None, []):
            msg = f'missing required field {field.name!r}'
            raise ValueError(msg)
        if field.validator_name is not None:
            validated[field.name] = VALIDATORS[field.validator_name](value)
        if field.name not in validated:
            if field.default_str is not None:
                validated[field.name] = field.default_str
            elif field.default_int is not None:
                validated[field.name] = field.default_int
            elif not field.required:
                validated[field.name] = None

    return validated


@dataclass(frozen=True)
class FieldSpec:
    """The persisted declaration of one data-node field."""

    name: str
    scalar_type: int
    required: bool = True
    default_str: str | None = None
    default_int: int | None = None
    validator_name: str | None = None
    description: str = ''


@dataclass(frozen=True)
class SchemaSpec:
    """The persisted declaration of one data-node schema."""

    name: str
    fields: tuple[FieldSpec, ...]
