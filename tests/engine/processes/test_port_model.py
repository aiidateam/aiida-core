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
    with pytest.raises(TypeError, match='takes 1 positional argument'):
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


def test_base_model_has_no_fields() -> None:
    """The bare base declares no fields, so specs raise the friendly error instead of crashing."""
    assert fields_of(PortModel) is None


def test_pydantic_flat_model_fields() -> None:
    import pydantic

    from aiida.engine.processes.port_model import _as_port_model

    class Flat(pydantic.BaseModel):
        count: int = 2
        label: str = pydantic.Field(default='x', description='A label.')
        nullable: int | None = None

    converted = _as_port_model(Flat)
    assert issubclass(converted, PortModel)
    fields = {item.name: item for item in fields_of(converted)}
    assert fields['count'].default == 2
    assert fields['nullable'].default is None
    assert not fields['nullable'].required
    assert fields['count'].required is False
    assert fields['label'].help == 'A label.'

    class Required(pydantic.BaseModel):
        name: str

    assert next(iter(fields_of(_as_port_model(Required)))).required


def test_pydantic_rejects_validators() -> None:
    import pydantic
    from pydantic import field_validator

    from aiida.engine.processes.port_model import _as_port_model

    class Validated(pydantic.BaseModel):
        count: int = 1

        @field_validator('count')
        @classmethod
        def _check(cls, value):
            return value

    with pytest.raises(TypeError, match=r'declares validators \(_check\)'):
        _as_port_model(Validated)


def test_pydantic_rejects_non_json_leaves() -> None:
    from pathlib import Path

    import pydantic

    from aiida.engine.processes.port_model import _as_port_model

    class BadLeaf(pydantic.BaseModel):
        path: Path = Path('/tmp')

    with pytest.raises(TypeError, match='pydantic field `path`'):
        _as_port_model(BadLeaf)

    class BadContainer(pydantic.BaseModel):
        tags: list[str] = pydantic.Field(default_factory=list)

    with pytest.raises(TypeError, match='pydantic field `tags`'):
        _as_port_model(BadContainer)


@pytest.mark.parametrize('option', ['alias', 'validation_alias', 'serialization_alias'])
def test_pydantic_rejects_aliases(option: str) -> None:
    """Pydantic fields addressed by alias fail loudly; ports use field names."""
    import pydantic

    from aiida.engine.processes.port_model import _as_port_model

    class Aliased(pydantic.BaseModel):
        count: int = pydantic.Field(default=1, **{option: 'c'})

    with pytest.raises(TypeError, match='uses an alias'):
        _as_port_model(Aliased)


@pytest.mark.parametrize('option', ['frozen', 'exclude'])
def test_pydantic_rejects_frozen_excluded_fields(option: str) -> None:
    """Frozen or excluded pydantic fields fail loudly; ports need plain mutable fields."""
    import pydantic

    from aiida.engine.processes.port_model import _as_port_model

    class Locked(pydantic.BaseModel):
        count: int = pydantic.Field(default=1, **{option: True})

    with pytest.raises(TypeError, match='is frozen or excluded'):
        _as_port_model(Locked)


def test_from_dict_rejects_unknown_keys() -> None:
    """Unknown mapping keys fail loudly instead of silently dropping."""
    import pydantic

    from aiida.engine.processes.port_model import _as_port_model

    class Flat(pydantic.BaseModel):
        count: int = 1

    model = _as_port_model(Flat)
    with pytest.raises(TypeError, match='unexpected keyword'):
        model.from_dict({'count': 1, 'bogus': 2})


def test_from_dict_rejects_missing_keys() -> None:
    """Missing required keys fail loudly instead of defaulting."""
    import pydantic

    from aiida.engine.processes.port_model import _as_port_model

    class Strict(pydantic.BaseModel):
        count: int

    model = _as_port_model(Strict)
    with pytest.raises(TypeError, match='missing'):
        model.from_dict({})


def test_unannotated_and_init_false_fields_are_skipped() -> None:
    """Fields without annotations or excluded from `__init__` declare no ports."""

    class Mixed(PortModel):
        count: int = 1
        constant = 5
        skipped: int = field(default=2, init=False)

    assert [item.name for item in fields_of(Mixed) or ()] == ['count']


def test_pydantic_nests_models() -> None:
    import pydantic

    from aiida.engine.processes.port_model import _as_port_model, fields_of, is_structured

    class Inner(pydantic.BaseModel):
        count: int = 1

    class Outer(pydantic.BaseModel):
        inner: Inner = Inner()
        label: str = 'test'

    converted = _as_port_model(Outer)
    assert converted is not Outer
    assert is_structured(converted)
    (inner_field, label_field) = fields_of(converted) or ()
    assert inner_field.name == 'inner'
    assert is_structured(inner_field.annotation)
    assert label_field.annotation is str
    rebuilt = converted.from_dict({'inner': {'count': 3}, 'label': 'x'})
    assert rebuilt.as_dict() == {'inner': {'count': 3}, 'label': 'x'}
    assert rebuilt.inner.as_dict() == {'count': 3}
    first, second = inner_field.default(), inner_field.default()
    assert first == second
    assert first is not second


def test_mapping_of_converts_adapted_instances() -> None:
    """Adapted instance defaults land as port mappings instead of being dropped."""
    import pydantic

    from aiida.engine.processes.process_spec import _mapping_of

    class Flat(pydantic.BaseModel):
        count: int = 2

    class Point(t.NamedTuple):
        count: int = 2

    assert _mapping_of(Settings(count=9)) == {'count': 9, 'tags': []}
    assert _mapping_of({'count': 1}) == {'count': 1}
    assert _mapping_of(Flat(count=3)) == {'count': 3}
    assert _mapping_of(Point(count=4)) == {'count': 4}
    assert _mapping_of(5) is None
    assert _mapping_of(None) is None


def test_non_json_leaf_rejection_names_model_kind() -> None:
    """Non-JSON leaves name the model kind that declared them."""
    import pydantic

    class BadModel(pydantic.BaseModel):
        payload: dict = {}

    class BadTuple(t.NamedTuple):
        payload: dict = {}

    with pytest.raises(TypeError, match='pydantic field `payload`'):
        fields_of(BadModel)
    with pytest.raises(TypeError, match='NamedTuple field `payload`'):
        fields_of(BadTuple)


def test_port_model_field_with_pydantic_default_factory() -> None:
    """A `PortModel` field holding a pydantic default factory rebuilds the model per launch."""
    import dataclasses

    import pydantic

    class Nested(pydantic.BaseModel):
        x: int = 1

    class Outer(PortModel):
        nested: Nested = dataclasses.field(default_factory=Nested)

    (field_,) = fields_of(Outer) or ()
    assert not field_.required
    rebuilt = field_.default()
    assert isinstance(rebuilt, PortModel)
    assert rebuilt.as_dict() == {'x': 1}


def test_port_model_field_with_pydantic_no_default_is_required() -> None:
    """A bare pydantic-typed `PortModel` field stays required instead of defaulting to missing."""
    import pydantic

    class Nested(pydantic.BaseModel):
        x: int = 1

    class Outer(PortModel):
        nested: Nested

    (field_,) = fields_of(Outer) or ()
    assert field_.required


def test_optional_pydantic_field_adapts_branches() -> None:
    """`Optional` pydantic annotations adapt the model branch while staying a leaf union."""
    import pydantic

    from aiida.engine.processes.port_model import field_from_annotation, is_structured

    class Nested(pydantic.BaseModel):
        x: int = 1

    field_ = field_from_annotation('nested', Nested | None)
    (branch,) = [option for option in t.get_args(field_.annotation) if option is not type(None)]
    assert is_structured(branch)
    assert fields_of(field_.annotation) is None


def test_annotated_optional_adapts_branches_and_keeps_help() -> None:
    """An `Annotated` optional model adapts its branch without losing `PortField` help."""
    import pydantic

    from aiida.engine.processes.port_model import field_from_annotation, is_structured

    class Nested(pydantic.BaseModel):
        x: int = 1

    field_ = field_from_annotation('nested', t.Annotated[Nested | None, PortField(help='A nested model.')])
    (branch,) = [option for option in t.get_args(field_.annotation) if option is not type(None)]
    assert is_structured(branch)
    assert field_.help == 'A nested model.'


def test_namedtuple_nests_models_and_keeps_help() -> None:
    """A `NamedTuple` field holding a model adapts it and keeps `PortField` help."""
    import pydantic

    from aiida.engine.processes.port_model import is_structured

    class Nested(pydantic.BaseModel):
        x: int = 1

    class Holder(t.NamedTuple):
        nested: t.Annotated[Nested, PortField(help='A nested model.')] = Nested()

    (field_,) = fields_of(Holder) or ()
    assert is_structured(field_.annotation)
    assert field_.help == 'A nested model.'
    assert field_.default().x == 1
