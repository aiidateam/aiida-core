###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Straight-line graph declarations shared by the behavior suites."""

from aiida.engine.processes.graphs.build_source import graph
from aiida.orm.nodes.data.int import Int
from tests.engine.processes.graphs.declarations.port_models import Configuration, DefaultedSettings
from tests.engine.processes.graphs.declarations.tasks import (
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
    """Expose summary statistics computed by plain Python."""
    stats = statistics(values=values)
    return {'mean': stats.mean, 'stdev': stats.stdev}


# Rejected declarations.
# TODO: Good error messages (verify)
# -> yes, we will still do


@graph
def expanded_task_arguments(values: dict[str, int]) -> int:
    """Call with unpacked arguments; mappings cannot expand statically.

    Declare the inputs explicitly instead:

    >>> @graph
    >>> def explicit_arguments(x: int, y: int) -> int:
    >>>     return add(x=x, y=y)
    """
    return add(**values)


@graph
def arithmetic_expression(value: int) -> int:
    """Compute an input inline; every value needs a producing task.

    Bind the intermediate explicitly:

    >>> @graph
    >>> def bound_expression(value: int) -> int:
    >>>     incremented = add(x=value, y=1)
    >>>     return add(x=incremented, y=2)
    """
    return add(x=value + 1, y=2)


@graph
def reassigned_name(value: int) -> int:
    """Rebind a name; single-assignment keeps the graph well-defined, not just readable.

    Use fresh names instead:

    >>> @graph
    >>> def assigned_twice(value: int) -> int:
    >>>     first = add(x=value, y=1)
    >>>     return add(x=first, y=2)
    """
    result = add(x=value, y=1)
    result = add(x=result, y=2)
    return result


@graph
def variadic_parameters(*values: int) -> int:
    """Declare variadic parameters; dynamic arity is unrepresentable in fixed ports.

    Plain Python takes any count, `total(1, 2, 3)`. Declare fixed arity instead:

    >>> @graph
    >>> def fixed_parameters(x: int, y: int) -> int:
    >>>     return add(x=x, y=y)
    """
    return add(*values)


@graph
def literal_return() -> int:
    """Return a literal; workflows return existing nodes, they never create data.

    Pass the value in as an input instead:

    >>> @graph
    >>> def constant_return(value: int) -> int:
    >>>     return value
    """
    return 42


# TODO: PortModel as return type should def be supported
# -> yes, we will still do
@graph
def namespace_return(config: Configuration) -> Configuration:
    """Return a whole namespace; outputs are flat leaves.

    Select a leaf field instead:

    >>> @graph
    >>> def leaf_return(config: Configuration) -> int:
    >>>     return config.settings.count
    """
    return config


@graph
def nested_outputs(x: int) -> dict[str, dict[str, int]]:
    """Return nested outputs; outputs are flat leaves.

    Keep outputs flat instead:

    >>> @graph
    >>> def flat_outputs(x: int) -> int:
    >>>     value = add(x=x, y=1)
    >>>     return {'inner': value}
    """
    value = add(x=x, y=1)
    return {'outer': {'inner': value}}


@graph
def missing_final_return(value: int) -> int:  # rejected at lowering
    """End without a return; graphs declare their outputs explicitly.

    Declare the output instead:

    >>> @graph
    >>> def final_return(value: int) -> int:
    >>>     return add(x=value, y=1)
    """
    add(x=value, y=1)


@graph
def recursive_call(value: int) -> int:
    """Call itself; the spec would be infinite.

    Factor the step into a task instead:

    >>> @task
    >>> def single_step(value: int) -> int:
    >>>     return value - 1
    """
    return recursive_call(value=value)


@graph
def wrong_type(x: str) -> int:
    """Feed a mistyped value; contracts fail fast at validation.

    Annotate the declared type instead:

    >>> @graph
    >>> def right_type(x: int) -> int:
    >>>     return add(x=x, y=1)
    """
    return add(x=x, y=1)


@graph
def unbound(value: int) -> int:
    """Reference an unbound name; every name must bind first.

    Bind the name first instead:

    >>> @graph
    >>> def bound(x: int) -> int:
    >>>     total = add(x=x, y=1)
    >>>     return add(x=total, y=1)
    """
    return add(x=value, y=missing)  # noqa: F821 - unbound names must fail at lowering


def plain_add(x: int, y: int) -> int:
    """Add without a task decorator; graphs only call registered tasks."""
    return x + y


@graph
def unregistered_call(value: int) -> int:
    """Call an undecorated function; only registered tasks and graphs lower.

    Decorate the callee instead:

    >>> @task
    >>> def plain_task(x: int, y: int) -> int:
    >>>     return x + y
    """
    return plain_add(x=value, y=1)


@graph
def subscript_assignment(value: int) -> int:
    """Mutate a placement in place; placements bind new names instead.

    Bind a new name instead:

    >>> @graph
    >>> def fresh_binding(value: int) -> int:
    >>>     first = add(x=value, y=1)
    >>>     return add(x=first, y=2)
    """
    chosen = add(x=value, y=1)
    chosen['count'] = add(x=chosen, y=2)
    return chosen


@graph
def nested_definition(value: int) -> int:
    """Define a helper inside the body; helpers belong in tasks.

    Move the helper into a task instead:

    >>> @task
    >>> def helper(x: int) -> int:
    >>>     return add(x=x, y=1)
    """

    def helper(x: int) -> int:
        return add(x=x, y=1)

    return helper(x=value)


@graph
def early_return(value: int, flag: bool) -> int:
    """Return from a branch; graphs declare one output at the end.

    Bind the branch instead:

    >>> @graph
    >>> def branched(value: int, flag: bool) -> int:
    >>>     if flag:
    >>>         chosen = add(x=value, y=1)
    >>>     else:
    >>>         chosen = add(x=value, y=2)
    >>>     return chosen
    """
    if flag:
        return add(x=value, y=1)
    return add(x=value, y=2)


@graph
def augmented_assignment(value: int) -> int:
    """Update a name in place; single-assignment keeps the graph well-defined.

    Bind a new name instead:

    >>> @graph
    >>> def fresh_total(value: int) -> int:
    >>>     first = add(x=value, y=1)
    >>>     return add(x=first, y=1)
    """
    total = add(x=value, y=1)
    total += 1
    return total


@graph
def annotated_assignment(value: int) -> int:
    """Annotate a local; locals carry no contracts in templates.

    Drop the annotation instead:

    >>> @graph
    >>> def plain_binding(value: int) -> int:
    >>>     total = add(x=value, y=1)
    >>>     return total
    """
    total: int = add(x=value, y=1)
    return total


@graph
def with_block(value: int) -> int:
    """Manage a resource in the body; templates hold no runtime resources.

    Move resource handling into a task instead.
    """
    with add(x=value, y=1):
        result = add(x=value, y=2)
    return result


@graph
def try_block(value: int) -> int:
    """Catch errors in the body; errors are values, not raises.

    Declare fallible results instead.
    """
    try:
        result = add(x=value, y=1)
    except ValueError:
        result = add(x=value, y=2)
    return result


@graph
def raise_statement(value: int) -> int:
    """Raise in the body; errors are values, not raises.

    Declare fallible results instead.
    """
    raise ValueError('graphs signal errors as values')
    return add(x=value, y=1)


@graph
def assert_statement(value: int) -> int:
    """Assert in the body; contracts validate at the boundary instead.

    Declare the contract on the ports instead.
    """
    assert value > 0
    return add(x=value, y=1)


@graph
def match_statement(value: int) -> int:
    """Match structurally; branch on conditions instead.

    >>> @graph
    >>> def matched(value: int) -> int:
    >>>     if value:
    >>>         chosen = add(x=value, y=1)
    >>>     else:
    >>>         chosen = add(x=value, y=2)
    >>>     return chosen
    """
    match value:
        case 0:
            return add(x=value, y=1)
        case _:
            return add(x=value, y=2)


@graph
def starred_call(value: int) -> int:
    """Spread a sequence into a call; arity is static.

    Pass each input by name instead:

    >>> @graph
    >>> def named_spread(value: int) -> int:
    >>>     return add(x=value, y=1)
    """
    return add(*[value, 1])


@graph
def subscript_load(values: list[int]) -> int:
    """Read one element; collections travel whole.

    Pass the collection instead:

    >>> @graph
    >>> def whole_collection(values: list[int]) -> int:
    >>>     return read_answer(values={'answer': 42})
    """
    return add(x=values[0], y=1)


@graph
def fstring_argument(value: int) -> int:
    """Format a string inline; every value needs a producing task.

    Format inside a task instead.
    """
    return add(x=value, y=f'{value}')


@graph
def boolean_condition(value: int, flag: bool) -> int:
    """Combine conditions with operators; conditions are calls or names.

    Compute the predicate in a task instead:

    >>> @task
    >>> def both(value: int, flag: bool) -> bool:
    >>>     return flag and value > 0
    """
    if flag and value:
        chosen = add(x=value, y=1)
    else:
        chosen = add(x=value, y=2)
    return chosen


@graph
def compare_condition(value: int) -> int:
    """Compare inline; conditions are calls or names.

    Compute the predicate in a task instead:

    >>> @task
    >>> def positive(value: int) -> bool:
    >>>     return value > 0
    """
    if value > 0:
        chosen = add(x=value, y=1)
    else:
        chosen = add(x=value, y=2)
    return chosen


@graph
def inline_conditional(value: int, flag: bool) -> int:
    """Select inline; branch explicitly instead.

    >>> @graph
    >>> def explicit_choice(value: int, flag: bool) -> int:
    >>>     if flag:
    >>>         chosen = add(x=value, y=1)
    >>>     else:
    >>>         chosen = add(x=value, y=2)
    >>>     return chosen
    """
    return add(x=value, y=1) if flag else add(x=value, y=2)


@graph
def walrus_condition(value: int, flag: bool) -> int:
    """Bind inside a condition; bind before branching instead.

    >>> @graph
    >>> def bound_before(value: int, flag: bool) -> int:
    >>>     picked = flag
    >>>     if picked:
    >>>         chosen = add(x=value, y=1)
    >>>     else:
    >>>         chosen = add(x=value, y=2)
    >>>     return chosen
    """
    if picked := flag:  # noqa: F841 - the binding itself is rejected
        chosen = add(x=value, y=1)
    else:
        chosen = add(x=value, y=2)
    return chosen


@graph
def list_comprehension(values: list[int]) -> int:
    """Map over inputs inline; scatter is a runtime control, not syntax.

    Unroll the placements instead.
    """
    doubled = [add(x=value, y=1) for value in values]  # noqa: F841 - the comprehension is rejected
    return add(x=values[0], y=1)
