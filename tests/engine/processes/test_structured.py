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
from decimal import Decimal

import pytest
from pydantic import BaseModel, ConfigDict, field_serializer
from pydantic import Field as ModelField
from typing_extensions import NotRequired, Required

from aiida.engine import (
    PortField,
    ProcessSpec,
    Whole,
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
from aiida.engine.processes.structured import as_dict, build, fields_of, is_structured
from aiida.orm import Float, Int, JsonableData, Str, load_node


class AsTypedDict(t.TypedDict):
    structure: str
    steps: int


class AsModel(BaseModel):
    structure: str
    steps: int = 10


@dataclass
class AsDataclass:
    structure: str
    steps: int = 10


class AsTuple(t.NamedTuple):
    structure: str
    steps: int = 10


KINDS = pytest.mark.parametrize(
    'container', (AsTypedDict, AsModel, AsDataclass, AsTuple), ids=lambda kind: kind.__name__
)


class Codes(t.TypedDict):
    kcp: t.Annotated[Int, PortField(help='The required KCP code.')]
    pw: NotRequired[t.Annotated[Int, PortField(help='The optional PW code.')]]
    nullable: Int | None


class CodeInputs(t.TypedDict):
    codes: t.Annotated[Codes, PortField(help='Configured calculation codes.')]


@task_source
def source_port_metadata(value: t.Annotated[Int, PortField(help='Explicit parameter help.')]) -> int:
    """Read a provenance node.

    :param value: docstring help used only without explicit metadata.
    """
    return value.value


@task_source
def source_namespace_metadata(codes: t.Annotated[Codes, PortField(help='Calculation codes.')]) -> int:
    return codes['kcp'].value


@task_source
def source_docstring_help(value: t.Annotated[int, PortField()]) -> int:
    """Preserve docstring help when no help is specified in metadata.

    :param value: fallback parameter help.
    """
    return value


@task_source
def source_whole_metadata(config: t.Annotated[AsDataclass, Whole, PortField(help='Opaque configuration.')]) -> int:
    return config.steps


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


def test_source_task_metadata_composes_with_whole():
    port = source_whole_metadata.process_class.spec().inputs['config']
    assert port.help == 'Opaque configuration.'
    assert port.valid_type == (JsonableData,)
    assert port.required


class OptionalParent(t.TypedDict, total=False):
    inherited_optional: int


class RequiredChild(OptionalParent):
    required: int
    explicit_optional: NotRequired[int]


class OptionalChild(RequiredChild, total=False):
    optional: int
    explicit_required: Required[int]


class PostponedKeys(t.TypedDict, total=False):
    required: 'Required[int]'
    optional: 'NotRequired[int]'
    annotated_required: "t.Annotated[Required[int], PortField(help='Required help.')]"


class PostponedRequiredKeys(t.TypedDict):
    required: 'int'
    optional: "t.Annotated[NotRequired[int], PortField(help='Optional help.')]"


@pytest.mark.parametrize(
    'container, required',
    [
        (RequiredChild, {'required'}),
        (OptionalChild, {'required', 'explicit_required'}),
        (PostponedKeys, {'required', 'annotated_required'}),
        (PostponedRequiredKeys, {'required'}),
    ],
)
def test_typed_dict_requiredness_uses_resolved_markers_and_inherited_totality(container, required):
    assert {item.name for item in fields_of(container) if item.required} == required
    assert all(item.annotation is int for item in fields_of(container))


@pytest.mark.parametrize('required', [True, False])
@pytest.mark.parametrize('outer_metadata', [True, False])
def test_metadata_composes_with_key_requiredness(required, outer_metadata):
    marker = Required if required else NotRequired
    annotated = t.Annotated[AsDataclass, Whole, PortField(help='Keep this configuration whole.')]
    hint = (
        t.Annotated[marker[AsDataclass], Whole, PortField(help='Keep this configuration whole.')]
        if outer_metadata
        else marker[annotated]
    )

    class Marked(t.TypedDict):
        config: hint

    (item,) = fields_of(Marked)

    assert item.annotation is AsDataclass
    assert item.required is required
    assert item.whole
    assert item.help == 'Keep this configuration whole.'

    spec = ProcessSpec()
    spec.input_namespace_from('given', Marked)
    port = spec.inputs['given']['config']
    assert port.valid_type == ((JsonableData,) if required else (JsonableData, type(None)))
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
    item = {item.name: item for item in fields_of(PostponedKeys)}['annotated_required']
    assert item.help == 'Required help.'
    assert item.required


@pytest.mark.parametrize('kind', ['dataclass', 'tuple', 'model'])
def test_structured_readers_preserve_help_and_defaults(kind):
    hint = t.Annotated[int, PortField(help='Number of iterations.')]
    if kind == 'dataclass':

        @dataclass
        class Container:
            steps: hint = 10
    elif kind == 'tuple':

        class Container(t.NamedTuple):
            steps: hint = 10
    else:

        class Container(BaseModel):
            steps: hint = 10

    (item,) = fields_of(Container)
    assert item.help == 'Number of iterations.'
    assert item.annotation is int
    assert item.default == 10
    assert not item.required
    spec = ProcessSpec()
    spec.input_namespace_from('given', Container)
    assert spec.inputs['given']['steps'].help == item.help


def test_model_descriptions_are_help_unless_explicitly_overridden():
    class Described(BaseModel):
        steps: int = ModelField(default=10, description='Model description.')
        override: t.Annotated[int, PortField(help='Explicit help.')] = ModelField(description='Other description.')
        unrelated: t.Annotated[int, 'Not port help.']

    items = {item.name: item for item in fields_of(Described)}
    assert items['steps'].help == 'Model description.'
    assert items['override'].help == 'Explicit help.'
    assert items['unrelated'].help is None
    spec = ProcessSpec()
    spec.input_namespace_from('given', Described)
    assert spec.inputs['given']['steps'].help == 'Model description.'
    assert spec.inputs['given']['override'].help == 'Explicit help.'


@KINDS
def test_the_fields_of_a_container_are_read(container):
    """Each kind says the same thing in different words, and this is what it says."""
    assert [(field.name, field.annotation) for field in fields_of(container)] == [
        ('structure', str),
        ('steps', int),
    ]


@KINDS
def test_which_fields_have_to_be_given(container):
    """A field with a default need not be given, and a `t.TypedDict` gives no default so all of them do."""
    required = {field.name for field in fields_of(container) if field.required}

    assert required == ({'structure', 'steps'} if container is AsTypedDict else {'structure'})


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

    # An instance of a `t.TypedDict` is a dict, so it is already what it would be flattened into.
    assert (built if container is AsTypedDict else as_dict(built)) == values


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
    assert ports['steps'].required is (container is AsTypedDict)


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
def takes_typed_dict(given: AsTypedDict) -> tuple[int, str]:
    return given['steps'], type(given).__name__


@task(outputs=['steps', 'kind'])
def takes_model(given: AsModel) -> tuple[int, str]:
    return given.steps, type(given).__name__


@task(outputs=['steps', 'kind'])
def takes_dataclass(given: AsDataclass) -> tuple[int, str]:
    return given.steps, type(given).__name__


@task(outputs=['steps', 'kind'])
def takes_tuple(given: AsTuple) -> tuple[int, str]:
    return given.steps, type(given).__name__


TAKES = {AsTypedDict: takes_typed_dict, AsModel: takes_model, AsDataclass: takes_dataclass, AsTuple: takes_tuple}


@task
def returns_model(structure: str) -> AsModel:
    return AsModel(structure=structure, steps=3)


@task
def returns_dataclass(structure: str) -> AsDataclass:
    return AsDataclass(structure=structure, steps=3)


@task
def returns_tuple(structure: str) -> AsTuple:
    return AsTuple(structure=structure, steps=3)


@task
def returns_typed_dict(structure: str) -> AsTypedDict:
    return AsTypedDict(structure=structure, steps=3)


RETURNS = {
    AsTypedDict: returns_typed_dict,
    AsModel: returns_model,
    AsDataclass: returns_dataclass,
    AsTuple: returns_tuple,
}


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
def test_a_task_is_handed_the_container_it_named(container):
    """The namespace holds what the structured type said it would, so the function is given one of those back."""
    results, _ = run_get_node(TAKES[container], given={'structure': 'si', 'steps': 3})

    assert results['kind'] == (dict.__name__ if container is AsTypedDict else container.__name__)


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


class Money(BaseModel):
    """A model that says how to render a value AiiDA has no way to store."""

    amount: Decimal

    @field_serializer('amount')
    def _dump_amount(self, value: Decimal) -> str:
        return str(value)


@task(outputs=['kind', 'doubled'])
def double(money: Money) -> tuple[str, str]:
    return type(money.amount).__name__, str(money.amount * 2)


def test_a_model_says_how_its_own_fields_are_stored():
    """What a model renders to is what is stored, and building it back gives the field its own type again."""
    results, node = run_get_node(double, money=Money(amount=Decimal('0.10')))

    assert node.is_finished_ok, node.exit_message
    assert node.inputs.money.amount == '0.10', 'stored as the model rendered it'
    assert results['kind'] == 'Decimal', 'and handed back as the type the model declares'
    assert results['doubled'] == '0.20'


def untyped(structure, steps):
    """A function from somewhere else, whose signature says nothing about what it takes."""
    return f'{structure}/{steps}'


described = task(untyped, inputs=AsModel, outputs=AsDataclass)


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


class Kpoints(BaseModel):
    mesh: int = 4
    offset: float = 0.0


class Nested(BaseModel):
    structure: str
    kpoints: Kpoints = Kpoints()


@dataclass
class NestedDataclass:
    structure: str
    kpoints: Kpoints = field(default_factory=Kpoints)


@task(outputs=['seen'])
def sees_nested(given: Nested) -> str:
    return f'{given.structure}/{given.kpoints.mesh}/{type(given.kpoints).__name__}'


@task(outputs=['mesh'])
def choose_mesh(structure: str) -> int:
    return len(structure) * 2


@pytest.mark.parametrize('container', (Nested, NestedDataclass), ids=('model', 'dataclass'))
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


def test_a_nested_container_is_handed_back_whole():
    """What the function named is what it is given, however deep the structured type goes."""
    results, node = run_get_node(sees_nested, given=Nested(structure='si'))

    assert node.is_finished_ok, node.exit_message
    assert results['seen'] == 'si/4/Kpoints'
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
    assert results['seen'] == 'silicon/14/Kpoints', 'the mesh the other task chose, not the default'


class Spacing(BaseModel):
    """A structured type declaring a node type beside a plain one."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

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


class Conf(BaseModel):
    """Opaque configuration, which nothing wires into."""

    tolerance: float = 1e-6


class Opaque(BaseModel):
    structure: str
    config: t.Annotated[Conf, Whole] = Conf()


@dataclass
class OpaqueDataclass:
    structure: str
    config: t.Annotated[Conf, Whole] = field(default_factory=Conf)


class OpaqueTypedDict(t.TypedDict):
    structure: str
    config: t.Annotated[Conf, Whole]


@task(outputs=['seen'])
def keeps_whole(given: Opaque) -> str:
    return f'{given.structure}/{type(given.config).__name__}/{given.config.tolerance}'


@pytest.mark.parametrize(
    'container', (Opaque, OpaqueDataclass, OpaqueTypedDict), ids=('model', 'dataclass', 'typed-dict')
)
def test_a_field_marked_whole_is_read_as_one_value(container):
    """The mark is metadata of the type, so every kind carries it where it writes its annotations."""
    fields = {field.name: field.whole for field in fields_of(container)}

    assert fields == {'structure': False, 'config': True}


def test_a_field_marked_whole_is_one_port_holding_the_object():
    """A structured type that nothing wires into is one node, rather than the namespace its fields would name."""
    ports = keeps_whole.process_class.spec().inputs['given']

    assert JsonableData in ports['config'].valid_type
    assert not hasattr(ports['config'], 'ports'), 'a port rather than a namespace'

    results, node = run_get_node(keeps_whole, given=Opaque(structure='si', config=Conf(tolerance=0.1)))

    assert node.is_finished_ok, node.exit_message
    assert sorted(node.base.links.get_incoming().all_link_labels()) == ['given__config', 'given__structure']
    assert isinstance(node.inputs.given.config, JsonableData)
    assert results['seen'] == 'si/Conf/0.1', 'handed back as the object it was, not as what it was stored as'


@task(outputs=['seen'])
def takes_a_whole_parameter(given: t.Annotated[Conf, Whole]) -> str:
    return f'{type(given).__name__}/{given.tolerance}'


def test_a_parameter_marked_whole_is_one_port_holding_the_object():
    """The mark reads the same on a parameter as on a field: one node holding the container."""
    port = takes_a_whole_parameter.process_class.spec().inputs['given']

    assert JsonableData in port.valid_type
    assert not hasattr(port, 'ports'), 'a port rather than a namespace'

    results, node = run_get_node(takes_a_whole_parameter, given=Conf(tolerance=0.1))

    assert node.is_finished_ok, node.exit_message
    assert sorted(node.base.links.get_incoming().all_link_labels()) == ['given']
    assert results['seen'] == 'Conf/0.1', 'handed back as the object it was'
    assert load_node(node.inputs.given.pk).obj.tolerance == 0.1, 'and the node holds it whole'


def test_a_port_holding_a_container_takes_its_fields_as_a_mapping():
    """A namespace takes the fields written out, so a port holding the whole structured type takes them too."""
    results, node = run_get_node(takes_a_whole_parameter, given={'tolerance': 0.25})

    assert results['seen'] == 'Conf/0.25', 'the mapping was read as the structured type it stands for'
    assert isinstance(node.inputs.given, JsonableData)


def test_a_model_is_stored_whole_and_read_back():
    """`JsonableData` takes a pydantic model as readily as anything else saying how it is written."""
    stored = JsonableData(Opaque(structure='si')).store()
    back = load_node(stored.pk).obj

    assert isinstance(back, Opaque)
    assert (back.structure, back.config.tolerance) == ('si', 1e-6), 'the nested one came back too'


class HoldsANode(BaseModel):
    """A structured type holding a node, which is not something JSON has a way to write."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    spacing: Float


class KeptWhole(BaseModel):
    label: str
    config: t.Annotated[HoldsANode, Whole]


@task(outputs=['seen'])
def keeps_a_node_whole(given: KeptWhole) -> str:
    return given.label


def test_a_whole_field_that_cannot_be_written_as_json_says_what_to_do():
    """One node holding a structured type holds it as JSON, which a node inside it has no way to be written as."""
    given = KeptWhole(label='si', config=HoldsANode(spacing=Float(0.2)))

    with pytest.raises(ValueError, match='drop the mark so that each field is stored as the node it is'):
        run_get_node(keeps_a_node_whole, given=given)
