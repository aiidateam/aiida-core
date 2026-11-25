"""Corrected (v2) hidden acceptance tests for the restart evaluation.

Tracked grader source (committed) — never copy into solver worktrees, never
show to solvers. The harness physically removes this directory from every
fresh solver checkout before the solve starts. Run AFTER both agents finish,
once per arm::

    ARM_SOLUTION_DIR=<scratch>/restart_solution ARM_ID=a \\
        uv run pytest utils/benchmarks/graph_restart_eval/grading/test_acceptance.py

`ARM_SOLUTION_DIR` must point at the agent's `restart_solution/` package and
`ARM_ID` must be `a` (BaseRestartWorkChain) or `b` (direct GraphIR).

Grading correction v2 (fixture-loading infrastructure ONLY): the frozen v1
grader imported the eval-root ``flaky_child`` module while both agent
solutions legally import ``fixtures.flaky_child`` from their scratch, so the
v1 contract identity check (``is``) and the ``QueryBuilder`` process-type
filter found zero children even though the wrappers behaved correctly. This
copy validates the scratch ``fixtures/flaky_child.py`` SHA-256 against the
frozen eval fixture, then pre-imports the canonical scratch
``fixtures.flaky_child`` module (aliased under both legal import names)
BEFORE loading the solution, and uses that same class for the contract check
and the child query. All acceptance semantics — output pk identity, retry
cap of 5, fatal single-run stop, non-zero exit statuses — are unchanged.
"""

from __future__ import annotations

import hashlib
import importlib
import importlib.util
import os
import sys
import typing as t
from pathlib import Path

import pytest

pytestmark = pytest.mark.presto

EVAL_DIR = Path(__file__).resolve().parents[1]
FIXTURE_PATH = EVAL_DIR / 'fixtures' / 'flaky_child.py'
FROZEN_FIXTURE_SHA256 = '1c5ffce8b69e893d532a6bffa3b14e63a62b78926d9d2ff08e34b791785feeb8'

ARM_ID = os.environ.get('ARM_ID', '')
SOLUTION_DIR = Path(os.environ.get('ARM_SOLUTION_DIR', ''))


def _sha256(path: Path) -> str:
    """Return the SHA-256 hex digest of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_solution() -> t.Any:
    """Import the agent's `restart_solution` package plus the canonical scratch fixture.

    The ONLY difference from the frozen v1 grader is fixture resolution: the
    scratch ``fixtures/flaky_child.py`` SHA-256 is validated against the
    frozen eval fixture, then the canonical scratch ``fixtures.flaky_child``
    module is imported first (registered under both legal import aliases) so
    the solution binds to the same class object used for the contract check
    and the child query.
    """
    if ARM_ID not in ('a', 'b'):
        pytest.skip('set ARM_ID=a|b')
    if not SOLUTION_DIR.is_dir():
        pytest.skip(f'missing ARM_SOLUTION_DIR: {SOLUTION_DIR}')
    scratch = SOLUTION_DIR.parent
    scratch_fixture = scratch / 'fixtures' / 'flaky_child.py'
    if not scratch_fixture.is_file():
        pytest.fail(f'missing scratch fixture: {scratch_fixture}')
    actual = _sha256(scratch_fixture)
    frozen = _sha256(FIXTURE_PATH)
    if actual != frozen or actual != FROZEN_FIXTURE_SHA256:
        pytest.fail(
            f'scratch fixture SHA mismatch: scratch={actual} eval={frozen} '
            f'frozen={FROZEN_FIXTURE_SHA256} (fixture infrastructure defect, not a solution failure)'
        )
    scratch_str = str(scratch)
    while scratch_str in sys.path:
        sys.path.remove(scratch_str)
    sys.path.insert(0, scratch_str)
    importlib.invalidate_caches()
    for name in ('flaky_child', 'fixtures.flaky_child', 'fixtures'):
        sys.modules.pop(name, None)
    canonical = importlib.import_module('fixtures.flaky_child')
    if Path(canonical.__file__).resolve() != scratch_fixture.resolve():
        pytest.fail(
            f'canonical fixture resolved to {canonical.__file__}, expected {scratch_fixture} '
            '(fixture infrastructure defect, not a solution failure)'
        )
    sys.modules['flaky_child'] = canonical
    sys.modules.pop('restart_solution', None)
    spec = importlib.util.spec_from_file_location(
        'restart_solution', SOLUTION_DIR / '__init__.py', submodule_search_locations=[str(SOLUTION_DIR)]
    )
    assert spec and spec.loader, 'restart_solution/__init__.py must exist'
    module = importlib.util.module_from_spec(spec)
    sys.modules['restart_solution'] = module
    spec.loader.exec_module(module)
    return module, canonical


def _child_calls(wrapper_node, flaky_child) -> list:
    """Return `FlakyChild` nodes CALL_WORK-linked from the wrapper, ordered by pk."""
    from aiida.common.links import LinkType
    from aiida.orm import QueryBuilder

    builder = QueryBuilder()
    builder.append(type(wrapper_node), tag='wrapper', filters={'id': wrapper_node.pk})
    builder.append(
        flaky_child.FlakyChild,
        tag='child',
        with_incoming='wrapper',
        edge_filters={'type': LinkType.CALL_WORK.value},
        project='*',
    )
    return sorted(builder.all(), key=lambda row: row[0].pk)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_solution_contract():
    """The solution exposes `run_restart` and uses its arm's method only."""
    module, flaky_child = _load_solution()
    assert callable(getattr(module, 'run_restart', None)), 'missing `run_restart(fail_until, fatal)`'

    sources = [(SOLUTION_DIR / f).read_text(encoding='utf-8') for f in os.listdir(SOLUTION_DIR) if f.endswith('.py')]
    blob = '\n'.join(sources)
    if ARM_ID == 'a':
        from aiida.engine import BaseRestartWorkChain

        assert hasattr(module, 'RestartWrapper'), 'arm A must define `RestartWrapper`'
        assert issubclass(module.RestartWrapper, BaseRestartWorkChain)
        assert module.RestartWrapper._process_class is flaky_child.FlakyChild
        assert 'process_handler' in blob and 'ProcessHandlerReport' in blob
        assert 'GraphIR' not in blob and 'lowering import graph' not in blob
    else:
        from aiida.engine.processes.graphs.ir import GraphIR, LoopControl

        assert callable(getattr(module, 'build_restart_graph', None)), 'arm B must define `build_restart_graph()`'
        assert 'BaseRestartWorkChain' not in blob and 'process_handler' not in blob
        graph = module.build_restart_graph()
        assert isinstance(graph, GraphIR)
        found: list = []

        def _walk(ir: GraphIR) -> None:
            for task in ir.tasks:
                if isinstance(task, LoopControl):
                    found.append(task)
                body = getattr(task, 'body', None)
                if isinstance(body, GraphIR):
                    _walk(body)
                branches = task.branches() if hasattr(task, 'branches') and callable(task.branches) else ()
                for branch in branches or ():
                    if isinstance(branch, GraphIR):
                        _walk(branch)

        _walk(graph)
        assert found, 'no LoopControl in the GraphIR declaration'
        assert all(t.max_iterations == 5 for t in found), 'loop must cap at MAX_ITERATIONS=5'


@pytest.mark.usefixtures('aiida_profile_clean')
def test_transient_failure_then_success():
    """fail_until=2 → 3 runs, finished ok, result == 30 from the child."""
    module, flaky_child = _load_solution()
    node = module.run_restart(fail_until=2, fatal=False)
    assert node.is_finished_ok, f'expected success, got exit_status={node.exit_status}'
    assert node.outputs.result.value == 30
    children = _child_calls(node, flaky_child)
    assert len(children) == 3
    assert children[-1][0].outputs.result.value == 30
    assert node.outputs.result.pk == children[-1][0].outputs.result.pk, 'result must be linked from the child run'


@pytest.mark.usefixtures('aiida_profile_clean')
def test_retry_cap():
    """fail_until=10 → exactly 5 runs, unfinished (non-zero exit status)."""
    module, flaky_child = _load_solution()
    node = module.run_restart(fail_until=10, fatal=False)
    assert not node.is_finished_ok
    assert node.exit_status != 0
    assert len(_child_calls(node, flaky_child)) == 5


@pytest.mark.usefixtures('aiida_profile_clean')
def test_permanent_failure_stops():
    """fatal=True → exactly 1 run, unfinished (non-zero exit status)."""
    module, flaky_child = _load_solution()
    node = module.run_restart(fatal=True)
    assert not node.is_finished_ok
    assert node.exit_status != 0
    assert len(_child_calls(node, flaky_child)) == 1
