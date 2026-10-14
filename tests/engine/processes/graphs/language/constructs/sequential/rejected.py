###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Sequential graph declarations rejected at lowering shared by the behavior suites."""

from aiida.engine.processes.graphs.build_source import graph
from tests.engine.processes.graphs.language.port_models import Configuration
from tests.engine.processes.graphs.language.tasks import add

__all__ = (
    'annotated_assignment',
    'arithmetic_expression',
    'assert_statement',
    'augmented_assignment',
    'early_return',
    'expanded_task_arguments',
    'fstring_argument',
    'list_comprehension',
    'literal_return',
    'match_statement',
    'missing_final_return',
    'namespace_return',
    'nested_definition',
    'nested_outputs',
    'plain_add',
    'raise_statement',
    'reassigned_name',
    'recursive_call',
    'starred_call',
    'subscript_assignment',
    'subscript_load',
    'try_block',
    'unbound',
    'unregistered_call',
    'variadic_parameters',
    'with_block',
    'wrong_type',
)


@graph
def expanded_task_arguments(values: dict[str, int]) -> int:
    """Call with unpacked arguments; mappings cannot expand statically."""
    return add(**values)


# Declare the inputs explicitly instead:

# @graph
# def explicit_arguments(x: int, y: int) -> int:
#     return add(x=x, y=y)


@graph
def arithmetic_expression(value: int) -> int:
    """Compute an input inline; every value needs a producing task."""
    return add(x=value + 1, y=2)


# Bind the intermediate explicitly:

# @graph
# def bound_expression(value: int) -> int:
#     incremented = add(x=value, y=1)
#     return add(x=incremented, y=2)


@graph
def reassigned_name(value: int) -> int:
    """Rebind a name; single-assignment keeps the graph well-defined, not just readable."""
    result = add(x=value, y=1)
    result = add(x=result, y=2)
    return result


# Use fresh names instead:

# @graph
# def assigned_twice(value: int) -> int:
#     first = add(x=value, y=1)
#     return add(x=first, y=2)


@graph
def variadic_parameters(*values: int) -> int:
    """Declare variadic parameters; dynamic arity is unrepresentable in fixed ports."""
    return add(*values)


# Plain Python takes any count, `total(1, 2, 3)`. Declare fixed arity instead:

# @graph
# def fixed_parameters(x: int, y: int) -> int:
#     return add(x=x, y=y)


@graph
def literal_return() -> int:
    """Return a literal; workflows return existing nodes, they never create data."""
    return 42


# Pass the value in as an input instead:

# @graph
# def constant_return(value: int) -> int:
#     return value


# TODO: PortModel as return type should def be supported
# -> yes, we will still do
@graph
def namespace_return(config: Configuration) -> Configuration:
    """Return a whole namespace; outputs are flat leaves."""
    return config


# Select a leaf field instead:

# @graph
# def leaf_return(config: Configuration) -> int:
#     return config.settings.count


@graph
def nested_outputs(x: int) -> dict[str, dict[str, int]]:
    """Return nested outputs; outputs are flat leaves."""
    value = add(x=x, y=1)
    return {'outer': {'inner': value}}


# Keep outputs flat instead:

# @graph
# def flat_outputs(x: int) -> int:
#     value = add(x=x, y=1)
#     return {'inner': value}


@graph
def missing_final_return(value: int) -> int:  # rejected at lowering
    """End without a return; graphs declare their outputs explicitly."""
    add(x=value, y=1)


# Declare the output instead:

# @graph
# def final_return(value: int) -> int:
#     return add(x=value, y=1)


@graph
def recursive_call(value: int) -> int:
    """Call itself; the spec would be infinite."""
    return recursive_call(value=value)


# Factor the step into a task instead:

# @task
# def single_step(value: int) -> int:
#     return value - 1


@graph
def wrong_type(x: str) -> int:
    """Feed a mistyped value; contracts fail fast at validation."""
    return add(x=x, y=1)


# Annotate the declared type instead:

# @graph
# def right_type(x: int) -> int:
#     return add(x=x, y=1)


@graph
def unbound(value: int) -> int:
    """Reference an unbound name; every name must bind first."""
    return add(x=value, y=missing)  # noqa: F821 - unbound names must fail at lowering


# Bind the name first instead:

# @graph
# def bound(x: int) -> int:
#     total = add(x=x, y=1)
#     return add(x=total, y=1)


def plain_add(x: int, y: int) -> int:
    """Add without a task decorator; graphs only call registered tasks."""
    return x + y


@graph
def unregistered_call(value: int) -> int:
    """Call an undecorated function; only registered tasks and graphs lower."""
    return plain_add(x=value, y=1)


# Decorate the callee instead:

# @task
# def plain_add(x: int, y: int) -> int:
#     return x + y


@graph
def subscript_assignment(value: int) -> int:
    """Mutate a placement in place; placements bind new names instead."""
    chosen = add(x=value, y=1)
    chosen['count'] = add(x=chosen, y=2)
    return chosen


# Bind a new name instead:

# @graph
# def fresh_binding(value: int) -> int:
#     first = add(x=value, y=1)
#     return add(x=first, y=2)


@graph
def nested_definition(value: int) -> int:
    """Define a helper inside the body; helpers belong in tasks."""

    def helper(x: int) -> int:
        return add(x=x, y=1)

    return helper(x=value)


# Move the helper into a task instead:

# @task
# def helper(x: int) -> int:
#     return add(x=x, y=1)


@graph
def early_return(value: int, flag: bool) -> int:
    """Return from a branch; graphs declare one output at the end."""
    if flag:
        return add(x=value, y=1)
    return add(x=value, y=2)


# Bind the branch instead:

# @graph
# def branched(value: int, flag: bool) -> int:
#     if flag:
#         chosen = add(x=value, y=1)
#     else:
#         chosen = add(x=value, y=2)
#     return chosen


@graph
def augmented_assignment(value: int) -> int:
    """Update a name in place; single-assignment keeps the graph well-defined."""
    total = add(x=value, y=1)
    total += 1
    return total


# Bind a new name instead:

# @graph
# def fresh_total(value: int) -> int:
#     first = add(x=value, y=1)
#     return add(x=first, y=1)


@graph
def annotated_assignment(value: int) -> int:
    """Annotate a local; locals carry no contracts in templates."""
    total: int = add(x=value, y=1)
    return total


# Drop the annotation instead:

# @graph
# def plain_binding(value: int) -> int:
#     total = add(x=value, y=1)
#     return total


@graph
def with_block(value: int) -> int:
    """Manage a resource in the body; templates hold no runtime resources.

    Move resource handling into a task instead.
    """
    with add(x=value, y=1):
        result = add(x=value, y=2)
    return result


# Move the block into a task instead:
# @task
# def resourced(value: int) -> int:
#     with acquire(value) as handle:
#         return use(handle)


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


# Declare fallible results instead:
# @task
# def fallible(value: int) -> Result[int, TaskErrors]: ...
#
# @graph
# def guarded(value: int) -> int:
#     outcome = fallible(value=value)
#     if outcome.error is None:
#         return outcome.result
#     return 0


@graph
def raise_statement(value: int) -> int:
    """Raise in the body; errors are values, not raises.

    Declare fallible results instead.
    """
    raise ValueError('graphs signal errors as values')
    return add(x=value, y=1)


# Return declared errors instead of raising:
# @task
# def fallible(value: int) -> Result[int, TaskErrors]: ...
#
# @graph
# def guarded(value: int) -> int:
#     outcome = fallible(value=value)
#     if outcome.error is None:
#         return outcome.result
#     return 0


@graph
def assert_statement(value: int) -> int:
    """Assert in the body; contracts validate at the boundary instead.

    Declare the contract on the ports instead.
    """
    assert value > 0
    return add(x=value, y=1)


# Check values where they execute, inside task bodies:
# @task
# def checked(value: int) -> int:
#     if value <= 0:
#         raise ValueError('expected a positive value')
#     return add(x=value, y=1)


@graph
def match_statement(value: int) -> int:
    """Match structurally; branch on conditions instead."""
    match value:
        case 0:
            return add(x=value, y=1)
        case _:
            return add(x=value, y=2)


# @graph
# def matched(value: int) -> int:
#     if value:
#         chosen = add(x=value, y=1)
#     else:
#         chosen = add(x=value, y=2)
#     return chosen


@graph
def starred_call(value: int) -> int:
    """Spread a sequence into a call; arity is static."""
    return add(*[value, 1])


# Pass each input by name instead:

# @graph
# def named_spread(value: int) -> int:
#     return add(x=value, y=1)


# TODO: Access by string?
# TODO: Could support it for Container types
@graph
def subscript_load(values: list[int]) -> int:
    """Read one element; collections travel whole."""
    return add(x=values[0], y=1)


# Pass the collection instead:

# @graph
# def whole_collection(values: list[int]) -> int:
#     return read_answer(values={'answer': 42})


@graph
def fstring_argument(value: int) -> int:
    """Format a string inline; every value needs a producing task.

    Format inside a task instead.
    """
    return add(x=value, y=f'{value}')


# Format inside a task instead:
# @task
# def greeting(value: int) -> str:
#     return f'result is {value}'
#
# @graph
# def formatted(value: int) -> str:
#     return greeting(value=value)


@graph
def list_comprehension(values: list[int]) -> int:
    """Map over inputs inline; scatter is a runtime control, not syntax.

    Unroll the placements instead.
    """
    doubled = [add(x=value, y=1) for value in values]  # noqa: F841 - the comprehension is rejected
    return add(x=values[0], y=1)


# Loop inside a task instead:
# @task
# def total(values: list[int]) -> int:
#     return sum(values)
#
# @graph
# def summed(values: list[int]) -> int:
#     return total(values=values)
