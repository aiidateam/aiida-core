###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tasks and graphs for the general ``partial(...)`` input-binding behavior suite.  # noqa: F821

A ``partial`` binds some inputs of a task or graph without running anything; each
use site merges the fixed values with its own arguments into one ordinary
placement. ``par_map`` over a partial fans out with the single remaining input
as its element. Fixed values capture the declaration-time references, so later
rebinding cannot change them.
"""

import typing as t

from aiida.engine import WorkChain, calcfunction, graph, par_map, task
from aiida.engine.processes.port_model import PortModel
from aiida.orm import Code, DataDict, DataList
from aiida.orm.nodes.data.int import Int
from tests.engine.processes.graphs.programs.calcjobs import add_calc


@task
def add(x: int, y: int) -> int:
    """Add two integers."""
    return x + y


@task
def add_three(x: int, y: int, z: int) -> int:
    """Add three integers."""
    return x + y + z


PickT = t.TypeVar('PickT', int, float)


@task
def pick_first(a: PickT, flag: bool) -> PickT:
    """Return the first input; the shared type variable rides only the fixed input."""
    return a


@task
def inc(value: int) -> int:
    """Add one to the input."""
    return value + 1


@task
def pack_three(a: int, b: int, c: int) -> DataList:
    """Pack three integers as an owned list."""
    return DataList([Int(a), Int(b), Int(c)])


@task
def pack_mapping(a: int, b: int) -> DataDict:
    """Pack two integers as an owned mapping."""
    return DataDict({'a': Int(a), 'b': Int(b)})


@task
def total(values: DataList) -> int:
    """Sum the owned integers."""
    assert isinstance(values, DataList)
    return sum(member.value for member in values)


@task
def empty_list() -> DataList:
    """Return an empty owned list."""
    return DataList()


@calcfunction
def chain_add(x: Int, y: Int) -> Int:
    """Add two stored integers; creating nodes belongs in a `calcfunction`, not the chain body."""
    return Int(x.value + y.value)


class AddChain(WorkChain):
    """Add two integers through a single outline step."""

    @classmethod
    def define(cls, spec) -> None:  # type: ignore[override]
        super().define(spec)
        spec.input('x', valid_type=Int)
        spec.input('y', valid_type=Int)
        spec.output('result', valid_type=Int)
        spec.outline(cls.add_numbers)

    def add_numbers(self):
        """Store the sum of the two inputs."""
        self.out('result', chain_add(self.inputs.x, self.inputs.y))


add_chain = task(AddChain)


@graph
def scaled(x: int, factor: int) -> int:
    """Scale in two steps, so graph partials inline more than one placement."""
    grown = add(x=x, y=x)
    return add.alias('scaled_add')(x=grown, y=factor)


@graph
def partial_task(x: int, y: int) -> int:
    """Call a task partial by keyword."""
    configured = partial(add, y=y)  # noqa: F821
    return configured(x=x)


@graph
def partial_positional(x: int, y: int) -> int:
    """Call a task partial with the remaining input positionally."""
    configured = partial(add, y=y)  # noqa: F821
    return configured(x)


@graph
def partial_reused(x: int, y: int, z: int) -> int:
    """Reuse one task partial for two placements, aliasing the second."""
    configured = partial(add, y=y)  # noqa: F821
    first = configured(x=x)
    second = configured.alias('second_add')(x=z)
    return add.alias('total_add')(x=first, y=second)


@graph
def partial_composed(x: int, y: int) -> int:
    """Compose a partial of a partial, fixing one input at each level."""
    base = partial(add, y=y)  # noqa: F821
    configured = partial(base, x=x)  # noqa: F821
    return configured()


@graph
def partial_inline(x: int, y: int) -> int:
    """Call an inline-constructed partial without binding a name."""
    return partial(add, y=y)(x=x)  # noqa: F821


@graph
def partial_graph(x: int, factor: int) -> int:
    """Call a multi-step graph partial, inlining its placements."""
    configured = partial(scaled, factor=factor)  # noqa: F821
    return configured(x=x)


@graph
def partial_branch(x: int, y: int, flag: bool) -> int:
    """Use one task partial on both arms of a branch."""
    configured = partial(add, y=y)  # noqa: F821
    if flag:
        result = configured(x=x)
    else:
        result = configured.alias('else_add')(x=y)
    return result


@graph
def partial_loop(start: int, step: int, limit: int, count: int = 0) -> int:
    """Use one task partial inside a loop body."""
    configured = partial(add, y=step)  # noqa: F821
    value = configured(x=start)
    while count < limit:
        count = count + 1
        value = configured(x=value)
    return value


@graph
def partial_rebound(start: int, step: int, limit: int, count: int = 0) -> int:
    """Fix loop state before the loop rebinds it; the fixed value must not follow."""
    seed = add.alias('seed_add')(x=start, y=0)
    configured = partial(add, y=seed)  # noqa: F821
    value = seed
    while count < limit:
        count = count + 1
        value = add(x=value, y=step)
    return configured(x=value)


@graph
def partial_workchain(x: int, y: int) -> int:
    """Call a `WorkChain` partial by keyword."""
    configured = partial(add_chain, y=y)  # noqa: F821
    return configured(x=x)


@graph
def partial_calcjob(x: int, y: int, code: Code) -> int | float:
    """Call a `CalcJob` partial, wiring the remaining inputs at the call."""
    configured = partial(add_calc, y=y)  # noqa: F821
    total = configured(x=x, code=code)
    return total.sum


@graph
def partial_generic_fixed(a: int, flag: bool) -> int:
    """Solve a generic target from its fixed input when the call carries no type variable."""
    configured = partial(pick_first, a=a)  # noqa: F821
    return configured(flag=flag)


@graph
def partial_aliased_target(x: int, y: int) -> int:
    """Bind a partial over an aliased target; uses keep the target alias."""
    configured = partial(add.alias('aliased_add'), y=y)  # noqa: F821
    return configured(x=x)


@graph
def partial_map_list(values: DataList, y: int) -> DataList:
    """Map a task partial over a list, fixing a graph input."""
    configured = partial(add, y=y)  # noqa: F821
    return par_map(configured, values)


@graph
def partial_map_upstream(a: int, b: int, c: int, y: int) -> DataList:
    """Map a task partial over a task-produced list with a fixed upstream output."""
    packed = pack_three(a=a, b=b, c=c)
    shared = add(x=a, y=y)
    configured = partial(add, y=shared)  # noqa: F821
    return par_map(configured, packed)


@graph
def partial_map_graph(values: DataList, factor: int) -> DataList:
    """Map a multi-step graph partial over a list."""
    configured = partial(scaled, factor=factor)  # noqa: F821
    return par_map(configured, values)


@graph
def partial_map_mapping(values: DataDict, y: int) -> DataDict:
    """Map a task partial over mapping values, keeping keys and order."""
    configured = partial(add, y=y)  # noqa: F821
    return par_map(configured, values)


@graph
def partial_map_inline(values: DataList, y: int) -> DataList:
    """Map an inline-constructed partial without binding a name."""
    return par_map(partial(add, y=y), values)  # noqa: F821


@graph
def partial_map_empty(y: int) -> DataList:
    """Map a task partial over a task-produced empty list."""
    empty = empty_list()
    configured = partial(add, y=y)  # noqa: F821
    return par_map(configured, empty)


@graph
def partial_map_chained(values: DataList, y: int) -> int:
    """Map a task partial and consume the result in a downstream task."""
    configured = partial(add, y=y)  # noqa: F821
    mapped = par_map(configured, values)
    return total(values=mapped)


@graph
def partial_map_after(x: int, values: DataList, y: int) -> DataList:
    """Map a task partial ordered after an earlier placement."""
    first = inc(value=x)
    configured = partial(add, y=y)  # noqa: F821
    return par_map(configured, values, after=first)


@graph
def partial_duplicate_fixed(x: int, y: int) -> int:
    """Fix one input twice; rejected as a duplicate fixed input."""
    configured = partial(partial(add, y=y), y=x)  # type: ignore[call-arg]  # noqa: F821
    return configured(x=x)


@graph
def partial_unknown_input(x: int, y: int) -> int:
    """Fix an undeclared input; rejected as an unknown input path."""
    configured = partial(add, nope=y)  # type: ignore[call-arg]  # noqa: F821
    return configured(x=x)


@graph
def partial_missing_required(x: int, y: int) -> int:
    """Leave a required input unwired; rejected as missing at the call."""
    configured = partial(add_three, y=y)  # noqa: F821
    return configured(x=x)


@graph
def partial_no_fixed(x: int) -> int:
    """Bind no inputs; rejected because a partial must fix at least one."""
    configured = partial(add)  # type: ignore[call-arg]  # noqa: F821
    return configured(x=x)


@graph
def partial_positional_fixed(x: int, y: int) -> int:
    """Fix an input positionally; rejected because fixed inputs bind by keyword."""
    configured = partial(add, y)  # type: ignore[call-arg]  # noqa: F821
    return configured(x=x)


@graph
def partial_illegal_target(values: DataList) -> DataList:
    """Bind a plain built-in; rejected as an illegal partial target."""
    configured = partial(len, y=1)  # type: ignore[arg-type]  # noqa: F821
    return par_map(configured, values)


@graph
def partial_after_binding(x: int, y: int) -> int:
    """Order a binding; rejected because `after` waits for the eventual call."""
    configured = partial(add, y=y, after=x)  # type: ignore[call-arg]  # noqa: F821
    return configured(x=x)


@graph
def partial_map_two_remaining(values: DataList) -> DataList:
    """Map a partial leaving two inputs open; rejected as not exactly one element."""
    configured = partial(pack_three, c=3)  # noqa: F821
    return par_map(configured, values)


@graph
def partial_map_no_output(values: DataList, y: int) -> DataList:
    """Map a partial of a task without outputs; rejected as missing an output."""
    configured = partial(no_output_task, y=y)  # noqa: F821
    return par_map(configured, values)


@task
def no_output_task(x: int, y: int) -> None:
    """Return nothing; mapping it is rejected as missing an output."""
    return None


@graph
def partial_map_unknown_fixed(values: DataList) -> DataList:
    """Map a partial with an unknown fixed input; rejected at the binding."""
    configured = partial(add, nope=1)  # type: ignore[call-arg]  # noqa: F821
    return par_map(configured, values)


@graph
def partial_call_fixed_again(x: int, y: int, z: int) -> int:
    """Pass a fixed input again at the call; rejected as a duplicate."""
    configured = partial(add, y=y)  # noqa: F821
    return configured(x=x, y=z)


@graph
def partial_map_calcjob(values: DataList, y: int) -> DataList:
    """Map a `CalcJob` partial; rejected like any mapped `CalcJob`."""
    configured = partial(add_calc, y=y)  # noqa: F821
    return par_map(configured, values)


class MergeSettings(PortModel):
    """Two leaves under one namespace, fixed and called disjointly."""

    first: int
    second: int


@task
def merge_settings(config: MergeSettings) -> int:
    """Add two namespaced leaves."""
    return config.first + config.second


@graph
def partial_namespace_merge(first: int, second: int) -> int:
    """Fix one namespaced leaf and supply the disjoint leaf at the call."""
    configured = partial(merge_settings, config={'first': first})  # noqa: F821
    return configured(config={'second': second})


@graph
def partial_namespace_conflict(first: int, second: int) -> int:
    """Repeat a namespaced leaf at the call; rejected as a duplicate leaf."""
    configured = partial(merge_settings, config={'first': first})  # noqa: F821
    return configured(config={'first': second})


@task
def add_collection(collection: int, other: int) -> int:
    """Add when the element input itself is named `collection`."""
    return collection + other


@graph
def partial_map_collection_element(values: DataList, other: int) -> DataList:
    """Map a partial whose remaining element input is named `collection`."""
    configured = partial(add_collection, other=other)  # noqa: F821
    return par_map(configured, values)


@graph
def partial_inline_alias(x: int, y: int) -> int:
    """Call an inline partial with a use-site alias."""
    return partial(add, y=y).alias('inline_add')(x=x)  # noqa: F821


@graph
def partial_map_inline_alias(values: DataList, y: int) -> DataList:
    """Map an inline partial with a use-site alias."""
    return par_map(partial(add, y=y).alias('map_inline_add'), values)  # noqa: F821


@graph
def partial_nested_alias(x: int, y: int) -> int:
    """Compose a partial over an aliased inline partial."""
    configured = partial(partial(add, y=y).alias('inner_add'), x=x)  # noqa: F821
    return configured()


Pick2T = t.TypeVar('Pick2T', int, float)


@task
def pick_either(a: Pick2T, b: Pick2T) -> Pick2T:
    """Return the first input; the type variable rides both inputs."""
    return a


@task
def need_int(value: int) -> int:
    """Add one to a statically typed integer."""
    return value + 1


@graph
def partial_generic_combined_same(a: int, b: int) -> int:
    """Solve a shared type variable from matching fixed and call-time evidence."""
    configured = partial(pick_either, a=a)  # noqa: F821
    picked = configured(b=b)
    return need_int(value=picked)


@graph
def partial_generic_combined_mixed(a: int, b: float) -> int | float:
    """Conflicting evidence stays unsolved; the call still runs."""
    configured = partial(pick_either, a=a)  # noqa: F821
    return configured(b=b)


@task
def shift(value: PickT, delta: PickT) -> PickT:
    """Shift the element; the type variable rides the element and the fixed input."""
    return value + delta  # type: ignore[return-value]


@graph
def partial_map_generic_fixed(values: DataList, delta: int) -> int:
    """Map a generic partial solved from its fixed input into a typed consumer."""
    configured = partial(shift, delta=delta)  # noqa: F821
    mapped = par_map(configured, values)
    return total(values=mapped)


@graph
def partial_branch_upstream(a: int, b: int, flag: bool) -> int:
    """Fix a task output outside the branch and use it on both arms."""
    shared = add(x=a, y=b)
    configured = partial(add, y=shared)  # noqa: F821
    if flag:
        result = configured.alias('take_add')(x=a)
    else:
        result = configured.alias('else_add')(x=b)
    return result


@graph
def partial_loop_upstream(start: int, step: int, limit: int, count: int = 0) -> int:
    """Fix a task output outside the loop and use it in every iteration."""
    shared = add(x=start, y=step)
    configured = partial(add, y=shared)  # noqa: F821
    value = start
    while count < limit:
        count = count + 1
        value = configured(x=value)
    return value


@graph
def partial_after_direct(x: int, y: int, z: int) -> int:
    """Order a direct partial use after an earlier placement."""
    first = add(x=x, y=y)
    configured = partial(add, y=z)  # noqa: F821
    return configured.alias('second_add')(x=first, after=first)


@graph
def partial_map_workchain(values: DataList, y: int) -> DataList:
    """Map a `WorkChain` partial over a list, fixing a graph input."""
    configured = partial(add_chain, y=y)  # noqa: F821
    return par_map(configured, values)
