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

from aiida.common.exceptions import GraphError, UnsupportedSyntax
from aiida.engine.processes.graphs.inputs import place
from aiida.engine.processes.graphs.ir import (
    CONDITION_PORT,
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
    NamespaceShape,
    Shape,
    json_default,
    shape_for_annotation,
    shape_for_annotations,
)
from aiida.engine.processes.graphs.tasks import TaskHandle, build_task

__all__ = ('GraphHandle', 'UnsupportedSyntax', 'graph', 'task')

P = t.ParamSpec('P')
R = t.TypeVar('R')


# Value forms the language rejects, with the guidance each carries. The key sets
# are the unsupported list; anything missing here reports the generic fallback.
_VALUE_REJECTIONS: dict[tuple[type[ast.expr], ...], str] = {
    (ast.BoolOp, ast.Compare): 'put this check in a task and branch on its result instead',
    (ast.IfExp,): 'write this as if and else instead',
    (ast.NamedExpr,): 'give it a name on its own line before the if instead',
    (ast.Subscript,): 'cannot pick elements here; pass the whole collection instead',
    (ast.Starred,): 'cannot unpack here; list each input by name instead',
    (ast.JoinedStr,): 'build this text in a task instead',
    (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp): ('write out one call per value instead'),
    (ast.Lambda,): 'write a task instead',
    (ast.Call,): 'put the inner call on its own line first',
    (ast.Dict,): 'list each output by name instead of nesting them',
    (ast.List, ast.Tuple, ast.Set): 'provide collections as graph inputs instead',
    (ast.Await, ast.Yield, ast.YieldFrom): ('tasks cannot wait or pause; write plain steps instead'),
}


class GraphHandle:
    """An importable source declaration that builds without executing its body."""

    def __init__(self, function: Callable[..., t.Any]) -> None:
        self._definition = _SourceDefinition.capture(function)
        self._template: GraphIR | None = None
        # Copy name and docstring, not the function state: the handle owns its identifier.
        functools.update_wrapper(self, function, updated=())

    def __call__(self, *args: t.Any, **kwargs: t.Any) -> t.NoReturn:
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
            self._template = _lower_graph(self, ())
        return self._template

    @property
    def process_class(self) -> type[GraphProcess]:
        """Return the process class executing lowered graphs."""
        return GraphProcess

    def get_launch_inputs(self, **inputs: t.Any) -> dict[str, t.Any]:
        """Validate graph arguments and prepare the declaration and provenance inputs."""
        # Launching binds by name, so positional-only parameters accept keywords at launch.
        parameters = [
            parameter.replace(kind=inspect.Parameter.POSITIONAL_OR_KEYWORD)
            if parameter.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.KEYWORD_ONLY)
            else parameter
            for parameter in inspect.signature(self.function).parameters.values()
        ]
        bound = inspect.Signature(parameters).bind_partial(**inputs)
        return GraphProcess._launch_inputs(self.build(), dict(bound.arguments))


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
            raise UnsupportedSyntax(msg) from exception
        try:
            hints = t.get_type_hints(function, include_extras=True)
        except (NameError, AttributeError) as exception:
            msg = f'Cannot resolve type hints for {key}: {exception}'
            raise UnsupportedSyntax(msg) from exception
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


CapturedValue: t.TypeAlias = '_Reference | int | float | str | bool | dict[str, CapturedValue] | None'


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


@t.overload
def task(function: Callable[P, R]) -> TaskHandle[P, R]: ...


@t.overload
def task(function: None = None) -> Callable[[Callable[P, R]], TaskHandle[P, R]]: ...
def task(function: Callable[..., t.Any] | None = None) -> t.Any:
    """Register an importable task with static outputs and fixed input namespaces.

    :param function: the function to decorate.
    :return: a callable, launchable task handle.
    """

    def decorate(target: Callable[..., t.Any]) -> t.Any:
        """Validate the importable task reference and construct its process wrapper."""
        _function_identifier(target)
        return build_task(target)

    if function is not None:
        return decorate(function)

    return decorate


@t.overload
def graph(function: Callable[..., t.Any]) -> GraphHandle: ...


@t.overload
def graph(function: None = None) -> Callable[[Callable[..., t.Any]], GraphHandle]: ...
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

    def decorate(target: Callable[..., t.Any]) -> GraphHandle:
        """Capture the graph source without executing its body."""
        return GraphHandle(target)

    if function is not None:
        return decorate(function)

    return decorate


def _function_identifier(function: Callable[..., t.Any]) -> str:
    """Return an importable function identifier, rejecting nested functions."""
    if not inspect.isfunction(function):
        raise UnsupportedSyntax('Registered declarations must be Python functions, not process classes or builders')
    if function.__qualname__ != function.__name__:
        raise UnsupportedSyntax('Registered functions must be defined at module scope, not nested in other code')
    if function.__module__ == '__main__':
        msg = 'Graph declarations require an importable module; save the function in a Python module.'
        raise UnsupportedSyntax(msg)
    return f'{function.__module__}:{function.__name__}'


def _task_spec_for(target: object) -> TaskIR | None:
    """Return the declaration of a task handle, or `None` for other call targets."""
    return target._task_spec if isinstance(target, TaskHandle) else None


def _reject(state: _LoweringState, node: ast.AST, reason: str) -> t.NoReturn:
    """Point at the offending node in the original file, not just the extracted function."""
    source = state.definition.source.splitlines()
    location = state.definition
    line: int | None = getattr(node, 'lineno', None)
    column: int | None = getattr(node, 'col_offset', None)
    if line is None or column is None or line > len(source):
        msg = f'{location.filename}: {state.key}: {reason}: {ast.unparse(node)}'
        raise UnsupportedSyntax(msg)

    text = source[line - 1]
    # AST columns are UTF-8 byte offsets; a displayed caret needs a character offset.
    before = text.encode('utf-8')[:column].decode('utf-8', errors='ignore')
    position = len(before)
    msg = (
        f'{location.filename}:{location.first_line + line - 1}:{position + 1}: '
        f'{state.key}: {reason}\n    {text}\n    {" " * position}^'
    )
    raise UnsupportedSyntax(msg)


def _parse_function(definition: _SourceDefinition) -> ast.FunctionDef:
    """Parse one registered definition to its function node."""
    module = ast.parse(definition.source)
    if len(module.body) != 1 or not isinstance(module.body[0], ast.FunctionDef):
        msg = f'{definition.key}: expected one function definition'
        raise UnsupportedSyntax(msg)
    return module.body[0]


def _check_signature(state: _LoweringState, function: ast.FunctionDef) -> None:
    """Reject parameter kinds the graph compiler cannot represent."""
    if function.args.vararg or function.args.kwarg:
        _reject(state, function, '`*args` and `**kwargs` are not supported; list each input separately instead')


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
            _reject(
                state,
                default,
                f'parameter default for `{parameter.arg}` must be a literal; use a task or an input instead',
            )
        try:
            json_default(value)
        except TypeError:
            _reject(
                state,
                default,
                f'parameter default for `{parameter.arg}` must be a finite JSON value; pass richer values as inputs',
            )
        defaults[parameter.arg] = value
    return defaults


def _declare_graph_inputs(state: _LoweringState, function: ast.FunctionDef) -> NamespaceShape:
    """Route every graph parameter to its input shape."""
    parameters = [*function.args.posonlyargs, *function.args.args, *function.args.kwonlyargs]
    defaults = _parameter_defaults(state, function)
    boundary = shape_for_annotations(state.definition.hints, tuple(arg.arg for arg in parameters), defaults=defaults)
    for arg in parameters:
        state.inputs[arg.arg] = []
        shape = boundary.select(arg.arg)
        state.input_shapes[arg.arg] = shape
        state.names[arg.arg] = _Reference(None, arg.arg, shape)
    return boundary


def _lower_function(state: _LoweringState) -> GraphIR:
    """Lower one registered graph definition to a static template."""
    function = _parse_function(state.definition)
    _check_signature(state, function)
    boundary = _declare_graph_inputs(state, function)
    statements = function.body
    if statements and isinstance(statements[0], ast.Expr) and isinstance(statements[0].value, ast.Constant):
        if isinstance(statements[0].value.value, str):
            statements = statements[1:]
    if not statements or not isinstance(statements[-1], ast.Return):
        msg = f'{state.key}: end the graph with a return declaring its outputs'
        raise UnsupportedSyntax(msg)
    for statement in statements[:-1]:
        if isinstance(statement, ast.If):
            _lower_branch(state, statement)
        elif isinstance(statement, ast.While):
            _lower_loop(state, statement)
        elif isinstance(statement, (ast.For, ast.AsyncFor)):
            _reject(state, statement, 'for loops are not supported; write out one call per value, or use a while loop')
        elif isinstance(statement, (ast.Import, ast.ImportFrom)):
            _reject(state, statement, 'imports are not supported in graph bodies; import inside task bodies instead')
        elif (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Tuple)
        ):
            _lower_unpack(state, statement)
        else:
            _lower_assignment(state, statement)
    result: ast.expr | None = statements[-1].value
    if result is None:
        msg = 'return must name a task or graph input; return placements, input leaves, or mappings'
        _reject(state, statements[-1], msg)
    outputs, output_typehints = _lower_outputs(state, result)
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
    references = _lower_return(state, result)
    returned = shape_for_annotation(hints.get('return'))
    if isinstance(returned, NamespaceShape):
        _reject(state, result, 'graphs cannot return a whole group; return single values instead')
    outputs = {name: Endpoint(task=reference.task, port=reference.port) for name, reference in references.items()}
    typehints: dict[str, tuple[type, ...]] = (
        {next(iter(outputs)): returned.types} if len(outputs) == 1 and returned.types else {}
    )
    return outputs, typehints


def _lower_return(state: _LoweringState, expression: ast.expr) -> dict[str, _Reference]:
    """Return a leaf reference or an explicit mapping of named leaf outputs."""
    if isinstance(expression, ast.Dict):
        outputs: dict[str, _Reference] = {}
        for key, value in zip(expression.keys, expression.values, strict=True):
            if not isinstance(key, ast.Constant) or not isinstance(key.value, str) or not key.value.isidentifier():
                _reject(state, expression, 'output names must be quoted names; write them out instead')
            if key.value in outputs:
                _reject(state, expression, 'duplicate graph output; name each output once')
            reference = _lower_value(state, value, allow_call=True)
            if not isinstance(reference, _Reference) or isinstance(reference.shape, NamespaceShape):
                _reject(state, value, 'return single values, not a whole group')
            outputs[key.value] = reference
        return outputs
    reference = _lower_value(state, expression, allow_call=True)
    if not isinstance(reference, _Reference) or not reference.port or isinstance(reference.shape, NamespaceShape):
        _reject(
            state,
            expression,
            'return a task output or graph input instead',
        )
    port = reference.port.split('.')[-1]
    return {port: reference}


def _lower_assignment(state: _LoweringState, statement: ast.stmt, *, rebind: bool = False) -> str:
    """Bind a call result to new placement names."""
    if isinstance(statement, ast.AnnAssign):
        _reject(state, statement, 'drop the annotation; types come from the task or input instead')
    if not isinstance(statement, ast.Assign) or not statement.targets:
        _reject(state, statement, 'this statement is not supported here; move it into a task instead')
    names: list[str] = [target.id for target in statement.targets if isinstance(target, ast.Name)]
    if len(names) != len(statement.targets):
        _reject(state, statement, 'assign to a plain name instead, one per line')
    for name in names:
        if name in state.names and not rebind:
            _reject(state, statement, 'assign each result a new name instead of reusing one')
    if not isinstance(statement.value, ast.Call):
        msg = 'each line must call a task or graph instead'
        _reject(state, statement.value, msg)
    ref: _Reference = _lower_call(state, statement.value)
    for name in names:
        state.names[name] = ref
    return names[0]


def _lower_unpack(state: _LoweringState, statement: ast.Assign) -> None:
    """Bind each tuple element to one output of a multi-output call."""
    target: ast.expr = statement.targets[0]
    assert isinstance(target, ast.Tuple)
    names: list[str] = [elt.id for elt in target.elts if isinstance(elt, ast.Name)]
    if not names or len(names) != len(target.elts) or any(name in state.names for name in names):
        _reject(state, statement, 'give each unpacked output a new name instead')
    if not isinstance(statement.value, ast.Call):
        msg = 'each line must call a task or graph instead'
        _reject(state, statement.value, msg)
    ref: _Reference = _lower_call(state, statement.value)
    if not isinstance(ref.shape, NamespaceShape):
        if len(names) == 1:
            state.names[names[0]] = ref
            return
        _reject(state, statement.value, 'this task has one output; assign it to one name instead')
    fields: tuple[tuple[str, Shape], ...] = ref.shape.fields
    if len(names) != len(fields):
        _reject(state, statement, f'name all {len(fields)} outputs, one name each')
    for name, (field_name, field_shape) in zip(names, fields):
        state.names[name] = _Reference(ref.task, field_name, field_shape)


def _lower_arm(state: _LoweringState, statements: list[ast.stmt]) -> _Arm:
    """Lower one branch arm to a named region body."""
    child = _collect_region_inputs(state, statements)
    name = _lower_assignment(child, statements[0])
    reference = child.names[name]
    return _Arm(name, child, _lower_region_body(child, {reference.port: reference}))


def _lower_branch(state: _LoweringState, statement: ast.If) -> None:
    """Lower an if statement to a branch control task."""
    _check_branch_shape(state, statement)
    bound = _bind_condition(state, statement.test)
    test: ast.expr = bound if bound is not None else statement.test
    first = _lower_arm(state, statement.body)
    second = _lower_arm(state, statement.orelse)
    _check_arms_agree(state, statement, first, second)
    instance = f'branch_{len(state.tasks) + 1}'
    given = _wire_branch_inputs(state, instance, first, second, test)
    state.tasks.append(BranchControl(name=instance, inputs=given, body=first.body, otherwise=second.body))
    selected = first.child.names[first.name]
    state.names[first.name] = _Reference(instance, selected.port, selected.shape)


def _check_branch_shape(state: _LoweringState, statement: ast.If) -> None:
    """Reject branch statements that do not assign one name on both sides."""
    if not statement.orelse or len(statement.body) != 1 or len(statement.orelse) != 1:
        _reject(state, statement, 'assign the same name on both sides instead')


def _check_arms_agree(state: _LoweringState, statement: ast.If, first: _Arm, second: _Arm) -> None:
    """Reject arms assigning different names, taken names, or the condition port."""
    if first.name != second.name or first.name in state.names:
        _reject(state, statement, 'both sides must share one new name instead')
    if CONDITION_PORT in first.body.inputs or CONDITION_PORT in second.body.inputs:
        _reject(state, statement, 'condition conflicts with a branch input; rename one of them')


def _wire_branch_inputs(
    state: _LoweringState, instance: str, first: _Arm, second: _Arm, test: ast.expr
) -> dict[str, CapturedValue]:
    """Wire the condition and the region inputs into a branch placement."""
    given: dict[str, CapturedValue] = {}
    _wire(state, instance, CONDITION_PORT, _lower_value(state, test), given)
    read = {path.split('.')[0] for side in (first, second) for path in side.child.inputs}
    for name in sorted(read):
        _wire(state, instance, name, state.names[name], given)
    return given


def _lower_loop(state: _LoweringState, statement: ast.While) -> None:
    """Lower a while statement to a resumable loop control task."""
    bound = _bind_condition(state, statement.test)
    body: list[ast.stmt] = list(statement.body)
    if bound is not None:
        update = ast.Assign(targets=[ast.Name(id=bound.id, ctx=ast.Store())], value=copy.deepcopy(statement.test))
        ast.copy_location(update, statement.test)
        ast.copy_location(update.targets[0], statement.test)
        body.append(update)
    test: ast.expr = bound if bound is not None else statement.test
    if statement.orelse or not isinstance(test, ast.Name) or test.id not in state.names:
        _reject(state, statement, 'while loops need a named check and no else')
    condition = test.id
    child = _collect_region_inputs(state, body)
    # Loop state is read from the previous iteration, including values rebound in the body.
    assigned: set[str] = {
        node.targets[0].id
        for node in body
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
    }
    for name in assigned:
        if name not in state.names:
            _reject(state, statement, f'set {name!r} before the loop instead')
        child.inputs.setdefault(name, [])
        child.input_shapes[name] = state.names[name].shape
        child.names[name] = _Reference(None, name, state.names[name].shape)
    if condition not in assigned:
        _reject(state, statement, 'update the check inside the loop body instead')
    for node in body:
        _lower_assignment(child, node, rebind=True)
    outputs: dict[str, _Reference] = {name: child.names[name] for name in assigned}
    body_spec = _lower_region_body(child, outputs)
    instance = f'loop_{len(state.tasks) + 1}'
    given: dict[str, CapturedValue] = {}
    _route_region(state, child, instance, given)
    state.tasks.append(LoopControl(name=instance, inputs=given, body=body_spec, condition_port=condition))
    for name in assigned:
        state.names[name] = _Reference(instance, name, child.names[name].shape)


def _collect_region_inputs(state: _LoweringState, statements: list[ast.stmt]) -> _LoweringState:
    """Collect the enclosing values a nested body reads as region inputs."""
    # Names read in the body become inputs of the nested graph. Calls are not values.
    assigned: set[str] = {
        target.id
        for stmt in statements
        if isinstance(stmt, ast.Assign)
        for target in stmt.targets
        if isinstance(target, ast.Name)
    }
    callees: set[int] = {id(node.func) for stmt in statements for node in ast.walk(stmt) if isinstance(node, ast.Call)}
    names: set[str] = {
        node.id
        for stmt in statements
        for node in ast.walk(stmt)
        if isinstance(node, ast.Name)
        and isinstance(node.ctx, ast.Load)
        and node.id not in assigned
        and id(node) not in callees
    }
    child = _LoweringState(state.definition, state.stack)
    for name in sorted(names):
        if name not in state.names:
            _reject(state, statements[0], f'{name!r} is not known here; assign it before the branch or loop instead')
        child.inputs[name] = []
        shape = state.names[name].shape
        child.input_shapes[name] = shape
        child.names[name] = _Reference(None, name, shape)
    return child


def _route_region(state: _LoweringState, child: _LoweringState, instance: str, given: dict[str, CapturedValue]) -> None:
    """Route the enclosing values a nested region reads."""
    for name in child.inputs:
        if name in state.names:
            _wire(state, instance, name, state.names[name], given)


def _bind_condition(state: _LoweringState, test: ast.expr) -> ast.Name | None:
    """Lower a call condition to a fresh binding."""
    if not isinstance(test, ast.Call):
        return None
    name = 'condition'
    count = 2
    while name in state.names:
        name = f'condition_{count}'
        count += 1
    bound = ast.Assign(targets=[ast.Name(id=name, ctx=ast.Store())], value=test)
    ast.copy_location(bound, test)
    ast.copy_location(bound.targets[0], test)
    _lower_assignment(state, bound)
    return ast.Name(id=name, ctx=ast.Load())


def _lower_region_body(state: _LoweringState, outputs: dict[str, _Reference]) -> GraphIR:
    """Lower collected region state to a nested graph template."""
    if any(isinstance(reference.shape, NamespaceShape) for reference in outputs.values()):
        msg = 'control-flow outputs must be static leaves, not namespaces.'
        raise UnsupportedSyntax(msg)
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
    """Return the target of a direct call, rejecting shadowed or indirect calls."""
    if not isinstance(expression, ast.Call) or not isinstance(expression.func, ast.Name):
        _reject(state, expression, 'call tasks and graphs by their plain names instead')
    if expression.func.id in state.names:
        _reject(state, expression, f'{expression.func.id!r} is also used as a result name; rename one of them instead')
    return expression.func.id


def _registered_target(state: _LoweringState, expression: ast.expr, name: str) -> TaskHandle | GraphHandle:
    """Return the task handle or graph behind a call target."""
    namespace = state.definition.function.__globals__
    target = namespace.get(name)
    if _task_spec_for(target) is None and not isinstance(target, GraphHandle):
        if target is None and name in vars(builtins):
            _reject(state, expression, f'built-in {name!r} cannot run here; wrap it in a task instead')
        if target is None and name not in namespace:
            _reject(state, expression, f'unknown name {name!r}; check the spelling instead')
        _reject(state, expression, f'unregistered call {name!r}; add `@task` or `@graph` above it instead')
    assert isinstance(target, (TaskHandle, GraphHandle))
    return target


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


def _lower_call(state: _LoweringState, expression: ast.expr) -> _Reference:
    """Place a task or graph call with wired inputs."""
    name: str = _call_target_name(state, expression)
    assert isinstance(expression, ast.Call)
    target: TaskHandle | GraphHandle = _registered_target(state, expression, name)
    instance: str = _claim_name(state, name)
    if isinstance(target, GraphHandle):
        body: GraphIR = _lower_graph(target, state.stack)
        task: ProcessTask | SubgraphTask = SubgraphTask(name=instance, inputs={}, body=body)
        inputs: NamespaceShape = body.input_shape
        result_port: str = body.result_port
        result_shape: Shape = body.result_shape
    else:
        spec: TaskIR | None = _task_spec_for(target)
        assert spec is not None
        task = ProcessTask(name=instance, inputs={}, spec=spec)
        inputs = spec.input_shape
        result_port = spec.result_port
        result_shape = spec.result_shape
    keywords: list[ast.keyword] = _bind_positional(state, expression, name, inputs)
    task = replace(task, inputs=_lower_keywords(state, instance, name, inputs, keywords))
    missing: list[str] = _missing_required_inputs(state, instance, inputs, task.inputs)
    if missing:
        _reject(state, expression, f'task {name!r} is missing required inputs: {missing}; pass them as call arguments')
    state.tasks.append(task)
    return _Reference(instance, result_port, result_shape)


def _bind_positional(
    state: _LoweringState, expression: ast.Call, name: str, inputs: NamespaceShape
) -> list[ast.keyword]:
    """Bind positional arguments through declared input order, like the explicit keywords."""
    if not expression.args:
        keywords = list(expression.keywords)
    else:
        order: list[str] = [field for field, _ in inputs.fields]
        if len(expression.args) > len(order):
            _reject(state, expression, f'too many positional arguments for `{name}`; drop the extras')
        keywords = [ast.keyword(arg=field, value=arg) for field, arg in zip(order, expression.args)]
        keywords.extend(expression.keywords)
    if any(keyword.arg is None for keyword in keywords):
        _reject(state, expression, 'name each argument like x=1 instead')
    return keywords


def _wire_after(state: _LoweringState, instance: str, keyword: ast.keyword) -> None:
    """Wire ordering edges from an `after` argument."""
    ordered: list[ast.expr] = (
        keyword.value.elts if isinstance(keyword.value, (ast.Tuple, ast.List)) else [keyword.value]
    )
    for predecessor in ordered:
        reference = _lower_value(state, predecessor)
        if not isinstance(reference, _Reference) or reference.task is None:
            _reject(state, predecessor, 'after needs a task from an earlier line instead')
        state.dependencies.append(Dependency(reference.task, instance))


def _lower_keywords(
    state: _LoweringState, instance: str, name: str, inputs: NamespaceShape, keywords: list[ast.keyword]
) -> dict[str, CapturedValue]:
    """Wire one call's arguments to literals, references, and ordering edges."""
    given: dict[str, CapturedValue] = {}
    seen: set[str] = set()
    for keyword in keywords:
        port = keyword.arg
        assert port is not None
        if port in seen:
            _reject(state, keyword, f'duplicate input {port!r}; pass it once')
        seen.add(port)
        if port == 'after':
            _wire_after(state, instance, keyword)
            continue
        try:
            shape = inputs.select(port)
        except KeyError:
            _reject(state, keyword, f'{port!r} is not an input of {name!r}; check the spelling instead')
        _lower_input(state, instance, port, keyword.value, shape, given)
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
            missing.extend(_missing_required_inputs(state, instance, child, mapping.get(field_name), path))
        elif child.required and field_name not in mapping and not _is_routed(state, instance, path):
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
        place(given, port, value)
    elif value.task is None:
        state.inputs.setdefault(value.port, []).append(Route(instance, port))
    else:
        state.dependencies.append(Dependency(value.task, instance, value.port, port))


def _lower_input(
    state: _LoweringState, instance: str, path: str, expression: ast.expr, shape: Shape, given: dict[str, CapturedValue]
) -> None:
    """Expand dictionary syntax only for declared fixed input namespaces."""
    if isinstance(expression, ast.Dict) and isinstance(shape, NamespaceShape):
        place(given, path, {})
        seen: set[str] = set()
        for key, value in zip(expression.keys, expression.values, strict=True):
            if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
                msg = 'namespace keys must be string literals without unpacking; compute dynamic keys in tasks'
                _reject(state, expression, msg)
            name: str = key.value
            if name in seen:
                _reject(state, expression, f'duplicate input {name!r}; pass it once')
            try:
                child = shape.select(name)
            except KeyError:
                _reject(state, expression, f'{name!r} is not a declared name here; check the spelling instead')
            seen.add(name)
            _lower_input(state, instance, f'{path}.{name}', value, child, given)
        return
    if isinstance(expression, ast.Dict):
        try:
            value = ast.literal_eval(expression)
        except (ValueError, TypeError) as exception:
            msg = 'Dictionary-valued ports require a literal value or a reference to the whole port.'
            raise UnsupportedSyntax(msg) from exception
        place(given, path, value)
        return
    _wire(state, instance, path, _lower_value(state, expression), given)


def _lower_value(
    state: _LoweringState, expression: ast.expr, *, allow_call: bool = False
) -> _Reference | int | float | str | bool | None:
    """Lower a value expression to a reference or literal."""
    if allow_call and isinstance(expression, ast.Call):
        return _lower_call(state, expression)
    if isinstance(expression, ast.Name):
        if expression.id not in state.names:
            _reject(state, expression, f'{expression.id!r} is not known here; assign it on an earlier line instead')
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
            _reject(state, expression, _unsupported_reason(expression))
        if value is None or isinstance(value, (int, float, str, bool)):
            return value
    _reject(state, expression, _unsupported_reason(expression))


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
        _reject(state, node, 'pick a task output or an input group instead')
    if not isinstance(reference.shape, NamespaceShape):
        if reference.task is not None and reference.port == attr:
            return reference
        _reject(state, node, 'only a group has named fields to select')
    path = f'{reference.port}.{attr}' if reference.port else attr
    try:
        shape = reference.shape.select(attr)
    except KeyError:
        _reject(state, node, f'{path!r} is not a declared field; check the spelling instead')
    return _Reference(reference.task, path, shape)


def _lower_graph(handle: GraphHandle, stack: tuple[str, ...]) -> GraphIR:
    """Lower a graph and its callees, rejecting recursive calls."""
    definition = handle._definition
    key = definition.key
    if key in stack:
        msg = f'Recursive graph call: {" -> ".join((*stack, key))}; express repetition with a while loop instead'
        raise UnsupportedSyntax(msg)
    return _lower_function(_LoweringState(definition, (*stack, key)))
