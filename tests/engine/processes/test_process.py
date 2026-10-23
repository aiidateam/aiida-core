###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `aiida.engine.processes.process.Process` runtime inputs."""

import typing as t
from dataclasses import field
from unittest.mock import Mock

import pytest

from aiida import orm
from aiida.common.extendeddicts import AttributesFrozendict
from aiida.common.links import LinkType
from aiida.engine import PortField, PortModel, WorkChain, run_get_node
from aiida.engine.processes.persistence import CheckpointPayload

pytestmark = pytest.mark.presto


class RuntimeWorkChain(WorkChain):
    """Work chain declaring plain Python runtime types on ordinary ports."""

    @classmethod
    def define(cls, spec) -> None:
        super().define(spec)
        spec.input('label', valid_type=str)
        spec.input('count', valid_type=int)
        spec.input('enabled', valid_type=bool)
        spec.input('ratio', valid_type=float)
        spec.input('value_list', valid_type=list)
        spec.input('parameters', valid_type=dict)
        spec.input('optional', valid_type=str, required=False, default='default')
        spec.outline(cls.check_values)

    def check_values(self) -> None:
        assert isinstance(self.inputs, AttributesFrozendict)
        assert type(self.inputs['label']) is str
        assert type(self.inputs['count']) is int
        assert type(self.inputs['enabled']) is bool
        assert type(self.inputs['ratio']) is float
        assert type(self.inputs['value_list']) is list
        assert type(self.inputs['parameters']) is dict
        assert self.inputs['optional'] == 'default'


def plain_inputs() -> dict[str, object]:
    return {
        'label': 'SCF',
        'count': 2,
        'enabled': True,
        'ratio': 1.5,
        'value_list': [1, 2],
        'parameters': {'value': 1},
    }


@pytest.mark.parametrize('as_nodes', [pytest.param(False, id='plain'), pytest.param(True, id='nodes')])
@pytest.mark.usefixtures('aiida_profile_clean')
def test_runtime_values_execute_with_node_provenance(as_nodes: bool) -> None:
    """Runtime inputs are plain values while provenance links retain ORM nodes."""
    given: dict[str, object] = plain_inputs()
    if as_nodes:
        given = {name: orm.to_aiida_type(value) for name, value in given.items()}
    process = RuntimeWorkChain(inputs=given)
    try:
        assert type(process.inputs['label']) is str
        assert type(process.inputs['value_list']) is list
        process.execute()
        assert process.node.is_finished_ok
        links = process.node.base.links.get_incoming(link_type=LinkType.INPUT_WORK).nested()
        assert isinstance(links['label'], orm.Str)
        assert isinstance(links['count'], orm.Int)
        assert isinstance(links['enabled'], orm.Bool)
        assert isinstance(links['ratio'], orm.Float)
        assert isinstance(links['value_list'], orm.List)
        assert isinstance(links['parameters'], orm.Dict)
        if as_nodes:
            for name, original in given.items():
                assert isinstance(original, orm.Data)
                assert links[name].uuid == original.uuid
    finally:
        process.close()


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize('through_builder', [pytest.param(False, id='direct'), pytest.param(True, id='builder')])
def test_checkpoint_preserves_runtime_values_and_original_nodes(through_builder: bool) -> None:
    """Checkpoint restoration keeps runtime values and original node identities."""
    given: dict[str, object] = plain_inputs()
    given['label'] = orm.Str('SCF')
    given['count'] = orm.Int(2)
    if through_builder:
        builder = RuntimeWorkChain.get_builder()
        for name, value in given.items():
            setattr(builder, name, value)
        given = dict(builder._inputs())
    process = RuntimeWorkChain(inputs=given)
    restored = None
    try:
        checkpoint = CheckpointPayload.from_object(process)
        process.close()
        restored = checkpoint.decode()
        assert type(restored.inputs['label']) is str
        assert type(restored.inputs['value_list']) is list
        assert restored.inputs['count'] == 2
        links = restored.node.base.links.get_incoming(link_type=LinkType.INPUT_WORK).nested()
        assert links['label'].uuid == given['label'].uuid
        assert links['count'].uuid == given['count'].uuid
        assert restored._flat_inputs()['count'].uuid == given['count'].uuid
        restored.execute()
        assert restored.node.is_finished_ok
    finally:
        if restored is not None:
            restored.close()
        process.close()


class Settings(PortModel):
    count: t.Annotated[int, PortField(help='Iteration count.')] = 2
    tags: list[str] = field(default_factory=list)


class Values(PortModel):
    label: str
    nullable: int | None
    settings: Settings = Settings()
    optional: str | None = None
    node: orm.Int | None = None


class NamespaceWorkChain(WorkChain):
    """Work chain taking a structured namespace of runtime inputs."""

    @classmethod
    def define(cls, spec) -> None:
        super().define(spec)
        spec.input_namespace_from('values', Values)
        spec.output('label', valid_type=orm.Str)
        spec.outline(cls.echo)

    def echo(self) -> None:
        assert isinstance(self.inputs['values'], AttributesFrozendict)
        assert isinstance(self.inputs['values'].settings, AttributesFrozendict)
        self.out('label', self.node.inputs.values.label)


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize('as_nodes', [pytest.param(False, id='plain'), pytest.param(True, id='nodes')])
@pytest.mark.parametrize('as_model', [pytest.param(False, id='mapping'), pytest.param(True, id='model')])
def test_runtime_mapping_defaults_and_provenance(as_nodes: bool, as_model: bool) -> None:
    """Model inputs run as plain values while provenance links retain ORM nodes."""
    original = orm.Str('test') if as_nodes else 'test'
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


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    'given, match',
    [
        ({'label': 'test'}, 'nullable'),
        ({'nullable': None}, 'label'),
        ({'label': 'test', 'nullable': None, 'settings': {'count': 'wrong'}}, 'count'),
        ({'label': 'test', 'nullable': None, 'unknown': 1}, 'unknown'),
    ],
)
def test_invalid_namespace_inputs(given, match) -> None:
    with pytest.raises(ValueError, match=match):
        run_get_node(NamespaceWorkChain, values=given)


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize('through_builder', [pytest.param(False, id='direct'), pytest.param(True, id='builder')])
def test_checkpoint_preserves_namespace_values_and_nodes(through_builder: bool) -> None:
    """Checkpoint restoration keeps namespace runtime values and original node identities."""
    original = orm.Str('test')
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


@pytest.mark.usefixtures('aiida_profile_clean')
def test_pre_process_inputs_hook_is_honored() -> None:
    """Subclass overrides of input preparation run in the construction flow."""
    seen: list[dict] = []

    class HookedWorkChain(RuntimeWorkChain):
        def _pre_process_inputs(self, inputs):
            seen.append(dict(inputs))
            return super()._pre_process_inputs(inputs)

    HookedWorkChain(inputs=plain_inputs())
    assert seen and seen[0]['label'] == 'SCF'


def test_invalid_runtime_value_is_rejected_before_serialization(monkeypatch: pytest.MonkeyPatch) -> None:
    """Validation rejects wrong runtime types without invoking serializers."""
    serializer = Mock(side_effect=AssertionError('must validate first'))
    port = RuntimeWorkChain.spec().inputs['count']
    monkeypatch.setattr(port, '_serializer', serializer)
    given: dict[str, object] = {**plain_inputs(), 'count': 'wrong'}
    with pytest.raises(ValueError, match='count'):
        RuntimeWorkChain(inputs=given)
    serializer.assert_not_called()
