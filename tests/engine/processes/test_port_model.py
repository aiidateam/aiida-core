###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `aiida.engine.processes.port_model.PortModel` declarations."""

import dataclasses
import typing as t
from dataclasses import FrozenInstanceError, field

import pytest

from aiida.engine import PortField, PortModel
from aiida.engine.processes.port_model import _fields_of
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
    with pytest.raises(TypeError, match='takes 1 positional argument'):
        Settings(3)
    value = Values(label='test', nullable=None)
    assert Values.from_dict(value.as_dict()) == value


def test_inherited_required_fields_and_metadata() -> None:
    class Child(Settings):
        required: str

    fields = {item.name: item for item in _fields_of(Child)}
    assert fields['required'].required
    assert not fields['count'].required
    assert fields['count'].help == 'Iteration count.'


@pytest.mark.parametrize('container', [int, dict, t.TypedDict('External', {'count': int})])
def test_other_types_have_no_fields(container) -> None:
    assert _fields_of(container) is None


def test_base_model_has_no_fields() -> None:
    """The bare base declares no fields, so specs raise the friendly error instead of crashing."""
    assert _fields_of(PortModel) is None


def test_model_spreads_with_double_star() -> None:
    """A model spreads its fields into a call."""
    assert dict(**Settings(count=3)) == {'count': 3, 'tags': []}


def test_model_item_access_reads_fields() -> None:
    """Item access reads what attribute access reads."""
    model = Settings(count=3)
    assert model['count'] == model.count == 3
    assert list(model) == ['count', 'tags']


def test_model_item_access_rejects_unknown_fields() -> None:
    """An unknown field raises `KeyError` naming the model."""
    with pytest.raises(KeyError, match='has no field'):
        Settings()['missing']


def test_model_keys_field_rejected() -> None:
    """A field named `keys` would shadow spreading."""

    with pytest.raises(TypeError, match='reserved for spreading'):

        class Clashing(PortModel):
            keys: str


def test_model_forward_reference_declares() -> None:
    """A field referencing a later-defined model declares without resolving hints."""

    class Early(PortModel):
        later: 'Late'

    class Late(PortModel):
        count: int = 0

    assert [declared.name for declared in dataclasses.fields(Early)] == ['later']
