###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Placement alias declarations shared by the graph behavior suites.

Each graph calls a task or subgraph through an explicit local placement
constructor, ``task.alias('scf')(...)``, which names the placement instead of
relying on the default task name or a generated numeric suffix. The ``scf``
name is a placeholder for any stable authored name; tests assert the compiled
template carries exactly that placement name and the run dispatches under it.

Wire and value aliases (``chosen = first`` in a branch, ``first = second = 0``
for constants, ``pair.sum`` field reads) are a separate language feature and
keep their existing fixtures in :mod:`branches <tests.engine.processes.graphs.programs.branches>`
and :mod:`constants <tests.engine.processes.graphs.programs.constants>`; this
module only covers the callable placement constructor. Module-global
``Forward`` type aliases (``AddInputs`` in ``calls``) are also unrelated and
stay where they are.
"""

from aiida.engine import par_map
from aiida.engine.processes.graphs.lowering import graph
from aiida.orm import Code, DataList
from tests.engine.processes.graphs.programs import calls as call_programs
from tests.engine.processes.graphs.programs import tasks
from tests.engine.processes.graphs.programs import tasks as task_module
from tests.engine.processes.graphs.programs.calcjobs import add_calc
from tests.engine.processes.graphs.programs.tasks import add, decrement, generic_add, is_positive
from tests.engine.processes.graphs.programs.workchains import add_chain


@graph
def aliased_function(x: int, y: int) -> int:
    """Place one function task under an explicit name."""
    return add.alias('scf')(x=x, y=y)


@graph
def aliased_two_functions(x: int, y: int) -> int:
    """Place the same function task twice under two explicit names."""
    first = add.alias('scf')(x=x, y=y)
    return add.alias('nscf')(x=first, y=y)


@graph
def aliased_calcjob(x: int, y: int, code: Code) -> int | float:
    """Place one `CalcJob` task under an explicit name."""
    total = add_calc.alias('scf')(x=x, y=y, code=code)
    return total.sum


@graph
def aliased_two_calcjobs(x: int, y: int, code: Code) -> int | float:
    """Place the same `CalcJob` task twice under two explicit names."""
    first = add_calc.alias('scf')(x=x, y=y, code=code)
    second = add_calc.alias('nscf')(x=first.sum, y=y, code=code)
    return second.sum


@graph
def aliased_workchain(x: int, y: int) -> int:
    """Place one `WorkChain` task under an explicit name."""
    total = add_chain.alias('scf')(x=x, y=y)
    return total.result


@graph
def aliased_two_workchains(x: int, y: int) -> int:
    """Place the same `WorkChain` task twice under two explicit names."""
    first = add_chain.alias('scf')(x=x, y=y)
    second = add_chain.alias('nscf')(x=first.result, y=y)
    return second.result


@graph
def aliased_graph(x: int, y: int, z: int) -> int:
    """Place one nested graph under an explicit name."""
    return call_programs.multiply_add.alias('stage')(x=x, y=y, z=z)


@graph
def aliased_inner(x: int, y: int) -> int:
    """Place a function task under an explicit name inside a nested graph."""
    return add.alias('pw')(x=x, y=y)


@graph
def aliased_nested(x: int, y: int) -> int:
    """Place a nested graph holding an aliased task under an explicit name."""
    return aliased_inner.alias('scf')(x=x, y=y)


@graph
def aliased_branch(value: int, flag: bool) -> int:
    """Place an aliased task on the taken branch arm."""
    if flag:
        chosen = add.alias('scf')(x=value, y=1)
    else:
        chosen = add.alias('scf')(x=value, y=2)
    return chosen


@graph
def aliased_loop(value: int, count: int) -> int:
    """Step an aliased task across loop iterations; one entry covers every pass."""
    total = add.alias('scf')(x=value, y=0)
    while is_positive(value=count):
        total = add.alias('scf')(x=total, y=1)
        count = decrement(value=count)
    return total


@graph
def aliased_ordered(x: int) -> int:
    """Order an aliased placement with `after`."""
    first = add.alias('prepare')(x=x, y=0)
    return add.alias('scf')(x=x, y=1, after=first)


@graph
def aliased_generic(x: int, y: int) -> int:
    """Place a generic task under an explicit name; constraints still check."""
    return generic_add.alias('scf')(a=x, b=y)


@graph
def aliased_dotted(x: int, y: int) -> int:
    """Place a task reached through a dotted module path under an explicit name."""
    return tasks.add.alias('scf')(x=x, y=y)


@graph
def aliased_module(x: int, y: int) -> int:
    """Place a task reached through an imported module under an explicit name."""
    return task_module.add.alias('scf')(x=x, y=y)


@graph
def aliased_map(values: DataList) -> DataList:
    """Map an aliased unary task over an owned list."""
    return par_map(decrement.alias('step'), values)


@graph
def aliased_inner_scf(x: int, y: int) -> int:
    """Place a function task under the outer alias name inside a nested graph."""
    return add.alias('scf')(x=x, y=y)


@graph
def aliased_scoped_nested(x: int, y: int) -> int:
    """Reuse one alias in the outer body and inside a nested graph; scopes keep them apart."""
    first = add.alias('scf')(x=x, y=y)
    return aliased_inner_scf.alias('stage')(x=first, y=y)


# rejected at build: each placement needs its own name; repeats take `.alias('unique_name')`.
@graph
def duplicate_implicit(x: int, y: int) -> int:
    """Call one task twice without aliases; the second placement reuses the task name."""
    first = add(x=x, y=y)
    return add(x=first, y=y)


# rejected at build: each placement needs its own name, so one alias cannot cover two calls.
@graph
def duplicate_explicit(x: int, y: int) -> int:
    """Place one task twice under one alias; each alias names a single placement."""
    first = add.alias('scf')(x=x, y=y)
    return add.alias('scf')(x=first, y=y)


# rejected at build: an explicit alias cannot reuse a name another placement already holds.
@graph
def duplicate_mixed(x: int, y: int) -> int:
    """Pair a bare call with an explicit alias colliding on the task name."""
    first = add(x=x, y=y)
    return add.alias('add')(x=first, y=y)


# rejected at build: nested calls hide a placement; put the inner call on its own line first.
@graph
def duplicate_nested_argument(x: int, y: int) -> int:
    """Nest one call inside another call to the same task; nesting never bypasses placement naming."""
    return add(x=add(x=x, y=y), y=y)


# rejected at build: repeated nested graphs name each subgraph placement, like tasks.
@graph
def duplicate_nested_graph(x: int, y: int, z: int) -> int:
    """Place one nested graph twice without aliases."""
    first = call_programs.multiply_add(x=x, y=y, z=z)
    return call_programs.multiply_add(x=first, y=y, z=z)


# rejected at build: repeated default maps share one map name; alias the callable instead.
@graph
def duplicate_map(values: DataList) -> DataList:
    """Map one task twice without aliases; both maps would place as `map_decrement`."""
    first = par_map(decrement, values)  # noqa: F841 - the first map is rejected before wiring matters
    return par_map(decrement, values)


# rejected at build: one map alias cannot cover two maps, like one task alias cannot cover two calls.
@graph
def duplicate_map_explicit(values: DataList) -> DataList:
    """Map one aliased task twice under one map name."""
    first = par_map(decrement.alias('step'), values)  # noqa: F841 - the first map is rejected before wiring matters
    return par_map(decrement.alias('step'), values)


# rejected at build: placement names are link labels and cannot be empty.
@graph
def alias_empty(x: int, y: int) -> int:
    """Alias with an empty name; names must be non-empty link labels."""
    return add.alias('')(x=x, y=y)


# rejected at build: placement names follow the link-label contract.
@graph
def alias_invalid(x: int, y: int) -> int:
    """Alias with spaces and punctuation; use alphanumerics and underscores instead."""
    return add.alias('bad alias!')(x=x, y=y)


# rejected at build: the alias must be a string literal the compiler can read.
@graph
def alias_nonliteral(x: int, y: int, label: str) -> int:
    """Alias through a graph input; the compiler only accepts a literal name."""
    return add.alias(label)(x=x, y=y)
