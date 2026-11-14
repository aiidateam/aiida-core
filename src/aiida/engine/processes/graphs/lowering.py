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
import textwrap
import typing as t
from collections import Counter
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass, field, replace
from types import UnionType

from aiida.common.exceptions import GraphError, GraphLanguageError, GraphTypeCheckError, GraphValidationError
from aiida.common.links import validate_link_label
from aiida.common.loaders import get_object_loader
from aiida.engine.processes.calcjobs import CalcJob
from aiida.engine.processes.exit_code import ExitCodeEnum
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
    PortDeclaration,
    WorkChainTaskHandle,
    _build_task,
    _typevar_solution,
)
from aiida.engine.processes.ports import _node_type
from aiida.engine.processes.workchains.workchain import WorkChain
from aiida.orm import Bool, DataDict, DataList

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
    (ast.BoolOp,): (
        'operators compute a new value, which only a task can create and record; '
        + 'put this check in a task and use its result instead'
    ),
    (ast.IfExp,): 'an inline conditional evaluates Python instead of branching; write this as if and else instead',
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
    """An importable source declaration that builds without executing its body."""

    def __init__(self, function: Callable[P, R]) -> None:
        self._definition: _SourceDefinition = _SourceDefinition.capture(function)
        self._template: GraphIR | None = None
        # Copy name and docstring, not the function state: the handle owns its identifier.
        functools.update_wrapper(self, function, updated=())

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        msg = f'`{self.identifier}` declares a graph; launch it with `run` or `submit`.'
        raise GraphError(msg)

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
        Per-placement `CalcJob` options ride under `task_metadata`; standard `metadata` passes through.
        """
        # `task_metadata` carries per-placement `CalcJob` options, not graph inputs.
        task_metadata = inputs.pop('task_metadata', None)
        metadata = inputs.pop('metadata', None)
        if isinstance(metadata, Mapping) and any(
            key != 'options' and isinstance(value, Mapping) and 'options' in value for key, value in metadata.items()
        ):
            msg = (
                'per-placement options ride under `task_metadata`, keyed by placement name; '
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
            compile_graph(self), dict(bound.arguments), task_metadata=task_metadata
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


@dataclass(frozen=True)
class _Reference:
    """A parsed reference to a leaf or fixed input namespace."""

    task: str | None  # None denotes a graph input.
    port: str
    shape: Shape


_CapturedValue: t.TypeAlias = '_Reference | int | float | str | bool | dict[str, _CapturedValue] | None'
_ReferenceTree: t.TypeAlias = '_Reference | dict[str, _ReferenceTree]'


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

    Accepts a task function, a `CalcJob` subclass, or a `WorkChain` subclass; task inputs
    wire task outputs and graph inputs alike. `CalcJob` tasks read their metadata from the
    launch inputs instead.

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
    outputs: dict[str, OutputTree] = {name: _endpoint_tree(reference) for name, reference in references.items()}
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


def _endpoint_tree(reference: _ReferenceTree) -> OutputTree:
    """Expand a leaf or namespace reference to endpoints regrouping existing nodes.

    Namespaces regroup their existing leaves instead of creating data; every leaf
    keeps its stored node, so workflows return but never create data.
    """
    if isinstance(reference, dict):
        return {name: _endpoint_tree(item) for name, item in reference.items()}
    if isinstance(reference.shape, NamespaceShape):
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
    if not names or len(names) != len(target.elts) or (not rebind and any(name in state.names for name in names)):
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
    ref: _Reference = _lower_call(state, expression=statement.value)
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
            state.names[name] = _Reference(ref.task, port=field_name, shape=field_shape)


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


def _lower_branch(state: _LoweringState, statement: ast.If) -> str:
    """Lower an if statement to a branch control task, returning the exposed wire."""
    _check_branch_shape(state, statement=statement)
    test: ast.expr = statement.test
    if isinstance(test, ast.Call):
        test = _bind_test_condition(state, test=test)
    condition_test: t.Literal['truthy', 'is_none', 'is_not_none', 'is_member', 'is_not_member'] = 'truthy'
    condition_member: tuple[str, str] | None = None
    if (none_test := _match_none_test(test)) is not None:
        test, condition_test = none_test
    elif (matched := _match_member_test(state, test)) is not None:
        test, condition_test, condition_member = matched
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
    state.names[first.name] = _Reference(instance, port=carried, shape=selected.shape)
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
    resolved = state.definition.function.__globals__.get(base.id)
    return resolved if isinstance(resolved, type) and issubclass(resolved, enum.Enum) else None


def _known_name(state: _LoweringState, node: ast.expr) -> bool:
    """Return whether a name or dotted path starts from a known wire or module."""
    base, _ = _attribute_path(node)
    if not isinstance(base, ast.Name):
        return True
    return base.id in state.names or base.id in state.definition.function.__globals__


def _resolve_enum_member(state: _LoweringState, node: ast.expr) -> tuple[str, str] | None:
    """Return the enum identifier and member name behind a reference, or `None`."""
    base, parts = _attribute_path(node)
    # A base shadowing an enclosing wire stays a wire, as with dotted calls.
    if not isinstance(base, ast.Name) or base.id in state.names:
        return None
    try:
        resolved: t.Any = state.definition.function.__globals__[base.id]
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
    read = {path.split('.')[0] for side in (first, second) for path in side.child.inputs}
    for name in sorted(read):
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
    elif isinstance(test, (ast.BinOp, ast.Compare, ast.UnaryOp)) and _identity_compare(test) is None:
        # Numeric inline operations bind to a boolean wire and recompute each pass;
        # `is`/`is not` presence and member tests stay branch-only, since loop
        # control carries a truthy check rather than a member selection.
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
    """Return whether a region call targets the `par_map` authoring operation, without rejecting."""
    try:
        if isinstance(node.func, ast.Attribute):
            target, _ = _resolve_dotted(state, expression=node)
            return target is par_map
        if isinstance(node.func, ast.Name):
            return state.definition.function.__globals__.get(node.func.id) is par_map
    except GraphLanguageError:
        return False
    return False


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
        # Dotted calls read through a module, not a wire; a base shadowing an
        # enclosing wire stays a read so the call rejects the ambiguity.
        func: ast.expr = node.func
        while isinstance(func, ast.Attribute):
            func = func.value
        if isinstance(func, ast.Name) and func.id not in enclosing:
            callees.add(id(func))
        if _is_par_map_call(state, node):
            callable_expr = _par_map_callable_expr(node)
            if isinstance(callable_expr, ast.Name):
                callees.add(id(callable_expr))
            elif isinstance(callable_expr, ast.Attribute):
                for inner in ast.walk(callable_expr):
                    if isinstance(inner, ast.Name) and isinstance(inner.ctx, ast.Load) and inner.id not in enclosing:
                        callees.add(id(inner))
    return callees


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


def _bind_test_condition(state: _LoweringState, test: ast.Call | ast.BinOp | ast.Compare | ast.UnaryOp) -> ast.Name:
    """Lower a call or inline comparison test to a fresh binding."""
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


def _call_target_name(state: _LoweringState, expression: ast.expr) -> str:
    """Return the placement name of a direct call, rejecting shadowed or indirect calls."""
    if not isinstance(expression, ast.Call):
        msg = (
            'calls resolve by module-level name to importable declarations; '
            + 'call tasks and graphs by their plain names instead'
        )
        _reject(state, node=expression, reason=msg)
    if isinstance(expression.func, ast.Name):
        if expression.func.id in state.names:
            msg = (
                'a name cannot be both a wire and a declaration; '
                + f'{expression.func.id!r} is also used as a result name; rename one of them instead'
            )
            _reject(state, node=expression, reason=msg)
        return expression.func.id
    if isinstance(expression.func, ast.Attribute):
        return _dotted_name(state, expression=expression)
    msg = (
        'calls resolve by module-level name to importable declarations; '
        + 'call tasks and graphs by their plain names instead'
    )
    _reject(state, node=expression, reason=msg)


def _split_dotted(expression: ast.Call) -> tuple[str, list[str]] | None:
    """Split a dotted call target into its base name and attributes, innermost first."""
    if not isinstance(expression.func, ast.Attribute):
        return None
    node: ast.expr = expression.func
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    return node.id, parts


def _dotted_name(state: _LoweringState, expression: ast.Call) -> str:
    """Return the last attribute of a dotted call target like `my_module.add`."""
    split = _split_dotted(expression)
    if split is None:
        msg = (
            'calls resolve by module-level name to importable declarations; '
            + 'call tasks and graphs by their plain names instead'
        )
        _reject(state, node=expression, reason=msg)
    base, parts = split
    if base in state.names:
        msg = (
            'a name cannot be both a wire and a declaration; '
            + f'{base!r} is also used as a result name; rename one of them instead'
        )
        _reject(state, node=expression, reason=msg)
    return parts[0]


def _registered_target(
    state: _LoweringState, expression: ast.expr, name: str
) -> FunctionTaskHandle[t.Any, t.Any] | CalcJobTaskHandle | WorkChainTaskHandle | GraphHandle:
    """Return the task handle or graph behind a call target."""
    namespace = state.definition.function.__globals__
    label = name
    if isinstance(expression, ast.Call) and isinstance(expression.func, ast.Attribute):
        target, label = _resolve_dotted(state, expression=expression)
    else:
        target = namespace.get(name)
    if isinstance(target, (FunctionTaskHandle, CalcJobTaskHandle, WorkChainTaskHandle, GraphHandle)):
        return target
    if target is None and label in vars(builtins):
        msg = (
            'built-ins run as plain Python with no record kept; '
            + f'built-in {label!r} cannot run here; wrap it in a task instead'
        )
        _reject(state, node=expression, reason=msg)
    if target is None and label not in namespace:
        msg = 'calls must name an importable declaration; ' + f'unknown name {label!r}; check the spelling instead'
        _reject(state, node=expression, reason=msg)
    msg = (
        'only registered declarations carry input and output contracts; '
        + f'unregistered call {label!r}; add `@task` or `@graph` above it instead'
    )
    _reject(state, node=expression, reason=msg)


def _resolve_dotted(state: _LoweringState, expression: ast.Call) -> tuple[t.Any, str]:
    """Resolve a dotted call target through modules, returning the declaration and its path."""
    split = _split_dotted(expression)
    assert split is not None, 'dotted targets are validated before resolution'
    base, parts = split
    namespace = state.definition.function.__globals__
    dotted = '.'.join([base, *reversed(parts)])
    target = namespace.get(base)
    if target is None:
        msg = 'calls must name an importable declaration; ' + f'unknown name {dotted!r}; check the spelling instead'
        _reject(state, node=expression, reason=msg)
    if not inspect.ismodule(target):
        msg = (
            'calls resolve through modules to registered declarations; '
            + f'{base!r} is not a module; import the module instead'
        )
        _reject(state, node=expression, reason=msg)
    for attr in reversed(parts):
        target = getattr(target, attr, None)
        if target is None:
            msg = 'calls must name an importable declaration; ' + f'unknown name {dotted!r}; check the spelling instead'
            _reject(state, node=expression, reason=msg)
    return target, dotted


def _claim_name(state: _LoweringState, name: str) -> str:
    """Return a placement name unused by earlier placements."""
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
        return _probe_field(state, expression.value, expression.attr)
    if (
        isinstance(expression, ast.Subscript)
        and isinstance(expression.slice, ast.Constant)
        and isinstance(expression.slice.value, str)
    ):
        return _probe_field(state, expression.value, expression.slice.value)
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


def _resolves_to_par_map(state: _LoweringState, expression: ast.Call, name: str) -> bool:
    """Return whether a call targets the `par_map` authoring operation."""
    if isinstance(expression.func, ast.Attribute):
        target, _ = _resolve_dotted(state, expression=expression)
        return target is par_map
    return state.definition.function.__globals__.get(name) is par_map


def _lower_par_map(state: _LoweringState, expression: ast.Call) -> _Reference:
    """Place a fan-out map over an owned container."""
    func_expr, collection_expr, after_keyword = _bind_par_map_arguments(state, expression=expression)
    target = _resolve_par_map_callable(state, expression=func_expr)
    if isinstance(func_expr, ast.Attribute):
        call_name = func_expr.attr
    else:
        assert isinstance(func_expr, ast.Name)
        call_name = func_expr.id
    if isinstance(target, CalcJobTaskHandle):
        msg = (
            'maps dispatch one child per element with shared inputs, so per-item launch metadata has no placement '
            f'to key by; `CalcJob` task `{call_name}` cannot run under `par_map`; map a task function, '
            'a `WorkChain`, or a nested graph instead'
        )
        _reject(state, node=func_expr, reason=msg)
    if isinstance(target, GraphHandle):
        mapped_body: GraphIR | None = _lower_graph(target, stack=state.stack)
        mapped_spec: TaskIR | None = None
    else:
        mapped_body = None
        mapped_spec = target._task_spec
    _check_par_map_callable(state, node=func_expr, label=call_name, spec=mapped_spec, body=mapped_body)
    collection = _lower_value(state, collection_expr)
    container = _check_par_map_collection(state, node=collection_expr, value=collection)
    instance = _claim_name(state, f'map_{call_name}')
    given: dict[str, _CapturedValue] = {}
    _wire(state, instance=instance, port='collection', value=collection, given=given)
    state.tasks.append(MapControl(name=instance, inputs=given, spec=mapped_spec, body=mapped_body, container=container))
    if after_keyword is not None:
        _wire_after(state, instance=instance, keyword=after_keyword)
    collected = DataList if container == 'list' else DataDict
    return _Reference(instance, port='result', shape=LeafShape(types=(collected,)))


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


def _resolve_par_map_callable(
    state: _LoweringState, expression: ast.expr
) -> FunctionTaskHandle[t.Any, t.Any] | CalcJobTaskHandle | WorkChainTaskHandle | GraphHandle:
    """Resolve the mapped callable to its task handle or graph, rejecting anything else."""
    if isinstance(expression, ast.Name):
        name = expression.id
        if name in state.names:
            msg = (
                'a name cannot be both a wire and a declaration; '
                f'{name!r} is also used as a result name; pass the task or graph by its declared name instead'
            )
            _reject(state, node=expression, reason=msg)
        target = state.definition.function.__globals__.get(name)
        label: str = name
    elif isinstance(expression, ast.Attribute):
        as_call = ast.Call(func=expression, args=[], keywords=[])
        ast.copy_location(as_call, expression)
        target, label = _resolve_dotted(state, expression=as_call)
    else:
        msg = 'maps apply a registered declaration per element; pass a `@task` or `@graph` by name instead.'
        _reject(state, node=expression, reason=msg)
    if isinstance(target, (FunctionTaskHandle, CalcJobTaskHandle, WorkChainTaskHandle, GraphHandle)):
        return target
    if target is None and label not in vars(builtins):
        msg = 'calls must name an importable declaration; ' + f'unknown name {label!r}; check the spelling instead'
        _reject(state, node=expression, reason=msg)
    msg = (
        'only registered declarations carry input and output contracts; '
        + f'unregistered call {label!r}; add `@task` or `@graph` above it instead'
    )
    _reject(state, node=expression, reason=msg)


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


def _lower_operation(state: _LoweringState, node: ast.BinOp | ast.Compare | ast.UnaryOp) -> _Reference:
    """Place one inline operation and return its result reference.

    Operands lower first, so nested operations become their own placements with dependency
    wires into the outer one. Primitive results are orchestration state, never `Data` nodes:
    the placement only records the operator and its operand contracts for the engine.
    """
    operation, raw = _operation_parts(state, node=node)
    lowered = tuple(_lower_operand(state, item) for item in raw)
    return _place_operation(state, operation=operation, operands=lowered, node=node)


def _lower_call(state: _LoweringState, expression: ast.expr) -> _Reference:
    """Place a task or graph call with wired graph inputs."""
    name: str = _call_target_name(state, expression=expression)
    assert isinstance(expression, ast.Call)
    if _resolves_to_par_map(state, expression, name):
        return _lower_par_map(state, expression)
    target: FunctionTaskHandle[t.Any, t.Any] | CalcJobTaskHandle | WorkChainTaskHandle | GraphHandle = (
        _registered_target(state, expression=expression, name=name)
    )
    instance: str = _claim_name(state, name=name)
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
    missing: list[str] = _missing_required_inputs(state, instance=instance, shape=inputs, given=task.inputs)
    if missing:
        msg = (
            'required inputs must be wired before the graph is stored; '
            + f'task {name!r} is missing required inputs: {missing}; pass them as call arguments'
        )
        _reject(state, node=expression, reason=msg)
    state.tasks.append(task)
    return _Reference(instance, port=result_port, shape=result_shape)


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
    state: _LoweringState, instance: str, shape: NamespaceShape, given: t.Any, prefix: str = ''
) -> list[str]:
    """Return the required task inputs that are neither wired nor routed from graph inputs."""
    missing: list[str] = []
    mapping = given if isinstance(given, Mapping) else {}
    for field_name, child in shape.fields:
        path = f'{prefix}.{field_name}' if prefix else field_name
        if isinstance(child, NamespaceShape):
            missing.extend(
                _missing_required_inputs(
                    state, instance=instance, shape=child, given=mapping.get(field_name), prefix=path
                )
            )
        elif child.required and field_name not in mapping and not _is_routed(state, instance=instance, path=path):
            missing.append(path)
    return missing


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
    if isinstance(expression, (ast.BinOp, ast.Compare)):
        return _lower_operation(state, node=expression)
    if isinstance(expression, ast.Name):
        if expression.id not in state.names:
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
        msg = 'a single stored value has no fields to select; use the value directly instead'
        _reject(state, node=node, reason=msg)
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
