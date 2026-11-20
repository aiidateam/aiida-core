###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Declaration-name resolution: canonical names resolve, global aliases do not.

Calls resolve to an importable declaration under its own name: the plain
``@task``/``@graph`` name, a module-qualified target such as ``tasks.add``,
or a ``task(CalcJob)``/``task(WorkChain)`` factory variable under its assigned
variable name. A module-global rebinding of a handle (``alias = add``,
``alias = nested_graph``), a stored ``alias = decl.alias('name')`` handle, or
a renamed import is not a declaration: name the placement inline with
``decl(...).alias('name')`` at the call site instead. Module-global scalars,
nodes, and other values are not wires either; pass them as graph inputs.
"""

import pytest

from aiida.common.exceptions import GraphLanguageError
from aiida.engine.processes.graphs.lowering import GraphHandle, compile_graph
from tests.engine.processes.graphs.programs import (
    calls,
    declaration_aliases,
    par_maps,
    workchains,
)

pytestmark = pytest.mark.presto


@pytest.mark.parametrize(
    'declaration',
    [
        pytest.param(declaration_aliases.calls_function_alias, id='function-alias'),
        pytest.param(declaration_aliases.calls_calcjob_alias, id='calcjob-alias'),
        pytest.param(declaration_aliases.calls_workchain_alias, id='workchain-alias'),
        pytest.param(declaration_aliases.calls_graph_alias, id='graph-alias'),
        pytest.param(declaration_aliases.calls_renamed_import, id='renamed-import'),
    ],
)
def test_implicit_callable_aliases_fail_during_build(declaration: GraphHandle) -> None:
    """Module-global rebinding of a handle is not a declaration; alias inline at the call."""
    with pytest.raises(GraphLanguageError, match=r"plain names.*\.alias\('name'\)"):
        declaration.build()


@pytest.mark.parametrize(
    'declaration',
    [
        pytest.param(declaration_aliases.calls_stored_function_alias, id='stored-function'),
        pytest.param(declaration_aliases.calls_stored_calcjob_alias, id='stored-calcjob'),
        pytest.param(declaration_aliases.calls_stored_graph_alias, id='stored-graph'),
    ],
)
def test_stored_alias_handles_fail_during_build(declaration: GraphHandle) -> None:
    """A stored `.alias(...)` handle is not a declaration; construct the alias at the call."""
    with pytest.raises(GraphLanguageError, match=r'\.alias.*inline'):
        declaration.build()


@pytest.mark.parametrize(
    'declaration',
    [
        pytest.param(declaration_aliases.reads_global_scalar, id='scalar'),
        pytest.param(declaration_aliases.reads_global_node, id='node'),
        pytest.param(declaration_aliases.reads_global_mapping, id='mapping'),
    ],
)
@pytest.mark.usefixtures('aiida_profile')
def test_global_values_are_not_wires(declaration: GraphHandle, monkeypatch: pytest.MonkeyPatch) -> None:
    """Module-global values carry no wire; pass them as graph inputs instead."""
    if declaration is declaration_aliases.reads_global_node:
        from aiida.orm import Int

        monkeypatch.setattr(declaration_aliases, 'GLOBAL_OFFSET', Int(3))
    with pytest.raises(GraphLanguageError, match='graph input'):
        declaration.build()


def test_canonical_function_name_still_resolves() -> None:
    """A plain `@task` name keeps resolving under its declared name."""
    assert compile_graph(calls.chain).task_names == ('add', 'add_2')


def test_canonical_factory_variables_still_resolve() -> None:
    """`task(CalcJob)`/`task(WorkChain)` variables resolve under their assigned names."""
    assert compile_graph(declaration_aliases.calls_canonical_factory).task_names == ('add_calc',)
    assert compile_graph(workchains.add_single).task_names == ('add_chain',)


def test_module_qualified_targets_still_resolve() -> None:
    """Module-qualified tasks keep resolving, with or without an inline alias."""
    assert compile_graph(declaration_aliases.calls_module_qualified).task_names == ('add',)
    assert compile_graph(calls.namespaced_call).task_names == ('add',)


def test_inline_alias_still_resolves() -> None:
    """An inline `decl(...).alias('name')` placement names the call locally."""
    assert compile_graph(declaration_aliases.calls_inline_alias).task_names == ('scf',)
    assert compile_graph(declaration_aliases.maps_inline_alias).task_names == ('step',)


def test_par_map_callable_resolution_unchanged() -> None:
    """`par_map` still takes the declared callable by name."""
    assert compile_graph(par_maps.map_list).task_names == ('map_increment',)


def test_enum_member_resolution_unchanged() -> None:
    """Declared error members keep resolving in member tests."""
    assert workchains.retry_chain_allowed.build() is None
