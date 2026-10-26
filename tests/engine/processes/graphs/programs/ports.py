###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Ports declarations shared by the graph behavior suites."""

from aiida.engine.processes.graphs.lowering import graph
from aiida.orm.nodes.data.int import Int
from tests.engine.processes.graphs.programs.port_models import Configuration, DefaultedSettings
from tests.engine.processes.graphs.programs.tasks import add, read_answer, read_nested_count, read_orm_node


@graph
def literal_return() -> int:  # rejected at lowering
    """Return a literal; workflows return existing nodes, they never create data."""
    return 42


@graph
def namespace_return(config: Configuration) -> Configuration:  # rejected at lowering
    """Return a whole namespace; outputs are flat leaves."""
    return config


@graph
def nested_outputs(x: int) -> dict[str, dict[str, int]]:  # rejected at lowering
    """Return nested outputs; outputs are flat leaves."""
    value = add(x=x, y=1)
    return {'outer': {'inner': value}}


@graph
def missing_final_return(value: int) -> int:  # rejected at lowering
    """End without a return; graphs declare their outputs explicitly."""
    add(x=value, y=1)


@graph
def wrong_type(x: str) -> int:  # rejected at lowering
    """Feed a mistyped value; contracts fail fast at validation."""
    return add(x=x, y=1)


@graph
def subscript_load(values: list[int]) -> int:  # rejected at lowering
    """Read one element; collections travel whole."""
    return add(x=values[0], y=1)


@graph
def direct_result(value: int) -> int:
    """Select the single output port explicitly."""
    return add(x=value, y=10).result


@graph
def single_named_scalar(value: int) -> int:
    """Return one named output with a scalar-style hint."""
    out = add(x=value, y=0)
    return {'only': out}


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
def nonfinite_dict_value() -> int:  # rejected at lowering
    """Dictionary literal values must be finite JSON."""
    return read_answer(values={'answer': 1e999})


@graph
def nonliteral_dict_value(value: int) -> int:  # rejected at lowering
    """Dictionary entries must be literal values."""
    return read_answer(values={'answer': value})


@graph
def orm_passthrough(value: Int) -> int:
    """Pass an ORM node through a task."""
    return read_orm_node(value=value)


@graph
def input_passthrough(value: int) -> int:
    """Pass a graph input straight to outputs."""
    return value


@graph
def nested_passthrough(config: Configuration) -> int:
    """Pass a nested input leaf straight to outputs."""
    return config.settings.count
