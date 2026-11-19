###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tasks and graphs shared by the `par_map` behavior suite.

Tasks take and return plain values or owned containers; graphs map unary
tasks and nested graphs over `DataList`/`DataDict` wires, including empty and
task-produced collections, downstream chaining, and invalid declarations.
"""

import typing as t

from aiida.engine import WorkChain, graph, par_map, task
from aiida.orm import DataDict, DataList, StructureData
from aiida.orm.nodes.data.int import Int


@task
def expand_structure(structure: StructureData) -> StructureData:
    """Double the cell vectors without changing the input."""
    expanded = structure.clone()
    expanded.set_cell([[2 * component for component in vector] for vector in structure.cell])
    return expanded


@task
def keep_structures(structures: DataList[StructureData]) -> DataList[StructureData]:
    """Exercise typed container input and output ports."""
    return structures.clone()


@graph
def map_typed_structures(structures: DataList[StructureData]) -> DataList[StructureData]:
    """Map structures, preserving annotations at the graph and task boundaries."""
    expanded = par_map(expand_structure, structures)
    return keep_structures(structures=expanded)


@task
def increment(x: int) -> int:
    """Add one to the input."""
    return x + 1


@task
def double(x: int) -> int:
    """Double the input."""
    return 2 * x


@task
def explode_on_two(x: int) -> int:
    """Fail when the element is two, for failure propagation."""
    if x == 2:
        raise ValueError('deliberately failed')
    return x + 1


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
def mapping_total(values: DataDict) -> int:
    """Sum the owned values."""
    assert isinstance(values, DataDict)
    return sum(member.value for member in values.values())


@task
def map_increment_0(x: int) -> int:
    """Add a hundred; the name collides with the first `map_increment` item label."""
    return x + 100


@task
def map_increment_collect(x: int) -> int:
    """Add a thousand; the name collides with the `map_increment` collector label."""
    return x + 1000


class DropSecondWorkChain(WorkChain):
    """Omit the declared output when the element is two, failing that map item."""

    @classmethod
    def define(cls, spec) -> None:  # type: ignore[override]
        super().define(spec)
        spec.input('x', valid_type=Int)
        spec.outputs.dynamic = True
        spec.outline(cls.produce)

    def produce(self):
        """Store the incremented input, except for the element under test."""
        if self.inputs.x.value == 2:
            return
        self.out('result', Int(self.inputs.x.value + 1))


drop_second_chain = task(DropSecondWorkChain, outputs={'result': Int})


class MistypeSecondWorkChain(WorkChain):
    """Return the wrong node type when the element is two, failing that map item."""

    @classmethod
    def define(cls, spec) -> None:  # type: ignore[override]
        super().define(spec)
        spec.input('x', valid_type=Int)
        spec.outputs.dynamic = True
        spec.outline(cls.produce)

    def produce(self):
        """Store the incremented input, mistyped for the element under test."""
        from aiida.orm import Str

        if self.inputs.x.value == 2:
            self.out('result', Str('oops'))
        else:
            self.out('result', Int(self.inputs.x.value + 1))


mistype_second_chain = task(MistypeSecondWorkChain, outputs={'result': Int})


@task
def empty_list() -> DataList:
    """Return an empty owned list."""
    return DataList()


@task
def empty_mapping() -> DataDict:
    """Return an empty owned mapping."""
    return DataDict()


@task
def two_inputs(x: int, y: int) -> int:
    """Take two inputs; mapping it is rejected as non-unary."""
    return x + y


class Pair(t.TypedDict):
    """Two named outputs; mapping it is rejected as multi-output."""

    first: int
    second: int


@task
def pair_outputs(x: int) -> Pair:
    """Return two named outputs."""
    return {'first': x, 'second': x}


@task
def no_output(x: int) -> None:
    """Return nothing; mapping it is rejected as missing an output."""
    return None


@graph
def add_one(x: int) -> int:
    """Add one inside a nested graph."""
    return increment(x=x)


@graph
def map_list(values: DataList) -> DataList:
    """Map a task over an owned list."""
    return par_map(increment, values)


@graph
def map_mapping(values: DataDict) -> DataDict:
    """Map a task over owned mapping values, keeping keys."""
    return par_map(increment, values)


@graph
def map_nested(values: DataList) -> DataList:
    """Map a nested graph over an owned list."""
    return par_map(add_one, values)


@graph
def map_computed(a: int, b: int, c: int) -> DataList:
    """Map over a task-produced list."""
    packed = pack_three(a=a, b=b, c=c)
    return par_map(double, packed)


@graph
def map_chained(values: DataList) -> int:
    """Map over a list and consume the result in a downstream task."""
    mapped = par_map(increment, values)
    return total(values=mapped)


@graph
def map_empty_list() -> DataList:
    """Map over a task-produced empty list."""
    empty = empty_list()
    return par_map(increment, empty)


@graph
def map_empty_mapping() -> DataDict:
    """Map over a task-produced empty mapping."""
    empty = empty_mapping()
    return par_map(increment, empty)


@graph
def map_empty_input(values: DataList) -> DataList:
    """Map over an empty list graph input."""
    return par_map(increment, values)


@graph
def map_fails(values: DataList) -> DataList:
    """Map a task that fails on one element."""
    return par_map(explode_on_two, values)


@graph
def map_avoids_placement_names(values: DataList, x: int) -> DataList:
    """Map beside ordinary placements named like the default item and collector labels."""
    first = map_increment_0(x=x)
    second = map_increment_collect(x=first, after=first)
    return par_map(increment, values, after=second)


@graph
def map_missing_workchain_output(values: DataList) -> DataList:
    """Map a `WorkChain` omitting its declared output for one element."""
    return par_map(drop_second_chain, values)


@graph
def map_mistyped_workchain_output(values: DataList) -> DataList:
    """Map a `WorkChain` mistyping its declared output for one element."""
    return par_map(mistype_second_chain, values)


@graph
def map_keyword(values: DataList) -> DataList:
    """Map with keyword arguments."""
    return par_map(func=increment, values=values)


@graph
def map_after(x: int, values: DataList) -> DataList:
    """Map ordered after an earlier placement."""
    first = increment(x=x)
    return par_map(increment, values, after=first)


@graph
def map_two_inputs(values: DataList) -> DataList:
    """Map a two-input task; rejected as non-unary."""
    return par_map(two_inputs, values)


@graph
def map_pair_outputs(values: DataList) -> DataList:
    """Map a two-output task; rejected as multi-output."""
    return par_map(pair_outputs, values)


@graph
def map_no_output(values: DataList) -> DataList:
    """Map a task without outputs; rejected as missing an output."""
    return par_map(no_output, values)


@graph
def map_plain_function(values: DataList) -> DataList:
    """Map an undecorated built-in; rejected as unregistered."""
    return par_map(len, values)


@graph
def map_unknown(values: DataList) -> DataList:
    """Map an unknown name; rejected as unresolvable."""
    return par_map(not_a_task, values)  # type: ignore[name-defined] # noqa: F821


@graph
def map_bad_collection(x: int) -> DataList:
    """Map over an integer; rejected as not a container."""
    return par_map(increment, x)


@graph
def map_missing_collection(values: DataList) -> DataList:
    """Map with only the callable; rejected as missing the collection."""
    return par_map(increment)  # type: ignore[call-arg]
