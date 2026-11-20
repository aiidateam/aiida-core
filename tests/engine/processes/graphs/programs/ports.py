###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Ports declarations shared by the graph behavior suites."""

import typing as t

from typing_extensions import NotRequired, TypedDict

from aiida.engine.processes.graphs.lowering import graph
from aiida.orm.nodes.data.data import Data
from aiida.orm.nodes.data.int import Int
from tests.engine.processes.graphs.programs.port_models import (
    Configuration,
    DefaultedSettings,
    FlatSettings,
    PointSettings,
    Settings,
)
from tests.engine.processes.graphs.programs.tasks import (
    ArithmeticPair,
    SummaryStats,
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


class OnlyOutput(t.TypedDict):
    """One named graph output."""

    only: int


class PairOutputs(TypedDict):
    """The sum and product of a pair under the names `total` and `product`."""

    total: int
    product: int


class TextPairOutputs(TypedDict):
    """A `total` declared as text, which a stored integer cannot fill."""

    total: str
    product: int


class OptionalProductOutputs(TypedDict):
    """A `total` with a `product` that the return may leave out."""

    total: int
    product: NotRequired[int]


class TextSumPair(TypedDict):
    """A `sum` declared as text, which a stored integer cannot fill."""

    sum: str
    product: int


class NestedTextSumPair(TypedDict):
    """A nested `pair` whose `sum` the annotation mistypes."""

    pair: TextSumPair


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
def single_named_scalar(value: int) -> OnlyOutput:
    """Return one named output declared by a `TypedDict`."""
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
def summarize(values: list[float]) -> SummaryStats:
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


@graph
def nullable_return(value: int | None = None) -> int | None:
    """Return an optional input; an absent value emits no output."""
    return value


@graph
def nullable_forward(value: int | None = None) -> int | None:
    """Forward the optional output of a child graph; an absent value emits no output."""
    return nullable_return(value=value)


@graph
def nullable_chain(value: int | None = None) -> int | None:
    """Wire the optional output of a child graph; an absent value leaves the next input unwired."""
    forwarded = nullable_return(value=value)
    return nullable_return(value=forwarded).alias('nullable_return_2')


@graph
def unrestricted_return(value: t.Any) -> Data:
    """Return an unrestricted required input; a `None` value emits no output."""
    return value


# rejected at lowering: workflows return existing nodes, they never create data.
@graph
def literal_return() -> int:
    """Return a literal; workflows return existing nodes, they never create data."""
    return 42


@graph
def namespace_return(config: Configuration) -> Configuration:
    """Return a whole namespace; outputs regroup existing nodes."""
    return config


@graph
def nested_outputs(x: int) -> dict[str, dict[str, int]]:
    """Return nested outputs; outputs regroup existing nodes."""
    value = add(x=x, y=1)
    return {'outer': {'inner': value}}


@graph
def return_pair(x: int, y: int) -> ArithmeticPair:
    """Return a whole task-outputs namespace."""
    produced = arithmetic_pair(x=x, y=y)
    return produced


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


@graph
def subscript_load(values: list[int]) -> int:
    """Read one element inline and pass it to a task."""
    return add(x=values[0], y=1)


# rejected at lowering: namespaces construct in tasks, not graphs.
@graph
def make_config(x: int) -> Configuration:
    """Build a namespace from task data; wrap construction in a task instead."""
    total = add(x=x, y=1)
    return Configuration(settings=Settings(count=total, nullable=None), label='test')


# rejected at lowering: graph outputs are checked against the return annotation.
@graph
def unannotated_return(value: int):
    """Leave out the return annotation; every graph declares one."""
    return add(x=value, y=1)


# rejected at lowering: `Any` declares no outputs to check the return against.
@graph
def any_return(value: int) -> t.Any:
    """Annotate the return with `Any`; graphs declare checkable outputs."""
    return add(x=value, y=1)


# rejected at lowering: the return must produce every declared output.
@graph
def missing_declared_output(x: int, y: int) -> PairOutputs:
    """Omit the declared `product` output."""
    pair = arithmetic_pair(x=x, y=y)
    return {'total': pair.sum}


# rejected at lowering: the return produces only declared outputs.
@graph
def undeclared_output(x: int, y: int) -> PairOutputs:
    """Return an `extra` output the annotation does not declare."""
    pair = arithmetic_pair(x=x, y=y)
    return {'total': pair.sum, 'product': pair.product, 'extra': pair.sum}


# rejected at lowering: a single-value annotation requires one returned value.
@graph
def mapping_for_single_value(x: int, y: int) -> int:
    """Return a mapping under a single-value annotation."""
    pair = arithmetic_pair(x=x, y=y)
    return {'total': pair.sum, 'product': pair.product}


# rejected at lowering: every early return agrees with the annotation too.
@graph
def early_return_missing_output(x: int, y: int, flag: bool) -> PairOutputs:
    """Omit a declared output on the early return only."""
    pair = arithmetic_pair(x=x, y=y)
    if flag:
        return {'total': pair.sum}
    return {'total': pair.sum, 'product': pair.product}


# rejected at validation: declared field types fit the stored outputs.
@graph
def mistyped_declared_output(x: int, y: int) -> TextPairOutputs:
    """Declare `total` as text while returning an integer."""
    pair = arithmetic_pair(x=x, y=y)
    return {'total': pair.sum, 'product': pair.product}


# rejected at lowering: nested field types agree with the annotation too.
@graph
def mistyped_nested_output(x: int, y: int) -> TextSumPair:
    """Return a whole namespace whose `sum` field the annotation mistypes."""
    return arithmetic_pair(x=x, y=y)


# rejected at lowering: nested mapping fields agree with the annotation too.
@graph
def mistyped_nested_mapping(x: int, y: int) -> NestedTextSumPair:
    """Return a nested mapping whose `pair.sum` field the annotation mistypes."""
    pair = arithmetic_pair(x=x, y=y)
    return {'pair': {'sum': pair.sum, 'product': pair.product}}


@graph
def optional_output_absent(x: int, y: int) -> OptionalProductOutputs:
    """Leave out an output the annotation marks `NotRequired`."""
    pair = arithmetic_pair(x=x, y=y)
    return {'total': pair.sum}


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
