###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for saying what a namespace of ports holds with a structured container."""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import NamedTuple, TypedDict

import pytest
from pydantic import BaseModel, field_serializer

from aiida.engine import WorkChain, graph, run_get_node, task
from aiida.engine.processes.containers import as_dict, build, fields_of, is_a_container
from aiida.orm import Int, Str


class AsTypedDict(TypedDict):
    structure: str
    steps: int


class AsModel(BaseModel):
    structure: str
    steps: int = 10


@dataclass
class AsDataclass:
    structure: str
    steps: int = 10


class AsTuple(NamedTuple):
    structure: str
    steps: int = 10


KINDS = pytest.mark.parametrize(
    'container', (AsTypedDict, AsModel, AsDataclass, AsTuple), ids=lambda kind: kind.__name__
)


@KINDS
def test_the_fields_of_a_container_are_read(container):
    """Each kind says the same thing in different words, and this is what it says."""
    assert [(field.name, field.annotation) for field in fields_of(container)] == [
        ('structure', str),
        ('steps', int),
    ]


@KINDS
def test_which_fields_have_to_be_given(container):
    """A field with a default need not be given, and a `TypedDict` gives no default so all of them do."""
    required = {field.name for field in fields_of(container) if field.required}

    assert required == ({'structure', 'steps'} if container is AsTypedDict else {'structure'})


@pytest.mark.parametrize('value', (3, 'three', [3], {'a': 3}, None, AsModel))
def test_what_is_not_a_container(value):
    """Plenty of things hold values without saying which they are, and a class is not one of its instances."""
    assert not is_a_container(type(value)) or value is AsModel
    assert as_dict(value) is None


@KINDS
def test_a_container_is_read_and_written_back(container):
    """What a container holds is what it is built back from, so the trip through the ports is a round one."""
    values = {'structure': 'si', 'steps': 3}
    built = build(container, values)

    # An instance of a `TypedDict` is a dict, so it is already what it would be flattened into.
    assert (built if container is AsTypedDict else as_dict(built)) == values


@KINDS
def test_a_container_names_a_namespace_of_ports(container):
    """The fields of a container are the ports of the namespace it names, wherever it is declared."""

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

    with pytest.raises(TypeError, match='`int` is not a structured container'):
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
    """A parameter annotated with a container takes one, so the task declares the namespace it names."""
    relax = TAKES[container]

    assert sorted(relax.process_class.spec().inputs['given']) == ['steps', 'structure']

    results, node = run_get_node(relax, given=build(container, {'structure': 'si', 'steps': 3}))

    assert node.is_finished_ok, node.exit_message
    assert results['steps'] == 3
    assert sorted(node.base.links.get_incoming().all_link_labels()) == ['given__steps', 'given__structure']


@KINDS
def test_a_task_is_handed_the_container_it_named(container):
    """The namespace holds what the container said it would, so the function is given one of those back."""
    results, _ = run_get_node(TAKES[container], given={'structure': 'si', 'steps': 3})

    assert results['kind'] == (dict.__name__ if container is AsTypedDict else container.__name__)


@KINDS
def test_a_returned_container_names_the_outputs(container):
    """A container says which output each of its fields is, on the way out as much as on the way in."""
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
    """A container is a way of saying what a namespace holds, so a graph wires into one field of it."""

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
    """A function that carries no annotations is described by the container the task is declared with."""
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
    with pytest.raises(TypeError, match='`int` is not a structured container'):

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
    """A container nests, and so does a namespace, so the one maps onto the other all the way down."""

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
    """What the function named is what it is given, however deep the container goes."""
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
