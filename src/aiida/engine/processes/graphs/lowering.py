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
import functools
import inspect
import textwrap
import typing as t
from collections import Counter
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace

from aiida.common.exceptions import GraphError, GraphLanguageError, GraphTypeCheckError, GraphValidationError
from aiida.common.links import validate_link_label
from aiida.engine.processes.calcjobs import CalcJob
from aiida.engine.processes.graphs.inputs import _place
from aiida.engine.processes.graphs.ir import (
    _CONDITION_PORT,
    BranchControl,
    Dependency,
    Endpoint,
    GraphIR,
    LoopControl,
    ProcessTask,
    Route,
    SubgraphTask,
    TaskIR,
)
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

__all__ = ('Forward', 'GraphHandle', 'graph', 'task')

P = t.ParamSpec('P')
R = t.TypeVar('R')


# Value forms the language rejects, with the guidance each carries. The key sets
# are the unsupported list; anything missing here reports the generic fallback.
_VALUE_REJECTIONS: dict[tuple[type[ast.expr], ...], str] = {
    (ast.BoolOp, ast.Compare): (
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

    def build(self) -> GraphIR:
        """Lower the declaration once and return the cached template.

        Lowering validates the source, so this raises its diagnostics early.
        """
        if self._template is None:
            self._template = _lower_graph(self, stack=())
        return self._template

    @property
    def process_class(self) -> type[GraphProcess]:
        """Return the process class executing lowered graphs."""
        return GraphProcess

    def get_launch_inputs(self, **inputs: t.Any) -> dict[str, t.Any]:
        """Validate graph arguments and prepare the declaration and provenance inputs.

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
        launch_inputs = GraphProcess._launch_inputs(self.build(), dict(bound.arguments), task_metadata=task_metadata)
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


@dataclass
class _LoweringState:
    """The placements, wirings, and references collected while lowering one graph body."""

    definition: _SourceDefinition
    stack: tuple[str, ...]
    tasks: list[ProcessTask | SubgraphTask | BranchControl | LoopControl] = field(default_factory=list)
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
    function: type[CalcJob], *, inputs: PortDeclaration | None = None, outputs: PortDeclaration | None = None
) -> CalcJobTaskHandle: ...


@t.overload
def task(  # type: ignore[overload-overlap]
    function: type[WorkChain], *, inputs: PortDeclaration | None = None, outputs: PortDeclaration | None = None
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
) -> t.Any:
    """Register an importable task with static ports and fixed graph inputs.

    Accepts a task function, a `CalcJob` subclass, or a `WorkChain` subclass; task inputs
    wire task outputs and graph inputs alike. `CalcJob` tasks read their metadata from the
    launch inputs instead.

    :param function: the function, `CalcJob` subclass, or `WorkChain` subclass to decorate.
    :param inputs: names and node types inside dynamic input namespaces of a process class,
        e.g. ``{'nodes': {'text': SinglefileData}}``.
    :param outputs: names and node types of the dynamic outputs of a process class.
    :return: a callable, launchable task handle.
    """

    def decorate(target: Callable[..., t.Any] | type[CalcJob] | type[WorkChain]) -> t.Any:
        """Validate the importable task reference and construct its process wrapper."""
        if not inspect.isclass(target):
            _function_identifier(target)
        return _build_task(target, inputs=inputs, outputs=outputs)

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


def _lower_outputs(state: _LoweringState, result: ast.expr) -> tuple[dict[str, Endpoint], dict[str, tuple[type, ...]]]:
    """Lower the return statement to named endpoints and their type hints."""
    hints = state.definition.hints
    references = _lower_return(state, expression=result)
    returned = shape_for_annotation(hints.get('return'))
    if isinstance(returned, NamespaceShape):
        msg = (
            'each output links one stored node, and a group has no single node; '
            + 'graphs cannot return a whole group; return single values instead'
        )
        _reject(state, node=result, reason=msg)
    outputs = {name: Endpoint(task=reference.task, port=reference.port) for name, reference in references.items()}
    if len(outputs) == 1 and not isinstance(result, ast.Dict):
        outputs = {'result': next(iter(outputs.values()))}
    typehints: dict[str, tuple[type, ...]] = (
        {next(iter(outputs)): returned.types}
        if len(outputs) == 1 and returned.types and not isinstance(result, ast.Dict)
        else {}
    )
    return outputs, typehints


def _lower_return(state: _LoweringState, expression: ast.expr) -> dict[str, _Reference]:
    """Return a leaf reference or an explicit mapping of named leaf outputs."""
    if isinstance(expression, ast.Dict):
        outputs: dict[str, _Reference] = {}
        for key, value in zip(expression.keys, expression.values, strict=True):
            if not isinstance(key, ast.Constant) or not isinstance(key.value, str) or not key.value.isidentifier():
                msg = (
                    'output names become port names when the graph is stored, so they must be written out; '
                    + 'output names must be quoted names; write them out instead'
                )
                _reject(state, node=expression, reason=msg)
            if key.value in outputs:
                msg = 'each output name points at one stored value; ' + 'duplicate graph output; name each output once'
                _reject(state, node=expression, reason=msg)
            reference = _lower_value(state, value, allow_call=True)
            if not isinstance(reference, _Reference) or isinstance(reference.shape, NamespaceShape):
                msg = 'outputs are flat leaves; return single values, not a whole group'
                _reject(state, node=value, reason=msg)
            outputs[key.value] = reference
        return outputs
    reference = _lower_value(state, expression, allow_call=True)
    if not isinstance(reference, _Reference) or not reference.port or isinstance(reference.shape, NamespaceShape):
        msg = 'graphs return existing nodes rather than creating data; ' + 'return a task output or graph input instead'
        _reject(state, node=expression, reason=msg)
    port = reference.port.split('.')[-1]
    return {port: reference}


def _lower_assignment(state: _LoweringState, statement: ast.stmt, *, rebind: bool = False) -> str:
    """Bind a call result to new placement names."""
    if isinstance(statement, ast.AnnAssign):
        msg = 'drop the annotation; types come from the task or input instead'
        _reject(state, node=statement, reason=msg)
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
    if not isinstance(statement.value, ast.Call):
        msg = (
            'only calls are recorded as work; plain values would run without leaving a trace; '
            + 'each line must call a task or graph instead'
        )
        _reject(state, node=statement.value, reason=msg)
    ref: _Reference = _lower_call(state, expression=statement.value)
    for name in names:
        state.names[name] = ref
    return names[0]


def _lower_unpack(state: _LoweringState, statement: ast.Assign) -> None:
    """Bind each tuple element to one output of a multi-output call."""
    target: ast.expr = statement.targets[0]
    assert isinstance(target, ast.Tuple)
    names: list[str] = [elt.id for elt in target.elts if isinstance(elt, ast.Name)]
    if not names or len(names) != len(target.elts) or any(name in state.names for name in names):
        msg = (
            'unpacking maps positions to declared output ports, so every element needs a fresh name; '
            + 'give each unpacked output a new name instead'
        )
        _reject(state, node=statement, reason=msg)
    if not isinstance(statement.value, ast.Call):
        msg = (
            'only calls are recorded as work; plain values would run without leaving a trace; '
            + 'each line must call a task or graph instead'
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
        child.names[name] = _Reference(None, port=outer.port, shape=outer.shape)
        body = _lower_region_body(child, {outer.port: _Reference(None, port=statement.value.id, shape=outer.shape)})
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
    else:
        name = _lower_assignment(child, statement=statement, rebind=True)
        reference = child.names[name]
    return _Arm(name, child=child, body=_lower_region_body(child, {reference.port: reference}))


def _single_assign_target(statement: ast.stmt) -> str | None:
    """Return the assigned plain name, or `None` for other statements."""
    if isinstance(statement, ast.Assign) and len(statement.targets) == 1 and isinstance(statement.targets[0], ast.Name):
        return statement.targets[0].id
    return None


def _passthrough_arm(state: _LoweringState, *, name: str, port: str, shape: Shape) -> _Arm:
    """Lower a missing `else` arm to a region passing the prior binding through."""
    child = _LoweringState(state.definition, stack=state.stack)
    child.inputs[name] = []
    child.input_shapes[name] = shape
    child.names[name] = _Reference(None, port=name, shape=shape)
    return _Arm(name, child=child, body=_lower_region_body(child, {port: _Reference(None, port=name, shape=shape)}))


def _merge_port(first: _Arm, second: _Arm) -> str | None:
    """Return the port alias arms rewire to: the call arm's port, or the first alias port.

    Rekeying is unconditional; validation judges whether the types agree.
    """
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
    return arm._replace(body=replace(arm.body, outputs={port: endpoint}))


def _lower_branch(state: _LoweringState, statement: ast.If) -> None:
    """Lower an if statement to a branch control task."""
    _check_branch_shape(state, statement=statement)
    test: ast.expr = statement.test
    if isinstance(test, ast.Call):
        test = _bind_call_condition(state, test=test)
    first = _lower_arm(state, statements=statement.body)
    if statement.orelse:
        second = _lower_arm(state, statements=statement.orelse)
    else:
        selected = first.child.names[first.name]
        second = _passthrough_arm(state, name=first.name, port=selected.port, shape=selected.shape)
    _check_arms_agree(state, statement=statement, first=first, second=second)
    port = _merge_port(first, second)
    if port is not None:
        first = _rekey_alias(first, port) if first.alias else first
        second = _rekey_alias(second, port) if second.alias else second
    instance = _claim_name(state, f'branch_{len(state.tasks) + 1}')
    given = _wire_branch_inputs(state, instance=instance, first=first, second=second, test=test)
    state.tasks.append(BranchControl(name=instance, inputs=given, body=first.body, otherwise=second.body))
    selected = first.child.names[first.name]
    state.names[first.name] = _Reference(instance, port=port or selected.port, shape=selected.shape)


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
        elif isinstance(node, ast.If):
            for arm in (*node.body, *node.orelse):
                if isinstance(arm, ast.Assign):
                    assigned.update(target.id for target in arm.targets if isinstance(target, ast.Name))
        elif isinstance(node, ast.While):
            assigned.update(_body_state_names(node.body))
    return assigned


def _lower_loop(state: _LoweringState, statement: ast.While) -> None:
    """Lower a while statement to a resumable loop control task."""
    body: list[ast.stmt] = list(statement.body)
    test: ast.expr = statement.test
    if isinstance(test, ast.Call):
        test = _bind_call_condition(state, test=test)
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
    for name in assigned:
        if name not in state.names:
            msg = (
                'loop state comes from enclosing names, so unknown names have nothing to start from; '
                + f'set {name!r} before the loop instead'
            )
            _reject(state, node=statement, reason=msg)
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
        if not isinstance(node, ast.Assign):
            msg = 'loop bodies only record task calls, branches, and loops; ' + 'move anything else into a task instead'
            _reject(state, node=node, reason=msg)
        _lower_assignment(child, node, rebind=True)
    outputs: dict[str, _Reference] = {name: child.names[name] for name in assigned}
    body_spec = _lower_region_body(child, outputs=outputs)
    instance = _claim_name(state, f'loop_{len(state.tasks) + 1}')
    given: dict[str, _CapturedValue] = {}
    _route_region(state, child=child, instance=instance, given=given)
    state.tasks.append(LoopControl(name=instance, inputs=given, body=body_spec, condition_port=condition))
    for name in assigned:
        state.names[name] = _Reference(instance, port=name, shape=child.names[name].shape)


def _collect_region_inputs(state: _LoweringState, statements: list[ast.stmt]) -> _LoweringState:
    """Collect the enclosing values a nested body reads as region inputs."""
    # Names read in the body become inputs of the nested graph. Calls are not values.
    assigned: set[str] = {
        node.id
        for stmt in statements
        if isinstance(stmt, ast.Assign)
        for target in stmt.targets
        for node in ast.walk(target)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
    }
    callees: set[int] = {id(node.func) for stmt in statements for node in ast.walk(stmt) if isinstance(node, ast.Call)}
    reads: dict[str, ast.Name] = {}
    for stmt in statements:
        for node in ast.walk(stmt):
            if (
                isinstance(node, ast.Name)
                and isinstance(node.ctx, ast.Load)
                and node.id not in assigned
                and id(node) not in callees
                and node.id not in reads
            ):
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
        if name in state.names:
            _wire(state, instance=instance, port=name, value=state.names[name], given=given)


def _bind_call_condition(state: _LoweringState, test: ast.Call) -> ast.Name:
    """Lower a call condition to a fresh binding."""
    name = 'condition'
    count = 2
    while name in state.names:
        name = f'condition_{count}'
        count += 1
    bound = ast.Assign(targets=[ast.Name(id=name, ctx=ast.Store())], value=test)
    ast.copy_location(bound, test)
    ast.copy_location(bound.targets[0], test)
    _lower_assignment(state, statement=bound)
    return ast.Name(id=name, ctx=ast.Load())


def _lower_region_body(state: _LoweringState, outputs: dict[str, _Reference]) -> GraphIR:
    """Lower collected region state to a nested graph template."""
    if any(isinstance(reference.shape, NamespaceShape) for reference in outputs.values()):
        msg = 'control-flow outputs must be static leaves, not namespaces.'
        raise GraphLanguageError(msg)
    endpoints: dict[str, Endpoint] = {
        name: Endpoint(task=reference.task, port=reference.port) for name, reference in outputs.items()
    }
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


def _wired_type(value: t.Any) -> type | None:
    """Return the ORM type a wired value carries, or `None` without evidence."""
    if isinstance(value, _Reference):
        shape = value.shape
        if not isinstance(shape, LeafShape) or not shape.types:
            return None
        mapped = [_node_type(kind) for kind in shape.types]
        mapped = [kind for kind in mapped if kind is not None and kind is not type(None)]
        return mapped[0] if len(mapped) == 1 else None
    if value is None:
        return None
    return _node_type(type(value))


def _solved_spec(
    target: FunctionTaskHandle[t.Any, t.Any] | CalcJobTaskHandle | WorkChainTaskHandle,
    keywords: list[ast.keyword],
    state: _LoweringState,
    *,
    spec: TaskIR,
    result_port: str,
) -> TaskIR:
    """Copy a generic task spec with solved output types, or return it unchanged.

    Solving reads the argument expressions because wiring routes references
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
        kind = _wired_type(_lower_value(state, keyword.value))
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


def _lower_call(state: _LoweringState, expression: ast.expr) -> _Reference:
    """Place a task or graph call with wired graph inputs."""
    name: str = _call_target_name(state, expression=expression)
    assert isinstance(expression, ast.Call)
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
    return any(edge.target == instance and edge.target_port == path for edge in state.dependencies)


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
    """Expand dictionary syntax only for declared fixed input namespaces."""
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
