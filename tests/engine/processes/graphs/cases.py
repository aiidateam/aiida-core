###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Importable straight-line task and graph declarations."""

from aiida.engine import PortModel, graph, task
from aiida.orm import Int


class Settings(PortModel):
    count: int = 2
    nullable: int | None


class Configuration(PortModel):
    settings: Settings
    label: str = 'test'


@task
def add(x: int, y: int) -> int:
    return x + y


@task
def multiply(x: int, y: int) -> int:
    return x * y


@task(outputs=('sum', 'product'))
def arithmetic(x: int, y: int) -> tuple[int, int]:
    return x + y, x * y


@task
def read_config(config: Configuration) -> int:
    return config.settings.count


@task
def read_dict(values: dict[str, int]) -> int:
    return values['answer']


@task
def read_node(value: int) -> int:
    return value


@task
def read_orm_node(value: Int) -> int:
    assert isinstance(value, Int)
    return value.value


@task
def prepare(value: int) -> None:
    assert value > 0


@task
def broken(x: int) -> int:
    raise ValueError('deliberately failed')


@task
def wrong_output(x: int) -> int:
    return 'wrong'


@task
def wrong_list(x: int) -> list[int]:
    return {'value': x}


@task
def wrong_dict(x: int) -> dict[str, int]:
    return [x]


@task
def add_2(x: int, y: int) -> int:
    return x + y


def no_output_declaration(x: int):
    return x


def dynamic_inputs(**kwargs) -> int:
    return 1


# Supported straight-line graphs.


@graph
def chain(x: int, y: int) -> int:
    first = add(x=x, y=y)
    return add(x=first, y=y)


@graph
def multiply_add(x: int, y: int, z: int) -> int:
    """Return the arithmetic result for the local multiply-add workflow example."""
    product = multiply(x=x, y=y)
    addition = add(x=product, y=z)
    return {'result': addition}


@graph
def diamond(x: int) -> int:
    left = add(x=x, y=1)
    right = add(x=x, y=2)
    return add(x=left, y=right)


@graph
def ordered(x: int) -> int:
    first = prepare(value=x)
    return add(x=x, y=1, after=first)


@graph
def multiple_ordered(x: int) -> int:
    first = prepare(value=x)
    second = prepare(value=x)
    return add(x=x, y=1, after=(first, second))


@graph
def named(x: int, y: int) -> dict[str, int]:
    pair = arithmetic(x=x, y=y)
    return {'total': pair.sum, 'product': pair.product}


@graph
def whole(config: Configuration) -> int:
    return read_config(config=config)


@graph
def selected(config: Configuration) -> int:
    return add(x=config.settings.count, y=1)


@graph
def wired(config: Configuration) -> int:
    chosen = add(x=config.settings.count, y=1)
    return read_config(config={'settings': {'count': chosen, 'nullable': config.settings.nullable}})


@graph
def dictionary_input(values: dict[str, int]) -> int:
    return read_dict(values=values)


@graph
def orm_passthrough(value: Int) -> int:
    return read_orm_node(value=value)


@graph(identifier='custom-label')
def labelled(x: int) -> int:
    return add(x=x, y=1)


@graph
def failed(x: int) -> int:
    first = broken(x=x)
    return add(x=first, y=1)


@graph
def collision(x: int) -> int:
    first = add(x=x, y=1)
    second = add(x=first, y=1)
    return add_2(x=second, y=1)


@graph
def missing_task_input(x: int) -> int:
    return add(x=x)


# Deferred composition constructs, rejected at this checkpoint.


@graph
def nested(x: int, y: int) -> int:
    inner = chain(x=x, y=y)
    return add(x=inner, y=x)


@graph
def external_choice(value: int, condition: bool) -> int:
    if condition:
        selected_branch = add(x=value, y=1)
    else:
        selected_branch = add(x=value, y=2)
    return selected_branch


@graph
def countdown(value: int, condition: bool) -> int:
    while condition:
        value = add(x=value, y=-1)
        condition = read_node(value=value)
    return value


# Rejected declarations.


@graph
def positional_task_arguments(value: int) -> int:
    return add(value, 1)


@graph
def expanded_task_arguments(values: dict[str, int]) -> int:
    return add(**values)


@graph
def arithmetic_expression(value: int) -> int:
    return add(x=value + 1, y=2)


@graph
def tuple_assignment(x: int, y: int) -> int:
    total, product = arithmetic(x=x, y=y)
    return add(x=total, y=product)


@graph
def chained_assignment(value: int) -> int:
    first = second = add(x=value, y=1)
    return add(x=first, y=second)


@graph
def reassigned_name(value: int) -> int:
    result = add(x=value, y=1)
    result = add(x=result, y=2)
    return result


@graph
def fanout(values: list[int]) -> int:
    for value in values:
        result = add(x=value, y=1)
    return result


@graph
def default_parameter(value: int = 2) -> int:
    return add(x=value, y=1)


@graph
def keyword_only_parameter(*, value: int) -> int:
    return add(x=value, y=1)


@graph
def positional_only_parameter(value: int, /) -> int:
    return add(x=value, y=1)


@graph
def variadic_parameters(*values: int) -> int:
    return add(x=1, y=2)


@graph
def literal_return() -> int:
    return 42


@graph
def namespace_return(config: Configuration) -> Configuration:
    return config


@graph
def nested_outputs(x: int):
    value = add(x=x, y=1)
    return {'outer': {'inner': value}}


@graph
def missing_final_return(value: int) -> int:
    add(x=value, y=1)


@graph
def recursive_call(value: int) -> int:
    return recursive_call(value=value)


@graph
def wrong_type(x: str) -> int:
    return add(x=x, y=1)


@graph
def unbound(value: int) -> int:
    return add(x=value, y=missing)  # noqa: F821 - unbound names must fail at lowering
