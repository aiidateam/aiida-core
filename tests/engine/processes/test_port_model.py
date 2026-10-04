###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for saying what a namespace of ports holds with a structured type."""

import typing as t
from dataclasses import dataclass, field

import pytest
from pydantic import BaseModel

from aiida.common.extendeddicts import AttributesFrozendict
from aiida.engine import (
    PortField,
    PortModel,
    ProcessSpec,
    WorkChain,
    run_get_node,
    task_source,
)
from aiida.engine import (
    graph_execution as graph,
)
from aiida.engine import (
    task_execution as task,
)
from aiida.engine.processes.port_model import as_dict, build, fields_of, is_structured
from aiida.orm import Dict, Float, Int, JsonableData, Str, load_node


class DeclarationOnly(PortModel):
    steps: int

    def __post_init__(self):
        raise AssertionError('declaration models must not be constructed by the engine')


@task(outputs=['steps'])
def reads_namespace(config: DeclarationOnly) -> int:
    assert isinstance(config, AttributesFrozendict)
    with pytest.raises(TypeError):
        config['steps'] = 99
    return config.steps


def test_models_are_not_constructed_during_validation_or_execution():
    ports = reads_namespace.process_class.spec().inputs['config']
    assert ports.validator is None
    results, node = run_get_node(reads_namespace, config={'steps': 3})
    assert node.is_finished_ok
    assert results['steps'] == 3
    with pytest.raises(ValueError, match='required value was not provided'):
        run_get_node(reads_namespace, config={})


def test_explicit_namespace_validators_are_preserved():
    def validator(values, port):
        return 'steps must be positive' if values['steps'].value <= 0 else None

    spec = ProcessSpec()
    spec.input_namespace_from('config', DeclarationOnly, validator=validator)
    assert spec.inputs['config'].validator is validator
    assert spec.inputs['config'].validate({'steps': Int(0)}) is not None


class AsModel(PortModel):
    structure: str
    steps: int = 10


KINDS = pytest.mark.parametrize('container', (AsModel,), ids=lambda kind: kind.__name__)


class Codes(PortModel):
    kcp: t.Annotated[Int, PortField(help='The required KCP code.')]
    pw: t.Annotated[Int | None, PortField(help='The optional PW code.')] = None
    nullable: Int | None


class CodeInputs(PortModel):
    codes: t.Annotated[Codes, PortField(help='Configured calculation codes.')]


@task_source
def source_port_metadata(value: t.Annotated[Int, PortField(help='Explicit parameter help.')]) -> int:
    """Read a provenance node.

    :param value: docstring help used only without explicit metadata.
    """
    return value.value


@task_source
def source_namespace_metadata(codes: t.Annotated[Codes, PortField(help='Calculation codes.')]) -> int:
    return codes.kcp.value


@task_source
def source_docstring_help(value: t.Annotated[int, PortField()]) -> int:
    """Preserve docstring help when no help is specified in metadata.

    :param value: fallback parameter help.
    """
    return value


@task_source
def source_opaque_metadata(config: t.Annotated[Dict, PortField(help='Opaque configuration.')]) -> int:
    return config.get_dict()['steps']


def test_source_task_parameter_metadata_preserves_help_and_node_types():
    port = source_port_metadata.process_class.spec().inputs['value']
    assert port.help == 'Explicit parameter help.'
    assert port.valid_type == (Int,)
    result, node = run_get_node(source_port_metadata, value=Int(7))
    assert node.is_finished_ok
    assert result == 7


def test_source_task_namespace_metadata_preserves_nested_help():
    ports = source_namespace_metadata.process_class.spec().inputs['codes']
    assert ports.help == 'Calculation codes.'
    assert ports['kcp'].help == 'The required KCP code.'
    assert ports['pw'].help == 'The optional PW code.'
    assert not ports['pw'].required
    result, node = run_get_node(source_namespace_metadata, codes={'kcp': Int(7), 'nullable': Int(3)})
    assert node.is_finished_ok
    assert result == 7


def test_source_task_metadata_without_help_preserves_docstring_help():
    port = source_docstring_help.process_class.spec().inputs['value']
    assert port.help == 'fallback parameter help.'
    assert port.valid_type == (Int,)


def test_source_task_metadata_composes_with_orm_nodes():
    port = source_opaque_metadata.process_class.spec().inputs['config']
    assert port.help == 'Opaque configuration.'
    assert port.valid_type == (Dict,)
    assert port.required
    value = Dict(dict={'steps': 3})
    result, node = run_get_node(source_opaque_metadata, config=value)
    assert result == 3
    assert node.inputs.config.uuid == value.uuid


class OptionalParent(PortModel):
    inherited_optional: int = 1


class RequiredChild(OptionalParent):
    required: int
    explicit_optional: int = 2


class PostponedFields(PortModel):
    required: 'int'
    optional: 'int' = 1
    annotated_required: "t.Annotated[int, PortField(help='Required help.')]"


@pytest.mark.parametrize(
    'container, required',
    [(RequiredChild, {'required'}), (PostponedFields, {'required', 'annotated_required'})],
)
def test_port_model_requiredness_uses_defaults_and_inherited_fields(container, required):
    assert {item.name for item in fields_of(container) if item.required} == required
    assert all(item.annotation is int for item in fields_of(container))


@pytest.mark.parametrize('required', [True, False])
def test_metadata_composes_with_defaults(required):
    hint = t.Annotated[Dict, PortField(help='Opaque configuration.')]
    if required:

        class Marked(PortModel):
            config: hint
    else:

        class Marked(PortModel):
            config: hint = None

    (item,) = fields_of(Marked)
    assert item.annotation is Dict
    assert item.required is required
    spec = ProcessSpec()
    spec.input_namespace_from('given', Marked)
    port = spec.inputs['given']['config']
    assert port.valid_type == ((Dict,) if required else (Dict, type(None)))
    assert port.required is required
    assert port.help == item.help


def test_nested_code_fields_preserve_help_and_key_optionality():
    spec = ProcessSpec()
    spec.input_namespace_from('given', CodeInputs)
    codes = spec.inputs['given']['codes']

    assert codes.help == 'Configured calculation codes.'
    assert codes['kcp'].required
    assert codes['kcp'].help == 'The required KCP code.'
    assert not codes['pw'].required
    assert codes['pw'].help == 'The optional PW code.'
    assert codes['nullable'].required, 'a nullable value still needs a key'
    assert {item.name: item for item in fields_of(Codes)}['nullable'].annotation == Int | None


@pytest.mark.parametrize('container', [CodeInputs, Codes])
def test_explicit_task_input_types_preserve_help(container):
    @task(inputs=container)
    def described_codes(**kwargs):
        return 1

    ports = described_codes.process_class.spec().inputs
    if container is CodeInputs:
        assert ports['codes'].help == 'Configured calculation codes.'
        ports = ports['codes']
    assert ports['kcp'].help == 'The required KCP code.'
    assert ports['pw'].help == 'The optional PW code.'
    assert not ports['pw'].required


def test_postponed_annotated_help_is_preserved():
    item = {item.name: item for item in fields_of(PostponedFields)}['annotated_required']
    assert item.help == 'Required help.'
    assert item.required


def test_port_model_preserves_help_and_defaults():
    hint = t.Annotated[int, PortField(help='Number of iterations.')]

    class Container(PortModel):
        steps: hint = 10

    (item,) = fields_of(Container)
    assert item.help == 'Number of iterations.'
    assert item.annotation is int
    assert item.default == 10
    assert not item.required
    spec = ProcessSpec()
    spec.input_namespace_from('given', Container)
    assert spec.inputs['given']['steps'].help == item.help


def test_port_model_inheritance_defaults_and_constructor():
    class Extended(AsModel):
        label: str
        tags: list[str] = field(default_factory=list)

    first = Extended(structure='si', label='first')
    second = Extended(structure='ge', label='second')
    assert first.steps == 10
    assert first.tags is not second.tags
    assert build(Extended, as_dict(first)) == first
    assert [item.name for item in fields_of(Extended)] == ['structure', 'steps', 'label', 'tags']
    with pytest.raises(TypeError):
        Extended(structure='si')
    with pytest.raises(TypeError):
        Extended(structure='si', label='first', unknown=True)
    with pytest.raises(AttributeError):
        first.steps = 20


def test_typed_dict_and_named_tuple_do_not_declare_namespaces():
    class Dictionary(t.TypedDict):
        steps: int

    class Tuple(t.NamedTuple):
        steps: int

    for container in (Dictionary, Tuple):
        assert fields_of(container) is None
        assert not is_structured(container)
        assert as_dict(container(steps=1)) is None
        with pytest.raises(TypeError, match='Use a `PortModel`'):
            ProcessSpec().input_namespace_from('given', container)


def test_arbitrary_dataclasses_do_not_declare_namespaces():
    @dataclass
    class ExternalConfig:
        steps: int = 10

    assert fields_of(ExternalConfig) is None
    assert not is_structured(ExternalConfig)
    assert as_dict(ExternalConfig()) is None
    with pytest.raises(TypeError, match='Use a `PortModel`'):
        ProcessSpec().input_namespace_from('given', ExternalConfig)


def test_pydantic_models_do_not_declare_namespaces():
    class ExternalModel(BaseModel):
        steps: int = 10

    assert fields_of(ExternalModel) is None
    assert not is_structured(ExternalModel)
    assert as_dict(ExternalModel()) is None


@KINDS
def test_the_fields_of_a_container_are_read(container):
    """Each kind says the same thing in different words, and this is what it says."""
    assert [(field.name, field.annotation) for field in fields_of(container)] == [
        ('structure', str),
        ('steps', int),
    ]


@KINDS
def test_which_fields_have_to_be_given(container):
    """Only fields without defaults must be supplied."""
    required = {field.name for field in fields_of(container) if field.required}

    assert required == {'structure'}


@pytest.mark.parametrize('value', (3, 'three', [3], {'a': 3}, None, AsModel))
def test_what_is_not_a_container(value):
    """Plenty of things hold values without saying which they are, and a class is not one of its instances."""
    assert not is_structured(type(value)) or value is AsModel
    assert as_dict(value) is None


@KINDS
def test_a_container_is_read_and_written_back(container):
    """What a structured type holds is what it is built back from, so the trip through the ports is a round one."""
    values = {'structure': 'si', 'steps': 3}
    built = build(container, values)

    assert as_dict(built) == values


@KINDS
def test_a_container_names_a_namespace_of_ports(container):
    """The fields of a structured type are the ports of the namespace it names, wherever it is declared."""

    class Runner(WorkChain):
        @classmethod
        def define(cls, spec):
            super().define(spec)
            spec.input_namespace_from('relax', container)
            spec.outline()

    ports = Runner.spec().inputs['relax']

    assert sorted(ports) == ['steps', 'structure']
    assert ports['structure'].valid_type == (Str,)
    assert not ports['steps'].required


def test_something_that_is_not_a_container_is_refused():
    """Nothing can be read off a class that does not say what it holds."""

    class Runner(WorkChain):
        @classmethod
        def define(cls, spec):
            super().define(spec)
            spec.input_namespace_from('relax', int)

    with pytest.raises(TypeError, match='`int` is not a structured type'):
        Runner.spec()


@task(outputs=['steps', 'kind'])
def takes_model(given: AsModel) -> tuple[int, str]:
    assert isinstance(given, AttributesFrozendict)
    assert not isinstance(given, PortModel)
    assert given.steps == given['steps']
    return given.steps, type(given).__name__


TAKES = {AsModel: takes_model}


@task
def returns_model(structure: str) -> AsModel:
    return AsModel(structure=structure, steps=3)


RETURNS = {AsModel: returns_model}


@KINDS
def test_a_task_takes_a_container_as_a_namespace(container):
    """A parameter annotated with a structured type takes one, so the task declares the namespace it names."""
    relax = TAKES[container]

    assert sorted(relax.process_class.spec().inputs['given']) == ['steps', 'structure']

    results, node = run_get_node(relax, given=build(container, {'structure': 'si', 'steps': 3}))

    assert node.is_finished_ok, node.exit_message
    assert results['steps'] == 3
    assert sorted(node.base.links.get_incoming().all_link_labels()) == ['given__steps', 'given__structure']


@KINDS
def test_a_task_receives_an_attribute_accessible_namespace(container):
    """Models declare ports; task arguments hold the validated namespace values."""
    results, _ = run_get_node(TAKES[container], given={'structure': 'si', 'steps': 3})

    assert results['kind'] == 'AttributesFrozendict'


@KINDS
def test_a_returned_container_names_the_outputs(container):
    """A structured type says which output each of its fields is, on the way out as much as on the way in."""
    relax = RETURNS[container]

    assert sorted(relax.process_class.spec().outputs) == ['steps', 'structure']

    results, node = run_get_node(relax, structure='si')

    assert node.is_finished_ok, node.exit_message
    assert (results['structure'], results['steps']) == ('si', 3)


@task(outputs=['structure'])
def prepare(label: str) -> str:
    return f'{label}-relaxed'


@task(outputs=['seen'])
def sees(given: AsModel) -> str:
    return given.structure


def test_a_field_takes_what_another_task_produced():
    """A structured type is a way of saying what a namespace holds, so a graph wires into one field of it."""

    @graph
    def prepare_and_relax(label):
        return {'seen': sees(given={'structure': prepare(label=label).structure}).seen}

    results, node = run_get_node(prepare_and_relax, label='si')

    assert node.is_finished_ok, node.exit_message
    assert results['seen'] == 'si-relaxed'


def untyped(structure, steps):
    """A function from somewhere else, whose signature says nothing about what it takes."""
    return f'{structure}/{steps}'


described = task(untyped, inputs=AsModel, outputs=AsModel)


def test_a_task_is_described_where_it_is_placed():
    """A function that carries no annotations is described by the structured type the task is declared with."""
    spec = described.process_class.spec()

    assert {name: port.required for name, port in spec.inputs.items() if name != 'metadata'} == {
        'structure': True,
        'steps': False,
    }
    assert sorted(spec.outputs) == ['steps', 'structure']


def test_a_described_task_takes_its_fields_one_by_one():
    """The fields are the ports at the top level, since the function takes them as its own parameters."""

    @task(inputs=AsModel, outputs=['seen'])
    def joined(structure, steps):
        return f'{structure}/{steps}'

    results, node = run_get_node(joined, structure='si', steps=3)

    assert node.is_finished_ok, node.exit_message
    assert results['seen'] == 'si/3'
    assert sorted(node.base.links.get_incoming().all_link_labels()) == ['steps', 'structure']


def test_describing_a_task_with_what_it_cannot_take_is_refused():
    """A field the function has no parameter for would be a port nothing reads."""
    with pytest.raises(TypeError, match="names \\['steps', 'structure'\\], which the function does not take"):

        @task(inputs=AsModel)
        def takes_neither(other):
            return other


def test_describing_a_task_with_something_that_is_not_a_container_is_refused():
    """Nothing can be read off a class that does not say what it holds."""
    with pytest.raises(TypeError, match='`int` is not a structured type'):

        @task(inputs=int)
        def whatever(x):
            return x


class Kpoints(PortModel):
    mesh: int = 4
    offset: float = 0.0


class Nested(PortModel):
    structure: str
    kpoints: Kpoints = Kpoints()


@task(outputs=['seen'])
def sees_nested(given: Nested) -> str:
    return f'{given.structure}/{given.kpoints.mesh}/{type(given.kpoints).__name__}'


@task(outputs=['mesh'])
def choose_mesh(structure: str) -> int:
    return len(structure) * 2


@pytest.mark.parametrize('container', (Nested,))
def test_a_field_that_is_a_container_names_a_namespace_under_this_one(container):
    """A structured type nests, and so does a namespace, so the one maps onto the other all the way down."""

    class Runner(WorkChain):
        @classmethod
        def define(cls, spec):
            super().define(spec)
            spec.input_namespace_from('relax', container)
            spec.outline()

    ports = Runner.spec().inputs['relax']

    assert sorted(ports['kpoints']) == ['mesh', 'offset']
    assert Int in ports['kpoints']['mesh'].valid_type


def test_nested_namespaces_have_attribute_access():
    """Nested model declarations produce nested namespace mappings at runtime."""
    results, node = run_get_node(sees_nested, given=Nested(structure='si'))

    assert node.is_finished_ok, node.exit_message
    assert results['seen'] == 'si/4/AttributesFrozendict'
    assert sorted(node.base.links.get_incoming().all_link_labels()) == [
        'given__kpoints__mesh',
        'given__kpoints__offset',
        'given__structure',
    ]


def test_a_task_fills_one_field_of_a_nested_container():
    """The fields are ordinary ports however deep they sit, so a graph wires into one of them."""

    @graph
    def pick_then_see(structure):
        chosen = choose_mesh(structure=structure)
        return {'seen': sees_nested(given={'structure': structure, 'kpoints': {'mesh': chosen.mesh}}).seen}

    (edge,) = pick_then_see.build().dependencies

    assert (edge.target, edge.target_port) == ('sees_nested', 'given.kpoints.mesh')

    results, node = run_get_node(pick_then_see, structure='silicon')

    assert node.is_finished_ok, node.exit_message
    assert results['seen'] == 'silicon/14/AttributesFrozendict', 'the mesh the other task chose, not the default'


class Spacing(PortModel):
    """A structured type declaring a node type beside a plain one."""

    spacing: Float
    points: int = 4


@task(outputs=['seen'])
def sees_spacing(given: Spacing) -> str:
    return f'{type(given.spacing).__name__}={given.spacing.value}/{type(given.points).__name__}={given.points}'


def test_a_field_declaring_a_node_takes_that_node():
    """What the structured type says a field holds is what the port takes, node types among them."""
    ports = sees_spacing.process_class.spec().inputs['given']

    assert ports['spacing'].valid_type == (Float,)
    assert Int in ports['points'].valid_type


@pytest.mark.parametrize('as_nodes', (False, True), ids=('plain-values', 'nodes'))
def test_a_value_is_converted_to_what_the_field_declares(as_nodes):
    """A port turns a plain value into the node it takes, which a field of a structured type inherits."""
    given = {'spacing': Float(0.2), 'points': Int(8)} if as_nodes else {'spacing': 0.2, 'points': 8}
    results, node = run_get_node(sees_spacing, given=given)

    assert node.is_finished_ok, node.exit_message
    assert isinstance(node.inputs.given.spacing, Float), 'stored as the node the field declares'
    assert results['seen'] == 'Float=0.2/int=8', 'and handed over as the field declares it, node or value'


class Conf(PortModel):
    tolerance: float = 1e-6


class Opaque(PortModel):
    structure: str
    config: JsonableData


@task(outputs=['seen'])
def consumes_opaque(given: Opaque) -> str:
    return f'{given.structure}/{given.config.obj.tolerance}'


def test_opaque_field_uses_an_explicit_orm_node():
    value = JsonableData(Conf(tolerance=0.1))
    results, node = run_get_node(consumes_opaque, given=Opaque(structure='si', config=value))
    assert node.is_finished_ok, node.exit_message
    assert results['seen'] == 'si/0.1'
    assert node.inputs.given.config.uuid == value.uuid
    assert sorted(node.base.links.get_incoming().all_link_labels()) == ['given__config', 'given__structure']
    assert load_node(value.pk).obj.tolerance == 0.1


@task(outputs=['seen'])
def consumes_opaque_parameter(config: JsonableData) -> float:
    return config.obj.tolerance


def test_opaque_parameter_stays_an_orm_node():
    value = JsonableData(Conf(tolerance=0.25))
    results, node = run_get_node(consumes_opaque_parameter, config=value)
    assert results['seen'] == 0.25
    assert node.inputs.config.uuid == value.uuid
    assert node.base.links.get_incoming().all_link_labels() == ['config']
