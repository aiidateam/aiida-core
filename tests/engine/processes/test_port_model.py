###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `aiida.engine.processes.port_model.PortModel` declarations."""

import typing as t
from dataclasses import FrozenInstanceError, field

import pytest

from aiida.engine import PortField, PortModel
from aiida.engine.processes.port_model import fields_of
from aiida.orm import Int


class Settings(PortModel):
    count: t.Annotated[int, PortField(help='Iteration count.')] = 2
    tags: list[str] = field(default_factory=list)


class Values(PortModel):
    label: str
    nullable: int | None
    settings: Settings = Settings()
    optional: str | None = None
    node: Int | None = None


def test_models_are_frozen_keyword_only_declarations() -> None:
    first = Settings()
    second = Settings()
    assert first.tags is not second.tags
    with pytest.raises(FrozenInstanceError):
        first.count = 3
    with pytest.raises(TypeError):
        Settings(3)
    value = Values(label='test', nullable=None)
    assert Values.from_dict(value.as_dict()) == value


def test_inherited_required_fields_and_metadata() -> None:
    class Child(Settings):
        required: str

    fields = {item.name: item for item in fields_of(Child)}
    assert fields['required'].required
    assert not fields['count'].required
    assert fields['count'].help == 'Iteration count.'


@pytest.mark.parametrize('container', [int, dict, t.TypedDict('External', {'count': int})])
def test_other_types_have_no_fields(container) -> None:
    assert fields_of(container) is None
