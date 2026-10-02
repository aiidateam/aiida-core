###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Build a GraphSpec from restricted graph source without executing graph bodies.

The decorators capture definitions; source-based building never executes graph bodies.
"""

from __future__ import annotations

import ast
import functools
import inspect
import textwrap
import typing as t
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field

from aiida.engine.processes.graphs.build_execution import ACTIVE_BUILDER
from aiida.engine.processes.graphs.build_execution import task as build_task
from aiida.engine.processes.graphs.process import GraphProcess
from aiida.engine.processes.graphs.spec import (
    CONDITION_PORT,
    BranchControl,
    Dependency,
    Endpoint,
    GraphSpec,
    LoopControl,
    MapGraphControl,
    ProcessTask,
    SubgraphTask,
)
from aiida.engine.processes.ports import infer_valid_type_from_type_annotation

# The source decorators are imported explicitly from this module, since ``graph``
# would otherwise shadow the graph-builder decorator exported by ``aiida.engine``.
__all__ = ('SourceGraphHandle', 'UnsupportedSyntax', 'build_from_source')


class UnsupportedSyntax(ValueError):  # noqa: N818 - keep the prototype's exception name
    """A registered graph contains syntax the source parser cannot represent."""


# Keys are module:name. Sources are captured at decoration time, not looked up later.
SOURCES: dict[str, str] = {}


@dataclass(frozen=True)
class _SourceLocation:
    filename: str
    first_line: int


_LOCATIONS: dict[str, _SourceLocation] = {}
_TASKS: dict[str, t.Any] = {}
_GRAPHS: set[str] = set()
_GRAPH_HINTS: dict[str, dict[str, t.Any]] = {}


def _key(function: Callable[..., t.Any]) -> str:
    if function.__qualname__ != function.__name__:
        raise UnsupportedSyntax('Registered functions must be defined at module scope')
    return f'{function.__module__}:{function.__name__}'


def _register(function: Callable[..., t.Any]) -> str:
    key = _key(function)
    if key in SOURCES:
        msg = f'Duplicate registered function {key}'
        raise UnsupportedSyntax(msg)
    lines, first_line = inspect.getsourcelines(function)
    SOURCES[key] = textwrap.dedent(''.join(lines))
    _LOCATIONS[key] = _SourceLocation(inspect.getsourcefile(function) or '<unknown>', first_line)
    return key


def _bind_arguments(function: Callable[..., t.Any], *args: t.Any, **kwargs: t.Any) -> dict[str, t.Any]:
    """Return the arguments of a call, by the name of the parameter each is bound to."""
    bound = inspect.signature(function).bind(*args, **kwargs)
    bound.apply_defaults()
    return dict(bound.arguments)


class SourceGraphHandle:
    """What the source :func:`graph` decorator returns: a graph that can be built, run, or submitted."""

    def __init__(self, function: Callable[..., t.Any], identifier: str | None = None) -> None:
        self._function = function
        self.identifier = identifier or function.__name__
        functools.update_wrapper(self, function)

    def __call__(self, *args: t.Any, **kwargs: t.Any) -> t.Any:
        builder = ACTIVE_BUILDER.get()

        if builder is None:
            msg = (
                f'`{self.identifier}` declares a graph, so it is launched rather than called. Pass it to `run` or '
                f'`submit`, as any other process, or use `.build(...)` for the declaration on its own.'
            )
            raise TypeError(msg)

        return builder.add_graph(self, _bind_arguments(self._function, *args, **kwargs))

    def build(self) -> GraphSpec:
        """Return the graph that the function declares, lowered from its registered source."""
        return build_from_source(self._function)

    @property
    def parameters(self) -> tuple[str, ...]:
        """Return the names of the inputs the graph takes, which are the parameters of its function."""
        kinds = (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
        return tuple(
            name for name, parameter in inspect.signature(self._function).parameters.items() if parameter.kind in kinds
        )

    @property
    def process_class(self) -> type[GraphProcess]:
        """Return the process that runs a graph."""
        return GraphProcess

    def get_launch_inputs(self, *args: t.Any, **kwargs: t.Any) -> dict[str, t.Any]:
        """Return the inputs with which to launch the graph for these arguments.

        The declaration says what to run and the arguments are what to run it on, so they travel side by side and
        the same declaration serves every run.
        """
        return GraphProcess.launch_inputs(self.build(), _bind_arguments(self._function, *args, **kwargs))


def task(function: Callable[..., t.Any]) -> t.Any:
    """Register a Python function as an AiiDA task and save its source."""
    try:
        inspect.get_annotations(function, eval_str=True)
    except (NameError, AttributeError) as exception:
        msg = f'Cannot resolve type hints for task `{function.__qualname__}`: {exception}'
        raise TypeError(msg) from exception
    key = _register(function)
    decorated = build_task(function)
    _TASKS[key] = decorated
    return decorated


def graph(function: Callable[..., t.Any] | None = None, *, identifier: str | None = None) -> t.Any:
    """Save a graph's source without executing its body.

    The body is never executed: its source is captured at decoration time and lowered to a declaration by
    :func:`build_from_source` (or the ``build`` method of the returned handle) when the graph runs.

    Example usage:

    >>> from aiida.engine.processes.graphs.build_source import build_from_source, graph, task
    >>>
    >>> @task
    >>> def add(x: int, y: int) -> int:
    >>>     return x + y
    >>>
    >>> @graph
    >>> def add_twice(x: int, y: int) -> int:
    >>>     first = add(x=x, y=y)
    >>>     return add(x=first, y=y)
    >>>
    >>> declaration = build_from_source(add_twice)

    A graph is launched like any other process, by passing it to ``run`` or ``submit``. Use ``build`` to get the
    declaration on its own, without running anything.

    :param function: The function to decorate.
    :param identifier: Name of the graph, which defaults to the name of the function.
    :return: A handle that can build, run, or submit the graph.
    """

    def decorator(function: Callable[..., t.Any]) -> SourceGraphHandle:
        key = _register(function)
        _GRAPHS.add(key)
        _GRAPH_HINTS[key] = t.get_type_hints(function)
        return SourceGraphHandle(function, identifier=identifier)

    if function is not None:
        return decorator(function)

    return decorator


@dataclass(frozen=True)
class _Reference:
    task: str | None  # None denotes a graph input.
    port: str


@dataclass
class _LoweringState:
    key: str
    stack: tuple[str, ...]
    tasks: list[ProcessTask | SubgraphTask | BranchControl | LoopControl | MapGraphControl] = field(
        default_factory=list
    )
    dependencies: list[Dependency] = field(default_factory=list)
    inputs: dict[str, list[tuple[str, str]]] = field(default_factory=dict)
    names: dict[str, _Reference] = field(default_factory=dict)
    used: Counter[str] = field(default_factory=Counter)


def _parse_function(key: str) -> ast.FunctionDef:
    module = ast.parse(SOURCES[key])
    if len(module.body) != 1 or not isinstance(module.body[0], ast.FunctionDef):
        msg = f'{key}: expected one function definition'
        raise UnsupportedSyntax(msg)
    return module.body[0]


def _lower_function(state: _LoweringState) -> GraphSpec:
    function = _parse_function(state.key)
    if function.args.posonlyargs or function.args.kwonlyargs or function.args.vararg or function.args.kwarg:
        msg = f'{state.key}: only ordinary positional parameters are supported'
        raise UnsupportedSyntax(msg)
    if function.args.defaults or any(default is not None for default in function.args.kw_defaults):
        msg = f'{state.key}: parameter defaults are not supported'
        raise UnsupportedSyntax(msg)
    for arg in function.args.args:
        state.inputs[arg.arg] = []
        state.names[arg.arg] = _Reference(None, arg.arg)
    statements = function.body
    if statements and isinstance(statements[0], ast.Expr) and isinstance(statements[0].value, ast.Constant):
        if isinstance(statements[0].value.value, str):
            statements = statements[1:]
    if not statements or not isinstance(statements[-1], ast.Return):
        msg = f'{state.key}: graph must end in a return'
        raise UnsupportedSyntax(msg)
    for statement in statements[:-1]:
        if isinstance(statement, ast.If):
            _lower_branch(state, statement)
        elif isinstance(statement, ast.While):
            _lower_loop(state, statement)
        elif isinstance(statement, ast.For):
            _lower_map(state, statement)
        else:
            _lower_assignment(state, statement)
    result = statements[-1].value
    if result is None:
        _reject(state, statements[-1], 'return must name a task or graph input')
    output = _lower_value(state, result, allow_call=True)
    if not isinstance(output, _Reference):
        _reject(state, result, 'return must name a task or graph input')
    hints = _GRAPH_HINTS[state.key]
    output_hint = infer_valid_type_from_type_annotation(hints.get('return'))
    return GraphSpec(
        tasks=tuple(state.tasks),
        dependencies=tuple(state.dependencies),
        inputs={name: tuple(targets) for name, targets in state.inputs.items()},
        outputs={output.port: Endpoint(task=output.task, port=output.port)},
        identifier=state.key.partition(':')[2],
        input_typehints={
            name: hint for name in state.inputs if (hint := infer_valid_type_from_type_annotation(hints.get(name)))
        },
        output_typehints={output.port: output_hint} if output_hint else {},
    )


def _lower_assignment(state: _LoweringState, statement: ast.stmt, *, rebind: bool = False) -> str:
    if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
        _reject(state, statement, 'only single-name assignments are supported')
    target = statement.targets[0]
    if not isinstance(target, ast.Name) or (target.id in state.names and not rebind):
        _reject(state, statement, 'assignment must bind a new name')
    if not isinstance(statement.value, ast.Call):
        _reject(state, statement.value, 'graph assignments must call a registered task or graph')
    state.names[target.id] = _lower_call(state, statement.value)
    return target.id


def _body(state: _LoweringState, outputs: dict[str, _Reference]) -> GraphSpec:
    return GraphSpec(
        tasks=tuple(state.tasks),
        dependencies=tuple(state.dependencies),
        inputs={name: tuple(targets) for name, targets in state.inputs.items()},
        outputs={name: Endpoint(task=ref.task, port=ref.port) for name, ref in outputs.items()},
    )


def _region(state: _LoweringState, statements: list[ast.stmt], *, item: str | None = None) -> _LoweringState:
    # Names read in the body become inputs of the nested graph. Calls are not values.
    assigned = {
        target.id
        for stmt in statements
        if isinstance(stmt, ast.Assign)
        for target in stmt.targets
        if isinstance(target, ast.Name)
    }
    callees = {id(node.func) for stmt in statements for node in ast.walk(stmt) if isinstance(node, ast.Call)}
    reads = {
        node.id
        for stmt in statements
        for node in ast.walk(stmt)
        if isinstance(node, ast.Name)
        and isinstance(node.ctx, ast.Load)
        and node.id not in assigned
        and node.id != item
        and id(node) not in callees
    }
    names = reads | ({item} if item is not None else set())
    child = _LoweringState(state.key, state.stack)
    for name in sorted(names):
        if name != item and name not in state.names:
            _reject(state, statements[0], f'unbound name {name!r}')
        child.inputs[name] = []
        child.names[name] = _Reference(None, name)
    return child


def _wire(
    state: _LoweringState,
    instance: str,
    port: str,
    value: _Reference | int | float | str | bool,
    given: dict[str, t.Any],
) -> None:
    if not isinstance(value, _Reference):
        given[port] = value
    elif value.task is None:
        state.inputs[value.port].append((instance, port))
    else:
        state.dependencies.append(Dependency(value.task, instance, value.port, port))


def _place(state: _LoweringState, child: _LoweringState, instance: str, given: dict[str, t.Any]) -> None:
    for name in child.inputs:
        if name in state.names:
            _wire(state, instance, name, state.names[name], given)


def _lower_branch(state: _LoweringState, statement: ast.If) -> None:
    if not statement.orelse or len(statement.body) != 1 or len(statement.orelse) != 1:
        _reject(state, statement, 'if requires one assignment to the same name on each side')
    sides = []
    for statements in (statement.body, statement.orelse):
        child = _region(state, statements)
        name = _lower_assignment(child, statements[0])
        sides.append((name, child, _body(child, {'result': child.names[name]})))
    if sides[0][0] != sides[1][0] or sides[0][0] in state.names:
        _reject(state, statement, 'if requires one new name shared by both sides')
    if CONDITION_PORT in sides[0][2].inputs or CONDITION_PORT in sides[1][2].inputs:
        _reject(state, statement, 'condition conflicts with a branch input')
    instance = f'branch_{len(state.tasks) + 1}'
    given: dict[str, t.Any] = {}
    _wire(state, instance, CONDITION_PORT, _lower_value(state, statement.test), given)
    for name in sorted(set(sides[0][1].inputs) | set(sides[1][1].inputs)):
        _wire(state, instance, name, state.names[name], given)
    state.tasks.append(BranchControl(name=instance, inputs=given, body=sides[0][2], otherwise=sides[1][2]))
    state.names[sides[0][0]] = _Reference(instance, 'result')


def _lower_loop(state: _LoweringState, statement: ast.While) -> None:
    if statement.orelse or not isinstance(statement.test, ast.Name) or statement.test.id not in state.names:
        _reject(state, statement, 'while requires a bound condition name and no else')
    condition = statement.test.id
    child = _region(state, statement.body)
    # Loop state is read from the previous iteration, including values rebound in the body.
    assigned = {
        node.targets[0].id
        for node in statement.body
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
    }
    for name in assigned:
        if name not in state.names:
            _reject(state, statement, f'loop state {name!r} must be initialized before the loop')
        child.inputs.setdefault(name, [])
        child.names[name] = _Reference(None, name)
    if condition not in assigned:
        _reject(state, statement, 'while body must update its condition')
    for node in statement.body:
        _lower_assignment(child, node, rebind=True)
    outputs = {name: child.names[name] for name in assigned}
    body = _body(child, outputs)
    instance = f'loop_{len(state.tasks) + 1}'
    given: dict[str, t.Any] = {}
    _place(state, child, instance, given)
    state.tasks.append(LoopControl(name=instance, inputs=given, body=body, condition_port=condition))
    for name in assigned:
        state.names[name] = _Reference(instance, name)


def _lower_map(state: _LoweringState, statement: ast.For) -> None:
    if statement.orelse or not isinstance(statement.target, ast.Name) or len(statement.body) != 1:
        _reject(state, statement, 'for requires a single item name and one assignment without else')
    item = statement.target.id
    if item in state.names:
        _reject(state, statement.target, 'loop item shadows a bound name')
    child = _region(state, statement.body, item=item)
    result = _lower_assignment(child, statement.body[0])
    if result in state.names or result == item:
        _reject(state, statement.body[0], 'loop result must bind a new name')
    body = _body(child, {'result': child.names[result]})
    instance = f'each_{len(state.tasks) + 1}'
    given: dict[str, t.Any] = {}
    _wire(state, instance, item, _lower_value(state, statement.iter), given)
    _place(state, child, instance, given)
    state.tasks.append(MapGraphControl(name=instance, inputs=given, body=body, item_port=item))
    state.names[result] = _Reference(instance, 'result')


def _lower_call(state: _LoweringState, expression: ast.expr) -> _Reference:
    if not isinstance(expression, ast.Call) or not isinstance(expression.func, ast.Name):
        _reject(state, expression, 'only direct calls to registered tasks or graphs are supported')
    if expression.args or any(keyword.arg is None for keyword in expression.keywords):
        _reject(state, expression, 'calls require named arguments without unpacking')
    name = expression.func.id
    key = f'{state.key.partition(":")[0]}:{name}'
    if key not in SOURCES or (key not in _TASKS and key not in _GRAPHS):
        _reject(state, expression, f'unregistered call {name!r}')
    if name in state.names:
        _reject(state, expression, f'call target {name!r} is shadowed')
    state.used[name] += 1
    instance = name if state.used[name] == 1 else f'{name}_{state.used[name]}'
    if key in _GRAPHS:
        body = _lower_registered_graph(key, state.stack)
        ports = body.inputs
        outputs = body.outputs

        def make_task(inputs: dict[str, t.Any]) -> ProcessTask | SubgraphTask:
            return SubgraphTask(name=instance, inputs=inputs, body=body)
    else:
        spec = _TASKS[key].task_spec
        ports = spec.inputs
        outputs = spec.outputs

        def make_task(inputs: dict[str, t.Any]) -> ProcessTask | SubgraphTask:
            return ProcessTask(name=instance, inputs=inputs, spec=spec)

    if len(outputs) != 1:
        _reject(state, expression, f'{name!r} must declare exactly one output')
    given: dict[str, t.Any] = {}
    for keyword in expression.keywords:
        port = keyword.arg
        assert port is not None
        if port in given or port not in ports:
            _reject(state, keyword, f'duplicate or unknown input {port!r} of {name!r}')
        value = _lower_value(state, keyword.value)
        _wire(state, instance, port, value, given)
    state.tasks.append(make_task(given))
    return _Reference(instance, next(iter(outputs)))


def _lower_value(
    state: _LoweringState, expression: ast.expr, *, allow_call: bool = False
) -> _Reference | int | float | str | bool:
    if isinstance(expression, ast.Name):
        if expression.id not in state.names:
            _reject(state, expression, f'unbound name {expression.id!r}')
        return state.names[expression.id]
    if isinstance(expression, ast.Constant) and isinstance(expression.value, (int, float, str, bool)):
        return expression.value
    if allow_call and isinstance(expression, ast.Call):
        return _lower_call(state, expression)
    _reject(state, expression, 'unsupported expression')


def _reject(state: _LoweringState, node: ast.AST, reason: str) -> t.NoReturn:
    """Point at the offending node in the original file, not just the extracted function."""
    source = SOURCES[state.key].splitlines()
    location = _LOCATIONS[state.key]
    line = getattr(node, 'lineno', None)
    column = getattr(node, 'col_offset', None)
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


def _lower_registered_graph(key: str, stack: tuple[str, ...]) -> GraphSpec:
    if key not in _GRAPHS:
        msg = f'Graph {key} is not registered'
        raise UnsupportedSyntax(msg)
    if key in stack:
        msg = f'Recursive graph call: {" -> ".join((*stack, key))}'
        raise UnsupportedSyntax(msg)
    return _lower_function(_LoweringState(key, (*stack, key)))


def build_from_source(function: Callable[..., t.Any]) -> GraphSpec:
    """Build a GraphSpec from a registered graph's source and its registered callees."""
    if isinstance(function, SourceGraphHandle):
        function = function._function
    return _lower_registered_graph(_key(function), ())
