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
from tests.engine.processes.graphs.programs.port_models import (
    Configuration,
    DefaultedSettings,
    FlatSettings,
    PointSettings,
    Settings,
)
from tests.engine.processes.graphs.programs.tasks import (
    add,
    arithmetic_pair,
    read_answer,
    read_flat_count,
    read_flat_count_defaulted,
    read_nested_count,
    read_orm_node,
    read_point_count,
    statistics,
)


@graph
def direct_result(value: int) -> int:
    """Select the single output port explicitly."""
    return add(x=value, y=10).result


@graph
def named(x: int, y: int) -> dict[str, int]:
    """Return multiple named outputs from one task."""
    pair = arithmetic_pair(x=x, y=y)
    return {'total': pair.sum, 'product': pair.product}


@graph
def single_named_scalar(value: int) -> int:
    """Return one named output with a scalar-style hint."""
    out = add(x=value, y=0)
    return {'only': out}


@graph
def single_named_mapping(value: int) -> dict[str, int]:
    """Return one named output with a mapping-style hint."""
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
def config_leaves(config: Configuration) -> dict[str, int | str]:
    """Expose namespace fields as flat leaf outputs (`None` cannot be an output leaf)."""
    total = add(x=config.settings.count, y=1)
    return {'count': total, 'label': config.label}


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


@graph
def nested_passthrough(config: Configuration) -> int:
    """Pass a nested input leaf straight to outputs."""
    return config.settings.count


@graph
def summarize(values: list[float]):
    """Expose summary statistics computed by plain Python, selected by key."""
    stats = statistics(values=values)
    return {'mean': stats['mean'], 'stdev': stats['stdev']}


@graph
def flat_model(config: FlatSettings) -> int:
    """Select a field from a flat pydantic model."""
    return read_flat_count(config=config)


@graph
def point_model(config: PointSettings) -> int:
    """Select a field from a flat named-tuple model."""
    return read_point_count(config=config)


@graph
def flat_model_defaulted() -> int:
    """Run an adapted model task on its instance default."""
    return read_flat_count_defaulted()


# rejected at lowering: workflows return existing nodes, they never create data.
@graph
def literal_return() -> int:
    """Return a literal; workflows return existing nodes, they never create data."""
    return 42


# rejected at lowering: outputs are flat leaves.
@graph
def namespace_return(config: Configuration) -> Configuration:
    """Return a whole namespace; outputs are flat leaves."""
    return config


# rejected at lowering: outputs are flat leaves.
@graph
def nested_outputs(x: int) -> dict[str, dict[str, int]]:
    """Return nested outputs; outputs are flat leaves."""
    value = add(x=x, y=1)
    return {'outer': {'inner': value}}


# rejected at lowering: graphs declare their outputs explicitly.
@graph
def missing_final_return(value: int) -> int:
    """End without a return; graphs declare their outputs explicitly."""
    add(x=value, y=1)


# rejected at lowering: contracts fail fast at validation.
@graph
def wrong_type(x: str) -> int:
    """Feed a mistyped value; contracts fail fast at validation."""
    return add(x=x, y=1)


# rejected at lowering: collections travel whole.
@graph
def subscript_load(values: list[int]) -> int:
    """Read one element; collections travel whole."""
    return add(x=values[0], y=1)


# rejected at lowering: namespaces construct in tasks, not graphs.
@graph
def make_config(x: int) -> Configuration:
    """Build a namespace from task data; wrap construction in a task instead."""
    total = add(x=x, y=1)
    return Configuration(settings=Settings(count=total, nullable=None), label='test')


# rejected at lowering: values must be finite JSON.
@graph
def nonfinite_dict_value() -> int:
    """Dictionary literal values must be finite JSON."""
    return read_answer(values={'answer': 1e999})


# rejected at lowering: entries must be literal values.
@graph
def nonliteral_dict_value(value: int) -> int:
    """Dictionary entries must be literal values."""
    return read_answer(values={'answer': value})
