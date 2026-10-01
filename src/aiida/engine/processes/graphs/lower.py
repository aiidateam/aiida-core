###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Lower restricted graph source to GraphSpec without executing graph bodies.

The decorators capture definitions; lowering never executes graph bodies.
"""

from __future__ import annotations

import ast
import inspect
import textwrap
import typing as t
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field

from aiida.engine.processes.graphs.build import task as build_task
from aiida.engine.processes.graphs.spec import Dependency, Endpoint, GraphSpec, ProcessTask, SubgraphTask

# The source decorators are imported explicitly from this module, since ``graph``
# would otherwise shadow the graph-builder decorator exported by ``aiida.engine``.
__all__ = ('UnsupportedSyntax', 'lower_to_graph_spec', 'parse_graph')


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


def task(function: Callable[..., t.Any]) -> t.Any:
    """Register a Python function as an AiiDA task and save its source."""
    key = _register(function)
    decorated = build_task(function)
    _TASKS[key] = decorated
    return decorated


def graph(function: Callable[..., t.Any]) -> Callable[..., t.Any]:
    """Save a graph's source without executing its body."""
    _GRAPHS.add(_register(function))
    return function


@dataclass(frozen=True)
class _Reference:
    task: str | None  # None denotes a graph input.
    port: str


@dataclass
class _LoweringState:
    key: str
    stack: tuple[str, ...]
    tasks: list[ProcessTask | SubgraphTask] = field(default_factory=list)
    dependencies: list[Dependency] = field(default_factory=list)
    inputs: dict[str, list[tuple[str, str]]] = field(default_factory=dict)
    names: dict[str, _Reference] = field(default_factory=dict)
    used: Counter[str] = field(default_factory=Counter)


def _lower_function(state: _LoweringState) -> GraphSpec:
    source = SOURCES[state.key]
    module = ast.parse(source)
    if len(module.body) != 1 or not isinstance(module.body[0], ast.FunctionDef):
        msg = f'{state.key}: expected one function definition'
        raise UnsupportedSyntax(msg)
    function = module.body[0]
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
        if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
            _reject(state, statement, 'only single-name assignments are supported')
        target = statement.targets[0]
        if not isinstance(target, ast.Name) or target.id in state.names:
            _reject(state, statement, 'assignment must bind a new name')
        if not isinstance(statement.value, ast.Call):
            _reject(state, statement.value, 'graph assignments must call a registered task or graph')
        state.names[target.id] = _lower_call(state, statement.value)
    result = statements[-1].value
    if result is None:
        _reject(state, statements[-1], 'return must name a task or graph input')
    output = _lower_value(state, result, allow_call=True)
    if not isinstance(output, _Reference):
        _reject(state, result, 'return must name a task or graph input')
    return GraphSpec(
        tasks=tuple(state.tasks),
        dependencies=tuple(state.dependencies),
        inputs={name: tuple(targets) for name, targets in state.inputs.items()},
        outputs={output.port: Endpoint(task=output.task, port=output.port)},
        identifier=state.key.partition(':')[2],
    )


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
        if isinstance(value, _Reference):
            if value.task is None:
                state.inputs[value.port].append((instance, port))
            else:
                state.dependencies.append(Dependency(value.task, instance, value.port, port))
        else:
            given[port] = value
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


def lower_to_graph_spec(function: Callable[..., t.Any]) -> GraphSpec:
    """Lower a registered graph and its registered callees to a GraphSpec."""
    return _lower_registered_graph(_key(function), ())


def parse_graph(function: Callable[..., t.Any]) -> GraphSpec:
    """Build a GraphSpec from the source of a registered graph."""
    return lower_to_graph_spec(function)
