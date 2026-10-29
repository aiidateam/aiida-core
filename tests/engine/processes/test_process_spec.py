###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for structured declarations of `aiida.engine.processes.process_spec.ProcessSpec`."""

import typing as t
from dataclasses import field
from itertools import count
from pathlib import Path

import pytest

from aiida.engine import PortField, PortModel, ProcessSpec
from aiida.engine.processes.port_model import field_from_annotation
from aiida.engine.processes.process_spec import GraphProcessSpec
from aiida.orm import Int, Str


class UnsupportedPortModel(PortModel):
    """A namespace with an unpersistable field, for declaration rejection."""

    log_path: Path


class Settings(PortModel):
    count: t.Annotated[int, PortField(help='Iteration count.')] = 2
    tags: list[str] = field(default_factory=list)


class Values(PortModel):
    label: str
    nullable: int | None
    settings: Settings = Settings()
    optional: str | None = None
    node: Int | None = None


@pytest.mark.parametrize('container', [int, dict, t.TypedDict('External', {'count': int})])
def test_other_types_are_not_namespace_declarations(container) -> None:
    with pytest.raises(TypeError, match='Use a `PortModel`'):
        ProcessSpec().input_namespace_from('config', container)


def test_declared_help_reaches_ports() -> None:
    spec = ProcessSpec()
    spec.input_namespace_from('config', Settings)
    assert spec.inputs['config']['count'].help == 'Iteration count.'


def test_nested_model_default_is_preserved() -> None:
    """An enclosing model instance supplies the nested namespace defaults."""

    class Config(PortModel):
        settings: Settings = Settings(count=9)

    spec = ProcessSpec()
    spec.input_namespace_from('config', Config)
    assert spec.inputs.pre_process({'config': {}})['config']['settings']['count'] == 9


def test_nonnullable_field_rejects_explicit_none() -> None:
    """A defaulted field without a nullable annotation rejects explicit `None`."""
    spec = ProcessSpec()
    spec.input_namespace_from('config', Settings)
    inputs = spec.inputs.pre_process({'config': {'count': None}})
    message = spec.inputs.validate(inputs)
    assert message is not None and 'count' in str(message)


def test_field_factory_is_evaluated_for_each_preprocess() -> None:
    """Field factories evaluate per preparation instead of freezing at declaration."""
    counter = count(1)

    class Generated(PortModel):
        value: int = field(default_factory=lambda: next(counter))

    spec = ProcessSpec()
    spec.input_namespace_from('config', Generated)
    first = spec.inputs.pre_process({'config': {}})['config']['value']
    second = spec.inputs.pre_process({'config': {}})['config']['value']
    assert first != second


def test_unpersistable_field_types_fail_at_declaration() -> None:
    """Field types without a storage representation are rejected naming the field."""

    with pytest.raises(TypeError, match='log_path'):
        ProcessSpec().input_namespace_from('config', UnsupportedPortModel)


def test_models_are_not_constructed_by_validation() -> None:
    class DeclarationOnly(PortModel):
        value: int

        def __post_init__(self):
            raise AssertionError('the engine must not reconstruct models')

    spec = ProcessSpec()
    spec.input_namespace_from('config', DeclarationOnly)
    prepared = spec.inputs.pre_process({'config': {'value': 2}})
    assert spec.inputs.validate(prepared) is None
    assert spec.inputs['config'].validator is None


def test_namespace_validator_is_preserved() -> None:
    def validator(values, port):
        return 'must be positive' if values['count'] <= 0 else None

    spec = ProcessSpec()
    spec.input_namespace_from('config', Settings, validator=validator)
    assert spec.inputs['config'].validator is validator
    message = spec.inputs['config'].validate({'count': 0, 'tags': []})
    assert message is not None and 'must be positive' in str(message)


def test_nested_output_namespace() -> None:
    spec = ProcessSpec()
    spec.outputs_from(Values)
    assert not spec.outputs.dynamic
    assert spec.outputs['settings']['count'].valid_type == (Int,)
    assert spec.outputs['label'].valid_type == (Str,)
    assert spec.outputs['nullable'].required
    assert not spec.outputs['optional'].required
    assert spec.outputs['settings']['count'].help == 'Iteration count.'


def test_prefixed_output_namespace() -> None:
    """A prefix nests every declared output under one namespace."""
    spec = ProcessSpec()
    spec.outputs_from(Values, prefix=f'relaxed{spec.namespace_separator}')
    assert spec.outputs['relaxed']['settings']['count'].valid_type == (Int,)
    assert spec.outputs['relaxed']['label'].valid_type == (Str,)
    assert spec.outputs['relaxed']['settings']['count'].help == 'Iteration count.'


def test_outputs_from_non_model_raises() -> None:
    """Outputs cannot be declared from a non-model container."""
    with pytest.raises(TypeError, match='nothing to declare the outputs from'):
        ProcessSpec().outputs_from(int)


def test_input_from_field_override_widens_valid_type_for_none() -> None:
    """Redeclaring an input with a ``None`` default accepts ``None`` at validation."""
    spec = GraphProcessSpec()
    spec.input_from_field('count', field_from_annotation('count', int, 2))
    assert type(None) not in spec.inputs['count'].valid_type
    spec.input_from_field('count', field_from_annotation('count', int, None))
    assert type(None) in spec.inputs['count'].valid_type
    assert spec.inputs['count'].default is None


def test_pydantic_model_declares_ports() -> None:
    import pydantic

    class FlatSettings(pydantic.BaseModel):
        count: int = 2
        label: str = pydantic.Field(default='test', description='A label.')
        nullable: int | None = None

    spec = ProcessSpec()
    spec.input_namespace_from('config', FlatSettings)
    assert spec.inputs['config']['count'].valid_type == (int,)
    assert spec.inputs['config']['label'].help == 'A label.'
    assert spec.inputs.pre_process({'config': {}})['config']['count'] == 2

    class Required(pydantic.BaseModel):
        name: str

    with pytest.raises(TypeError, match='Use a `PortModel`'):
        ProcessSpec().input_namespace_from('config', int)
    spec_required = ProcessSpec()
    spec_required.input_namespace_from('config', Required)
    assert spec_required.inputs['config']['name'].required


def test_pydantic_rejections_surface_at_declaration() -> None:
    import pydantic
    from pydantic import field_validator

    class Validated(pydantic.BaseModel):
        count: int = 1

        @field_validator('count')
        @classmethod
        def _check(cls, value):
            return value

    with pytest.raises(TypeError, match='move validation'):
        ProcessSpec().input_namespace_from('config', Validated)


def test_pydantic_nested_models_declare_namespaces() -> None:
    import pydantic

    class Inner(pydantic.BaseModel):
        count: int = 1

    class Outer(pydantic.BaseModel):
        inner: Inner = Inner()
        label: str = 'test'

    spec = ProcessSpec()
    spec.input_namespace_from('config', Outer)
    assert spec.inputs['config']['inner']['count'].valid_type == (int,)
    assert spec.inputs['config']['label'].valid_type == (str,)
    assert spec.inputs.pre_process({'config': {}})['config']['inner']['count'] == 1
    assert spec.inputs.pre_process({'config': {'inner': {'count': 3}}})['config']['inner']['count'] == 3


def test_none_default_declares_optional_port_in_both_paths() -> None:
    """A `None` default stays optional with a nullable type on both declaration paths."""

    class MaybeCount(PortModel):
        count: int = None  # type: ignore[assignment]

    spec = ProcessSpec()
    spec.input_namespace_from('config', MaybeCount)
    port = spec.inputs['config']['count']
    assert not port.required
    assert port.default is None
    assert type(None) in port.valid_type

    fieldspec = GraphProcessSpec()
    fieldspec.input_from_field('count', field_from_annotation('count', int, None))
    leaf = fieldspec.inputs['count']
    assert not leaf.required
    assert leaf.default is None
    assert type(None) in leaf.valid_type


def test_optional_model_is_rejected_on_all_paths() -> None:
    """An optional structured value fails loudly instead of declaring a broken leaf."""

    class MaybeSettings(PortModel):
        settings: Settings | None = None

    with pytest.raises(TypeError, match='optional namespaces are not supported yet'):
        ProcessSpec().input_namespace_from('config', MaybeSettings)
    with pytest.raises(TypeError, match='optional namespaces are not supported yet'):
        GraphProcessSpec().input_from_field('settings', field_from_annotation('settings', Settings | None, None))
    with pytest.raises(TypeError, match='optional namespaces are not supported yet'):
        ProcessSpec().outputs_from(MaybeSettings)


def test_nested_factory_default_reaches_leaf_ports() -> None:
    """A nested default factory supplies the leaf port defaults once at declaration."""

    class ConfigWithFactory(PortModel):
        settings: Settings = field(default_factory=lambda: Settings(count=9))

    spec = ProcessSpec()
    spec.input_namespace_from('config', ConfigWithFactory)
    assert spec.inputs.pre_process({'config': {}})['config']['settings']['count'] == 9
