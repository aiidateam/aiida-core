###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Namespace declarations and runtime values, independently of graph authoring."""

import typing as t
from dataclasses import FrozenInstanceError, field

import pytest

from aiida.common.extendeddicts import AttributesFrozendict
from aiida.common.links import LinkType
from aiida.engine import PortField, PortModel, ProcessSpec, WorkChain, run_get_node
from aiida.engine.processes.persistence import CheckpointPayload
from aiida.engine.processes.port_model import as_dict, fields_of
from aiida.orm import Int, Str

pytestmark = pytest.mark.presto


class Settings(PortModel):
    count: t.Annotated[int, PortField(help='Iteration count.')] = 2
    tags: list[str] = field(default_factory=list)


class Values(PortModel):
    label: str
    nullable: int | None
    settings: Settings = Settings()
    optional: str | None = None
    node: Int | None = None


class NamespaceWorkChain(WorkChain):
    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input_namespace_from('values', Values)
        spec.output('label', valid_type=Str)
        spec.outline(cls.echo)

    def echo(self):
        assert isinstance(self.inputs['values'], AttributesFrozendict)
        assert isinstance(self.inputs['values'].settings, AttributesFrozendict)
        self.out('label', self.node.inputs.values.label)


def test_models_are_frozen_keyword_only_declarations():
    first = Settings()
    second = Settings()
    assert first.tags is not second.tags
    with pytest.raises(FrozenInstanceError):
        first.count = 3
    with pytest.raises(TypeError):
        Settings(3)
    value = Values(label='test', nullable=None)
    assert Values.from_dict(value.as_dict()) == value
    assert as_dict(3) is None


def test_inherited_required_fields_and_metadata():
    class Child(Settings):
        required: str

    fields = {item.name: item for item in fields_of(Child)}
    assert fields['required'].required
    assert not fields['count'].required
    assert fields['count'].help == 'Iteration count.'
    spec = ProcessSpec()
    spec.input_namespace_from('config', Child)
    assert spec.inputs['config']['count'].help == fields['count'].help
    assert spec.inputs['config']['required'].required


@pytest.mark.parametrize('container', [int, dict, t.TypedDict('External', {'count': int})])
def test_other_types_are_not_namespace_declarations(container):
    assert fields_of(container) is None
    with pytest.raises(TypeError, match='Use a `PortModel`'):
        ProcessSpec().input_namespace_from('config', container)


@pytest.mark.parametrize('as_nodes', [False, True])
@pytest.mark.parametrize('as_model', [False, True])
def test_runtime_mapping_defaults_and_provenance(as_nodes, as_model):
    original = Str('test') if as_nodes else 'test'
    supplied = Values(label=original, nullable=None)
    given = supplied if as_model else supplied.as_dict()
    outputs, node = run_get_node(NamespaceWorkChain, values=given)
    assert node.is_finished_ok
    assert outputs['label'].value == 'test'
    assert node.inputs.values.settings.count.value == 2
    assert node.inputs.values.settings.tags.get_list() == []
    if as_nodes:
        assert node.inputs.values.label.uuid == original.uuid
    assert node.base.links.get_incoming(link_type=LinkType.INPUT_WORK).get_node_by_label('values__label')


@pytest.mark.parametrize(
    'given, match',
    [
        ({'label': 'test'}, 'nullable'),
        ({'nullable': None}, 'label'),
        ({'label': 'test', 'nullable': None, 'settings': {'count': 'wrong'}}, 'count'),
        ({'label': 'test', 'nullable': None, 'unknown': 1}, 'unknown'),
    ],
)
def test_invalid_namespace_inputs(given, match):
    with pytest.raises(ValueError, match=match):
        run_get_node(NamespaceWorkChain, values=given)


def test_models_are_not_constructed_by_validation():
    class DeclarationOnly(PortModel):
        value: int

        def __post_init__(self):
            raise AssertionError('the engine must not reconstruct models')

    spec = ProcessSpec()
    spec.input_namespace_from('config', DeclarationOnly)
    prepared = spec.inputs.pre_process({'config': {'value': 2}})
    assert spec.inputs.validate(prepared) is None
    assert spec.inputs['config'].validator is None


def test_namespace_validator_is_preserved():
    def validator(values, port):
        return 'must be positive' if values['count'] <= 0 else None

    spec = ProcessSpec()
    spec.input_namespace_from('config', Settings, validator=validator)
    assert spec.inputs['config'].validator is validator
    assert spec.inputs['config'].validate({'count': 0, 'tags': []}) is not None


def test_nested_output_namespace():
    spec = ProcessSpec()
    spec.outputs_from(Values)
    assert not spec.outputs.dynamic
    assert spec.outputs['settings']['count'].valid_type == (Int,)
    assert spec.outputs['label'].valid_type == (Str,)
    assert spec.outputs['nullable'].required
    assert not spec.outputs['optional'].required
    assert spec.outputs['settings']['count'].help == 'Iteration count.'


@pytest.mark.parametrize('through_builder', [False, True])
def test_checkpoint_preserves_runtime_values_and_nodes(through_builder):
    original = Str('test')
    given = Values(label=original, nullable=None).as_dict()
    if through_builder:
        builder = NamespaceWorkChain.get_builder()
        builder['values'] = given
        given = builder._inputs()['values']
    process = NamespaceWorkChain(inputs={'values': given})
    restored = None
    try:
        assert process.inputs['values'].label == 'test'
        checkpoint = CheckpointPayload.from_object(process)
        process.close()
        restored = checkpoint.decode()
        assert restored.inputs['values'].label == 'test'
        assert restored.inputs['values'].settings.count == 2
        assert restored._flat_inputs()['values__label'].uuid == original.uuid
        restored.execute()
        assert restored.node.is_finished_ok
    finally:
        if restored is not None:
            restored.close()
        process.close()
