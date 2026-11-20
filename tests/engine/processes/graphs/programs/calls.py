###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Calls declarations shared by the graph behavior suites."""

import typing as t

from aiida.engine import PortField, dataflow, expose
from aiida.engine.processes.graphs.lowering import graph
from tests.engine.processes.graphs.programs import tasks
from tests.engine.processes.graphs.programs.port_models import AddBundle, ConfigBundle, PartialBundle
from tests.engine.processes.graphs.programs.tasks import (
    add,
    collision_add,
    decrement,
    fail_always,
    generic_add,
    is_positive,
    maybe_add,
    multiply,
    prepare,
    read_nested_count,
)


def plain_add(x: int, y: int) -> int:
    """Add without a task decorator; graphs only call registered tasks."""
    return x + y


@graph
def chain(x: int, y: int) -> int:
    """Two whole-result placements."""
    first = add(x=x, y=y)
    return add(x=first, y=y).alias('add_2')


@graph
def multiply_add(x: int, y: int, z: int) -> int:
    """Return the arithmetic result for the local multiply-add workflow example."""
    product = multiply(x=x, y=y)
    return add(x=product, y=z)


@graph
def diamond(x: int) -> int:
    """Fan two additions into one."""
    left = add(x=x, y=1)
    right = add(x=x, y=2).alias('add_2')
    return add(x=left, y=right).alias('add_3')


@graph
def ordered(x: int) -> int:
    """Run two placements in source order without passing a value between them."""
    _prepared = prepare(value=x)
    return add(x=x, y=1)


@graph
def scoped_fanout(x: int) -> int:
    """Fork after preparation and join before the final placement."""
    _prepared = prepare(value=x)
    with dataflow():
        left = add(x=x, y=1).alias('left')
        _right = add(x=x, y=2).alias('right')
        summary = add(x=left, y=3).alias('summary')
    return add(x=summary, y=4).alias('finish')


@graph
def loop_dataflow(x: int, n: int) -> int:
    """Rebind loop state through a dataflow block."""
    result = add(x=x, y=0)
    while n > 0:
        with dataflow():
            result = add(x=result, y=1)
            _checked = prepare(value=n)
            n = n - 1
    return result


@graph
def dataflow_return(x: int) -> int:
    """Reject a nonlocal return inside a parallel block."""
    with dataflow():
        if x > 0:
            return x
    return x


@graph
def dataflow_as(x: int) -> int:
    """Reject binding the declaration as a context manager."""
    with dataflow() as _scope:
        result = add(x=x, y=1)
    return result


@graph
def obsolete_after(x: int) -> int:
    """Reject ordering keywords not declared as task inputs."""
    first = prepare(value=x)
    return add(x=x, y=1, after=first)


@graph
def passes_after_input(x: int) -> int:
    """Wire an ordinary task input named after."""
    return tasks.after_parameter(x=x, after=2)


@graph()
def labelled(x: int) -> int:
    """Use the fully qualified name with the parenthesized decorator."""
    return add(x=x, y=1)


@graph
def failed(x: int) -> int:
    """Fail before reaching the next placement, even without a data dependency."""
    _failed = fail_always(x=x)
    return add(x=x, y=1)


@graph
def collision(x: int) -> int:
    """Place three tasks across two callees."""
    first = add(x=x, y=1)
    second = add(x=first, y=1).alias('add_2')
    return collision_add(x=second, y=1)


@graph
def positional_task_arguments(value: int) -> int:
    """Call with positional arguments, bound through signature order."""
    return add(value, 1)


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
def optional_result(x: int, flag: bool) -> int | None:
    """Return an optional task output."""
    return maybe_add(x=x, flag=flag)


@graph
def spread_bundle(bundle: AddBundle) -> int:
    """Spread a namespace across task ports."""
    return add(**bundle)


@graph
def spread_nested(bundle: ConfigBundle) -> int:
    """Spread a namespace-typed port whole."""
    return read_nested_count(**bundle)


@graph
def forwarded_add(bundle: expose(add)) -> int:
    """Mirror a task's inputs as one group input."""
    return add(**bundle)


@graph
def forwarded_nested(bundle: expose(nested_multiply_add)) -> int:
    """Mirror a nested graph's inputs as one group input."""
    return nested_multiply_add(**bundle)


@graph
def forwarded_exclude(bundle: expose(add, exclude=('y',))) -> int:
    """Mirror a task's inputs minus excluded ports."""
    return add(**bundle, y=2)


# rejected at lowering: dynamic mappings have no static fields to spread.
@graph
def expanded_task_arguments(values: dict[str, int]) -> int:
    """Call with unpacked arguments; dynamic mappings have no static fields to spread."""
    return add(**values)


# rejected at lowering: calls cannot recurse.
@graph
def recursive_call(value: int) -> int:
    """Call itself; the spec would be infinite."""
    return recursive_call(value=value)


# rejected at lowering: built-ins cannot run here.
@graph
def builtin_call(values: list[int]) -> int:
    """Call a built-in; built-ins cannot run here."""
    count = len(values)
    return add(x=count, y=1)


# rejected at lowering: calls resolve to declared names.
@graph
def unknown_call(value: int) -> int:
    """Call an undefined name; check the spelling."""
    return frobnicate(value)  # noqa: F821 - the undefined name is rejected


# rejected at lowering: only registered tasks and graphs lower.
@graph
def unregistered_call(value: int) -> int:
    """Call an undecorated function; only registered tasks and graphs lower."""
    return plain_add(x=value, y=1)


# rejected at lowering: sequences cannot spread; each input wires by name.
@graph
def starred_call(value: int) -> int:
    """Spread a sequence into a call; each input wires by name."""
    return add(*[value, 1])


# rejected at lowering: calls wire every required input.
@graph
def missing_task_input(x: int) -> int:
    """Omit a required task input."""
    return add(x=x)


# rejected at lowering: collections enter as declared inputs.
@graph
def list_argument(value: int) -> int:
    """Pass a collection inline; collections enter as declared inputs."""
    return add(x=[1, 2], y=value)


# rejected at lowering: spread bundles carry every required port.
@graph
def spread_missing(bundle: PartialBundle) -> int:
    """Spread without a required port; the missing check reports it."""
    return add(**bundle)


# rejected at lowering: only namespaces spread.
@graph
def spread_leaf(value: int) -> int:
    """Spread a single value; only namespaces spread."""
    return add(**value)


# rejected at lowering: each port is given once.
@graph
def spread_override(bundle: AddBundle) -> int:
    """Spread a port given explicitly too; each port is given once."""
    return add(**bundle, x=1)


# rejected at lowering: each port is given once.
@graph
def spread_double(bundle: AddBundle) -> int:
    """Spread one port twice; each port is given once."""
    return add(**bundle, **bundle)


# rejected at lowering: every spread field matches a port.
@graph
def spread_extra(bundle: ConfigBundle) -> int:
    """Spread a field no port wants; every field must match."""
    return add(**bundle)


# rejected at lowering: only tasks and graphs can be exposed.
@graph
def forwarded_unknown(bundle: expose(int)) -> int:
    """Expose a non-task; only tasks and graphs can be exposed."""
    return add(**bundle)


# rejected at lowering: exclusions name declared input paths.
@graph
def forwarded_exclude_unknown(bundle: expose(add, exclude=('z',))) -> int:
    """Exclude an unknown input; exclusions name declared paths."""
    return add(**bundle)


@graph
def namespaced_call(x: int, y: int) -> int:
    """Call tasks through a module namespace."""
    return tasks.add(x=x, y=y)


# rejected at lowering: calls must name an importable declaration.
@graph
def namespaced_unknown(x: int) -> int:
    """Call through an unimported module; check the spelling."""
    return nosuchmod.add(x=x, y=1)  # noqa: F821 - the unknown module is rejected


# rejected at lowering: a name cannot be both a wire and a declaration.
@graph
def namespaced_shadowed(x: int) -> int:
    """Call through a name that is also a wire."""
    tasks = add(x=x, y=1)
    return tasks.add(x=tasks, y=1)


@graph
def generic_chain(x: int, y: int) -> int:
    """Chain a solved generic output into a typed port."""
    total = generic_add(a=x, b=y)
    return decrement(value=total)


@graph
def generic_mixed(x: int, y: float) -> int | float:
    """A mixed generic call stays broad."""
    return generic_add(a=x, b=y)


# rejected at lowering: wirings outside the constraint union fail.
@graph
def generic_str_input(value: str) -> int:
    """Wire outside the constraint union; constraints still check."""
    return generic_add(a=value, b=1)


@graph
def daemon_proving(x: int, flag: bool) -> int:
    """Combine solved generics with a loop in a missing-else arm."""
    total = generic_add(a=x, b=1)
    if flag:
        while is_positive(value=total):
            total = decrement(value=total)
    return total


AddInputs = expose(add)


@graph
def forwarded_alias(bundle: AddInputs) -> int:
    """Mirror a task's inputs through a module-level alias."""
    return add(**bundle)


@graph
def forwarded_annotated(bundle: t.Annotated[AddInputs, PortField(help='The inputs of `add`.')]) -> int:
    """Mirror a task's inputs through an `expose` class wrapped in `Annotated` metadata."""
    return add(**bundle)
