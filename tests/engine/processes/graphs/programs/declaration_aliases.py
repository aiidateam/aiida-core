###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Declaration-name resolution fixtures shared by the graph behavior suites.

Calls resolve to the declared name of an importable task or graph: the plain
``@task``/``@graph`` name in the graph's module, or a module-qualified target
such as ``tasks.add``. Legacy ``task(CalcJob)``/``task(WorkChain)`` factory
variables (``add_calc``, ``add_chain``) are the declaration under their
assigned variable name and keep resolving. Anything else at module scope is
not a declaration, even when it holds a handle:

* ``function_alias = add`` reuses the ``add`` handle under another name.
* ``stored_alias = add.alias('scf')`` stores an explicit placement outside
  the graph body, where no placement exists yet.
* ``renamed_add`` renames ``add`` at import time.

Each of those must be called through the declared name with an inline
``.alias('name')`` placement instead. Module-global scalars, nodes, and other
values are not wires either; pass them as graph inputs instead of reading a
global. Enum members, module-qualified tasks, and ``par_map`` callables keep
their existing resolution and are covered by the positive tests.
"""

from aiida.engine import par_map
from aiida.engine.processes.graphs.lowering import graph
from aiida.orm import Code, DataList, Int
from tests.engine.processes.graphs.programs import calls as call_programs
from tests.engine.processes.graphs.programs import tasks as task_module
from tests.engine.processes.graphs.programs.calcjobs import add_calc
from tests.engine.processes.graphs.programs.tasks import add, decrement
from tests.engine.processes.graphs.programs.tasks import add as renamed_add
from tests.engine.processes.graphs.programs.workchains import add_chain

# Implicit callable aliases: each reuses a declaration under another module-global name.
function_alias = add
calcjob_alias = add_calc
workchain_alias = add_chain
graph_alias = call_programs.multiply_add
renamed_function_alias = renamed_add

# Stored placement handles: the alias constructor belongs on the call inside the graph body.
stored_function_alias = add.alias('scf')
stored_calcjob_alias = add_calc.alias('scf')
stored_graph_alias = call_programs.multiply_add.alias('stage')

# Module-global values: scientific inputs travel through graph inputs, not globals.
GLOBAL_SCALE = 5
GLOBAL_OFFSET: Int | None = None
GLOBAL_OPTIONS = {'resources': {'num_machines': 1}}


@graph
def calls_function_alias(x: int, y: int) -> int:
    """Call a function task through a module-global alias instead of its declared name."""
    return function_alias(x=x, y=y)


@graph
def calls_calcjob_alias(x: int, y: int, code: Code) -> int | float:
    """Call a `CalcJob` factory handle through a module-global alias."""
    total = calcjob_alias(x=x, y=y, code=code)
    return total.sum


@graph
def calls_workchain_alias(x: int, y: int) -> int:
    """Call a `WorkChain` factory handle through a module-global alias."""
    total = workchain_alias(x=x, y=y)
    return total.result


@graph
def calls_graph_alias(x: int, y: int, z: int) -> int:
    """Call a nested graph through a module-global alias."""
    return graph_alias(x=x, y=y, z=z)


@graph
def calls_renamed_import(x: int, y: int) -> int:
    """Call a task renamed at import time instead of its declared name."""
    return renamed_add(x=x, y=y)


@graph
def calls_stored_function_alias(x: int, y: int) -> int:
    """Call a stored `.alias(...)` handle instead of placing the alias inline."""
    return stored_function_alias(x=x, y=y)


@graph
def calls_stored_calcjob_alias(x: int, y: int, code: Code) -> int | float:
    """Call a stored `CalcJob` `.alias(...)` handle instead of placing the alias inline."""
    total = stored_calcjob_alias(x=x, y=y, code=code)
    return total.sum


@graph
def calls_stored_graph_alias(x: int, y: int, z: int) -> int:
    """Call a stored nested-graph `.alias(...)` handle instead of placing the alias inline."""
    return stored_graph_alias(x=x, y=y, z=z)


# rejected at lowering: module globals are not wires; pass the value as a graph input instead.
@graph
def reads_global_scalar(x: int) -> int:
    """Read a module-global number instead of taking it as a graph input."""
    return add(x=x, y=GLOBAL_SCALE)


# rejected at lowering: stored nodes enter through graph inputs, not module globals.
@graph
def reads_global_node(x: int) -> int:
    """Read a module-global node instead of taking it as a graph input."""
    return add(x=x, y=GLOBAL_OFFSET)


# rejected at lowering: opaque module values carry no wire; pass them as graph inputs instead.
@graph
def reads_global_mapping(x: int) -> int:
    """Read a module-global mapping instead of taking it as a graph input."""
    return add(x=x, y=GLOBAL_OPTIONS)


@graph
def calls_module_qualified(x: int, y: int) -> int:
    """Call a task through its module; module-qualified declarations keep resolving."""
    return task_module.add(x=x, y=y)


@graph
def calls_canonical_factory(x: int, y: int, code: Code) -> int | float:
    """Call a `CalcJob` factory variable under its assigned declaration name."""
    total = add_calc(x=x, y=y, code=code)
    return total.sum


@graph
def calls_inline_alias(x: int, y: int) -> int:
    """Place an inline `.alias(...)` at the call; aliases are local to the graph body."""
    return add(x=x, y=y).alias('scf')


@graph
def maps_inline_alias(values: DataList) -> DataList:
    """Map an inline-aliased callable; the alias stays on the mapped callable."""
    return par_map(decrement.alias('step'), values)
