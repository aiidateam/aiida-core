###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Supported sequential graph declarations shared by the behavior suites."""

from aiida.engine.processes.graphs.lowering import graph
from aiida.orm.nodes.data.int import Int
from tests.engine.processes.graphs.language.port_models import Configuration, DefaultedSettings
from tests.engine.processes.graphs.language.tasks import (
    add,
    arithmetic_pair,
    collision_add,
    fail_always,
    multiply,
    prepare,
    read_answer,
    read_nested_count,
    read_orm_node,
    statistics,
)

__all__ = (
    'chain',
    'chained_assignment',
    'collision',
    'default_parameter',
    'diamond',
    'dictionary_input',
    'direct_result',
    'failed',
    'input_passthrough',
    'keyword_only_parameter',
    'labelled',
    'literal_dictionary',
    'missing_task_input',
    'multiple_ordered',
    'multiply_add',
    'named',
    'nested',
    'nested_multiply_add',
    'ordered',
    'ordered_named',
    'orm_passthrough',
    'positional_only_parameter',
    'positional_task_arguments',
    'selected',
    'selected_field',
    'summarize',
    'tuple_assignment',
    'whole',
    'wired',
)


@graph
def direct_result(value: int) -> int:
    """Select the single output port explicitly."""
    return add(x=value, y=10).result


@graph
def chain(x: int, y: int) -> int:
    """Two whole-result placements."""
    first = add(x=x, y=y)
    return add(x=first, y=y)


@graph
def multiply_add(x: int, y: int, z: int) -> int:
    """Return the arithmetic result for the local multiply-add workflow example."""
    product = multiply(x=x, y=y)
    return add(x=product, y=z)


@graph
def diamond(x: int) -> int:
    """Fan two additions into one."""
    left = add(x=x, y=1)
    right = add(x=x, y=2)
    return add(x=left, y=right)


@graph
def ordered(x: int) -> int:
    """Order a placement with `after`."""
    first = prepare(value=x)
    return add(x=x, y=1, after=first)


@graph
def ordered_named(value: int) -> int:
    """Order on a task; the bare return takes the single output."""
    prepared = prepare(value=value)
    return add(x=value, y=1, after=prepared)


@graph
def multiple_ordered(x: int) -> int:
    """Order on two placements at once."""
    first = prepare(value=x)
    second = prepare(value=x)
    return add(x=x, y=1, after=(first, second))


@graph
def named(x: int, y: int) -> dict[str, int]:
    """Return multiple named outputs from one task."""
    pair = arithmetic_pair(x=x, y=y)
    return {'total': pair.sum, 'product': pair.product}


@graph
def whole(config: Configuration) -> int:
    """Pass a whole namespace through."""
    return read_nested_count(config=config)


@graph
def selected(config: Configuration) -> int:
    """Select one namespace field."""
    return add(x=config.settings.count, y=1)


@graph
def selected_field(settings: DefaultedSettings) -> int:
    """Select a defaulted namespace field, without passing any inputs."""
    return add(x=settings.count, y=1)


@graph
def wired(config: Configuration) -> int:
    """Wire constructed namespaces between tasks."""
    chosen = add(x=config.settings.count, y=1)
    return read_nested_count(config={'settings': {'count': chosen, 'nullable': config.settings.nullable}})


@graph
def dictionary_input(values: dict[str, int]) -> int:
    """Read a passed mapping."""
    return read_answer(values=values)


@graph
def literal_dictionary() -> int:
    """Read a dictionary literal, without passing any inputs."""
    return read_answer(values={'answer': 42})


@graph
def orm_passthrough(value: Int) -> int:
    """Pass an ORM node through a task."""
    return read_orm_node(value=value)


@graph
def input_passthrough(value: int) -> int:
    """Pass a graph input straight to outputs."""
    return value


@graph(identifier='custom-label')
def labelled(x: int) -> int:
    """Carry a custom identifier."""
    return add(x=x, y=1)


@graph
def failed(x: int) -> int:
    """Fail through a broken placement."""
    first = fail_always(x=x)
    return add(x=first, y=1)


@graph
def collision(x: int) -> int:
    """Place three tasks across two callees."""
    first = add(x=x, y=1)
    second = add(x=first, y=1)
    return collision_add(x=second, y=1)


@graph
def missing_task_input(x: int) -> int:
    """Omit a required task input."""
    return add(x=x)


@graph
def positional_task_arguments(value: int) -> int:
    """Call with positional arguments, bound through signature order."""
    return add(value, 1)


@graph
def tuple_assignment(x: int, y: int) -> int:
    """Bind two names at once from multiple outputs."""
    total, product = arithmetic_pair(x=x, y=y)
    return add(x=total, y=product)


@graph
def chained_assignment(value: int) -> int:
    """Assign two names in one statement to one placement."""
    first = second = add(x=value, y=1)
    return add(x=first, y=second)


@graph
def default_parameter(value: int = 2) -> int:
    """Declare a parameter default, filled when absent."""
    return add(x=value, y=1)


@graph
def keyword_only_parameter(*, value: int) -> int:
    """Declare a keyword-only parameter, treated as ordinary."""
    return add(x=value, y=1)


@graph
def positional_only_parameter(value: int, /) -> int:
    """Declare a positional-only parameter, treated as ordinary."""
    return add(x=value, y=1)


@graph
def nested(x: int, y: int) -> int:
    """Nest one graph in another."""
    inner = chain(x=x, y=y)
    return add(x=inner, y=x)


@graph
def nested_multiply_add(x: int, y: int, z: int) -> int:
    """Nest the multiply-add graph once."""
    intermediate = multiply_add(x=x, y=y, z=z)
    return add(x=intermediate, y=1)


@graph
def summarize(values: list[float]):
    """Expose summary statistics computed by plain Python, selected by key."""
    stats = statistics(values=values)
    return {'mean': stats['mean'], 'stdev': stats['stdev']}
