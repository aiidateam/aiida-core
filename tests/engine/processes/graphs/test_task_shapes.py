###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""TaskIR annotation elements and declaration round-trips."""

import json
import typing as t

from aiida.engine import ExitCode, ExitCodeEnum, Result, task
from aiida.engine.processes.graphs.ir import GraphIR, TaskIR
from aiida.engine.processes.graphs.lowering import compile_graph, graph
from aiida.engine.processes.graphs.shapes import LeafShape, NamespaceShape
from aiida.engine.processes.port_model import PortModel
from aiida.orm import EnumData, Int, List


class CollectErrors(ExitCodeEnum):
    """Declared failure of the collecting task."""

    EMPTY = ExitCode(412, 'Nothing collected.')


@task
def collect(n: int) -> list[int]:
    """Collect a range as a scalar collection."""
    return list(range(n))


class NamedLists(t.TypedDict):
    """Named outputs with one collection member."""

    first: list[int]
    second: int


@task
def named_lists(n: int) -> NamedLists:
    """Return a collection and a scalar as named outputs."""
    return {'first': list(range(n)), 'second': n}


class Inner(PortModel):
    """Nested namespace carrying a collection."""

    values: list[int]


class Outer(PortModel):
    """Top-level namespace with a nested model."""

    inner: Inner
    label: str = 'other'


@task
def read_nested(outer: Outer) -> int:
    """Sum the nested collection."""
    return sum(outer.inner.values)


@task
def collect_or_fail(n: int) -> Result[list[int], CollectErrors]:
    """Collect a range, declaring the empty input failure."""
    from aiida.engine.processes.graphs.results import Err, Ok

    return Ok(list(range(n))) if n else Err(CollectErrors.EMPTY)


def test_scalar_collection_result_carries_element() -> None:
    """Collection returns keep port types and record the member contract."""
    assert collect._task_spec.result_shape == LeafShape(types=(List,), element=LeafShape(types=(int,)))


def test_typeddict_result_expands_named_members() -> None:
    """Named outputs overlay elements per field, not on the namespace."""
    shape = named_lists._task_spec.result_shape
    assert isinstance(shape, NamespaceShape)
    assert shape.select('first') == LeafShape(types=(List,), element=LeafShape(types=(int,)))
    assert shape.select('second') == LeafShape(types=(Int,))


def test_port_model_nested_field_carries_element() -> None:
    """Nested model fields overlay members while keeping port types."""
    shape = read_nested._task_spec.input_shape
    outer = shape.select('outer')
    assert isinstance(outer, NamespaceShape)
    inner = outer.select('inner')
    assert isinstance(inner, NamespaceShape)
    assert inner.select('values') == LeafShape(types=(list,), element=LeafShape(types=(int,)))


def test_result_value_arm_carries_element() -> None:
    """Result overlays the success arm only; the error arm stays element-free."""
    shape = collect_or_fail._task_spec.result_shape
    assert isinstance(shape, NamespaceShape)
    assert shape.select('value') == LeafShape(types=(List,), element=LeafShape(types=(int,)), required=False)
    assert shape.select('error') == LeafShape(types=(EnumData,), required=False)


def test_task_ir_json_round_trip_preserves_contracts() -> None:
    """Serialized declarations reload the same ports, codes and shapes."""
    spec = collect_or_fail._task_spec
    restored = TaskIR.from_dict(json.loads(json.dumps(spec.to_dict())))
    assert restored == spec
    assert restored.exit_codes == spec.exit_codes
    assert restored.input_shape == spec.input_shape
    assert restored.result_shape == spec.result_shape


@task
def pack_nested(x: int, y: int) -> list[int]:
    """Pack two integers as a plain list for a nested producer."""
    return [x, y]


@task
def sum_nested(values: list[int]) -> int:
    """Sum plain integers for a nested consumer."""
    return sum(values)


@graph
def inner_producer(x: int, y: int) -> list[int]:
    """Produce a collection inside a nested graph."""
    return pack_nested(x=x, y=y)


@graph
def inner_passthrough(values: list[int]) -> list[int]:
    """Pass a collection straight through a nested graph."""
    return values


@graph
def outer_produced(x: int, y: int, scale: int) -> int:
    """Scale a nested-produced collection inline."""
    packed = inner_producer(x=x, y=y)
    scaled = [item * scale for item in packed]
    return sum_nested(values=scaled)


@graph
def outer_passthrough(values: list[int], scale: int) -> int:
    """Scale a nested-passed collection inline."""
    passed = inner_passthrough(values=values)
    scaled = [item * scale for item in passed]
    return sum_nested(values=scaled)


def test_nested_producer_result_shape_carries_element() -> None:
    """A nested produced collection keeps its member contract."""
    assert compile_graph(inner_producer).result_shape == LeafShape(types=(List,), element=LeafShape(types=(int,)))


def test_nested_passthrough_result_shape_carries_element() -> None:
    """A nested passed-through collection keeps its member contract."""
    assert compile_graph(inner_passthrough).result_shape == LeafShape(types=(List,), element=LeafShape(types=(int,)))


def test_nested_collection_graphs_round_trip() -> None:
    """Nested templates survive JSON and keep elements for comprehensions."""
    for handle in (inner_producer, inner_passthrough, outer_produced, outer_passthrough):
        assert handle.build() is None
        spec = compile_graph(handle)
        assert GraphIR.from_dict(json.loads(json.dumps(spec.to_dict()))).to_dict() == spec.to_dict()
    assert compile_graph(outer_produced).result_shape == compile_graph(outer_passthrough).result_shape
