###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Process-wide adaptation of ORM values at Python-valued input ports."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from aiida import orm
from aiida.calculations.arithmetic.add import ArithmeticAddCalculation
from aiida.common.extendeddicts import AttributesFrozendict
from aiida.common.links import LinkType
from aiida.engine import (
    GraphProcess,
    PortModel,
    WorkChain,
    calcfunction,
    graph_execution,
    run_get_node,
    select,
    submit,
    task_execution,
    task_from_workchain,
    workfunction,
)
from aiida.engine.processes.persistence import CheckpointPayload

pytestmark = pytest.mark.presto


class EchoWorkChain(WorkChain):
    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('parameters', valid_type=orm.Dict)
        spec.input_namespace('settings', non_db=True)
        spec.input('settings.count', valid_type=int, default=2)
        spec.input('settings.optional', valid_type=str, required=False)
        spec.output('result', valid_type=orm.Dict)
        spec.outline(cls.echo)

    def echo(self):
        assert self.inputs.settings.count == 2
        assert 'optional' not in self.inputs.settings
        self.out('result', self.inputs.parameters)


class Metadata(PortModel):
    label: str


class Prepared(PortModel):
    parameters: orm.Dict
    metadata: Metadata


@task_execution
def prepare() -> Prepared:
    return Prepared(parameters=orm.Dict({'value': 1}), metadata=Metadata(label='SCF'))


EchoStep = task_from_workchain(EchoWorkChain)


@graph_execution
def prepared_process() -> orm.Dict:
    prepared = prepare()
    output = EchoStep(parameters=prepared.parameters, metadata=prepared.metadata)
    return output.result


@pytest.mark.parametrize('node_label', [False, True])
def test_direct_metadata(node_label):
    parameters = orm.Dict({'value': 1})
    outputs, node = run_get_node(
        EchoWorkChain,
        parameters=parameters,
        metadata={'label': orm.Str('SCF') if node_label else 'SCF'},
        settings={'count': orm.Int(2)},
    )
    assert outputs['result'] is parameters
    assert node.label == 'SCF'
    assert node.base.links.get_incoming(link_type=LinkType.INPUT_WORK).one().node.uuid == parameters.uuid


def test_process_construction():
    process = EchoWorkChain(inputs={'parameters': orm.Dict(), 'metadata': {'label': orm.Str('SCF')}})
    try:
        assert process.inputs.metadata.label == 'SCF'
        assert process.inputs.settings.count == 2
    finally:
        process.close()


def test_prepared_metadata():
    outputs, node = run_get_node(GraphProcess, **prepared_process.get_launch_inputs())
    assert next(iter(outputs.values())).get_dict() == {'value': 1}
    children = [child for child in node.called if child.process_label == 'EchoWorkChain']
    assert len(children) == 1
    assert children[0].label == 'SCF'


def test_wrong_metadata_type():
    with pytest.raises(ValueError, match=r'metadata\.label'):
        EchoWorkChain(inputs={'parameters': orm.Dict(), 'metadata': {'label': orm.Int(3)}})


@calcfunction
def echo_function(value: str) -> orm.Str:
    assert isinstance(value, orm.Str)
    return orm.Str(value.value)


@pytest.mark.parametrize('as_node', [False, True])
def test_process_function_preserves_legacy_python_annotation(as_node):
    value = orm.Str('value') if as_node else 'value'
    assert echo_function.spec().inputs['value'].valid_type == (orm.Str,)
    result, node = echo_function.run_get_node(value, metadata={'label': orm.Str('SCF')})
    assert result.value == 'value'
    assert node.label == 'SCF'
    linked = node.base.links.get_incoming(link_type=LinkType.INPUT_CALC).one().node
    assert isinstance(linked, orm.Str)
    if as_node:
        assert linked.uuid == value.uuid


@workfunction
def legacy_passthrough(value: str = 'default') -> orm.Str:
    assert isinstance(value, orm.Str)
    return value


def test_workfunction_preserves_legacy_arguments_and_defaults():
    result, node = legacy_passthrough.run_get_node()
    assert result.value == 'default'
    assert node.inputs.value.uuid == result.uuid


@task_execution
def echo_task(value: str) -> str:
    assert type(value) is str
    return value


@graph_execution
def string_process(value: str) -> str:
    return echo_task(value=value)


def test_task_python_annotation_preserves_input_link():
    assert echo_task.process_class.spec().inputs['value'].valid_type == (str,)
    value = orm.Str('value')
    outputs, node = run_get_node(GraphProcess, **string_process.get_launch_inputs(value=value))
    assert next(iter(outputs.values())).value == 'value'
    child = node.called[0]
    assert child.base.links.get_incoming(link_type=LinkType.INPUT_CALC).one().node.uuid == value.uuid


def test_scheduler_metadata():
    inputs = {
        'metadata': {
            'options': {
                'resources': orm.Dict({'num_machines': 1}),
                'max_wallclock_seconds': orm.Int(300),
                'withmpi': orm.Bool(False),
                'mpirun_extra_params': orm.List(['--verbose']),
                'queue_name': orm.Str('queue'),
            }
        }
    }
    options = ArithmeticAddCalculation.spec().inputs.prepare(inputs)['metadata']['options']
    assert options == {
        'resources': {'num_machines': 1},
        'max_wallclock_seconds': 300,
        'withmpi': False,
        'mpirun_extra_params': ['--verbose'],
        'queue_name': 'queue',
    }
    assert type(options['max_wallclock_seconds']) is int
    assert type(options['withmpi']) is bool
    assert ArithmeticAddCalculation.spec().inputs['metadata']['options'].validate(options) is None


def test_submission(monkeypatch, manager):
    """Submission adapts inputs before checkpointing, without needing a live daemon."""
    runner = manager.get_runner()
    controller = Mock()
    monkeypatch.setattr(runner, '_controller', controller)
    monkeypatch.setattr(manager, 'get_daemon_client', lambda: SimpleNamespace(is_daemon_running=True))
    node = submit(EchoWorkChain, parameters=orm.Dict(), metadata={'label': orm.Str('SCF')})
    assert node.label == 'SCF'
    controller.continue_process.assert_called_once_with(node.pk, nowait=False, no_reply=True)


class RuntimeValues(PortModel):
    label: str
    count: int
    enabled: bool
    ratio: float
    items: list[int]
    parameters: dict[str, int]
    mixed: str | orm.Str = 'default'
    optional: str | None = None


class RuntimeWorkChain(WorkChain):
    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input_namespace_from('values', RuntimeValues)
        spec.outline(cls.check_values)

    def check_values(self):
        assert isinstance(self.inputs['values'], AttributesFrozendict)
        for name, expected in (
            ('label', str),
            ('count', int),
            ('enabled', bool),
            ('ratio', float),
            ('items', list),
            ('parameters', dict),
        ):
            assert type(self.inputs['values'][name]) is expected


@pytest.mark.parametrize('as_nodes', [False, True])
def test_scientific_runtime_values_and_provenance(as_nodes):
    given = {'label': 'SCF', 'count': 2, 'enabled': True, 'ratio': 1.5, 'items': [1, 2], 'parameters': {'value': 1}}
    if as_nodes:
        given = {name: orm.to_aiida_type(value) for name, value in given.items()}
    process = RuntimeWorkChain(inputs={'values': given})
    try:
        assert process.spec().inputs['values']['label'].valid_type == (str,)
        assert isinstance(process._input_sources, AttributesFrozendict)
        assert isinstance(process._input_sources['values'], AttributesFrozendict)
        if not as_nodes:
            assert type(process._input_sources['values']['parameters']) is dict
        assert process.inputs['values'].mixed == 'default'
        assert type(process.inputs['values'].mixed) is str
        assert process.inputs['values'].optional is None
        process.execute()
        links = process.node.base.links.get_incoming(link_type=LinkType.INPUT_WORK).nested()['values']
        assert isinstance(links['label'], orm.Str)
        assert isinstance(links['count'], orm.Int)
        assert isinstance(links['items'], orm.List)
        assert isinstance(links['parameters'], orm.Dict)
        if as_nodes:
            for name, original in given.items():
                assert links[name].uuid == original.uuid
    finally:
        process.close()


@pytest.mark.parametrize('through_builder', [False, True])
def test_checkpoint_preserves_runtime_values_and_original_nodes(through_builder):
    given = RuntimeValues(
        label='SCF', count=2, enabled=True, ratio=1.5, items=[1, 2], parameters={'value': 1}
    ).as_dict()
    given['label'] = orm.Str('SCF')
    given['mixed'] = orm.Str('accepted node')
    if through_builder:
        builder = RuntimeWorkChain.get_builder()
        builder.values = given
        given = builder._inputs()['values']
    process = RuntimeWorkChain(inputs={'values': given})
    restored = None
    try:
        checkpoint = CheckpointPayload.from_object(process)
        process.close()
        restored = checkpoint.decode()
        assert type(restored.inputs['values'].label) is str
        assert type(restored.inputs['values']['items']) is list
        assert restored.inputs['values'].mixed.uuid == given['mixed'].uuid
        links = restored.node.base.links.get_incoming(link_type=LinkType.INPUT_WORK).nested()['values']
        assert links['label'].uuid == given['label'].uuid
        assert links['mixed'].uuid == given['mixed'].uuid
        assert restored._flat_inputs()['values__label'].uuid == given['label'].uuid
        restored.execute()
        assert restored.node.is_finished_ok
    finally:
        if restored is not None:
            restored.close()
        process.close()


def test_invalid_runtime_value_is_rejected_before_provenance_serialization(monkeypatch):
    serializer = Mock(side_effect=AssertionError('must validate first'))
    port = RuntimeWorkChain.spec().inputs['values']['count']
    monkeypatch.setattr(port, '_serializer', serializer)
    given = RuntimeValues(label='SCF', count='wrong', enabled=True, ratio=1.5, items=[1], parameters={}).as_dict()
    with pytest.raises(ValueError, match=r'values\.count'):
        RuntimeWorkChain(inputs={'values': given})
    serializer.assert_not_called()


@graph_execution
def selected_node(value: orm.Str) -> orm.Str:
    return select(condition=True, then=value, otherwise=value).value


def test_selection_preserves_original_nodes():
    original = orm.Str('selected')
    outputs, _ = run_get_node(GraphProcess, **selected_node.get_launch_inputs(value=original))
    assert next(iter(outputs.values())).uuid == original.uuid


def test_raw_graph_boundary_preserves_input_link():
    outputs, node = run_get_node(
        GraphProcess,
        graph=orm.Dict(dict=string_process.build().to_dict()),
        graph_inputs={'value': 'raw input'},
    )
    assert next(iter(outputs.values())).value == 'raw input'
    linked = node.base.links.get_incoming(link_type=LinkType.INPUT_WORK).get_node_by_label('graph_inputs__value')
    assert isinstance(linked, orm.Str)
    child_input = node.called[0].base.links.get_incoming(link_type=LinkType.INPUT_CALC).one().node
    assert child_input.uuid == linked.uuid


def test_graph_checkpoint_preserves_original_boundary_node():
    original = orm.Str('value')
    process = GraphProcess(inputs=string_process.get_launch_inputs(value=original))
    restored = None
    try:
        assert type(process.inputs.graph_inputs['value']) is str
        checkpoint = CheckpointPayload.from_object(process)
        process.close()
        restored = checkpoint.decode()
        assert type(restored.inputs.graph_inputs['value']) is str
        assert restored.run_state.given['value'].uuid == original.uuid
    finally:
        if restored is not None:
            restored.close()
        process.close()
