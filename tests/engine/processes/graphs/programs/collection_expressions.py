###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Graph programs exercising pure inline collection expressions.

Accepted graphs thread collection expressions (filtered and nested
comprehensions, indexing, ``.value`` reads) through ``@task`` consumers, so
every root output is a task-produced node with normal provenance. Rejected
graphs name the inline form that must stay a task call, a declared annotation,
or a task output instead.
"""

from aiida.engine.processes.graphs.lowering import graph, task
from aiida.orm import Int
from tests.engine.processes.graphs.programs.tasks import add


@task
def sum_values(values: list[int]) -> int:
    """Sum plain integers; runtime values stay a plain list."""
    assert type(values) is list
    assert all(type(item) is int for item in values)
    return sum(values)


@task
def sum_mapping(values: dict[str, int]) -> int:
    """Sum plain mapping values; runtime values stay a plain dict."""
    assert type(values) is dict
    assert all(type(item) is int for item in values.values())
    return sum(values.values())


@task
def sum_orm_list(values: list[Int]) -> int:
    """Sum owned integers; runtime values stay a plain list of nodes."""
    assert type(values) is list
    assert all(isinstance(item, Int) for item in values)
    return sum(item.value for item in values)


@task
def sum_orm_mapping(values: dict[str, Int]) -> int:
    """Sum owned mapping values; runtime values stay a plain dict of nodes."""
    assert type(values) is dict
    assert all(isinstance(item, Int) for item in values.values())
    return sum(item.value for item in values.values())


@task
def count_items(values: list[str]) -> int:
    """Count collected keys; runtime values stay a plain list of strings."""
    assert type(values) is list
    assert all(type(item) is str for item in values)
    return len(values)


@task
def total(x: int, y: int) -> int:
    """Combine two scalars; expression results arrive as plain values."""
    assert type(x) is int
    assert type(y) is int
    return x + y


@task
def forward(value: int) -> int:
    """Pass one scalar through; indexed values arrive as plain values."""
    assert type(value) is int
    return value


@task
def pack_pair(x: int, y: int) -> list[int]:
    """Pack two integers as a plain list, carrying the element hint downstream."""
    return [x, y]


@task
def pack_orm_pair(x: int, y: int) -> list[Int]:
    """Pack two integers as owned nodes, carrying the element hint downstream."""
    return [Int(x), Int(y)]


@task
def pack_mapping(a: int, b: int) -> dict[str, int]:
    """Pack two integers as a plain mapping, carrying the element hint downstream."""
    return {'a': a, 'b': b}


@graph
def scaled_filtered(values: list[int], scale: int) -> int:
    """Scale positive inputs inline, dropping the rest through the filter."""
    scaled = [item * scale for item in values if item > 0]
    return sum_values(values=scaled)


@graph
def nested_pairs(xs: list[int], ys: list[int]) -> int:
    """Combine every pair across two inputs through nested generators."""
    pairs = [a + b for a in xs for b in ys]
    return sum_values(values=pairs)


@graph
def orm_bumped(values: list[Int]) -> int:
    """Unwrap owned members inline, collecting plain integers for the consumer."""
    bumped = [item.value + 1 for item in values]
    return sum_values(values=bumped)


@graph
def mapped_bumped(values: dict[str, Int]) -> int:
    """Rebuild a mapping inline, unwrapping each owned value under its key."""
    bumped = {key: value.value + 1 for key, value in values.items()}
    return sum_mapping(values=bumped)


@graph
def plain_scaled_mapping(values: dict[str, int], factor: int) -> int:
    """Rebuild a plain mapping inline, scaling each value under its key."""
    doubled = {key: value * factor for key, value in values.items()}
    return sum_mapping(values=doubled)


@graph
def head_plus_last(values: list[int]) -> int:
    """Index both ends inline, including the negative position."""
    first = values[0]
    last = values[-1]
    return total(x=first, y=last)


@graph
def keyed_forward(values: dict[str, int], key: str) -> int:
    """Select one entry inline through a runtime key."""
    picked = values[key]
    return forward(value=picked)


@graph
def first_member(values: list[Int]) -> int:
    """Select the first owned member inline, then read its value."""
    first = values[0].value
    return forward(value=first)


@graph
def packed_scaled(x: int, y: int, scale: int) -> int:
    """Scale a task-produced list inline; the packing hint types the comprehension."""
    packed = pack_pair(x=x, y=y)
    scaled = [item * scale for item in packed]
    return sum_values(values=scaled)


@graph
def orm_packed_bumped(x: int, y: int) -> int:
    """Bump a task-produced owned list inline; the packing hint types the members."""
    packed = pack_orm_pair(x=x, y=y)
    bumped = [item.value + 1 for item in packed]
    return sum_values(values=bumped)


@graph
def mapping_packed_doubled(a: int, b: int) -> int:
    """Double a task-produced mapping inline; the packing hint types the pairs."""
    packed = pack_mapping(a=a, b=b)
    doubled = {key: value * 2 for key, value in packed.items()}
    return sum_mapping(values=doubled)


@graph
def shadowed_target(values: list[int], item: int) -> int:
    """Bind the comprehension target over the same name as a graph input.

    The element reads the bound member while the outer input still wires below,
    so the result proves which binding each position observed.
    """
    scaled = [item * 2 for item in values]
    subtotal = sum_values(values=scaled)
    return total(x=subtotal, y=item)


@graph
def counted_keys(values: dict[str, int]) -> int:
    """Collect mapping keys inline, iterating the mapping directly."""
    keys = [key for key in values]  # noqa: C416 - exercise comprehension syntax
    return count_items(values=keys)


@graph
def select_member(values: list[Int]) -> Int:
    """Return the selected existing member itself, preserving its identity."""
    return values[0]


# rejected at lowering: computed scalars never leave through the root; materialize them in a task instead.
@graph
def laundered_scalar(values: list[Int]) -> int:
    """Read then shift a member value inline; return a task output instead."""
    return values[0].value + 1


# rejected at lowering: attribute reads expose public fields only, not underscore names.
@graph
def private_attr_comp(values: list[Int]) -> int:
    """Read a private member inline; expose a public property or compute in a task instead."""
    names = [item._hidden for item in values]
    return sum_values(values=names)


# rejected at lowering: methods never run inline; compute call results in a task instead.
@graph
def method_call_comp(values: list[int]) -> int:
    """Call a member method inline; compute the value in a task instead."""
    widths = [item.bit_length() for item in values]
    return sum_values(values=widths)


# rejected at lowering: calls never run inline; compute call results in a task instead.
@graph
def task_call_comp(values: list[int]) -> int:
    """Call a task inside a comprehension; write out one call per value instead."""
    bumped = [add(x=item, y=1) for item in values]
    return sum_values(values=bumped)


# rejected at lowering: comprehensions need a declared element type; annotate the collection instead.
@graph
def untyped_comp(values: list) -> int:  # type: ignore[type-arg]
    """Iterate a bare list; spell the member type instead of guessing."""
    bumped = [item + 1 for item in values]
    return sum_values(values=bumped)


# rejected at lowering: indexing a list needs an `int` index, not a `str` key.
@graph
def wrong_index_type(values: list[int], key: str) -> int:
    """Index a list by key; index lists by position or map over them instead."""
    picked = values[key]  # type: ignore[index] - lowering rejects the index before use
    return forward(value=picked)


# rejected at lowering: slices have no fixed shape; index one element instead.
@graph
def sliced_index(values: list[int]) -> int:
    """Slice a list inline; select one element or consume the whole list instead."""
    head = values[1:2]
    return sum_values(values=head)
