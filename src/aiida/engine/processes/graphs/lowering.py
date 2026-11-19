###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Build a GraphIR from restricted graph source without executing graph bodies.

Each graph handle owns its captured source definition. Graph bodies are never executed.
"""

from __future__ import annotations

import ast
import builtins
import copy
import enum
import functools
import inspect
import linecache
import textwrap
import typing as t
from collections import Counter
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass, field, replace
from types import ModuleType, UnionType

from aiida.common.exceptions import GraphError, GraphLanguageError, GraphTypeCheckError, GraphValidationError
from aiida.common.links import validate_link_label
from aiida.common.loaders import get_object_loader
from aiida.engine.execution import ExecutionEnvironment, PreparedRun
from aiida.engine.processes.calcjobs import CalcJob
from aiida.engine.processes.exit_code import ExitCodeEnum
from aiida.engine.processes.graphs.expressions import compile_expression, infer_expression_shape
from aiida.engine.processes.graphs.inputs import _drops_none_value, _place
from aiida.engine.processes.graphs.ir import (
    _CONDITION_PORT,
    BranchControl,
    Dependency,
    Endpoint,
    GraphIR,
    InlineOperation,
    LoopControl,
    MapControl,
    OutputTree,
    ProcessTask,
    Route,
    SubgraphTask,
    TaskIR,
    merge_branch_shape,
)
from aiida.engine.processes.graphs.operations import (
    CONSTANT_PORT,
    LEFT_PORT,
    OPERAND_PORT,
    RESULT_PORT,
    RIGHT_PORT,
    OperationKind,
    const_result_shape,
    infer_operation_shape,
)
from aiida.engine.processes.graphs.par_map import par_map
from aiida.engine.processes.graphs.process import GraphProcess
from aiida.engine.processes.graphs.results import catch_error
from aiida.engine.processes.graphs.shapes import (
    Forward,
    LeafShape,
    NamespaceShape,
    Shape,
    json_default,
    namespace_shape_for,
    shape_for_annotation,
)
from aiida.engine.processes.graphs.tasks import (
    CalcJobTaskHandle,
    FunctionTaskHandle,
    PlacementHandle,
    PortDeclaration,
    WorkChainTaskHandle,
    _build_task,
    _typevar_solution,
)
from aiida.engine.processes.ports import _node_type
from aiida.engine.processes.workchains.workchain import WorkChain
from aiida.orm import Bool, DataDict, DataList, EnumData

__all__ = ('Forward', 'GraphHandle', 'graph', 'par_map', 'task')

# `compile_graph` is intentionally absent from `__all__` and from the
# `aiida.engine.processes.graphs` and `aiida.engine` re-exports: it is the
# core-only compilation entrypoint for the engine, shapes, IR, and test
# helpers. User code validates with `GraphHandle.build`, which returns
# `None`, and launches with `run`/`submit`.

P = t.ParamSpec('P')
R = t.TypeVar('R')


# Value forms the language rejects, with the guidance each carries. The key sets
# are the unsupported list; anything missing here reports the generic fallback.
_VALUE_REJECTIONS: dict[tuple[type[ast.expr], ...], str] = {
    (ast.NamedExpr,): 'bindings must stay visible as wires; give it a name on its own line before the if instead',
    (ast.Subscript,): (
        'collections travel whole through ports and indexing is computation; '
        + 'cannot pick elements here; pass the whole collection instead'
    ),
    (ast.Starred,): (
        'each input wires by name, so spreading a sequence hides which is which; '
        + 'cannot unpack here; list each input by name instead'
    ),
    (ast.JoinedStr,): 'formatting is computation; build this text in a task instead',
    (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp): (
        'scatter over runtime data has no fixed placement list; write out one call per value instead'
    ),
    (ast.Lambda,): 'anonymous functions carry no importable declaration; write a task instead',
    (ast.Call,): 'nested calls hide a placement; put the inner call on its own line first',
    (ast.Dict,): 'outputs stay flat leaves; list each output by name instead of nesting them',
    (ast.List, ast.Tuple, ast.Set): 'collections enter as declared inputs; provide collections as graph inputs instead',
    (ast.Await, ast.Yield, ast.YieldFrom): (
        'tasks run to completion on workers; tasks cannot wait or pause; write plain steps instead'
    ),
}


# Source operators lowering to fixed inline operations. Only these spellings run without a task:
# `+`, `-`, `*`, `//`, `%`, comparisons, and unary `-`, `+`, `not`. Anything else stays a task call.
# In-place updates reuse the same binary operators, so `/=`, `**=`, and shifts stay tasks.
_BINARY_OPERATIONS: dict[type[ast.operator], OperationKind] = {
    ast.Add: 'add',
    ast.Sub: 'sub',
    ast.Mult: 'mul',
    ast.FloorDiv: 'floordiv',
    ast.Mod: 'mod',
}
_COMPARISON_OPERATIONS: dict[type[ast.cmpop], OperationKind] = {
    ast.Lt: 'lt',
    ast.LtE: 'le',
    ast.Gt: 'gt',
    ast.GtE: 'ge',
    ast.Eq: 'eq',
    ast.NotEq: 'ne',
}
_UNARY_OPERATIONS: dict[type[ast.unaryop], OperationKind] = {
    ast.USub: 'neg',
    ast.UAdd: 'pos',
    ast.Not: 'not',
}


class GraphHandle(t.Generic[P, R]):
    """An importable source declaration that builds without executing its body.

    See :func:`graph` for the authoring contract and nested-helper composition.
    Launch with ``run`` or ``submit``; ``build`` lowers the source early to surface diagnostics.
    """

    def __init__(self, function: Callable[P, R]) -> None:
        self._definition: _SourceDefinition = _SourceDefinition.capture(function)
        self._template: GraphIR | None = None
        # Copy name and docstring, not the function state: the handle owns its identifier.
        functools.update_wrapper(self, function, updated=())

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        msg = f'`{self.identifier}` declares a graph; launch it with `run` or `submit`.'
        raise GraphError(msg)

    def alias(self, name: str) -> PlacementHandle[P, R]:
        """Return an immutable handle placing this graph under an explicit placement name."""
        return PlacementHandle(self, name)

    @property
    def identifier(self) -> str:
        """Return the fully qualified name of the graph declaration."""
        return self._definition.key

    @property
    def function(self) -> Callable[..., t.Any]:
        """Return the declared function for the lowering pipeline."""
        return self._definition.function

    def build(self) -> None:
        """Validate the declaration without executing it.

        Checking raises the declaration diagnostics early. It runs no placement, stores no node, and creates no data;
        use `run` or `submit` to execute. The validated template stays private to the implementation.

        :return: `None`.
        """
        compile_graph(self)

    @property
    def process_class(self) -> type[GraphProcess]:
        """Return the process class executing lowered graphs."""
        return GraphProcess

    def get_launch_inputs(self, **inputs: t.Any) -> dict[str, t.Any]:
        """Validate graph arguments and prepare the declaration and provenance inputs.

        Engine `Launchable` adapter consumed by `run`/`submit`; not an
        authoring or inspection API. It serializes the compiled template into
        the stored `graph` input alongside the `graph_inputs` namespace.

        Binds the function signature by name first, so every parameter arrives as a keyword.
        Execution inputs ride under `runtime_config`; standard `metadata` passes through.
        """
        if 'task_metadata' in inputs:
            msg = (
                '`task_metadata` was replaced by `runtime_config`; '
                "put task metadata under the placement's `metadata` key."
            )
            raise GraphValidationError(msg)
        metadata = inputs.pop('metadata', None)
        protocol_record = None
        if 'prepared_run' in inputs:
            prepared = inputs.pop('prepared_run')
            if inputs or not isinstance(prepared, PreparedRun):
                msg = 'pass a PreparedRun without additional scientific inputs or execution channels.'
                raise GraphValidationError(msg)
            inputs = dict(prepared.inputs)
            environment = prepared.execution_environment
            runtime_config, execution_policy = environment.runtime_config, environment.execution_policy
            protocol_record = {
                'protocol': prepared.protocol,
                'version': prepared.version,
                'overrides': prepared.overrides,
            }
            explicit_channels = False
        else:
            explicit_channels = bool(inputs.keys() & {'execution_environment', 'runtime_config', 'execution_policy'})
            if 'execution_environment' in inputs:
                environment = inputs.pop('execution_environment')
                if inputs.keys() & {'runtime_config', 'execution_policy'}:
                    msg = 'execution_environment cannot be combined with runtime_config or execution_policy.'
                    raise GraphValidationError(msg)
                if not isinstance(environment, ExecutionEnvironment):
                    msg = 'execution_environment must be an ExecutionEnvironment.'
                    raise GraphValidationError(msg)
                runtime_config, execution_policy = environment.runtime_config, environment.execution_policy
            else:
                runtime_config = inputs.pop('runtime_config', {})
                execution_policy = inputs.pop('execution_policy', {})
        if (
            protocol_record is None
            and 'inputs' in inputs
            and (explicit_channels or 'inputs' not in inspect.signature(self.function).parameters)
        ):
            scientific = inputs.pop('inputs')
            if not isinstance(scientific, Mapping):
                msg = '`inputs` must be a mapping of workflow arguments.'
                raise GraphValidationError(msg)
            if inputs.keys() & scientific.keys():
                msg = 'workflow arguments were supplied both through `inputs` and flattened keywords.'
                raise GraphValidationError(msg)
            inputs = {**scientific, **inputs}
        if isinstance(metadata, Mapping) and any(
            key != 'options' and isinstance(value, Mapping) and 'options' in value for key, value in metadata.items()
        ):
            msg = (
                'per-placement execution inputs ride under `runtime_config`, keyed by placement name; '
                'standard keys (label, `store_provenance`, ...) go directly under `metadata`'
            )
            raise GraphValidationError(msg)
        # Launching binds by name, so positional-only parameters accept keywords at launch.
        # Keyword-only parameters already bind by name and must keep their kind: converting
        # them breaks signatures where a default precedes them.
        parameters = [
            parameter.replace(kind=inspect.Parameter.POSITIONAL_OR_KEYWORD)
            if parameter.kind is inspect.Parameter.POSITIONAL_ONLY
            else parameter
            for parameter in inspect.signature(self.function).parameters.values()
        ]
        bound = inspect.Signature(parameters).bind_partial(**inputs)
        launch_inputs = GraphProcess._launch_inputs(
            compile_graph(self), dict(bound.arguments), runtime_config, execution_policy, protocol_record
        )
        if metadata is not None:
            launch_inputs['metadata'] = metadata
        return launch_inputs


@dataclass(frozen=True)
class _SourceDefinition:
    """The source and annotations captured by a graph handle."""

    key: str
    function: Callable[..., t.Any]
    source: str
    filename: str
    first_line: int
    hints: Mapping[str, t.Any]

    @functools.cached_property
    def symbols(self) -> _DeclarationNamespace:
        """Resolve declaration references without exposing global values as graph inputs."""
        return _DeclarationNamespace(getattr(self.function, '__globals__', {}), self.filename)

    @classmethod
    def capture(cls, function: Callable[..., t.Any]) -> _SourceDefinition:
        """Capture a graph declaration without executing its body."""
        key = _function_identifier(function)
        try:
            lines, first_line = inspect.getsourcelines(function)
        except OSError as exception:
            msg = f'Cannot read the source of {key}: definitions need retrievable source.'
            raise GraphLanguageError(msg) from exception
        try:
            hints = t.get_type_hints(function, include_extras=True)
        except (NameError, AttributeError, SyntaxError, TypeError) as exception:
            msg = f'Cannot resolve type hints for {key}: {exception}'
            raise GraphLanguageError(msg) from exception
        return cls(
            key=key,
            function=function,
            source=textwrap.dedent(''.join(lines)),
            filename=inspect.getsourcefile(function) or '<unknown>',
            first_line=first_line,
            hints=hints,
        )


@dataclass
class _DeclarationNamespace:
    """A module's declarations, distinct from its ordinary Python variables."""

    values: Mapping[str, t.Any]
    filename: str
    modules: dict[ModuleType, _DeclarationNamespace] = field(default_factory=dict)

    @functools.cached_property
    def aliases(self) -> set[str]:
        """Exclude explicit global rebindings without guessing factory names from process names."""
        linecache.checkcache(self.filename)
        source = ''.join(linecache.getlines(self.filename))
        try:
            statements = ast.parse(source).body
        except (SyntaxError, ValueError):
            return set()
        names: set[str] = set()
        for statement in statements:
            if isinstance(statement, ast.ImportFrom):
                for alias in statement.names:
                    name = alias.asname or alias.name
                    if alias.asname not in (None, alias.name):
                        names.add(name)
                    else:
                        names.discard(name)
            elif isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                names.discard(statement.name)
            elif isinstance(statement, ast.Assign) or (
                isinstance(statement, ast.AnnAssign) and statement.value is not None
            ):
                targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
                bound = {target.id for target in targets if isinstance(target, ast.Name)}
                names.update(bound)
                value = statement.value
                if isinstance(value, ast.Call) and (
                    (isinstance(value.func, ast.Name) and value.func.id == 'task')
                    or (isinstance(value.func, ast.Attribute) and value.func.attr == 'task')
                ):
                    names.difference_update(bound)
        return names

    def lookup(self, name: str) -> t.Any:
        """Resolve a declaration by its own name, rejecting implicit placement aliases."""
        target = self.values.get(name)
        if isinstance(target, PlacementHandle):
            msg = 'stored `.alias(...)` handles are not declarations; construct the alias inline at the call instead'
            raise GraphLanguageError(msg)
        if isinstance(target, (FunctionTaskHandle, GraphHandle)) or target is par_map:
            valid = name == getattr(target, '__name__', name) and name not in self.aliases
        elif isinstance(target, (CalcJobTaskHandle, WorkChainTaskHandle)):
            valid = name not in self.aliases
        else:
            return target
        if not valid:
            msg = (
                f'calls resolve by plain names to declarations; {name!r} is a global alias; '
                "use `.alias('name')` inline instead"
            )
            raise GraphLanguageError(msg)
        return target

    def module(self, module: ModuleType) -> _DeclarationNamespace:
        """Share the declaration table of each qualified module reference."""
        if module not in self.modules:
            self.modules[module] = _DeclarationNamespace(vars(module), getattr(module, '__file__', '') or '')
        return self.modules[module]


@dataclass(frozen=True)
class _Reference:
    """A parsed reference to a leaf or fixed input namespace."""

    task: str | None  # None denotes a graph input.
    port: str
    shape: Shape


_CapturedValue: t.TypeAlias = '_Reference | int | float | str | bool | dict[str, _CapturedValue] | None'
_ReferenceTree: t.TypeAlias = '_Reference | dict[str, _ReferenceTree]'


@dataclass
class _PartialBinding:
    """A `partial` bound in one graph body, fixing some inputs of a task or graph.

    The binding carries no placement: it records the ultimate target and the fixed
    input values captured at declaration time. Each fixed value is a lowered
    `_CapturedValue` holding declaration-time references, so later rebinding of the
    same name cannot change it. Each use site merges these with its own arguments
    into one ordinary placement; a `par_map` use fans out with the remaining input
    as its element. `fixed` keys are top-level input names; namespace values nest.
    """

    target: FunctionTaskHandle[t.Any, t.Any] | CalcJobTaskHandle | WorkChainTaskHandle | GraphHandle
    call_name: str
    explicit: str | None
    fixed: dict[str, _CapturedValue]


@dataclass
class _LoweringState:
    """The placements, wirings, and references collected while lowering one graph body."""

    definition: _SourceDefinition
    stack: tuple[str, ...]
    tasks: list[ProcessTask | SubgraphTask | BranchControl | LoopControl | MapControl | InlineOperation] = field(
        default_factory=list
    )
    dependencies: list[Dependency] = field(default_factory=list)
    inputs: dict[str, list[Route]] = field(default_factory=dict)
    input_shapes: dict[str, Shape] = field(default_factory=dict)
    names: dict[str, _Reference] = field(default_factory=dict)
    used: Counter[str] = field(default_factory=Counter)
    partials: dict[str, _PartialBinding] = field(default_factory=dict)
    synthetic_fixed: dict[str, _CapturedValue] = field(default_factory=dict)

    @property
    def key(self) -> str:
        """Return the fully qualified name of the lowered graph."""
        return self.definition.key


class _Arm(t.NamedTuple):
    """One lowered branch arm with its region state."""

    name: str
    child: _LoweringState
    body: GraphIR
    alias: bool = False


# `type[CalcJob]`/`type[WorkChain]` intentionally precede `Callable`: classes are
# callable, so the general overload would swallow them (binding `R` to the instance).
# Overload resolution tries these first, which both checkers honor at call sites;
# the `overload-overlap` ignores below record that this overlap is deliberate.
@t.overload
def task(  # type: ignore[overload-overlap]
    function: type[CalcJob],
    *,
    inputs: PortDeclaration | None = None,
    outputs: PortDeclaration | None = None,
    errors: type[ExitCodeEnum] | UnionType | None = None,
) -> CalcJobTaskHandle: ...


@t.overload
def task(  # type: ignore[overload-overlap]
    function: type[WorkChain],
    *,
    inputs: PortDeclaration | None = None,
    outputs: PortDeclaration | None = None,
    errors: type[ExitCodeEnum] | UnionType | None = None,
) -> WorkChainTaskHandle: ...


@t.overload
def task(function: Callable[P, R]) -> FunctionTaskHandle[P, R]: ...


@t.overload
def task(
    function: None = None,
) -> Callable[
    [Callable[P, R] | type[CalcJob] | type[WorkChain]],
    FunctionTaskHandle[P, R] | CalcJobTaskHandle | WorkChainTaskHandle,
]: ...


def task(
    function: Callable[..., t.Any] | type[CalcJob] | type[WorkChain] | None = None,
    *,
    inputs: PortDeclaration | None = None,
    outputs: PortDeclaration | None = None,
    errors: type[ExitCodeEnum] | UnionType | None = None,
) -> t.Any:
    """Register an importable task with static ports and fixed graph inputs.

    A task is an independent, provenance-bearing calculation: each call runs as its own child
    process and its outputs become stored nodes. Accepts a task function, a `CalcJob` subclass,
    or a `WorkChain` subclass; task inputs wire task outputs and graph inputs alike. `CalcJob`
    tasks read their metadata from the launch inputs instead.

    Keep counters and predicates inline in the graph (see :func:`graph`) to avoid
    a child process per check. Validation-only tasks returning ``None`` remain useful
    when failure must stop the graph without replacing its scientific output.

    :param function: the function, `CalcJob` subclass, or `WorkChain` subclass to decorate.
    :param inputs: names and node types inside dynamic input namespaces of a process class,
        e.g. ``{'nodes': {'text': SinglefileData}}``.
    :param outputs: names and node types of the dynamic outputs of a process class.
    :param errors: an `ExitCodeEnum` subclass, or a union of them, mapping the exit
        statuses a `CalcJob` or `WorkChain` task may finish with onto declared failures.
    :return: a callable, launchable task handle.
    """

    def decorate(target: Callable[..., t.Any] | type[CalcJob] | type[WorkChain]) -> t.Any:
        """Validate the importable task reference and construct its process wrapper."""
        if not inspect.isclass(target):
            _function_identifier(target)
        return _build_task(target, inputs=inputs, outputs=outputs, errors=errors)

    if function is not None:
        return decorate(function)

    return decorate


@t.overload
def graph(function: Callable[P, R]) -> GraphHandle[P, R]: ...


@t.overload
def graph(function: None = None) -> Callable[[Callable[P, R]], GraphHandle[P, R]]: ...
def graph(function: Callable[..., t.Any] | None = None) -> t.Any:
    """Save a graph's source without executing its body.

    The body is never executed: its source is captured at decoration time and lowered to a declaration by
    the engine when the graph runs.

    Example usage:

    >>> from aiida.engine import graph, task
    >>>
    >>> @task
    ... def add(x: int, y: int) -> int:
    ...     return x + y
    >>> @graph
    ... def add_twice(x: int, y: int) -> int:
    ...     first = add(x=x, y=y)
    ...     return add(x=first, y=y)

    A `@task` is an independent, provenance-bearing calculation, while ordinary orchestration
    -- arithmetic (``+ - * // %``), comparisons (``< <= > >= == !=``), and ``is None`` /
    ``is not None`` / ``is Member`` branch tests -- belongs here directly, not in `@task`
    boolean wrappers; each `@task` call is its own child process with its own nodes, so a
    task per increment or comparison stores a node per check. The scientific result stays an
    existing task output, while a validation-only task returning `None` stays legitimate.

    Generic retry shape (default-seeded counter and short-circuiting member check)::

        @task
        def step(x: int, attempt: int) -> Result[int, MyErrors]:
            ...

        @task
        def ensure(value: int | None) -> None:
            if value is None:
                raise ValueError('the step never succeeded.')

        @graph
        def retrying(x: int, limit: int, attempt: int = 0) -> int:
            value, error = catch_error(step(x=x, attempt=attempt))
            retry = error is MyErrors.RETRYABLE and attempt < limit
            while retry:
                attempt = attempt + 1
                value, error = catch_error(step(x=x, attempt=attempt))
                retry = error is MyErrors.RETRYABLE and attempt < limit
            checked = ensure(value=value)
            return value

    The counter seeds from its default graph input (``attempt: int = 0``); scalar
    literals can also initialize counters and flags without creating nodes.
    ``and`` and ``or`` short-circuit boolean checks, so the budget is evaluated only
    for the matching error member. The graph returns the step's stored output;
    ``ensure`` only validates and creates no output nodes.

    Shared orchestration composes through nested `@graph` helpers: the callee's placements
    inline at the call site, so a helper returning an inline comparison costs no stored
    nodes. Bind its result and branch on it::

        @task
        def advance(x: int) -> int:
            ...

        @graph
        def within_budget(attempt: int, limit: int) -> bool:
            return attempt < limit

        @graph
        def spending(x: int, limit: int) -> int:
            value = advance(x=x)
            ok = within_budget(attempt=value, limit=limit)
            if ok:
                value = advance(x=value)
            return value

    `ok` is orchestration state for the branch, not scientific data: returning it as the
    root output would fail at run time, since root graph outputs must be existing task
    outputs or graph inputs. Create a returned value in a `@task` and return that task's
    output instead.

    A graph is launched like any other process, by passing it to ``run`` or ``submit``.

    :param function: The function to decorate.
    :return: A handle that can build, run, or submit the graph.
    """

    def decorate(target: Callable[..., t.Any]) -> GraphHandle[t.Any, t.Any]:
        """Capture the graph source without executing its body."""
        return GraphHandle(target)

    if function is not None:
        return decorate(function)

    return decorate


def _function_identifier(function: Callable[..., t.Any]) -> str:
    """Return the function identifier; unimportable modules persist through pickled executors."""
    if not inspect.isfunction(function):
        raise GraphLanguageError('Registered declarations must be Python functions, not process classes or builders')
    if function.__qualname__ != function.__name__:
        raise GraphLanguageError('Registered functions must be defined at module scope, not nested in other code')
    try:
        validate_link_label(function.__name__)
    except ValueError as exception:
        msg = (
            f'declaration name `{function.__name__}` is invalid as a link label ({exception}); '
            + 'use alphanumerics and underscores without leading or trailing underscores instead'
        )
        raise GraphLanguageError(msg) from exception
    return f'{function.__module__}:{function.__name__}'


def _reject(state: _LoweringState, node: ast.AST, reason: str) -> t.NoReturn:
    """Point at the offending node in the original file, not just the extracted function."""
    source = state.definition.source.splitlines()
    location = state.definition
    line: int | None = getattr(node, 'lineno', None)
    column: int | None = getattr(node, 'col_offset', None)
    if line is None or column is None or line > len(source):
        msg = f'{location.filename}: {state.key}: {reason}: {ast.unparse(node)}'
        raise GraphLanguageError(msg)

    text = source[line - 1]
    # AST columns are UTF-8 byte offsets; a displayed caret needs a character offset.
    before = text.encode('utf-8')[:column].decode('utf-8', errors='ignore')
    position = len(before)
    msg = (
        f'{location.filename}:{location.first_line + line - 1}:{position + 1}: '
        f'{state.key}: {reason}\n    {text}\n    {" " * position}^'
    )
    raise GraphLanguageError(msg)


def _parse_function(definition: _SourceDefinition) -> ast.FunctionDef:
    """Parse one registered definition to its function node."""
    module = ast.parse(definition.source)
    if len(module.body) != 1 or not isinstance(module.body[0], ast.FunctionDef):
        msg = f'{definition.key}: expected one function definition'
        raise GraphLanguageError(msg)
    return module.body[0]


def _check_signature(state: _LoweringState, function: ast.FunctionDef) -> None:
    """Reject parameter kinds the graph compiler cannot represent."""
    if function.args.vararg or function.args.kwarg:
        msg = (
            'every input needs its own declared port, so a varying number of inputs cannot wire; '
            + '`*args` and `**kwargs` are not supported; list each input separately instead'
        )
        _reject(state, node=function, reason=msg)


def _parameter_defaults(state: _LoweringState, function: ast.FunctionDef) -> dict[str, t.Any]:
    """Read literal parameter defaults; only finite JSON values travel, as with model defaults."""
    positional = [*function.args.posonlyargs, *function.args.args]
    parameters = [*positional, *function.args.kwonlyargs]
    leading = len(positional) - len(function.args.defaults)
    raw: list[ast.expr | None] = [None] * leading
    raw.extend(function.args.defaults)
    raw.extend(function.args.kw_defaults)
    defaults: dict[str, t.Any] = {}
    for parameter, default in zip(parameters, raw):
        if default is None:
            continue
        try:
            value: t.Any = ast.literal_eval(default)
        except (ValueError, TypeError, SyntaxError):
            msg = (
                'defaults are saved with the graph, so they must be plain values; '
                + f'parameter default for `{parameter.arg}` must be a literal; use a task or an input instead'
            )
            _reject(state, node=default, reason=msg)
        try:
            json_default(value)
        except GraphTypeCheckError:
            msg = (
                'defaults are saved with the graph, which only holds finite JSON values; '
                + f'parameter default for `{parameter.arg}` must be a finite JSON value; '
                + 'pick a finite default, or use a task or an input instead'
            )
            _reject(
                state,
                node=default,
                reason=msg,
            )
        defaults[parameter.arg] = value
    return defaults


def _declare_graph_inputs(state: _LoweringState, function: ast.FunctionDef) -> NamespaceShape:
    """Route every graph parameter to its input shape."""
    parameters = [*function.args.posonlyargs, *function.args.args, *function.args.kwonlyargs]
    defaults = _parameter_defaults(state, function=function)
    boundary = namespace_shape_for(state.definition.hints, tuple(arg.arg for arg in parameters), defaults=defaults)
    for arg in parameters:
        if arg.arg == 'partial':
            msg = (
                '`partial` is reserved for binding fixed inputs without an import, '
                + 'so no graph input may take that name; rename the input instead'
            )
            _reject(state, node=arg, reason=msg)
        state.inputs[arg.arg] = []
        shape = boundary.select(arg.arg)
        state.input_shapes[arg.arg] = shape
        state.names[arg.arg] = _Reference(None, port=arg.arg, shape=shape)
    return boundary


def _lower_function(state: _LoweringState) -> GraphIR:
    """Lower one registered graph definition to a static template."""
    function = _parse_function(state.definition)
    _check_signature(state, function=function)
    boundary = _declare_graph_inputs(state, function=function)
    statements = function.body
    if statements and isinstance(statements[0], ast.Expr) and isinstance(statements[0].value, ast.Constant):
        if isinstance(statements[0].value.value, str):
            statements = statements[1:]
    if not statements or not isinstance(statements[-1], ast.Return):
        msg = (
            f'{state.key}: the final return declares the graph outputs, so without it the graph promises nothing; '
            + 'end the graph with a return declaring its outputs'
        )
        raise GraphLanguageError(msg)
    for statement in statements[:-1]:
        if isinstance(statement, ast.If):
            _lower_branch(state, statement=statement)
        elif isinstance(statement, ast.While):
            _lower_loop(state, statement=statement)
        elif isinstance(statement, (ast.For, ast.AsyncFor)):
            msg = (
                'the list of placements is fixed before anything runs, '
                + 'while a collection holds its length only when it runs; '
                + 'for loops are not supported; write out one call per value, or use a while loop'
            )
            _reject(state, node=statement, reason=msg)
        elif isinstance(statement, (ast.Import, ast.ImportFrom)):
            msg = (
                'the body declares a template and never executes, so imports there would do nothing; '
                + 'imports are not supported in graph bodies; import inside task bodies instead'
            )
            _reject(state, node=statement, reason=msg)
        elif isinstance(statement, ast.ClassDef):
            msg = (
                'body-local classes have no importable source for the daemon to re-import; '
                + 'define process classes at module scope and reference them with `@task` instead'
            )
            _reject(state, node=statement, reason=msg)
        elif (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Tuple)
        ):
            _lower_unpack(state, statement=statement)
        else:
            _lower_assignment(state, statement=statement)
    result: ast.expr | None = statements[-1].value
    if result is None:
        msg = (
            'graphs only pass along existing nodes, so a bare return with no value names nothing; '
            + 'return must name a task or graph input; return placements, input leaves, or mappings'
        )
        _reject(state, node=statements[-1], reason=msg)
    outputs, output_typehints = _lower_outputs(state, result=result)
    return GraphIR(
        tasks=tuple(state.tasks),
        dependencies=tuple(state.dependencies),
        inputs={name: tuple(targets) for name, targets in state.inputs.items()},
        outputs=outputs,
        identifier=state.key,
        output_typehints=output_typehints,
        input_shape=boundary,
    )


def _lower_outputs(
    state: _LoweringState, result: ast.expr
) -> tuple[dict[str, OutputTree], dict[str, tuple[type, ...]]]:
    """Lower the return statement to named endpoints and their type hints."""
    hints = state.definition.hints
    references = _lower_return(state, expression=result)
    returned = shape_for_annotation(hints.get('return'))
    outputs: dict[str, OutputTree] = {
        name: _endpoint_tree(reference, preserve_optional_namespaces=True) for name, reference in references.items()
    }
    if len(outputs) == 1 and not isinstance(result, ast.Dict):
        outputs = {'result': next(iter(outputs.values()))}
    typehints: dict[str, tuple[type, ...]] = (
        {next(iter(outputs)): returned.types}
        if len(outputs) == 1
        and isinstance(returned, LeafShape)
        and returned.types
        and not isinstance(result, ast.Dict)
        and isinstance(next(iter(outputs.values())), Endpoint)
        else {}
    )
    return outputs, typehints


def _endpoint_tree(reference: _ReferenceTree, *, preserve_optional_namespaces: bool = False) -> OutputTree:
    """Expand a leaf or namespace reference to endpoints regrouping existing nodes.

    Namespaces regroup their existing leaves instead of creating data; every leaf
    keeps its stored node, so workflows return but never create data.
    """
    if isinstance(reference, dict):
        return {
            name: _endpoint_tree(item, preserve_optional_namespaces=preserve_optional_namespaces)
            for name, item in reference.items()
        }
    if isinstance(reference.shape, NamespaceShape):
        if preserve_optional_namespaces and not reference.shape.required and reference.task and reference.port:
            # A missing whole arm must not turn into an empty mapping at an invocation boundary.
            return Endpoint(task=reference.task, port=reference.port)
        return {name: _endpoint_tree(field) for name, field in _fields(reference).items()}
    return Endpoint(task=reference.task, port=reference.port)


def _fields(reference: _Reference) -> dict[str, _Reference]:
    """Return one reference per field of a namespace reference."""
    assert isinstance(reference.shape, NamespaceShape)
    prefix = f'{reference.port}.' if reference.port else ''
    return {
        name: _Reference(reference.task, port=f'{prefix}{name}', shape=shape) for name, shape in reference.shape.fields
    }


def _lower_return(state: _LoweringState, expression: ast.expr) -> dict[str, _ReferenceTree]:
    """Return a leaf reference, a namespace reference, or a nested mapping of those."""
    if isinstance(expression, ast.Dict):
        lowered = _lower_return_value(state, expression)
        assert isinstance(lowered, dict)
        return lowered
    reference = _lower_value(state, expression, allow_call=True)
    if not isinstance(reference, _Reference) or (
        not reference.port and not isinstance(reference.shape, NamespaceShape)
    ):
        msg = 'graphs return existing nodes rather than creating data; ' + 'return a task output or graph input instead'
        _reject(state, node=expression, reason=msg)
    assert isinstance(reference, _Reference)
    _reject_const_return(state, reference, node=expression)
    if isinstance(reference.shape, NamespaceShape):
        return {'result': reference}
    port = reference.port.split('.')[-1]
    return {port: reference}


def _lower_return_value(state: _LoweringState, expression: ast.expr) -> _ReferenceTree:
    """Lower one output mapping value to a leaf, a namespace, or a nested mapping."""
    if isinstance(expression, ast.Dict):
        nested: dict[str, _ReferenceTree] = {}
        for key, value in zip(expression.keys, expression.values, strict=True):
            if not isinstance(key, ast.Constant) or not isinstance(key.value, str) or not key.value.isidentifier():
                msg = (
                    'output names become port names when the graph is stored, so they must be written out; '
                    + 'output names must be quoted names; write them out instead'
                )
                _reject(state, node=expression, reason=msg)
            if key.value in nested:
                msg = 'each output name points at one stored value; ' + 'duplicate graph output; name each output once'
                _reject(state, node=expression, reason=msg)
            nested[key.value] = _lower_return_value(state, value)
        return nested
    reference = _lower_value(state, expression, allow_call=True)
    if not isinstance(reference, _Reference):
        msg = 'graphs return existing nodes rather than creating data; ' + 'return a task output or graph input instead'
        _reject(state, node=expression, reason=msg)
    assert isinstance(reference, _Reference)
    _reject_const_return(state, reference, node=expression)
    return reference


def _is_inline_operation(value: ast.expr) -> bool:
    """Return whether an assignment value computes an inline operation rather than a literal."""
    if isinstance(value, (ast.BinOp, ast.Compare)):
        return True
    if not isinstance(value, ast.UnaryOp):
        return False
    try:
        ast.literal_eval(value)
    except (ValueError, TypeError):
        return True
    return False


def _lower_augmented(state: _LoweringState, statement: ast.AugAssign, *, rebind: bool) -> str:
    """Lower an in-place update to a rebinding through the matching inline operation."""
    if not rebind:
        msg = (
            'the body declares a template and never executes, so only calls, branches, and loops belong here; '
            + 'this statement is not supported here; move it into a task instead'
        )
        _reject(state, node=statement, reason=msg)
    if not isinstance(statement.target, ast.Name):
        msg = (
            'each line wires one placement, so targets cannot nest or repeat; '
            + 'assign to a plain name instead, one per line'
        )
        _reject(state, node=statement, reason=msg)
    operation = _BINARY_OPERATIONS.get(type(statement.op))
    if operation is None:
        _reject(state, node=statement, reason=_unsupported_operation_reason())
    target = statement.target.id
    if target not in state.names:
        msg = (
            'names only exist after a call or an input introduces them; '
            + f'{target!r} is not known here; assign it on an earlier line instead'
        )
        _reject(state, node=statement.target, reason=msg)
    reference = _place_operation(
        state,
        operation=operation,
        operands=(state.names[target], _lower_operand(state, statement.value)),
        node=statement,
    )
    state.names[target] = reference
    return target


def _lower_assignment(state: _LoweringState, statement: ast.stmt, *, rebind: bool = False) -> str:
    """Bind a call or inline operation result to new placement names."""
    if isinstance(statement, ast.AnnAssign):
        msg = 'drop the annotation; types come from the task or input instead'
        _reject(state, node=statement, reason=msg)
    if isinstance(statement, ast.AugAssign):
        return _lower_augmented(state, statement=statement, rebind=rebind)
    if not isinstance(statement, ast.Assign) or not statement.targets:
        msg = (
            'the body declares a template and never executes, so only calls, branches, and loops belong here; '
            + 'this statement is not supported here; move it into a task instead'
        )
        _reject(state, node=statement, reason=msg)
    names: list[str] = [target.id for target in statement.targets if isinstance(target, ast.Name)]
    if len(names) != len(statement.targets):
        msg = (
            'each line wires one placement, so targets cannot nest or repeat; '
            + 'assign to a plain name instead, one per line'
        )
        _reject(state, node=statement, reason=msg)
    for name in names:
        if name == 'partial':
            msg = (
                '`partial` is reserved for binding fixed inputs without an import, '
                + 'so it cannot name a placement or binding; pick another name instead'
            )
            _reject(state, node=statement, reason=msg)
        if name in state.partials and not rebind:
            msg = (
                'each placement is stored once under its name, so names cannot be reused; '
                + f'{name!r} already binds a `partial`; assign each result a new name instead of reusing one'
            )
            _reject(state, node=statement, reason=msg)
        if name in state.names and not rebind:
            if name in state.input_shapes:
                msg = (
                    'graph inputs are recorded once at launch and cannot be reassigned; '
                    + 'bind the result to a new name instead'
                )
                _reject(state, node=statement, reason=msg)
            msg = (
                'each placement is stored once under its name, so names cannot be reused; '
                + 'assign each result a new name instead of reusing one'
            )
            _reject(state, node=statement, reason=msg)
    value = statement.value
    if isinstance(value, ast.Call) and _is_partial_call(state, value):
        if len(names) != 1:
            msg = (
                'a `partial` binds fixed inputs without running anything, so it takes one name; '
                + 'bind it to one name instead'
            )
            _reject(state, node=statement, reason=msg)
        _bind_partial(state, name=names[0], node=value)
        return names[0]
    if isinstance(value, ast.Call):
        ref: _Reference = _lower_call(state, expression=value)
    elif _is_inline_operation(value):
        assert isinstance(value, (ast.BinOp, ast.Compare, ast.UnaryOp))
        ref = _lower_operation(state, node=value)
    else:
        # A plain name or dotted field aliases an existing wire (structured outputs
        # bind whole namespaces this way); a scalar literal binds ephemeral control state.
        reference = _lower_value(state, value)
        if isinstance(reference, _Reference):
            for name in names:
                state.names[name] = reference
            return names[0]
        ref = _place_constant(state, value=reference, node=value)
    for name in names:
        state.names[name] = ref
    return names[0]


def _lower_alias(state: _LoweringState, statement: ast.Assign) -> _Reference:
    """Lower a non-call assignment to its wire, rejecting plain values."""
    reference = _lower_value(state, statement.value)
    if not isinstance(reference, _Reference):
        msg = (
            'only calls are recorded as work; plain values would run without leaving a trace; '
            + 'each line must call a task or graph instead'
        )
        _reject(state, node=statement.value, reason=msg)
    return reference


def _lower_unpack(state: _LoweringState, statement: ast.Assign, *, rebind: bool = False) -> None:
    """Bind each tuple element to one output of a multi-output call."""
    target: ast.expr = statement.targets[0]
    assert isinstance(target, ast.Tuple)
    names: list[str] = [elt.id for elt in target.elts if isinstance(elt, ast.Name)]
    if (
        not names
        or len(names) != len(target.elts)
        or (not rebind and any(name in state.names or name in state.partials for name in names))
    ):
        msg = (
            'unpacking maps positions to declared output ports, so every element needs a fresh name; '
            + 'give each unpacked output a new name instead'
        )
        _reject(state, node=statement, reason=msg)
    if not isinstance(statement.value, ast.Call):
        msg = (
            'unpacking maps positions to declared output ports, so only a multi-output call unpacks; '
            + 'call a task or graph with one output per name instead'
        )
        _reject(state, node=statement.value, reason=msg)
    call = statement.value
    capture = _is_catch_error(state, call)
    if capture:
        if len(statement.targets) != 1 or len(names) != 2 or (names[0] == names[1] and names[0] != '_'):
            _reject(state, node=target, reason='`catch_error` must unpack into exactly two names')
        if len(call.args) != 1 or call.keywords or not isinstance(call.args[0], ast.Call):
            _reject(state, node=call, reason='`catch_error` requires one direct fallible task or graph invocation')
        call = call.args[0]
    ref = _lower_call(state, expression=call, capture=capture, unpack=True)
    if not isinstance(ref.shape, NamespaceShape):
        if len(names) == 1:
            state.names[names[0]] = ref
            return
        msg = (
            'a single stored value has no fields to select; '
            + 'this task has one output; assign it to one name instead'
        )
        _reject(state, node=statement.value, reason=msg)
    fields: tuple[tuple[str, Shape], ...] = ref.shape.fields
    if len(names) != len(fields):
        msg = 'leaving ports unwired would drop declared outputs; ' + f'name all {len(fields)} outputs, one name each'
        _reject(state, node=statement, reason=msg)
    for name, (field_name, field_shape) in zip(names, fields):
        # `_` discards its arm: it never becomes a wire, so regions never route it.
        if name != '_':
            port = f'{ref.port}.{field_name}' if ref.port else field_name
            state.names[name] = _Reference(ref.task, port=port, shape=field_shape)


def _lower_arm(state: _LoweringState, statements: list[ast.stmt]) -> _Arm:
    """Lower one branch arm to a named region body."""
    child = _collect_region_inputs(state, statements=statements)
    statement = statements[0]
    if (
        isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
        and isinstance(statement.value, ast.Name)
    ):
        name = statement.targets[0].id
        outer = state.names[statement.value.id]  # _collect_region_inputs rejects unknown reads above
        if isinstance(outer.shape, NamespaceShape):
            return _namespace_arm(child, name=name, value=child.names[statement.value.id], alias=True)
        # The outer port may be a dotted field path, so the region output takes the assigned name.
        child.names[name] = _Reference(None, port=name, shape=outer.shape)
        body = _lower_region_body(child, {name: _Reference(None, port=statement.value.id, shape=outer.shape)})
        return _Arm(name, child=child, body=body, alias=True)
    elif (
        isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
        and isinstance(statement.value, (ast.Attribute, ast.Subscript))
    ):
        # A field selection reads like an alias but names a field inside a namespace.
        # A leaf re-keys the region output under the assigned name; dotted paths are
        # references, not port names, and only the assigned name is a port.
        name = statement.targets[0].id
        field = _lower_value(child, statement.value)
        assert isinstance(field, _Reference)  # `_select_field` returns a reference or rejects
        if isinstance(field.shape, NamespaceShape):
            return _namespace_arm(child, name=name, value=field, alias=True)
        child.names[name] = _Reference(None, port=name, shape=field.shape)
        body = _lower_region_body(child, {name: _Reference(None, port=field.port, shape=field.shape)})
        return _Arm(name, child=child, body=body, alias=True)
    elif isinstance(statement, ast.While):
        _lower_loop(child, statement=statement)
        rebound = [name for name in _body_state_names(statement.body) if name in state.names]
        if len(rebound) != 1:
            msg = (
                'a loop arm exposes one wire, so it must rebind exactly one outer name; '
                + 'rebind one name in the loop instead'
            )
            _reject(state, node=statement, reason=msg)
        name = rebound[0]
        reference = child.names[name]
    elif isinstance(statement, ast.If):
        name = _lower_branch(child, statement=statement)
        reference = child.names[name]
        if isinstance(reference.shape, NamespaceShape):
            return _namespace_arm(child, name=name, value=reference, alias=False)
        # A nested branch only forwards its exposed wire, so the enclosing
        # branch may rekey it like an alias arm when the other arm calls.
        return _Arm(name, child=child, body=_lower_region_body(child, {reference.port: reference}), alias=True)
    else:
        name = _lower_assignment(child, statement=statement, rebind=True)
        reference = child.names[name]
    if isinstance(reference.shape, NamespaceShape):
        return _namespace_arm(child, name=name, value=reference, alias=False)
    return _Arm(name, child=child, body=_lower_region_body(child, {reference.port: reference}))


def _namespace_arm(child: _LoweringState, *, name: str, value: _Reference, alias: bool) -> _Arm:
    """Bind a namespace arm, exposing its fields at the region root.

    `_lower_branch` restarts the carried name at the branch root, so every
    namespace arm takes this layout, whichever statement binds it.
    """
    child.names[name] = value
    return _Arm(name, child=child, body=_lower_region_body(child, _fields(value)), alias=alias)


def _is_namespace_arm(arm: _Arm) -> bool:
    """Return whether an arm binds a namespace, so its fields sit at the region root."""
    return isinstance(arm.child.names[arm.name].shape, NamespaceShape)


def _single_assign_target(statement: ast.stmt) -> str | None:
    """Return the assigned plain name, or `None` for other statements."""
    if isinstance(statement, ast.Assign) and len(statement.targets) == 1 and isinstance(statement.targets[0], ast.Name):
        return statement.targets[0].id
    if isinstance(statement, ast.AugAssign) and isinstance(statement.target, ast.Name):
        return statement.target.id
    return None


def _passthrough_arm(state: _LoweringState, *, name: str, port: str, shape: Shape) -> _Arm:
    """Lower a missing `else` arm to a region passing the prior binding through."""
    child = _LoweringState(state.definition, stack=state.stack)
    child.inputs[name] = []
    child.input_shapes[name] = shape
    child.names[name] = _Reference(None, port=name, shape=shape)
    if isinstance(shape, NamespaceShape):
        return _namespace_arm(child, name=name, value=child.names[name], alias=False)
    return _Arm(name, child=child, body=_lower_region_body(child, {port: _Reference(None, port=name, shape=shape)}))


def _merge_port(first: _Arm, second: _Arm) -> str | None:
    """Return the port alias arms rewire to: the call arm's port, or the first alias port.

    Rekeying is unconditional; validation judges whether the types agree. Namespace
    outputs already share field names, so they never rekey.
    """
    if _is_namespace_arm(first) or _is_namespace_arm(second):
        return None
    call_ports = {port for arm in (first, second) if not arm.alias for port in arm.body.outputs}
    if len(call_ports) == 1:
        return next(iter(call_ports))
    if call_ports:
        return None
    first_ports = list(first.body.outputs)
    second_ports = list(second.body.outputs)
    if len(first_ports) == 1 and len(second_ports) == 1:
        return first_ports[0]
    return None


def _rekey_alias(arm: _Arm, port: str) -> _Arm:
    """Expose an alias arm's passthrough value under the merged port."""
    [(_, endpoint)] = list(arm.body.outputs.items())
    assert isinstance(endpoint, Endpoint)
    return arm._replace(body=replace(arm.body, outputs={port: endpoint}))


def _fresh_wire(state: _LoweringState, base: str) -> str:
    """Return a wire name unused by any enclosing binding."""
    name = base
    count = 2
    while name in state.names:
        name = f'{base}_{count}'
        count += 1
    return name


def _lower_bool_operand(state: _LoweringState, expression: ast.expr, *, op: str) -> _Reference:
    """Lower one `and`/`or` operand to a boolean reference, rejecting non-boolean values.

    Python returns the operand itself (`1 and 2` gives `2`); graphs have no such values, so
    every operand must statically read as a boolean instead.
    """
    if isinstance(expression, ast.BoolOp):
        return _lower_boolop(state, node=expression)
    if isinstance(expression, ast.Call):
        reference = _lower_call(state, expression=expression)
    elif isinstance(expression, (ast.BinOp, ast.Compare, ast.UnaryOp)):
        reference = _lower_operation(state, node=expression)
    else:
        lowered = _lower_value(state, expression)
        if not isinstance(lowered, _Reference):
            if not isinstance(lowered, bool):
                msg = (
                    f'boolean `{op}` combines true/false values, so operands must be boolean; '
                    + 'compare values or call a task returning a boolean instead'
                )
                _reject(state, node=expression, reason=msg)
            return _place_constant(state, value=lowered, node=expression)
        reference = lowered
    if not _is_bool_reference(reference):
        msg = (
            f'boolean `{op}` combines true/false values, so operands must be boolean; '
            + 'compare values or call a task returning a boolean instead'
        )
        _reject(state, node=expression, reason=msg)
    return reference


def _combine_bool(state: _LoweringState, op: str, left: ast.expr, right: ast.expr, node: ast.BoolOp) -> _Reference:
    """Lower one `and`/`or` pair to a branch selecting the joined boolean.

    The right side lowers inside the taken arm, so it never runs when skipped: `and` evaluates
    it only when the left side holds, `or` only when it does not. Presence and member tests on
    the left stay branch tests instead of values, reusing the same selection machinery. The left
    side lowers before the joined wire is claimed, so a nested combination never reuses the
    outer alias for its inner branch.
    """
    if _match_none_test(left) is None and _match_member_test(state, left) is None:
        # A computed left side wires through an alias the branch test reads; claim the alias only
        # after lowering the left side so nested combinations claim distinct wires.
        lowered = _lower_bool_operand(state, left, op=op)
        armed = _fresh_wire(state, 'conjunction')
        state.names[armed] = lowered
        test: ast.expr = ast.Name(id=armed, ctx=ast.Load())
        ast.copy_location(test, left)
    else:
        armed = _fresh_wire(state, 'conjunction')
        test = left
    taken: ast.expr = right
    skipped: ast.expr = ast.Constant(value=op == 'or')
    ast.copy_location(skipped, node)
    if op == 'and':
        body, orelse = taken, skipped
    else:
        body, orelse = skipped, taken
    statement = ast.If(
        test=test,
        body=[ast.Assign(targets=[ast.Name(id=armed, ctx=ast.Store())], value=body)],
        orelse=[ast.Assign(targets=[ast.Name(id=armed, ctx=ast.Store())], value=orelse)],
    )
    ast.copy_location(statement, node)
    ast.fix_missing_locations(statement)
    _lower_branch(state, statement=statement)
    if not _is_bool_reference(state.names[armed]):
        # Alias arms carry the right side through unchecked, so a non-boolean right side only
        # shows up in the joined shape here; reject it with the operator diagnostic instead of a
        # downstream condition or contract failure.
        msg = (
            f'boolean `{op}` combines true/false values, so operands must be boolean; '
            + 'compare values or call a task returning a boolean instead'
        )
        _reject(state, node=node, reason=msg)
    return state.names[armed]


def _lower_boolop(state: _LoweringState, node: ast.BoolOp) -> _Reference:
    """Lower an `and`/`or` chain to left-folded branch selections, returning the joined boolean."""
    op = 'and' if isinstance(node.op, ast.And) else 'or'
    combined = _combine_bool(state, op, node.values[0], node.values[1], node)
    for extra in node.values[2:]:
        alias = _fresh_wire(state, 'conjunction')
        state.names[alias] = combined
        name = ast.Name(id=alias, ctx=ast.Load())
        ast.copy_location(name, node)
        combined = _combine_bool(state, op, name, extra, node)
    return combined


def _lower_ifexp(state: _LoweringState, node: ast.IfExp) -> _Reference:
    """Lower a conditional expression to a branch selecting one arm, returning the joined wire.

    Only the taken arm ever runs: each arm lowers inside its own region, so task calls there
    become placements of the taken side alone. Both arms must expose the same wire.
    """
    armed = _fresh_wire(state, 'conditional')
    statement = ast.If(
        test=node.test,
        body=[ast.Assign(targets=[ast.Name(id=armed, ctx=ast.Store())], value=node.body)],
        orelse=[ast.Assign(targets=[ast.Name(id=armed, ctx=ast.Store())], value=node.orelse)],
    )
    ast.copy_location(statement, node)
    ast.fix_missing_locations(statement)
    _lower_branch(state, statement=statement)
    return state.names[armed]


def _lower_branch(state: _LoweringState, statement: ast.If) -> str:
    """Lower an if statement to a branch control task, returning the exposed wire."""
    _check_branch_shape(state, statement=statement)
    test: ast.expr = statement.test
    if isinstance(test, (ast.Call, ast.BoolOp, ast.IfExp)):
        test = _bind_test_condition(state, test=test)
    condition_test: t.Literal['truthy', 'is_none', 'is_not_none', 'is_member', 'is_not_member'] = 'truthy'
    condition_member: tuple[str, str] | None = None
    if (none_test := _match_none_test(test)) is not None:
        test, condition_test = none_test
    elif (matched := _match_member_test(state, test)) is not None:
        test, condition_test, condition_member = matched
        shape = _probe_shape(state, test)
        if isinstance(shape, LeafShape) and shape.error_enums and condition_member[0] not in shape.error_enums:
            _reject(state, node=statement.test, reason='this enum is not declared by the captured invocation')
    elif isinstance(test, (ast.BinOp, ast.Compare, ast.UnaryOp)):
        # Numeric inline operations bind to a fresh boolean wire; `is`/`is not`
        # presence and member tests above must win over this numeric path.
        test = _bind_test_condition(state, test=test)
    first = _lower_arm(state, statements=statement.body)
    if statement.orelse:
        second = _lower_arm(state, statements=statement.orelse)
    else:
        if first.name not in state.names:
            msg = (
                'without an `else` arm the branch keeps the prior binding, so '
                + f'`{first.name}` must be assigned before the `if`; assign it first or add an `else` arm instead'
            )
            _reject(state, node=statement, reason=msg)
        selected = first.child.names[first.name]
        second = _passthrough_arm(state, name=first.name, port=selected.port, shape=selected.shape)
    _check_arms_agree(state, statement=statement, first=first, second=second)
    port = _merge_port(first, second)
    if port is not None:
        first = _rekey_alias(first, port) if first.alias else first
        second = _rekey_alias(second, port) if second.alias else second
    instance = _claim_name(state, f'branch_{len(state.tasks) + 1}')
    given = _wire_branch_inputs(state, instance=instance, first=first, second=second, test=test)
    state.tasks.append(
        BranchControl(
            name=instance,
            inputs=given,
            body=first.body,
            otherwise=second.body,
            condition_test=condition_test,
            condition_member=condition_member,
        )
    )
    selected = first.child.names[first.name]
    # Namespace arms expose their fields at the branch root, so the carried
    # name restarts at the whole branch namespace instead of the call port.
    carried = '' if _is_namespace_arm(first) or _is_namespace_arm(second) else port or selected.port
    merged = merge_branch_shape(selected.shape, second.child.names[second.name].shape)
    # Incompatible arms retain the existing validation path, including boolean diagnostics.
    state.names[first.name] = _Reference(instance, port=carried, shape=merged if merged is not None else selected.shape)
    return first.name


def _identity_compare(node: ast.AST) -> tuple[ast.expr, ast.expr, bool] | None:
    """Split a single `is` or `is not` comparison into its sides and whether it is `is`."""
    if (
        isinstance(node, ast.Compare)
        and len(node.ops) == 1
        and isinstance(node.ops[0], (ast.Is, ast.IsNot))
        and len(node.comparators) == 1
    ):
        return node.left, node.comparators[0], isinstance(node.ops[0], ast.Is)
    return None


def _attribute_path(node: ast.expr) -> tuple[ast.expr, list[str]]:
    """Return the base of an attribute chain and its attribute names, base first."""
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    return node, parts[::-1]


def _match_none_test(test: ast.expr) -> tuple[ast.expr, t.Literal['is_none', 'is_not_none']] | None:
    """Split `wire is None` into its wire and test kind, or return `None`."""
    compared = _identity_compare(test)
    if compared is None:
        return None
    wire, other, is_test = compared
    if not (isinstance(other, ast.Constant) and other.value is None):
        return None
    kind: t.Literal['is_none', 'is_not_none'] = 'is_none' if is_test else 'is_not_none'
    return wire, kind


def _match_member_test(
    state: _LoweringState, test: ast.expr
) -> tuple[ast.expr, t.Literal['is_member', 'is_not_member'], tuple[str, str]] | None:
    """Lower `wire is Enum.MEMBER` to a member test, or reject an unknown member.

    The first side resolving to an enum member wins; the other side is the
    wire, checked as usual when it is lowered. A wire tested against an
    unknown name reports the missing member instead of a generic rejection.
    """
    compared = _identity_compare(test)
    if compared is None:
        return None
    left, right, is_test = compared
    for wire, other in ((left, right), (right, left)):
        member = _resolve_enum_member(state, other)
        if member is not None and not isinstance(wire, ast.Constant):
            kind: t.Literal['is_member', 'is_not_member'] = 'is_member' if is_test else 'is_not_member'
            return wire, kind, member
    _reject_unknown_member(state, left, right)
    return None


def _is_supported_predicate(state: _LoweringState, expression: ast.expr) -> bool:
    """Return whether an expression is a supported presence or member test, optionally negated.

    Only the already-supported `is None`, `is not None`, and declared error-member forms count;
    arbitrary `x is y` identities never do. A leading `not` inverts the boolean without changing
    which identities are supported, so `not (value is None)` counts while `not flag` does not.
    """
    if _match_none_test(expression) is not None:
        return True
    if _match_member_test(state, expression) is not None:
        return True
    if isinstance(expression, ast.UnaryOp) and isinstance(expression.op, ast.Not):
        return _is_supported_predicate(state, expression.operand)
    return False


def _lower_predicate_value(state: _LoweringState, expression: ast.expr, node: ast.AST) -> _Reference | None:
    """Lower a presence or member test to an ephemeral boolean control value, or return `None`.

    The test reuses the branch selection machinery to choose between `True` and `False`, so the
    joined wire reads as a boolean without running any task. `None` means the expression is no
    supported predicate and the caller falls through to its usual rejection.
    """
    if isinstance(expression, ast.UnaryOp) and isinstance(expression.op, ast.Not):
        if not _is_supported_predicate(state, expression.operand):
            return None
        inner = _lower_predicate_value(state, expression.operand, node=expression.operand)
        assert inner is not None
        return _place_operation(state, operation='not', operands=(inner,), node=node)
    matched_none = _match_none_test(expression)
    matched_member = None if matched_none is not None else _match_member_test(state, expression)
    if matched_none is None and matched_member is None:
        return None
    armed = _fresh_wire(state, 'predicate')
    test = copy.deepcopy(expression)
    taken: ast.expr = ast.Constant(value=True)
    skipped: ast.expr = ast.Constant(value=False)
    ast.copy_location(taken, node)
    ast.copy_location(skipped, node)
    statement = ast.If(
        test=test,
        body=[ast.Assign(targets=[ast.Name(id=armed, ctx=ast.Store())], value=taken)],
        orelse=[ast.Assign(targets=[ast.Name(id=armed, ctx=ast.Store())], value=skipped)],
    )
    ast.copy_location(statement, node)
    ast.fix_missing_locations(statement)
    _lower_branch(state, statement=statement)
    return state.names[armed]


def _reject_unknown_member(state: _LoweringState, left: ast.expr, right: ast.expr) -> None:
    """Reject a wire compared against a name that is no declared enum member."""
    for value, other in ((left, right), (right, left)):
        reason = _unknown_member(state, other) if _compares_wire_to_name(state, value, other) else None
        if reason is not None:
            msg = (
                'conditions test declared error members, so the compared name must be one; '
                + f'{ast.unparse(other)!r} {reason}; check the spelling instead'
            )
            _reject(state, node=other, reason=msg)


def _compares_wire_to_name(state: _LoweringState, value: ast.expr, other: ast.expr) -> bool:
    """Return whether one side is a known wire and the other a plain or dotted name."""
    return isinstance(value, ast.Name) and value.id in state.names and isinstance(other, (ast.Name, ast.Attribute))


def _unknown_member(state: _LoweringState, node: ast.expr) -> str | None:
    """Return why a compared name is no enum member, or `None` when it may be one."""
    if not _known_name(state, node):
        return 'is not a known enum member'
    if isinstance(node, ast.Attribute) and _resolve_enum_member(state, node) is None and _enum_base(state, node):
        return 'is not a member of its enum'
    return None


def _enum_base(state: _LoweringState, node: ast.Attribute) -> type | None:
    """Return the enum class a dotted member reference starts from, or `None`."""
    base, _ = _attribute_path(node)
    if not isinstance(base, ast.Name) or base.id in state.names:
        return None
    resolved = state.definition.symbols.values.get(base.id)
    return resolved if isinstance(resolved, type) and issubclass(resolved, enum.Enum) else None


def _known_name(state: _LoweringState, node: ast.expr) -> bool:
    """Return whether a name or dotted path starts from a known wire or module."""
    base, _ = _attribute_path(node)
    if not isinstance(base, ast.Name):
        return True
    return base.id in state.names or base.id in state.definition.symbols.values


def _resolve_enum_member(state: _LoweringState, node: ast.expr) -> tuple[str, str] | None:
    """Return the enum identifier and member name behind a reference, or `None`."""
    base, parts = _attribute_path(node)
    # A base shadowing an enclosing wire stays a wire, as with dotted calls.
    if not isinstance(base, ast.Name) or base.id in state.names:
        return None
    try:
        resolved: t.Any = state.definition.symbols.values[base.id]
        for part in parts:
            resolved = getattr(resolved, part)
    except (KeyError, AttributeError):
        return None
    if isinstance(resolved, enum.Enum):
        return get_object_loader().identify_object(type(resolved)), resolved.name
    return None


def _check_branch_shape(state: _LoweringState, statement: ast.If) -> None:
    """Reject branch statements that do not assign one name on both sides."""
    if len(statement.body) != 1 or (statement.orelse and len(statement.orelse) != 1):
        msg = (
            'only one side runs, but wiring resolves beforehand against one name; '
            + 'assign the same name on both sides instead'
        )
        _reject(state, node=statement, reason=msg)
    if not statement.orelse:
        target = _single_assign_target(statement.body[0])
        if target is not None and target not in state.names:
            msg = (
                'without an `else` arm the branch keeps the prior binding, so '
                + f'`{target}` must be assigned before the `if`; assign it first or add an `else` arm instead'
            )
            _reject(state, node=statement, reason=msg)


def _check_arms_agree(state: _LoweringState, statement: ast.If, first: _Arm, second: _Arm) -> None:
    """Reject arms assigning different names or the condition port."""
    if statement.orelse and first.name != second.name:
        msg = (
            'the branch exposes one wire no matter which side runs, so it must be fresh and shared; '
            + 'both sides must share one new name instead'
        )
        _reject(state, node=statement, reason=msg)
    if _CONDITION_PORT in first.body.inputs or _CONDITION_PORT in second.body.inputs:
        msg = (
            'the condition travels on a reserved port, so a body input with that name would collide; '
            + 'condition conflicts with a branch input; rename one of them'
        )
        _reject(state, node=statement, reason=msg)


def _wire_branch_inputs(
    state: _LoweringState, instance: str, first: _Arm, second: _Arm, test: ast.expr
) -> dict[str, _CapturedValue]:
    """Wire the condition and the region inputs into a branch placement."""
    given: dict[str, _CapturedValue] = {}
    _wire(state, instance=instance, port=_CONDITION_PORT, value=_lower_value(state, test), given=given)
    for side in (first, second):
        for name in side.child.inputs:
            if name in side.child.synthetic_fixed:
                _wire_fixed_value(state, instance, name, side.child.synthetic_fixed[name], given)
    read = {path.split('.')[0] for side in (first, second) for path in side.child.inputs}
    for name in sorted(read):
        if any(name in side.child.synthetic_fixed for side in (first, second)):
            continue
        _wire(state, instance=instance, port=name, value=state.names[name], given=given)
    return given


def _body_state_names(body: list[ast.stmt]) -> set[str]:
    """Return the state names a loop body assigns, at any nesting depth."""
    assigned: set[str] = set()
    for node in body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            assigned.add(node.targets[0].id)
        elif isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Tuple):
            # A `_` element discards its arm, so it never carries across iterations.
            assigned.update(elt.id for elt in node.targets[0].elts if isinstance(elt, ast.Name) and elt.id != '_')
        elif isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name):
            assigned.add(node.target.id)
        elif isinstance(node, ast.If):
            assigned.update(_body_state_names([*node.body, *node.orelse]))
        elif isinstance(node, ast.While):
            assigned.update(_body_state_names(node.body))
    return assigned


def _lower_loop(state: _LoweringState, statement: ast.While) -> None:
    """Lower a while statement to a resumable loop control task."""
    body: list[ast.stmt] = list(statement.body)
    test: ast.expr = statement.test
    if isinstance(test, ast.Call):
        test = _bind_test_condition(state, test=test)
        update = ast.Assign(targets=[ast.Name(id=test.id, ctx=ast.Store())], value=copy.deepcopy(statement.test))
        ast.copy_location(update, statement.test)
        ast.copy_location(update.targets[0], statement.test)
        body.append(update)
    elif isinstance(test, (ast.BinOp, ast.Compare, ast.UnaryOp, ast.BoolOp, ast.IfExp)) and (
        _identity_compare(test) is None or _is_supported_predicate(state, test)
    ):
        # Inline conditions bind to a boolean wire and recompute each pass, including supported
        # presence and member predicates, which lower to ephemeral boolean control values; other
        # `is`/`is not` identities stay rejected when the binding lowers them.
        test = _bind_test_condition(state, test=test)
        update = ast.Assign(targets=[ast.Name(id=test.id, ctx=ast.Store())], value=copy.deepcopy(statement.test))
        ast.copy_location(update, statement.test)
        ast.copy_location(update.targets[0], statement.test)
        body.append(update)
    if statement.orelse or not isinstance(test, ast.Name) or test.id not in state.names:
        msg = (
            'the loop runs again from one stored true/false value each pass and has no other exit; '
            + 'while loops need a named check and no else'
        )
        _reject(state, node=statement, reason=msg)
    condition = test.id
    child = _collect_region_inputs(state, statements=body)
    # Loop state is read from the previous iteration, including values rebound in the body.
    # Branches in the body assign loop state through their arms, and nested loops through
    # their own state, so both join it; every name still starts from an enclosing binding.
    assigned = _body_state_names(body)
    live = _loop_live_in(state, body)
    carried: set[str] = set()
    for name in assigned:
        if name != condition and name not in live and name not in state.names:
            # Iteration-local: declared on its first write, fresh every pass, never routed
            # in, carried, or exported. Reads before that write fail at the use instead.
            continue
        if name not in state.names:
            msg = (
                'loop state comes from enclosing names, so unknown names have nothing to start from; '
                + f'set {name!r} before the loop instead'
            )
            _reject(state, node=statement, reason=msg)
        carried.add(name)
        child.inputs.setdefault(name, [])
        child.input_shapes[name] = state.names[name].shape
        child.names[name] = _Reference(None, port=name, shape=state.names[name].shape)
    if condition not in assigned:
        msg = 'without an update the loop never ends; ' + 'update the check inside the loop body instead'
        _reject(state, node=statement, reason=msg)
    for node in body:
        if isinstance(node, ast.If):
            _lower_branch(child, statement=node)
            continue
        if isinstance(node, ast.While):
            _lower_loop(child, statement=node)
            continue
        if not isinstance(node, (ast.Assign, ast.AugAssign)):
            msg = (
                'loop bodies only record task calls, inline operations, branches, and loops; '
                + 'move anything else into a task instead'
            )
            _reject(state, node=node, reason=msg)
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Tuple):
            _lower_unpack(child, node, rebind=True)
            continue
        _lower_assignment(child, node, rebind=True)
    outputs: dict[str, _Reference] = {name: child.names[name] for name in carried}
    body_spec = _lower_region_body(child, outputs=outputs)
    instance = _claim_name(state, f'loop_{len(state.tasks) + 1}')
    given: dict[str, _CapturedValue] = {}
    _route_region(state, child=child, instance=instance, given=given)
    state.tasks.append(LoopControl(name=instance, inputs=given, body=body_spec, condition_port=condition))
    for name in carried:
        state.names[name] = _Reference(instance, port=name, shape=child.names[name].shape)


def _loop_live_in(state: _LoweringState, body: list[ast.stmt]) -> set[str]:
    """Return the body names read before any write on some path, excluding declarations.

    Called names, dotted-module bases, and enum members in member tests resolve without
    enclosing state, so they never count as loop-carried reads.
    """
    skipped = _callee_ids(state, body, state.names) | _member_test_skips(state, body)
    live: set[str] = set()
    _collect_live(body, written=set(), live=live, skipped=skipped)
    return live


def _collect_loads(node: ast.AST, *, written: set[str], live: set[str], skipped: set[int]) -> None:
    """Add the names a value expression reads before they are written."""
    for child in ast.walk(node):
        if (
            isinstance(child, ast.Name)
            and isinstance(child.ctx, ast.Load)
            and child.id not in written
            and id(child) not in skipped
        ):
            live.add(child.id)


def _collect_live(statements: list[ast.stmt], *, written: set[str], live: set[str], skipped: set[int]) -> None:
    """Accumulate read-before-write names in order, threading definite writes through branches."""
    for statement in statements:
        if isinstance(statement, ast.If):
            _collect_loads(statement.test, written=written, live=live, skipped=skipped)
            definite: set[str] | None = None
            for arm in (statement.body, statement.orelse):
                arm_written = set(written)
                _collect_live(arm, written=arm_written, live=live, skipped=skipped)
                delta = arm_written - written
                definite = delta if definite is None else definite & delta
            written |= definite or set()
        elif isinstance(statement, ast.While):
            _collect_loads(statement.test, written=written, live=live, skipped=skipped)
            # Zero iterations are possible, so nested writes never count as definite here,
            # but nested reads still observe the enclosing iteration state.
            _collect_live(statement.body, written=set(written), live=live, skipped=skipped)
        elif isinstance(statement, ast.AugAssign) and isinstance(statement.target, ast.Name):
            if statement.target.id not in written and id(statement.target) not in skipped:
                live.add(statement.target.id)
            _collect_loads(statement.value, written=written, live=live, skipped=skipped)
            written.add(statement.target.id)
        elif isinstance(statement, ast.Assign):
            _collect_loads(statement.value, written=written, live=live, skipped=skipped)
            for target in statement.targets:
                if isinstance(target, ast.Name):
                    written.add(target.id)
                elif isinstance(target, ast.Tuple):
                    for element in target.elts:
                        if isinstance(element, ast.Name):
                            written.add(element.id)


def _walk_region(statements: list[ast.stmt]) -> Iterator[ast.AST]:
    """Yield every node of each region statement, in order."""
    for stmt in statements:
        yield from ast.walk(stmt)


def _assigned_names(statements: list[ast.stmt]) -> set[str]:
    """Return the plain names a region body binds, at any nesting depth."""
    return {
        node.id for node in _walk_region(statements) if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
    }


def _is_par_map_call(state: _LoweringState, node: ast.Call) -> bool:
    """Recognize the map intrinsic during region collection without rejecting other calls."""
    try:
        target, _ = _resolve_base(state, node.func)
    except GraphLanguageError:
        return False
    return target is par_map


def _par_map_callable_expr(node: ast.Call) -> ast.expr | None:
    """Return the mapped callable expression of a `par_map` call, without validating the collection."""
    if node.args:
        return node.args[0]
    for keyword in node.keywords:
        if keyword.arg == 'func':
            return keyword.value
    return None


def _callee_ids(state: _LoweringState, statements: list[ast.stmt], enclosing: Mapping[str, _Reference]) -> set[int]:
    """Return the identities of called expressions, unshadowed module bases, and mapped callables."""
    callees: set[int] = set()
    for node in _walk_region(statements):
        if not isinstance(node, ast.Call):
            continue
        callees.add(id(node.func))
        if isinstance(node.func, ast.Attribute) and node.func.attr == 'alias':
            aliased_self = _partial_alias_binding(state, node)
            if aliased_self is not None:
                _add_partial_target_callees(state, aliased_self, enclosing, callees)
            else:
                for inner in ast.walk(node.func.value):
                    if isinstance(inner, ast.Name) and isinstance(inner.ctx, ast.Load) and inner.id not in enclosing:
                        callees.add(id(inner))
        if isinstance(node.func, ast.Call) and isinstance(node.func.func, ast.Attribute):
            alias_call = node.func
            assert isinstance(alias_call.func, ast.Attribute)
            if alias_call.func.attr == 'alias':
                aliased_partial = _partial_alias_binding(state, alias_call)
                if aliased_partial is not None:
                    _add_partial_target_callees(state, aliased_partial, enclosing, callees)
                else:
                    for inner in ast.walk(alias_call.func.value):
                        if (
                            isinstance(inner, ast.Name)
                            and isinstance(inner.ctx, ast.Load)
                            and inner.id not in enclosing
                        ):
                            callees.add(id(inner))
        # Dotted calls read through a module, not a wire; a base shadowing an
        # enclosing wire stays a read so the call rejects the ambiguity.
        func: ast.expr = node.func
        while isinstance(func, ast.Attribute):
            func = func.value
        if isinstance(func, ast.Name) and func.id not in enclosing:
            callees.add(id(func))
        if _is_par_map_call(state, node):
            callable_expr = _par_map_callable_expr(node)
            if isinstance(callable_expr, ast.Call) and _is_partial_call(state, callable_expr):
                _add_partial_target_callees(state, callable_expr, enclosing, callees)
            elif callable_expr is not None and _partial_alias_binding(state, callable_expr) is not None:
                aliased = _partial_alias_binding(state, callable_expr)
                assert aliased is not None
                _add_partial_target_callees(state, aliased, enclosing, callees)
            elif isinstance(callable_expr, ast.Call):
                for inner in ast.walk(callable_expr):
                    if isinstance(inner, ast.Name) and isinstance(inner.ctx, ast.Load) and inner.id not in enclosing:
                        callees.add(id(inner))
            elif isinstance(callable_expr, ast.Name):
                callees.add(id(callable_expr))
            elif isinstance(callable_expr, ast.Attribute):
                for inner in ast.walk(callable_expr):
                    if isinstance(inner, ast.Name) and isinstance(inner.ctx, ast.Load) and inner.id not in enclosing:
                        callees.add(id(inner))
        if _is_partial_call(state, node):
            # Only the bound target resolves as a declaration; fixed values are
            # ordinary wires and stay readable as region inputs.
            _add_partial_target_callees(state, node, enclosing, callees)
        aliased_binding = _partial_alias_binding(state, node)
        if aliased_binding is not None:
            _add_partial_target_callees(state, aliased_binding, enclosing, callees)
    return callees


def _add_partial_target_callees(
    state: _LoweringState, binding_call: ast.Call, enclosing: Mapping[str, _Reference], callees: set[int]
) -> None:
    """Mark only the declaration names behind a partial binding as callees.

    Fixed values stay readable as region inputs, so only the ultimate target
    chain counts; nested partial targets recurse without their fixed keywords.
    """
    target = _partial_target_expr(binding_call)
    if target is None:
        return
    if isinstance(target, ast.Call) and _is_partial_call(state, target):
        _add_partial_target_callees(state, target, enclosing, callees)
        return
    if (
        isinstance(target, ast.Call)
        and isinstance(target.func, ast.Attribute)
        and target.func.attr == 'alias'
        and isinstance(target.func.value, ast.Call)
        and _is_partial_call(state, target.func.value)
    ):
        _add_partial_target_callees(state, target.func.value, enclosing, callees)
        return
    for inner in ast.walk(target):
        if (
            isinstance(inner, ast.Name)
            and isinstance(inner.ctx, ast.Load)
            and inner.id not in enclosing
            and inner.id != 'partial'
        ):
            callees.add(id(inner))


def _partial_alias_binding(state: _LoweringState, expression: ast.expr) -> ast.Call | None:
    """Return the inline ``partial(...)`` behind an ``.alias(...)`` use, or ``None``."""
    if (
        isinstance(expression, ast.Call)
        and isinstance(expression.func, ast.Attribute)
        and expression.func.attr == 'alias'
        and isinstance(expression.func.value, ast.Call)
        and _is_partial_call(state, expression.func.value)
    ):
        return expression.func.value
    return None


def _member_test_skips(state: _LoweringState, statements: list[ast.stmt]) -> set[int]:
    """Return the identities of names in a member-test position.

    A compared enum member resolves when the graph is built and never
    travels as a region input, so collection skips it; the wire side
    still collects as usual. An unknown compared name skips too, so the
    member matcher reports the spelling instead of a generic rejection.
    """
    skipped: set[int] = set()
    for node in _walk_region(statements):
        compared = _identity_compare(node)
        if compared is None:
            continue
        left, right, _ = compared
        for value, other in ((left, right), (right, left)):
            if _resolve_enum_member(state, other) is not None or (
                _compares_wire_to_name(state, value, other) and not _known_name(state, other)
            ):
                skipped.update(id(part) for part in ast.walk(other) if isinstance(part, ast.Name))
    return skipped


def _collect_region_inputs(state: _LoweringState, statements: list[ast.stmt]) -> _LoweringState:
    """Collect the enclosing values a nested body reads as region inputs."""
    # Names read in the body become inputs of the nested graph. Calls are not values.
    assigned = _assigned_names(statements)
    callees = _callee_ids(state, statements, state.names)
    skipped = _member_test_skips(state, statements)
    reads: dict[str, ast.Name] = {}
    for node in _walk_region(statements):
        if not isinstance(node, ast.Name) or not isinstance(node.ctx, ast.Load):
            continue
        if node.id in assigned or id(node) in callees or id(node) in skipped or node.id in reads:
            continue
        reads[node.id] = node
    child = _LoweringState(state.definition, stack=state.stack)
    for partial_name, binding in state.partials.items():
        if partial_name not in assigned:
            child.partials[partial_name] = binding
    for name in sorted(reads):
        if name not in state.names:
            msg = (
                'a branch or loop body only sees names defined around it; '
                + f'{name!r} is not known here; assign it before the branch or loop instead'
            )
            _reject(state, node=reads[name], reason=msg)
        child.inputs[name] = []
        shape = state.names[name].shape
        child.input_shapes[name] = shape
        child.names[name] = _Reference(None, port=name, shape=shape)
    for name in sorted(assigned):
        if name in state.names:
            child.inputs.setdefault(name, [])
            child.input_shapes[name] = state.names[name].shape
            child.names[name] = _Reference(None, port=name, shape=state.names[name].shape)
    return child


def _route_region(
    state: _LoweringState, child: _LoweringState, instance: str, given: dict[str, _CapturedValue]
) -> None:
    """Route the enclosing values a nested region reads."""
    for name in child.inputs:
        if name in child.synthetic_fixed:
            _wire_fixed_value(state, instance, name, child.synthetic_fixed[name], given)
            continue
        base, _, sub = name.partition('.')
        if base not in state.names:
            continue
        value = state.names[base]
        if sub:
            value = _select_subpath(value, sub)
        _wire(state, instance=instance, port=name, value=value, given=given)


def _select_subpath(value: _Reference, sub: str) -> _Reference:
    """Carry a dotted read into a region, selecting each segment."""
    port = f'{value.port}.{sub}' if value.port else sub
    shape = value.shape
    for segment in sub.split('.'):
        # Dotted region inputs arrive through `_select_field`, so the base shape is a namespace.
        assert isinstance(shape, NamespaceShape)
        shape = shape.select(segment)
    return _Reference(value.task, port=port, shape=shape)


def _is_bool_reference(value: _Reference | int | float | str | bool | None) -> bool:
    """Return whether a lowered test statically reads as a boolean."""
    if isinstance(value, bool):
        return True
    if not isinstance(value, _Reference) or not isinstance(value.shape, LeafShape):
        return False
    types = [kind for kind in value.shape.types or () if kind is not type(None)]
    return bool(types) and all(kind is bool or kind is Bool for kind in types)


def _bind_test_condition(
    state: _LoweringState, test: ast.Call | ast.BinOp | ast.Compare | ast.UnaryOp | ast.BoolOp | ast.IfExp
) -> ast.Name:
    """Lower a call, inline comparison, boolean combination, or conditional test to a fresh binding."""
    name = 'condition'
    count = 2
    while name in state.names:
        name = f'condition_{count}'
        count += 1
    bound = ast.Assign(targets=[ast.Name(id=name, ctx=ast.Store())], value=test)
    ast.copy_location(bound, test)
    ast.copy_location(bound.targets[0], test)
    _lower_assignment(state, statement=bound)
    if not isinstance(test, ast.Call) and not _is_bool_reference(state.names[name]):
        msg = (
            'conditions decide between two sides, so they must be true or false; '
            + 'compare values or call a task returning a boolean instead'
        )
        _reject(state, node=test, reason=msg)
    return ast.Name(id=name, ctx=ast.Load())


def _lower_region_body(state: _LoweringState, outputs: dict[str, _Reference]) -> GraphIR:
    """Lower collected region state to a nested graph template."""
    endpoints: dict[str, OutputTree] = {name: _endpoint_tree(value) for name, value in outputs.items()}
    return GraphIR(
        tasks=tuple(state.tasks),
        dependencies=tuple(state.dependencies),
        inputs={name: tuple(targets) for name, targets in state.inputs.items()},
        outputs=endpoints,
        input_shape=NamespaceShape(fields=tuple(state.input_shapes.items())),
    )


def _alias_call_parts(state: _LoweringState, alias_call: ast.Call) -> tuple[ast.expr, str]:
    """Split one `.alias('name')` call into its declaration reference and explicit placement name."""
    candidate: ast.expr | None = alias_call.args[0] if len(alias_call.args) == 1 else None
    if (
        candidate is None
        or alias_call.keywords
        or not isinstance(candidate, ast.Constant)
        or not isinstance(candidate.value, str)
    ):
        msg = (
            'placement aliases name the stored placement, so they must be written out; '
            + "call `.alias('name')` with one quoted name instead"
        )
        _reject(state, node=alias_call, reason=msg)
    alias: str = candidate.value
    try:
        validate_link_label(alias)
    except ValueError as exception:
        msg = (
            f'placement alias `{alias}` is invalid as a link label ({exception}); '
            + 'use alphanumerics and underscores without leading or trailing underscores instead'
        )
        _reject(state, node=alias_call, reason=msg)
    assert isinstance(alias_call.func, ast.Attribute)
    base = alias_call.func.value
    if not isinstance(base, (ast.Name, ast.Attribute)):
        msg = (
            'calls resolve by module-level name to importable declarations; '
            + "call tasks and graphs by their plain names with `.alias('name')` on the declaration instead"
        )
        _reject(state, node=alias_call, reason=msg)
    return base, alias


def _resolve_base(state: _LoweringState, expression: ast.expr) -> tuple[t.Any, str]:
    """Resolve a declaration reference through module namespaces, never arbitrary objects."""
    base, parts = _attribute_path(expression)
    if not isinstance(base, ast.Name):
        msg = 'calls resolve by plain names to importable declarations; use a task or graph declaration instead'
        _reject(state, node=expression, reason=msg)
    if base.id in state.names:
        msg = f'a name cannot be both a wire and a declaration; {base.id!r} is also used as a result name'
        _reject(state, node=expression, reason=msg)
    if base.id in state.partials:
        msg = (
            f'{base.id!r} binds a `partial`, not a task or graph; '
            + 'call it with its remaining inputs, or pass it to `par_map` instead'
        )
        _reject(state, node=expression, reason=msg)
    symbols = state.definition.symbols
    label = '.'.join([base.id, *parts])
    name = base.id
    for part in parts:
        parent = symbols.values.get(name)
        if parent is None:
            msg = f'calls must name an importable declaration; unknown name {label!r}; check the spelling instead'
            _reject(state, node=expression, reason=msg)
        if not isinstance(parent, ModuleType):
            msg = f'calls resolve through modules; {name!r} is not a module; import the module instead'
            _reject(state, node=expression, reason=msg)
        symbols = symbols.module(parent)
        name = part
    if name not in symbols.values and name not in vars(builtins):
        msg = f'calls must name an importable declaration; unknown name {label!r}; check the spelling instead'
        _reject(state, node=expression, reason=msg)
    try:
        return symbols.lookup(name), label
    except GraphLanguageError as exception:
        _reject(state, node=expression, reason=str(exception))


def _resolve_callable(
    state: _LoweringState, expression: ast.expr
) -> tuple[
    FunctionTaskHandle[t.Any, t.Any] | CalcJobTaskHandle | WorkChainTaskHandle | GraphHandle | Callable[..., t.Any],
    str,
    str | None,
]:
    """Resolve an ordinary or explicitly aliased callable for both calls and maps."""
    explicit = None
    base = expression
    if (
        isinstance(expression, ast.Call)
        and isinstance(expression.func, ast.Attribute)
        and expression.func.attr == 'alias'
    ):
        base, explicit = _alias_call_parts(state, expression)
    target, label = _resolve_base(state, base)
    if (
        isinstance(target, (FunctionTaskHandle, CalcJobTaskHandle, WorkChainTaskHandle, GraphHandle))
        or target is par_map
    ):
        return target, label.rsplit('.', 1)[-1], explicit
    if target is None and label in vars(builtins):
        msg = f'only registered declarations carry provenance; built-in {label!r}: wrap it in a task instead'
    else:
        msg = f'only registered declarations carry port contracts; unregistered call {label!r}; add `@task` or `@graph`'
    _reject(state, node=expression, reason=msg)


def _partial_target_shape(
    target: FunctionTaskHandle[t.Any, t.Any] | CalcJobTaskHandle | WorkChainTaskHandle | GraphHandle,
    state: _LoweringState,
) -> NamespaceShape:
    """Return the input contract a partial target binds against."""
    if isinstance(target, GraphHandle):
        return _lower_graph(target, stack=state.stack).input_shape
    return target._task_spec.input_shape


def _is_partial_call(state: _LoweringState, node: ast.Call) -> bool:
    """Return whether a call is the intrinsic bare ``partial(...)`` binding."""
    if not isinstance(node.func, ast.Name) or node.func.id != 'partial':
        return False
    return 'partial' not in state.names and 'partial' not in state.partials and 'partial' not in state.input_shapes


def _partial_target_expr(node: ast.Call) -> ast.expr | None:
    """Return the bound target of a ``partial(...)`` call, or ``None`` when absent."""
    if node.args:
        return node.args[0]
    return None


def _resolve_partial_target(
    state: _LoweringState, expression: ast.expr
) -> tuple[
    FunctionTaskHandle[t.Any, t.Any] | CalcJobTaskHandle | WorkChainTaskHandle | GraphHandle,
    str,
    str | None,
    dict[str, _CapturedValue],
]:
    """Resolve a partial target to its ultimate declaration, carrying composed bindings."""
    if isinstance(expression, ast.Call) and _is_partial_call(state, expression):
        nested = _build_partial_binding(state, expression)
        return nested.target, nested.call_name, nested.explicit, dict(nested.fixed)
    base: ast.expr = expression
    explicit: str | None = None
    if (
        isinstance(expression, ast.Call)
        and isinstance(expression.func, ast.Attribute)
        and expression.func.attr == 'alias'
    ):
        assert isinstance(expression.func.value, ast.expr)
        candidate_base: ast.expr = expression.func.value
        if isinstance(candidate_base, ast.Call) and _is_partial_call(state, candidate_base):
            nested = _build_partial_binding(state, candidate_base)
            return nested.target, nested.call_name, _alias_name(state, expression), dict(nested.fixed)
        base, explicit = _alias_call_parts(state, expression)
    if isinstance(base, ast.Name) and base.id in state.partials:
        binding = state.partials[base.id]
        return binding.target, binding.call_name, explicit or binding.explicit, dict(binding.fixed)
    target, label = _resolve_base(state, base)
    if target is par_map:
        msg = '`par_map` fans out over a collection; it cannot be bound by `partial`; bind a task or graph instead'
        _reject(state, node=expression, reason=msg)
    if not isinstance(target, (FunctionTaskHandle, CalcJobTaskHandle, WorkChainTaskHandle, GraphHandle)):
        if target is None and label in vars(builtins):
            msg = f'only registered declarations carry provenance; built-in {label!r}: wrap it in a task instead'
        else:
            msg = (
                f'only registered declarations carry port contracts; unregistered call {label!r}; '
                + 'add `@task` or `@graph`'
            )
        _reject(state, node=expression, reason=msg)
    return target, label.rsplit('.', 1)[-1], explicit, {}


def _capture_fixed_value(state: _LoweringState, shape: Shape, expression: ast.expr) -> _CapturedValue:
    """Lower one fixed input value, capturing declaration-time references."""
    if isinstance(expression, ast.Call):
        msg = (
            'a `partial` fixes inputs without running anything, so fixed values cannot call; '
            + 'pass a wire or literal instead'
        )
        _reject(state, node=expression, reason=msg)
    if isinstance(expression, ast.Dict) and isinstance(shape, NamespaceShape):
        seen = set()
        nested = {}
        for key, value in zip(expression.keys, expression.values, strict=True):
            if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
                msg = (
                    'dictionary syntax for fixed namespaces must be known before anything runs; '
                    + 'namespace keys must be string literals without unpacking; compute dynamic keys in tasks'
                )
                _reject(state, node=expression, reason=msg)
            name = key.value
            if name in seen:
                msg = 'one port takes one value; ' + f'duplicate input {name!r}; pass it once'
                _reject(state, node=expression, reason=msg)
            try:
                child = shape.select(name)
            except KeyError:
                msg = (
                    'namespaces wire against declared contracts; '
                    + f'{name!r} is not a declared name here; check the spelling instead'
                )
                _reject(state, node=expression, reason=msg)
            seen.add(name)
            nested[name] = _capture_fixed_value(state, child, value)
        return nested
    if isinstance(expression, ast.Dict):
        try:
            value = ast.literal_eval(expression)
        except (ValueError, TypeError):
            msg = (
                'a mapping here either spells out fixed inputs or points at a whole input, nothing in between; '
                + 'dictionary-valued ports require a literal value or a reference to the whole port'
            )
            _reject(state, node=expression, reason=msg)
        try:
            checked = json_default(value)
        except GraphTypeCheckError:
            msg = (
                'stored inputs only hold finite JSON values; dictionary values must be finite JSON, '
                + 'so compute non-finite values in tasks instead'
            )
            _reject(state, node=expression, reason=msg)
        return t.cast('_CapturedValue', checked)
    if isinstance(expression, ast.Constant) and expression.value is None and _drops_none_value(shape):
        return {}
    return _lower_value(state, expression)


def _build_partial_binding(state: _LoweringState, node: ast.Call) -> _PartialBinding:
    """Build an unnamed partial binding from a ``partial(...)`` call without storing it."""
    if len(node.args) != 1:
        msg = (
            '`partial` binds one callable with its fixed inputs; '
            + 'call `partial(target, fixed=value, ...)` with the target positionally and the rest by keyword instead'
        )
        _reject(state, node=node, reason=msg)
    target_expr = _partial_target_expr(node)
    if target_expr is None:
        msg = (
            '`partial` binds one callable with its fixed inputs; '
            + 'call `partial(target, fixed=value, ...)` with the target positionally and the rest by keyword instead'
        )
        _reject(state, node=node, reason=msg)
    target, call_name, explicit, composed = _resolve_partial_target(state, target_expr)
    shape = _partial_target_shape(target, state)
    fixed = dict(composed)
    for keyword in node.keywords:
        if keyword.arg is None:
            msg = 'inputs wire by name, so spreading hides which is which; bind each fixed input by keyword instead'
            _reject(state, node=keyword, reason=msg)
        if keyword.arg == 'after':
            msg = 'a `partial` fixes inputs without running anything, so ordering waits for the eventual call instead'
            _reject(state, node=keyword, reason=msg)
        if keyword.arg in fixed:
            msg = 'one port takes one value; ' + f'duplicate fixed input {keyword.arg!r}; pass it once'
            _reject(state, node=keyword, reason=msg)
        try:
            child = shape.select(keyword.arg)
        except KeyError:
            msg = (
                'calls wire against declared contracts; '
                + f'{keyword.arg!r} is not an input of {call_name!r}; check the spelling instead'
            )
            _reject(state, node=keyword, reason=msg)
        captured = _capture_fixed_value(state, child, keyword.value)
        if isinstance(captured, dict) and not captured:
            continue
        fixed[keyword.arg] = captured
    if not fixed:
        msg = (
            'a `partial` fixes inputs without running anything, so it needs at least one fixed input; '
            + 'pass one by keyword instead'
        )
        _reject(state, node=node, reason=msg)
    return _PartialBinding(target=target, call_name=call_name, explicit=explicit, fixed=fixed)


def _bind_partial(state: _LoweringState, name: str, node: ast.Call) -> None:
    """Store a named partial binding, capturing fixed values at declaration time."""
    binding = _build_partial_binding(state, node)
    state.partials[name] = binding


def _alias_name(state: _LoweringState, alias_call: ast.Call) -> str:
    """Return the placement alias of an ``.alias('name')`` call, validating the name."""
    candidate: ast.expr | None = alias_call.args[0] if len(alias_call.args) == 1 else None
    if (
        candidate is None
        or alias_call.keywords
        or not isinstance(candidate, ast.Constant)
        or not isinstance(candidate.value, str)
    ):
        msg = (
            'placement aliases name the stored placement, so they must be written out; '
            + "call `.alias('name')` with one quoted name instead"
        )
        _reject(state, node=alias_call, reason=msg)
    alias: str = candidate.value
    try:
        validate_link_label(alias)
    except ValueError as exception:
        msg = (
            f'placement alias `{alias}` is invalid as a link label ({exception}); '
            + 'use alphanumerics and underscores without leading or trailing underscores instead'
        )
        _reject(state, node=alias_call, reason=msg)
    return alias


def _partial_call_parts(state: _LoweringState, func: ast.expr) -> tuple[_PartialBinding, str | None] | None:
    """Split a partial use into its binding and a use-site alias, or return ``None``."""
    if isinstance(func, ast.Name) and func.id in state.partials:
        return state.partials[func.id], None
    if isinstance(func, ast.Call) and isinstance(func.func, ast.Attribute) and func.func.attr == 'alias':
        base = func.func.value
        binding: _PartialBinding | None = None
        if isinstance(base, ast.Name) and base.id in state.partials:
            binding = state.partials[base.id]
        elif isinstance(base, ast.Call) and _is_partial_call(state, base):
            binding = _build_partial_binding(state, base)
        if binding is not None:
            return binding, _alias_name(state, func)
        return None
    if isinstance(func, ast.Call) and _is_partial_call(state, func):
        return _build_partial_binding(state, func), None
    return None


def _synthetic_name(state: _LoweringState, base: str) -> str:
    """Return a valid branch/loop input name carrying one outer fixed value."""
    cleaned = ''.join(character if character.isalnum() else '_' for character in base).strip('_') or 'partial'
    if not cleaned[0].isalpha():
        cleaned = f'partial_{cleaned}'
    taken = {placed.name for placed in state.tasks} | set(state.used)
    name = cleaned
    count = 2
    while name in state.inputs or name in state.input_shapes or name in state.names or name in taken:
        name = f'{cleaned}_{count}'
        count += 1
    state.used[name] = 1
    return name


def _needs_synthetic(state: _LoweringState, captured: _CapturedValue) -> bool:
    """Return whether a captured fixed value points outside the current template.

    Task outputs of enclosing scopes cannot edge into a nested template, and neither
    can graph inputs the region collection never saw because the binding hid them.
    Both travel on synthetic region inputs; visible wires lower directly.
    """
    if isinstance(captured, dict):
        return any(_needs_synthetic(state, item) for item in captured.values())
    if not isinstance(captured, _Reference):
        return False
    if captured.task is not None:
        return captured.task not in {placed.name for placed in state.tasks}
    base = captured.port.split('.')[0] if captured.port else ''
    return base not in state.names


def _wire_fixed_value(
    state: _LoweringState, instance: str, port: str, captured: _CapturedValue, given: dict[str, _CapturedValue]
) -> None:
    """Wire one captured fixed value, routing outer task outputs through region inputs."""
    if isinstance(captured, dict):
        for field, item in captured.items():
            _wire_fixed_value(state, instance, f'{port}.{field}', item, given)
        return
    if _needs_synthetic(state, captured):
        assert isinstance(captured, _Reference)
        name = _synthetic_name(state, f'partial_{port.replace(".", "_")}')
        if name not in state.inputs:
            state.inputs[name] = []
            state.input_shapes[name] = captured.shape
            state.names[name] = _Reference(None, port=name, shape=captured.shape)
            state.synthetic_fixed[name] = captured
        elif state.synthetic_fixed.get(name) != captured:
            # A different value (or a real input colliding with the deterministic
            # name) needs its own region input rather than reusing this wire.
            name = _synthetic_name(state, f'{name}_fixed')
            state.inputs[name] = []
            state.input_shapes[name] = captured.shape
            state.names[name] = _Reference(None, port=name, shape=captured.shape)
            state.synthetic_fixed[name] = captured
        _wire(state, instance=instance, port=port, value=state.names[name], given=given)
        return
    _wire(state, instance=instance, port=port, value=captured, given=given)


def _merge_given(
    first: dict[str, _CapturedValue],
    second: dict[str, _CapturedValue],
    state: _LoweringState,
    node: ast.AST,
    *,
    shape: NamespaceShape,
) -> dict[str, _CapturedValue]:
    """Merge fixed and call-time wirings, rejecting conflicting leaf paths.

    Namespace inputs merge field by field, so a fixed ``config={'a': x}`` and a
    call-time ``config={'b': y}`` combine while a repeated leaf still rejects.
    """
    merged = dict(first)
    for path, value in second.items():
        if path not in merged:
            merged[path] = value
            continue
        try:
            child = shape.select(path)
        except KeyError:
            child = None
        merged[path] = _merge_values(merged[path], value, f'{path}', child, state, node)
    return merged


def _merge_values(
    first: _CapturedValue,
    second: _CapturedValue,
    path: str,
    shape: Shape | None,
    state: _LoweringState,
    node: ast.AST,
) -> _CapturedValue:
    """Merge two wirings at one input path, recursing only through namespaces."""
    if isinstance(first, dict) and isinstance(second, dict) and isinstance(shape, NamespaceShape):
        merged: dict[str, _CapturedValue] = dict(first)
        for field, value in second.items():
            if field not in merged:
                merged[field] = value
                continue
            try:
                child = shape.select(field)
            except KeyError:
                child = None
            merged[field] = _merge_values(merged[field], value, f'{path}.{field}', child, state, node)
        return merged
    msg = f'{path!r} is already fixed by the `partial`; pass the remaining inputs instead'
    _reject(state, node=node, reason=msg)


def _fixed_leaf_paths(fixed: dict[str, _CapturedValue], shape: NamespaceShape) -> set[str]:
    """Return the dotted leaf paths a partial binding already occupies."""
    paths: set[str] = set()

    def _collect(value: _CapturedValue, contract: Shape | None, prefix: str) -> None:
        if isinstance(value, dict) and isinstance(contract, NamespaceShape):
            if not value:
                paths.add(prefix)
                return
            for field, item in value.items():
                try:
                    child = contract.select(field)
                except KeyError:
                    child = None
                _collect(item, child, f'{prefix}.{field}')
            return
        paths.add(prefix)

    for name, item in fixed.items():
        try:
            child = shape.select(name)
        except KeyError:
            child = None
        _collect(item, child, name)
    return paths


def _call_leaf_paths(keyword: ast.keyword, shape: NamespaceShape) -> set[str]:
    """Return the dotted leaf paths one call-time keyword would occupy."""
    assert keyword.arg is not None
    try:
        child = shape.select(keyword.arg)
    except KeyError:
        return {keyword.arg}
    return _expression_leaf_paths(keyword.value, child, keyword.arg)


def _expression_leaf_paths(expression: ast.expr, contract: Shape, prefix: str) -> set[str]:
    """Return the dotted paths a call-time expression would occupy under a contract."""
    if isinstance(expression, ast.Dict) and isinstance(contract, NamespaceShape):
        paths: set[str] = set()
        for key, value in zip(expression.keys, expression.values, strict=True):
            if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
                return {prefix}
            try:
                nested = contract.select(key.value)
            except KeyError:
                nested = contract
            paths.update(_expression_leaf_paths(value, nested, f'{prefix}.{key.value}'))
        return paths or {prefix}
    return {prefix}


def _check_partial_overlap(
    state: _LoweringState,
    binding: _PartialBinding,
    call_keywords: list[ast.keyword],
    shape: NamespaceShape,
) -> None:
    """Reject call-time inputs that repeat a leaf the partial already fixed."""
    fixed = _fixed_leaf_paths(binding.fixed, shape)
    for keyword in call_keywords:
        assert keyword.arg is not None
        for path in _call_leaf_paths(keyword, shape):
            for taken in fixed:
                if path == taken or path.startswith(f'{taken}.') or taken.startswith(f'{path}.'):
                    msg = f'{path!r} is already fixed by the `partial`; pass the remaining inputs instead'
                    _reject(state, node=keyword, reason=msg)


def _lower_partial_call(
    state: _LoweringState,
    binding: _PartialBinding,
    expression: ast.Call,
    explicit_override: str | None,
    *,
    capture: bool,
    unpack: bool,
) -> _Reference:
    """Place one partial use, merging fixed and call-time inputs into one ordinary placement."""
    inputs = _partial_target_shape(binding.target, state)
    after = None
    positional = list(expression.args)
    keywords = []
    for keyword in expression.keywords:
        if keyword.arg == 'after':
            if after is not None:
                msg = 'one port takes one value; duplicate input `after`; pass it once.'
                _reject(state, node=keyword, reason=msg)
            after = keyword
            continue
        keywords.append(keyword)
    if any(keyword.arg is None for keyword in keywords):
        keywords = _spread_keywords(
            state, expression=expression, name=binding.call_name, inputs=inputs, keywords=keywords
        )
    remaining = [field for field, _ in inputs.fields if field not in binding.fixed]
    bound_positional = []
    if positional:
        if len(positional) > len(remaining):
            msg = (
                'positional arguments follow declared input order, so extras map to nothing; '
                + f'too many positional arguments for partial of `{binding.call_name}`; drop the extras'
            )
            _reject(state, node=expression, reason=msg)
        for field, arg in zip(remaining, positional):
            bound_positional.append(ast.keyword(arg=field, value=arg))
    seen: set[str | None] = set()
    call_keywords: list[ast.keyword] = []
    for keyword in [*bound_positional, *keywords]:
        if keyword.arg in seen:
            msg = 'one port takes one value; ' + f'duplicate input {keyword.arg!r}; pass it once'
            _reject(state, node=keyword, reason=msg)
        seen.add(keyword.arg)
        call_keywords.append(keyword)
    _check_partial_overlap(state, binding, call_keywords, inputs)
    explicit = explicit_override or binding.explicit
    if explicit is not None:
        instance = _claim_placement(state, explicit, node=expression)
    else:
        instance = _claim_placement(state, name=binding.call_name, node=expression)
    task: ProcessTask | SubgraphTask
    given: dict[str, _CapturedValue]
    if isinstance(binding.target, GraphHandle):
        body = _lower_graph(binding.target, stack=state.stack)
        given = {}
        for port, captured in binding.fixed.items():
            _wire_fixed_value(state, instance, port, captured, given)
        wired = _lower_keywords(
            state, instance=instance, name=binding.call_name, inputs=body.input_shape, keywords=call_keywords
        )
        given = _merge_given(given, wired, state, expression, shape=body.input_shape)
        task = SubgraphTask(name=instance, inputs=given, body=body)
        shape_inputs = body.input_shape
        result_port = body.result_port
        result_shape = body.result_shape
    else:
        spec = binding.target._task_spec
        narrowed = _solved_partial_spec(
            binding.target, binding, call_keywords, state, spec=spec, result_port=spec.result_port
        )
        given = {}
        for port, captured in binding.fixed.items():
            _wire_fixed_value(state, instance, port, captured, given)
        wired = _lower_keywords(
            state, instance=instance, name=binding.call_name, inputs=narrowed.input_shape, keywords=call_keywords
        )
        given = _merge_given(given, wired, state, expression, shape=narrowed.input_shape)
        task = ProcessTask(name=instance, inputs=given, spec=narrowed)
        shape_inputs = narrowed.input_shape
        result_port = narrowed.result_port
        result_shape = narrowed.result_shape
    if isinstance(task, ProcessTask):
        runtime_paths = task.spec.runtime_input_paths()
    else:
        runtime_paths = frozenset()
    missing = _missing_required_inputs(
        state, instance=instance, shape=shape_inputs, given=task.inputs, runtime_paths=runtime_paths
    )
    if missing:
        msg = (
            'required inputs must be wired before the graph is stored; '
            + f'partial of `{binding.call_name}` is missing required inputs: {missing}; pass them at the call'
        )
        _reject(state, node=expression, reason=msg)
    reference = _place_invocation(state, expression, task, result_port, result_shape, capture=capture, unpack=unpack)
    if after is not None:
        _wire_after(state, instance=instance, keyword=after)
    return reference


def _claim_placement(state: _LoweringState, name: str, node: ast.AST, *, is_map: bool = False) -> str:
    """Claim one authored placement name, rejecting reuse within the same static body."""
    taken: set[str] = {placed.name for placed in state.tasks}
    if name in taken or state.used.get(name, 0) > 0:
        if is_map:
            msg = (
                f'map placement name `{name}` is already used in this graph; '
                + "pass a unique name with `par_map(task.alias('name'), values)` instead"
            )
        else:
            msg = (
                f'placement name `{name}` is already used in this graph; '
                + "pass a unique name with `.alias('unique_name')` on the call instead"
            )
        _reject(state, node=node, reason=msg)
    state.used[name] = 1
    return name


def _claim_name(state: _LoweringState, name: str) -> str:
    """Return an internal generated placement name, suffixing on collision."""
    state.used[name] += 1
    count = state.used[name]
    taken: set[str] = {placed.name for placed in state.tasks}
    instance = name if count == 1 else f'{name}_{count}'
    while instance in taken:
        count += 1
        instance = f'{name}_{count}'
    state.used[name] = count
    return instance


def _probe_shape(state: _LoweringState, expression: ast.expr) -> Shape | None:
    """Return the static contract of a generic-call argument without placing anything."""
    if isinstance(expression, ast.Name):
        reference = state.names.get(expression.id)
        if reference is None:
            return None
        return reference.shape
    if isinstance(expression, ast.Attribute):
        field = _probe_field(state, expression.value, expression.attr)
        return field if field is not None else _probe_expression_shape(state, expression)
    if (
        isinstance(expression, ast.Subscript)
        and isinstance(expression.slice, ast.Constant)
        and isinstance(expression.slice.value, str)
    ):
        field = _probe_field(state, expression.value, expression.slice.value)
        return field if field is not None else _probe_expression_shape(state, expression)
    if isinstance(expression, (ast.Subscript, ast.ListComp, ast.DictComp)):
        return _probe_expression_shape(state, expression)
    if isinstance(expression, (ast.Constant, ast.UnaryOp)):
        try:
            value = ast.literal_eval(expression)
        except (ValueError, TypeError):
            return _probe_operation_shape(state, expression) if isinstance(expression, ast.UnaryOp) else None
        if value is None or isinstance(value, (int, float, str, bool)):
            return LeafShape(types=(type(value),))
        return None
    if isinstance(expression, (ast.BinOp, ast.Compare, ast.UnaryOp)):
        return _probe_operation_shape(state, expression)
    return None


def _probe_field(state: _LoweringState, parent: ast.expr, attr: str) -> Shape | None:
    """Return the declared contract of a selected field, or `None` without evidence."""
    shape = _probe_shape(state, parent)
    if not isinstance(shape, NamespaceShape):
        return None
    try:
        return shape.select(attr)
    except KeyError:
        return None


def _probe_expression_shape(state: _LoweringState, node: ast.expr) -> Shape | None:
    """Infer a collection expression without placing operations or binding locals."""

    def resolve(expression: ast.expr) -> tuple[str, Shape]:
        assert isinstance(expression, ast.Name)
        shape = _probe_shape(state, expression)
        if shape is None:
            msg = f'unknown expression input `{expression.id}`.'
            raise GraphTypeCheckError(msg)
        return expression.id, shape

    try:
        expression, inputs = compile_expression(node, resolve)
        return infer_expression_shape(expression, inputs)
    except GraphTypeCheckError:
        return None


def _probe_operation_shape(state: _LoweringState, node: ast.BinOp | ast.Compare | ast.UnaryOp) -> Shape | None:
    """Infer an operation result without placing it; `None` means solving stays generic."""
    try:
        operation, raw = _operation_parts(state, node=node)
    except GraphLanguageError:
        return None
    shapes: list[Shape] = []
    for item in raw:
        probed = _probe_shape(state, item)
        if probed is None:
            return None
        shapes.append(probed)
    try:
        return infer_operation_shape(operation, tuple(shapes))
    except GraphTypeCheckError:
        return None


def _probe_wired_type(state: _LoweringState, expression: ast.expr) -> type | None:
    """Return the ORM type a generic-call argument carries, or `None` without evidence."""
    shape = _probe_shape(state, expression)
    if not isinstance(shape, LeafShape) or not shape.types:
        return None
    mapped = [_node_type(kind) for kind in shape.types]
    mapped = [kind for kind in mapped if kind is not None and kind is not type(None)]
    return mapped[0] if len(mapped) == 1 else None


def _solved_spec(
    target: FunctionTaskHandle[t.Any, t.Any] | CalcJobTaskHandle | WorkChainTaskHandle,
    keywords: list[ast.keyword],
    state: _LoweringState,
    *,
    spec: TaskIR,
    result_port: str,
) -> TaskIR:
    """Copy a generic task spec with solved output types, or return it unchanged.

    Solving probes the argument expressions because wiring routes references
    outside the placed inputs, so the placed mapping alone cannot solve.
    """
    typevars, output_var = _typevar_solution(target)
    if output_var is None or not result_port:
        return spec
    kinds: list[type] = []
    tainted = False
    for name in typevars.get(output_var, []):
        keyword = next((keyword for keyword in keywords if keyword.arg == name), None)
        if keyword is None:
            continue
        kind = _probe_wired_type(state, keyword.value)
        if kind is None:
            tainted = True
        else:
            kinds.append(kind)
    if tainted or not kinds or any(kind != kinds[0] for kind in kinds):
        return spec
    merged = dict(spec.declared_outputs.fields)
    merged[result_port] = LeafShape(types=(kinds[0],))
    narrowed = NamespaceShape(fields=tuple(merged.items()))
    return replace(spec, declared_outputs=narrowed)


def _lower_par_map(state: _LoweringState, expression: ast.Call) -> _Reference:
    """Place a fan-out map over an owned container."""
    if isinstance(expression.func, ast.Call):
        msg = (
            'maps take their name from the mapped callable, so the map call itself takes no alias; '
            + "pass the alias on the callable instead, e.g. `par_map(task.alias('name'), values)`"
        )
        _reject(state, node=expression.func, reason=msg)
    func_expr, collection_expr, after_keyword = _bind_par_map_arguments(state, expression=expression)
    partial_use = _partial_call_parts(state, func_expr)
    if partial_use is not None:
        return _lower_partial_map(
            state, partial_use[0], expression, func_expr, collection_expr, after_keyword, partial_use[1]
        )
    target, call_name, explicit = _resolve_callable(state, func_expr)
    if not isinstance(target, (FunctionTaskHandle, CalcJobTaskHandle, WorkChainTaskHandle, GraphHandle)):
        msg = 'maps apply registered declarations per element; pass a task or graph instead'
        _reject(state, node=func_expr, reason=msg)
    if isinstance(target, CalcJobTaskHandle):
        msg = (
            'maps dispatch one child per element with shared inputs, so per-item launch metadata has no placement '
            f'to key by; `CalcJob` task `{call_name}` cannot run under `par_map`; map a task function, '
            'a `WorkChain`, or a nested graph instead'
        )
        _reject(state, node=func_expr, reason=msg)
    mapped_body: GraphIR | None = None
    mapped_spec: TaskIR | None = None
    if explicit is not None:
        instance = _claim_placement(state, explicit, node=func_expr, is_map=True)
    else:
        instance = _claim_placement(state, f'map_{call_name}', node=func_expr, is_map=True)
    if isinstance(target, GraphHandle):
        mapped_body = _lower_graph(target, stack=state.stack)
        mapped_spec = None
    else:
        mapped_body = None
        mapped_spec = target._task_spec
    _check_par_map_callable(state, node=func_expr, label=call_name, spec=mapped_spec, body=mapped_body)
    collection = _lower_value(state, collection_expr)
    container = _check_par_map_collection(state, node=collection_expr, value=collection)
    given: dict[str, _CapturedValue] = {}
    _wire(state, instance=instance, port='collection', value=collection, given=given)
    state.tasks.append(MapControl(name=instance, inputs=given, spec=mapped_spec, body=mapped_body, container=container))
    if after_keyword is not None:
        _wire_after(state, instance=instance, keyword=after_keyword)
    collected = DataList if container == 'list' else DataDict
    return _Reference(instance, port='result', shape=LeafShape(types=(collected,)))


def _captured_kind(captured: _CapturedValue) -> type | None:
    """Return the single ORM type a captured fixed value carries, or ``None`` without evidence."""
    if isinstance(captured, _Reference):
        shape = captured.shape
        if not isinstance(shape, LeafShape) or not shape.types:
            return None
        mapped = [_node_type(kind) for kind in shape.types]
        mapped = [kind for kind in mapped if kind is not None and kind is not type(None)]
        return mapped[0] if len(mapped) == 1 else None
    if isinstance(captured, bool):
        return _node_type(bool)
    if isinstance(captured, int):
        return _node_type(int)
    if isinstance(captured, float):
        return _node_type(float)
    if isinstance(captured, str):
        return _node_type(str)
    return None


def _solved_partial_spec(
    target: FunctionTaskHandle[t.Any, t.Any] | CalcJobTaskHandle | WorkChainTaskHandle,
    binding: _PartialBinding,
    call_keywords: list[ast.keyword],
    state: _LoweringState,
    *,
    spec: TaskIR,
    result_port: str,
) -> TaskIR:
    """Solve a generic partial target combining call-time and fixed evidence.

    Ordinary solving probes the call expressions; a type variable carried only by
    fixed inputs would stay unsolved, so fixed captures contribute their stored
    shapes alongside the call arguments. Conflicting evidence stays unsolved,
    matching the plain-task contract for shared type variables.
    """
    typevars, output_var = _typevar_solution(target)
    if output_var is None or not result_port:
        return spec
    kinds: list[type] = []
    tainted = False
    for name in typevars.get(output_var, []):
        keyword = next((item for item in call_keywords if item.arg == name), None)
        if keyword is not None:
            kind = _probe_wired_type(state, keyword.value)
            if kind is None:
                tainted = True
            else:
                kinds.append(kind)
        elif name in binding.fixed:
            kind = _captured_kind(binding.fixed[name])
            if kind is None:
                tainted = True
            else:
                kinds.append(kind)
    if tainted or not kinds or any(kind != kinds[0] for kind in kinds):
        return spec
    merged = dict(spec.declared_outputs.fields)
    merged[result_port] = LeafShape(types=(kinds[0],))
    narrowed_shape = NamespaceShape(fields=tuple(merged.items()))
    return replace(spec, declared_outputs=narrowed_shape)


def _lower_partial_map(
    state: _LoweringState,
    binding: _PartialBinding,
    expression: ast.Call,
    func_expr: ast.expr,
    collection_expr: ast.expr,
    after_keyword: ast.keyword | None,
    explicit_override: str | None,
) -> _Reference:
    """Place a fan-out map over a partial, binding every input but the element."""
    if isinstance(binding.target, CalcJobTaskHandle):
        msg = (
            'maps dispatch one child per element with shared inputs, so per-item launch metadata has no placement '
            f'to key by; `CalcJob` task `{binding.call_name}` cannot run under `par_map`; map a task function, '
            'a `WorkChain`, or a nested graph instead'
        )
        _reject(state, node=func_expr, reason=msg)
    shape = _partial_target_shape(binding.target, state)
    remaining = [field for field, _ in shape.fields if field not in binding.fixed]
    if len(remaining) != 1:
        msg = (
            f'map `partial` of `{binding.call_name}` binds every input but one, naming the remaining input; '
            + f'{len(remaining)} inputs remain unbound; fix all but one input instead'
        )
        _reject(state, node=func_expr, reason=msg)
    element = remaining[0]
    if 'collection' in binding.fixed and element != 'collection':
        msg = (
            f'map `{binding.call_name}` wires its collection under `collection`, '
            'so a mapped input named `collection` cannot be bound; '
            'map the `collection` input as the element instead'
        )
        _reject(state, node=func_expr, reason=msg)
    mapped_body: GraphIR | None = None
    mapped_spec: TaskIR | None = None
    explicit = explicit_override or binding.explicit
    if explicit is not None:
        instance = _claim_placement(state, explicit, node=func_expr, is_map=True)
    else:
        instance = _claim_placement(state, f'map_{binding.call_name}', node=func_expr, is_map=True)
    if isinstance(binding.target, GraphHandle):
        mapped_body = _lower_graph(binding.target, stack=state.stack)
        mapped_spec = None
    else:
        mapped_body = None
        base_spec = binding.target._task_spec
        mapped_spec = _solved_partial_spec(
            binding.target, binding, [], state, spec=base_spec, result_port=base_spec.result_port
        )
    _check_partial_map_callable(state, node=func_expr, label=binding.call_name, spec=mapped_spec, body=mapped_body)
    collection = _lower_value(state, collection_expr)
    container = _check_par_map_collection(state, node=collection_expr, value=collection)
    given: dict[str, _CapturedValue] = {}
    for port, captured in binding.fixed.items():
        _wire_fixed_value(state, instance, port, captured, given)
    _wire(state, instance=instance, port='collection', value=collection, given=given)
    state.tasks.append(
        MapControl(
            name=instance, inputs=given, spec=mapped_spec, body=mapped_body, container=container, element=element
        )
    )
    if after_keyword is not None:
        _wire_after(state, instance=instance, keyword=after_keyword)
    collected = DataList if container == 'list' else DataDict
    return _Reference(instance, port='result', shape=LeafShape(types=(collected,)))


def _check_partial_map_callable(
    state: _LoweringState, node: ast.AST, label: str, spec: TaskIR | None, body: GraphIR | None
) -> None:
    """Reject partial-mapped callables without exactly one leaf output per element."""
    if spec is not None:
        result_port = spec.result_port
        result_shape: Shape = spec.result_shape
    elif body is not None:
        result_port = body.result_port
        result_shape = body.result_shape
    else:
        msg = (
            'maps collect one output per element into the result container, so the callable returns exactly one value; '
            + f'`{label}` must declare a single output; map a unary task or graph with one output instead'
        )
        _reject(state, node=node, reason=msg)
    if not result_port or not isinstance(result_shape, LeafShape):
        msg = (
            'maps collect one output per element into the result container, so the callable returns exactly one value; '
            + f'`{label}` must declare a single output; map a unary task or graph with one output instead'
        )
        _reject(state, node=node, reason=msg)


def _bind_par_map_arguments(
    state: _LoweringState, expression: ast.Call
) -> tuple[ast.expr, ast.expr, ast.keyword | None]:
    """Bind `par_map(func, values)` positionally or by keyword, separating `after` ordering."""
    after: ast.keyword | None = None
    positional: list[ast.expr] = list(expression.args)
    named: dict[str, ast.expr] = {}
    for keyword in expression.keywords:
        if keyword.arg is None:
            msg = 'inputs wire by name, so spreading hides which is which; pass `func` and `values` explicitly instead.'
            _reject(state, node=keyword, reason=msg)
        if keyword.arg == 'after':
            if after is not None:
                msg = 'one port takes one value; duplicate input `after`; pass it once.'
                _reject(state, node=keyword, reason=msg)
            after = keyword
            continue
        named[keyword.arg] = keyword.value
    for key in ('func', 'values'):
        if key in named and positional:
            msg = f'`{key}` is given twice, positionally and by keyword; pass it once instead.'
            _reject(state, node=expression, reason=msg)
    if positional and named:
        msg = 'pass the callable and the collection positionally as `par_map(func, values)`, or by keyword instead.'
        _reject(state, node=expression, reason=msg)
    if len(positional) == 2:
        return positional[0], positional[1], after
    if len(positional) == 1 or len(positional) > 2 or set(named) != {'func', 'values'}:
        msg = 'maps apply one callable to one collection; call `par_map(func, values)` with both instead.'
        _reject(state, node=expression, reason=msg)
    return named['func'], named['values'], after


def _check_par_map_callable(
    state: _LoweringState, node: ast.AST, label: str, spec: TaskIR | None, body: GraphIR | None
) -> None:
    """Reject mapped callables that are not unary with exactly one leaf output."""
    shape = spec.input_shape if spec is not None else body.input_shape  # type: ignore[union-attr]
    assert isinstance(shape, NamespaceShape)
    if len(shape.fields) != 1:
        msg = (
            'maps wire one element into one input, so the callable takes exactly one input; '
            + f'`{label}` declares {len(shape.fields)} inputs; map a unary task or graph instead'
        )
        _reject(state, node=node, reason=msg)
    result_port = spec.result_port if spec is not None else body.result_port  # type: ignore[union-attr]
    result_shape = spec.result_shape if spec is not None else body.result_shape  # type: ignore[union-attr]
    if not result_port or not isinstance(result_shape, LeafShape):
        msg = (
            'maps collect one output per element into the result container, so the callable returns exactly one value; '
            + f'`{label}` must declare a single output; map a unary task or graph with one output instead'
        )
        _reject(state, node=node, reason=msg)


def _check_par_map_collection(
    state: _LoweringState,
    node: ast.AST,
    value: _Reference | int | float | str | bool | dict[str, _CapturedValue] | None,
) -> t.Literal['list', 'dict']:
    """Reject collections that are not a `DataList`/`DataDict` wire, returning the container kind."""
    if not isinstance(value, _Reference) or not isinstance(value.shape, LeafShape):
        msg = (
            'maps iterate a stored collection, so literals and namespaces cannot drive them; '
            + 'pass a `DataList` or `DataDict` input or task output instead'
        )
        _reject(state, node=node, reason=msg)
    kinds = value.shape.types
    if kinds is not None and len(kinds) == 1 and issubclass(kinds[0], DataList):
        return 'list'
    if kinds is not None and len(kinds) == 1 and issubclass(kinds[0], DataDict):
        return 'dict'
    msg = (
        'maps iterate owned containers element by element, so the collection contract must name its kind; '
        + 'annotate the collection as `DataList` or `DataDict` instead'
    )
    _reject(state, node=node, reason=msg)


def _unsupported_operation_reason() -> str:
    """Explain that only the fixed scalar operators run inline."""
    return (
        'only `+`, `-`, `*`, `//`, `%`, comparisons, and unary `-`, `+`, `not` run inline; '
        + 'put this calculation in a task instead'
    )


def _operation_parts(
    state: _LoweringState, node: ast.BinOp | ast.Compare | ast.UnaryOp
) -> tuple[OperationKind, tuple[ast.expr, ...]]:
    """Split one operation node into its operator and operand expressions."""
    if isinstance(node, ast.BinOp):
        operation = _BINARY_OPERATIONS.get(type(node.op))
        if operation is None:
            _reject(state, node=node, reason=_unsupported_operation_reason())
        return operation, (node.left, node.right)
    if isinstance(node, ast.Compare):
        if len(node.ops) != 1 or len(node.comparators) != 1:
            msg = (
                'comparisons compare two values at a time, so chained comparisons never run; '
                + 'compare two values per line instead'
            )
            _reject(state, node=node, reason=msg)
        if isinstance(node.ops[0], (ast.Is, ast.IsNot)):
            msg = (
                'only `is None`, `is not None`, and `is` against a declared error member are supported; '
                + 'arbitrary `is` identity tests never run; '
                + 'test presence or a declared member instead, or put the comparison in a task'
            )
            _reject(state, node=node, reason=msg)
        operation = _COMPARISON_OPERATIONS.get(type(node.ops[0]))
        if operation is None:
            _reject(state, node=node, reason=_unsupported_operation_reason())
        return operation, (node.left, node.comparators[0])
    operation = _UNARY_OPERATIONS.get(type(node.op))
    if operation is None:
        _reject(state, node=node, reason=_unsupported_operation_reason())
    return operation, (node.operand,)


def _operand_shape(value: _Reference | int | float | str | bool | None) -> Shape:
    """Return the static contract of a lowered operand."""
    if isinstance(value, _Reference):
        return value.shape
    return LeafShape(types=(type(value),))


def _lower_operand(state: _LoweringState, expression: ast.expr) -> _Reference | int | float | str | bool | None:
    """Lower one operation operand, rejecting hidden placements."""
    if isinstance(expression, ast.Call):
        msg = 'nested calls hide a placement; put the inner call on its own line first'
        _reject(state, node=expression, reason=msg)
    # Signed literals fold in `_lower_value`; anything else unary places an operation there.
    return _lower_value(state, expression)


def _const_task(state: _LoweringState, reference: _Reference) -> InlineOperation | None:
    """Return the `const` placement a reference resolves to, or `None` for other wires."""
    if reference.task is None:
        return None
    for placed in state.tasks:
        if placed.name == reference.task:
            return placed if isinstance(placed, InlineOperation) and placed.operation == 'const' else None
    return None


def _reject_const_return(state: _LoweringState, reference: _Reference, node: ast.AST) -> None:
    """Reject a bound scalar literal as a root graph output.

    Constants are ephemeral orchestration state, never stored data: returning one would publish
    a value with no creating task, breaking the rule that workflows return existing data while
    only tasks create new data. Only the root return is rejected here: a nested graph lowers
    through this same path with a deeper stack, and may thread constants as control state for
    its caller to consume, with the runtime root boundary still guarding the final outputs.
    """
    if len(state.stack) != 1 or _const_task(state, reference) is None:
        return
    msg = (
        'graphs return existing nodes rather than creating data; '
        + 'this name binds a scalar constant held as orchestration state, not a stored node; '
        + 'create the value in a `@task` and return the task output instead'
    )
    _reject(state, node=node, reason=msg)


def _place_constant(state: _LoweringState, *, value: int | float | str | bool | None, node: ast.AST) -> _Reference:
    """Bind one scalar literal as ephemeral orchestration state, returning its result.

    The literal is finite JSON by the time it arrives here (`_lower_value` validates), so the
    placement checkpoints with the scope and serializes with the template, but the runtime
    evaluates it to a plain Python value that is never stored or linked.
    """
    try:
        result_shape = const_result_shape(value)
    except GraphTypeCheckError as exception:
        _reject(state, node=node, reason=str(exception))
    instance = _claim_name(state, f'constant_{len(state.tasks) + 1}')
    state.tasks.append(
        InlineOperation(
            name=instance,
            inputs={CONSTANT_PORT: value},
            operation='const',
            input_shape=NamespaceShape(fields=((CONSTANT_PORT, result_shape),)),
            result_shape=result_shape,
        )
    )
    return _Reference(instance, port=RESULT_PORT, shape=result_shape)


def _place_operation(
    state: _LoweringState,
    *,
    operation: OperationKind,
    operands: tuple[_Reference | int | float | str | bool | None, ...],
    node: ast.AST,
) -> _Reference:
    """Infer, place, and wire one inline operation, returning its result."""
    shapes = tuple(_operand_shape(value) for value in operands)
    try:
        result_shape = infer_operation_shape(operation, shapes)
    except GraphTypeCheckError as exception:
        _reject(state, node=node, reason=str(exception))
    ports = (LEFT_PORT, RIGHT_PORT) if len(operands) == 2 else (OPERAND_PORT,)
    instance = _claim_name(state, f'operation_{len(state.tasks) + 1}')
    given: dict[str, _CapturedValue] = {}
    for port, value in zip(ports, operands, strict=True):
        _wire(state, instance=instance, port=port, value=value, given=given)
    state.tasks.append(
        InlineOperation(
            name=instance,
            inputs=given,
            operation=operation,
            input_shape=NamespaceShape(fields=tuple(zip(ports, shapes, strict=True))),
            result_shape=result_shape,
        )
    )
    return _Reference(instance, port=RESULT_PORT, shape=result_shape)


def _place_expression(state: _LoweringState, node: ast.expr) -> _Reference:
    """Place a pure collection expression with captured wires and lexically scoped locals."""
    references: dict[str, _Reference] = {}

    def resolve(expression: ast.expr) -> tuple[str, Shape]:
        assert isinstance(expression, ast.Name)
        reference = _lower_value(state, expression)
        assert isinstance(reference, _Reference)
        references[expression.id] = reference
        return expression.id, reference.shape

    try:
        expression, inputs = compile_expression(node, resolve)
        result = infer_expression_shape(expression, inputs)
        if not isinstance(result, LeafShape):
            msg = 'inline collection expressions produce one value, not an output namespace.'
            raise GraphTypeCheckError(msg)
    except GraphTypeCheckError as exception:
        _reject(state, node=node, reason=str(exception))
    instance = _claim_name(state, f'expression_{len(state.tasks) + 1}')
    given: dict[str, _CapturedValue] = {}
    for port, reference in references.items():
        _wire(state, instance=instance, port=port, value=reference, given=given)
    state.tasks.append(
        InlineOperation(
            name=instance,
            operation='expression',
            expression=expression,
            inputs=given,
            input_shape=NamespaceShape(fields=tuple(inputs.items())),
            result_shape=result,
        )
    )
    return _Reference(instance, port=RESULT_PORT, shape=result)


def _lower_operation(state: _LoweringState, node: ast.BinOp | ast.Compare | ast.UnaryOp) -> _Reference:
    """Place one inline operation and return its result reference.

    Supported presence and member tests lower to ephemeral boolean control values through the
    branch machinery instead of computing inline, so `x is y` arbitrary identities still reject
    below while `value is None` and declared members return booleans. Operands lower first, so
    nested operations become their own placements with dependency wires into the outer one.
    Primitive results are orchestration state, never `Data` nodes: the placement only records
    the operator and its operand contracts for the engine.
    """
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        predicate = _lower_predicate_value(state, node, node=node)
        if predicate is not None:
            return predicate
    if isinstance(node, ast.Compare) and isinstance(node.ops[0], (ast.Is, ast.IsNot)):
        predicate = _lower_predicate_value(state, node, node=node)
        if predicate is not None:
            return predicate
    operation, raw = _operation_parts(state, node=node)
    lowered = tuple(_lower_operand(state, item) for item in raw)
    return _place_operation(state, operation=operation, operands=lowered, node=node)


def _is_catch_error(state: _LoweringState, expression: ast.Call) -> bool:
    """Recognize the intrinsic by identity, including imported aliases."""
    try:
        target, _ = _resolve_base(state, expression.func)
    except GraphLanguageError:
        return False
    return target is catch_error


def _place_invocation(
    state: _LoweringState,
    expression: ast.Call,
    task: ProcessTask | SubgraphTask,
    result_port: str,
    result_shape: Shape,
    *,
    capture: bool,
    unpack: bool,
) -> _Reference:
    """Select the invocation's success shape or its explicitly captured pair."""
    errors = task.spec.result_errors if isinstance(task, ProcessTask) else task.body.declared_errors
    if capture:
        if not errors:
            _reject(state, node=expression, reason='`catch_error` requires an invocation with declared failures')
        task = replace(task, capture_error=True)
        if isinstance(task, ProcessTask):
            assert isinstance(result_shape, NamespaceShape)
            result_shape = result_shape.select('value')
        result_port = ''
        result_shape = NamespaceShape(
            fields=(
                ('value', replace(result_shape, required=False)),
                ('error', LeafShape(types=(EnumData,), required=False, error_enums=frozenset(errors))),
            )
        )
    elif isinstance(task, ProcessTask) and errors:
        if unpack:
            _reject(
                state,
                node=expression,
                reason='bare Result calls expose only success; use `value, error = catch_error(call(...))` '
                'to unpack or bind the success to one name and select its fields',
            )
        assert isinstance(result_shape, NamespaceShape)
        result_shape = replace(result_shape.select('value'), required=not task.spec.result_nullable)
        result_port = 'value'
    state.tasks.append(task)
    return _Reference(task.name, port=result_port, shape=result_shape)


def _lower_call(
    state: _LoweringState, expression: ast.expr, *, capture: bool = False, unpack: bool = False
) -> _Reference:
    """Place a task or graph call with wired graph inputs."""
    assert isinstance(expression, ast.Call)
    if _is_catch_error(state, expression):
        _reject(state, node=expression, reason='use `value, error = catch_error(call(...))` in a tuple assignment')
    partial_use = _partial_call_parts(state, expression.func)
    if partial_use is not None:
        binding, explicit_override = partial_use
        return _lower_partial_call(state, binding, expression, explicit_override, capture=capture, unpack=unpack)
    target, name, explicit = _resolve_callable(state, expression.func)
    if target is par_map:
        if capture:
            _reject(state, node=expression, reason='`catch_error` captures only direct task or graph invocations')
        return _lower_par_map(state, expression)
    assert isinstance(target, (FunctionTaskHandle, CalcJobTaskHandle, WorkChainTaskHandle, GraphHandle))
    if explicit is not None:
        instance = _claim_placement(state, explicit, node=expression)
    else:
        instance = _claim_placement(state, name=name, node=expression)
    if isinstance(target, GraphHandle):
        body: GraphIR = _lower_graph(target, stack=state.stack)
        task: ProcessTask | SubgraphTask = SubgraphTask(name=instance, inputs={}, body=body)
        inputs: NamespaceShape = body.input_shape
        result_port: str = body.result_port
        result_shape: Shape = body.result_shape
    else:
        spec = target._task_spec
        if isinstance(target, CalcJobTaskHandle):
            names = [field for field, _ in spec.input_shape.fields]
            assert 'metadata' not in names, 'CalcJob metadata must stay out of the graph contract'
        task = ProcessTask(name=instance, inputs={}, spec=spec)
        inputs = spec.input_shape
        result_port = spec.result_port
        result_shape = spec.result_shape
    keywords: list[ast.keyword] = _bind_positional(state, expression=expression, name=name, inputs=inputs)
    if isinstance(target, GraphHandle):
        given = _lower_keywords(state, instance=instance, name=name, inputs=inputs, keywords=keywords)
        task = replace(task, inputs=given)
    else:
        spec = target._task_spec
        narrowed = _solved_spec(target, keywords, state, spec=spec, result_port=result_port)
        given = _lower_keywords(state, instance=instance, name=name, inputs=inputs, keywords=keywords)
        task = ProcessTask(name=instance, inputs=given, spec=narrowed)
        if narrowed is not spec:
            result_shape = narrowed.result_shape
    if isinstance(task, ProcessTask):
        runtime_paths = task.spec.runtime_input_paths()
    else:
        runtime_paths = frozenset()
    missing: list[str] = _missing_required_inputs(
        state, instance=instance, shape=inputs, given=task.inputs, runtime_paths=runtime_paths
    )
    if missing:
        msg = (
            'required inputs must be wired before the graph is stored; '
            + f'task {name!r} is missing required inputs: {missing}; pass them as call arguments'
        )
        _reject(state, node=expression, reason=msg)
    return _place_invocation(state, expression, task, result_port, result_shape, capture=capture, unpack=unpack)


def _bind_positional(
    state: _LoweringState, expression: ast.Call, name: str, inputs: NamespaceShape
) -> list[ast.keyword]:
    """Bind positional arguments through declared input order, like the explicit keywords."""
    if not expression.args:
        keywords = list(expression.keywords)
    else:
        order: list[str] = [field for field, _ in inputs.fields]
        if len(expression.args) > len(order):
            msg = (
                'positional arguments follow declared input order, so extras map to nothing; '
                + f'too many positional arguments for `{name}`; drop the extras'
            )
            _reject(state, node=expression, reason=msg)
        keywords = [ast.keyword(arg=field, value=arg) for field, arg in zip(order, expression.args)]
        keywords.extend(expression.keywords)
    if any(keyword.arg is None for keyword in keywords):
        keywords = _spread_keywords(state, expression=expression, name=name, inputs=inputs, keywords=keywords)
    return keywords


def _spread_keywords(
    state: _LoweringState, *, expression: ast.Call, name: str, inputs: NamespaceShape, keywords: list[ast.keyword]
) -> list[ast.keyword]:
    """Expand `**bundle` against the target contract; every wire must resolve exactly once."""
    explicit = {keyword.arg for keyword in keywords if keyword.arg is not None}
    spread_at: dict[str, str] = {}
    expanded: list[ast.keyword] = []
    for keyword in keywords:
        if keyword.arg is not None:
            expanded.append(keyword)
            continue
        label = keyword.value.id if isinstance(keyword.value, ast.Name) else '<value>'
        reference = _lower_value(state, keyword.value)
        if not isinstance(reference, _Reference) or not isinstance(reference.shape, NamespaceShape):
            msg = (
                'spreading copies a whole namespace wire by wire, so only a namespace-typed name spreads; '
                + f'`{label}` is not a namespace; wire its ports one by one instead'
            )
            _reject(state, node=keyword, reason=msg)
        for field_name, _ in reference.shape.fields:
            if not any(field_name == target for target, _ in inputs.fields):
                msg = (
                    f'`**{label}` field `{field_name}` matches no input of `{name}`; '
                    + 'spread a namespace matching the task inputs instead'
                )
                _reject(state, node=keyword, reason=msg)
        provides = {field_name for field_name, _ in reference.shape.fields}
        for field_name, _ in inputs.fields:
            if field_name not in provides:
                continue
            if field_name in explicit:
                msg = f'`{field_name}` is given twice, explicitly and through `**{label}`; ' + 'pass it once instead'
                _reject(state, node=keyword, reason=msg)
            if field_name in spread_at:
                msg = (
                    f'`{field_name}` is given twice, through `**{spread_at[field_name]}` and `**{label}`; '
                    + 'pass it once instead'
                )
                _reject(state, node=keyword, reason=msg)
            spread = ast.keyword(
                arg=field_name,
                value=ast.Attribute(value=keyword.value, attr=field_name, ctx=ast.Load()),
            )
            ast.copy_location(spread, keyword)
            ast.copy_location(spread.value, keyword)
            spread_at[field_name] = label
            expanded.append(spread)
    return expanded


def _wire_after(state: _LoweringState, instance: str, keyword: ast.keyword) -> None:
    """Wire ordering edges from an `after` argument."""
    ordered: list[ast.expr] = (
        keyword.value.elts if isinstance(keyword.value, (ast.Tuple, ast.List)) else [keyword.value]
    )
    for predecessor in ordered:
        reference = _lower_value(state, expression=predecessor)
        if not isinstance(reference, _Reference) or reference.task is None:
            msg = (
                'ordering edges run between placed tasks, not values; '
                + 'after needs a task from an earlier line instead'
            )
            _reject(state, node=predecessor, reason=msg)
        state.dependencies.append(Dependency(reference.task, target=instance))


def _lower_keywords(
    state: _LoweringState, instance: str, name: str, inputs: NamespaceShape, keywords: list[ast.keyword]
) -> dict[str, _CapturedValue]:
    """Wire one call's arguments to literals, references, and ordering edges."""
    given: dict[str, _CapturedValue] = {}
    seen: set[str] = set()
    for keyword in keywords:
        port = keyword.arg
        assert port is not None
        if port in seen:
            msg = 'one port takes one value; ' + f'duplicate input {port!r}; pass it once'
            _reject(state, node=keyword, reason=msg)
        seen.add(port)
        if port == 'after':
            _wire_after(state, instance=instance, keyword=keyword)
            continue
        try:
            shape = inputs.select(port)
        except KeyError:
            msg = (
                'calls wire against declared contracts; '
                + f'{port!r} is not an input of {name!r}; check the spelling instead'
            )
            _reject(state, node=keyword, reason=msg)
        _lower_input(state, instance=instance, path=port, expression=keyword.value, shape=shape, given=given)
    return given


def _missing_required_inputs(
    state: _LoweringState,
    instance: str,
    shape: NamespaceShape,
    given: t.Any,
    prefix: str = '',
    runtime_paths: frozenset[str] = frozenset(),
) -> list[str]:
    """Return the required task inputs that are neither wired nor routed from graph inputs.

    Unwired configuration-capable inputs stay buildable: explicit wiring owns an
    input, otherwise an externally bindable one may arrive through `runtime_config`,
    so only workflow-owned inputs are reported here.
    """
    missing: list[str] = []
    mapping = given if isinstance(given, Mapping) else {}
    for field_name, child in shape.fields:
        path = f'{prefix}.{field_name}' if prefix else field_name
        if isinstance(child, NamespaceShape):
            missing.extend(
                _missing_required_inputs(
                    state,
                    instance=instance,
                    shape=child,
                    given=mapping.get(field_name),
                    prefix=path,
                    runtime_paths=runtime_paths,
                )
            )
        elif (
            child.required
            and field_name not in mapping
            and not _is_routed(state, instance=instance, path=path)
            and not _covered_by_runtime(path, runtime_paths)
        ):
            missing.append(path)
    return missing


def _covered_by_runtime(path: str, runtime_paths: frozenset[str]) -> bool:
    """Return whether an unwired input path sits at or beneath a runtime prefix."""
    return any(path == prefix or path.startswith(f'{prefix}.') for prefix in runtime_paths)


def _is_routed(state: _LoweringState, instance: str, path: str) -> bool:
    """Return whether a wired value reaches a task input."""
    routed = [entry for targets in state.inputs.values() for target, entry in targets if target == instance]
    if any(path == entry or path.startswith(f'{entry}.') for entry in routed):
        return True
    return any(
        edge.target == instance
        and edge.target_port is not None
        and (edge.target_port == path or path.startswith(f'{edge.target_port}.'))
        for edge in state.dependencies
    )


def _wire(
    state: _LoweringState,
    instance: str,
    port: str,
    value: _Reference | int | float | str | bool | None,
    given: dict[str, t.Any],
) -> None:
    """Route a literal, input, or task output into a placement."""
    if not isinstance(value, _Reference):
        _place(given, port, value)
    elif value.task is None:
        state.inputs.setdefault(value.port, []).append(Route(instance, port=port))
    else:
        state.dependencies.append(Dependency(value.task, target=instance, source_port=value.port, target_port=port))


def _lower_input(
    state: _LoweringState,
    instance: str,
    path: str,
    expression: ast.expr,
    shape: Shape,
    given: dict[str, _CapturedValue],
) -> None:
    """Expand dictionary syntax only for declared fixed input namespaces.

    An explicit `None` means absent unless the contract accepts it, so dropped
    `None` literals read as not provided.
    """
    if isinstance(expression, ast.Constant) and expression.value is None and _drops_none_value(shape):
        return
    if isinstance(expression, ast.Dict) and isinstance(shape, NamespaceShape):
        _place(given, path, {})
        seen: set[str] = set()
        for key, value in zip(expression.keys, expression.values, strict=True):
            if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
                msg = (
                    'dictionary syntax for fixed namespaces must be known before anything runs; '
                    + 'namespace keys must be string literals without unpacking; compute dynamic keys in tasks'
                )
                _reject(state, node=expression, reason=msg)
            name: str = key.value
            if name in seen:
                msg = 'one port takes one value; ' + f'duplicate input {name!r}; pass it once'
                _reject(state, node=expression, reason=msg)
            try:
                child = shape.select(name)
            except KeyError:
                msg = (
                    'namespaces wire against declared contracts; '
                    + f'{name!r} is not a declared name here; check the spelling instead'
                )
                _reject(state, node=expression, reason=msg)
            seen.add(name)
            _lower_input(state, instance=instance, path=f'{path}.{name}', expression=value, shape=child, given=given)
        return
    if isinstance(expression, ast.Dict):
        try:
            value = ast.literal_eval(expression)
        except (ValueError, TypeError):
            for key, item in zip(expression.keys, expression.values, strict=True):
                try:
                    ast.literal_eval(item)
                except (ValueError, TypeError):
                    name = f' `{key.value}`' if isinstance(key, ast.Constant) and isinstance(key.value, str) else ''
                    msg = (
                        'dictionary syntax for fixed namespaces must be known before anything runs; '
                        + f'dictionary entry{name} must be a literal value; '
                        + 'compute it in a task or pass the whole mapping instead'
                    )
                    _reject(state, node=item, reason=msg)
            msg = (
                'a mapping here either spells out fixed inputs or points at a whole input, nothing in between; '
                + 'dictionary-valued ports require a literal value or a reference to the whole port'
            )
            _reject(state, node=expression, reason=msg)
        try:
            checked = json_default(value)
        except GraphTypeCheckError:
            msg = (
                'stored inputs only hold finite JSON values; dictionary values must be finite JSON, '
                + 'so compute non-finite values in tasks instead'
            )
            _reject(state, node=expression, reason=msg)
        _place(given, path, checked)
        return
    _wire(state, instance=instance, port=path, value=_lower_value(state, expression), given=given)


def _lower_value(
    state: _LoweringState, expression: ast.expr, *, allow_call: bool = False
) -> _Reference | int | float | str | bool | None:
    """Lower a value expression to a reference or literal."""
    if allow_call and isinstance(expression, ast.Call):
        return _lower_call(state, expression=expression)
    if isinstance(expression, (ast.ListComp, ast.DictComp)):
        return _place_expression(state, expression)
    if isinstance(expression, ast.Subscript):
        parent_shape = _probe_shape(state, expression.value)
        if not isinstance(parent_shape, NamespaceShape):
            return _place_expression(state, expression)
    if isinstance(expression, ast.BoolOp):
        return _lower_boolop(state, node=expression)
    if isinstance(expression, ast.IfExp):
        return _lower_ifexp(state, node=expression)
    if isinstance(expression, (ast.BinOp, ast.Compare)):
        return _lower_operation(state, node=expression)
    if isinstance(expression, ast.Name):
        if expression.id not in state.names:
            namespace = state.definition.symbols.values
            if expression.id in namespace:
                msg = (
                    'module-global values are not wires; '
                    + f'{expression.id!r} lives outside the graph body; pass it as a graph input instead'
                )
                _reject(state, node=expression, reason=msg)
            msg = (
                'names only exist after a call or an input introduces them; '
                + f'{expression.id!r} is not known here; assign it on an earlier line instead'
            )
            _reject(state, node=expression, reason=msg)
        return state.names[expression.id]
    if isinstance(expression, ast.Attribute):
        return _select_field(state, expression.value, expression.attr, expression, allow_call=allow_call)
    if (
        isinstance(expression, ast.Subscript)
        and isinstance(expression.slice, ast.Constant)
        and isinstance(expression.slice.value, str)
    ):
        return _select_field(state, expression.value, expression.slice.value, expression, allow_call=allow_call)
    if isinstance(expression, (ast.Constant, ast.UnaryOp)):
        try:
            value = ast.literal_eval(expression)
        except (ValueError, TypeError):
            if isinstance(expression, ast.UnaryOp):
                return _lower_operation(state, node=expression)
            _reject(state, node=expression, reason=_unsupported_reason(expression))
        if value is None or isinstance(value, (int, float, str, bool)):
            try:
                # Validate finiteness; valid values pass through unchanged below.
                json_default(value)
            except GraphTypeCheckError:
                msg = (
                    'literals are saved with the graph, which only holds finite values; '
                    + 'inline numbers must be finite; compute non-finite values in tasks instead'
                )
                _reject(state, node=expression, reason=msg)
            return value
    _reject(state, node=expression, reason=_unsupported_reason(expression))


def _unsupported_reason(expression: ast.expr) -> str:
    """Explain one unsupported expression with its working alternative."""
    for kinds, guidance in _VALUE_REJECTIONS.items():
        if isinstance(expression, kinds):
            return guidance
    return 'put this calculation in a task instead'


def _select_field(
    state: _LoweringState, parent: ast.expr, attr: str, node: ast.AST, *, allow_call: bool = False
) -> _Reference:
    """Resolve a named field on a task output or a declared namespace."""
    reference = _lower_value(state, parent, allow_call=allow_call)
    if not isinstance(reference, _Reference):
        msg = (
            'field selection starts from a wire with declared fields; ' + 'pick a task output or an input group instead'
        )
        _reject(state, node=node, reason=msg)
    if not isinstance(reference.shape, NamespaceShape):
        if reference.task is not None and reference.port == attr:
            return reference
        assert isinstance(node, ast.expr)
        return _place_expression(state, node)
    path = f'{reference.port}.{attr}' if reference.port else attr
    try:
        shape = reference.shape.select(attr)
    except KeyError:
        msg = (
            'selection follows the declared inputs and outputs; '
            + f'{path!r} is not a declared field; check the spelling instead'
        )
        _reject(state, node=node, reason=msg)
    return _Reference(reference.task, port=path, shape=shape)


def compile_graph(handle: GraphHandle) -> GraphIR:
    """Lower a handle to its cached template without executing or storing anything.

    Core-only compilation entrypoint for the engine, shapes, IR tooling, and
    tests. Not re-exported through the user API: user code validates with
    `GraphHandle.build`, which returns `None`, and launches with `run` or
    `submit`. Compiling fabricates no `Data` nodes; it only reads declared
    annotations and source.

    :param handle: the graph handle to compile.
    :return: the cached static template.
    """
    if handle._template is None:
        handle._template = _lower_graph(handle, stack=())
    return handle._template


def _lower_graph(handle: GraphHandle, stack: tuple[str, ...]) -> GraphIR:
    """Lower a graph and its callees, rejecting recursive calls."""
    definition = handle._definition
    key = definition.key
    if key in stack:
        msg = (
            "a call copies the callee's placements into the graph, so self-reference never ends; "
            + f'Recursive graph call: {" -> ".join((*stack, key))}; express repetition with a while loop instead'
        )
        raise GraphLanguageError(msg)
    return _lower_function(_LoweringState(definition, stack=(*stack, key)))
