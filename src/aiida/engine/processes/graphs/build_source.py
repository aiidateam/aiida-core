###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Build a GraphSpec from restricted graph source without executing graph bodies.

Lowering retrieves each graph definition once and passes it through the parser without further registry reads.
Graph bodies are never executed.
"""

from __future__ import annotations

import ast
import inspect
import typing as t
from collections import Counter
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

from aiida.common.exceptions import UnsupportedSyntax
from aiida.engine.processes.graphs.inputs import place
from aiida.engine.processes.graphs.interface import GraphHandle
from aiida.engine.processes.graphs.shapes import (
    NamespaceShape,
    Shape,
    dump_shape,
    shape_for_annotation,
    shape_for_annotations,
)
from aiida.engine.processes.graphs.spec import Dependency, Endpoint, GraphSpec, ProcessTask, Route, TaskSpec
from aiida.engine.processes.graphs.tasks import (
    _SOURCE_REGISTRY,
    TaskHandle,
    _key,
    _SourceDefinition,
    build_task,
)

__all__ = ('UnsupportedSyntax', 'build_from_source', 'graph', 'task')

P = t.ParamSpec('P')
R = t.TypeVar('R')


def _resolve_binding(function: Callable[..., t.Any], name: str) -> object:
    """Return the call target visible where the graph was declared, without invoking it."""
    return function.__globals__.get(name)


def _task_spec_for(target: object) -> TaskSpec | None:
    """Return the declaration of a task handle, or `None` for other call targets."""
    return target.task_spec if isinstance(target, TaskHandle) else None


@t.overload
def task(function: Callable[P, R]) -> TaskHandle[P, R]: ...


@t.overload
def task(
    function: None = None, *, outputs: tuple[str, ...] | None = None
) -> Callable[[Callable[P, R]], TaskHandle[P, R]]: ...


def task(function: Callable[..., t.Any] | None = None, *, outputs: tuple[str, ...] | None = None) -> t.Any:
    """Register an importable task with static outputs and fixed input namespaces.

    :param function: the function to decorate.
    :param outputs: optional names for leaf outputs, returned as a tuple in this order.
    :return: a callable, launchable task handle.
    """

    def decorator(function: Callable[..., t.Any]) -> t.Any:
        _key(function)
        try:
            inspect.get_annotations(function, eval_str=True)
        except (NameError, AttributeError) as exception:
            msg = f'Cannot resolve type hints for task `{function.__qualname__}`: {exception}'
            raise TypeError(msg) from exception
        handle = build_task(function, outputs=outputs)
        _SOURCE_REGISTRY.register(function, kind='task')
        return handle

    return decorator(function) if function is not None else decorator


@t.overload
def graph(function: Callable[..., t.Any]) -> GraphHandle: ...


@t.overload
def graph(function: None = None, *, identifier: str | None = None) -> Callable[[Callable[..., t.Any]], GraphHandle]: ...
def graph(function: Callable[..., t.Any] | None = None, *, identifier: str | None = None) -> t.Any:
    """Save a graph's source without executing its body.

    The body is never executed: its source is captured at decoration time and lowered to a declaration by
    :func:`build_from_source` (or the ``build`` method of the returned handle) when the graph runs.

    Example usage:

    >>> from aiida.engine.processes.graphs.build_source import graph, task
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
    >>> declaration = add_twice.build()

    A graph is launched like any other process, by passing it to ``run`` or ``submit``. Use ``build`` to get the
    declaration on its own, without running anything.

    :param function: The function to decorate.
    :param identifier: Name of the graph, which defaults to the name of the function.
    :return: A handle that can build, run, or submit the graph.
    """

    def decorator(function: Callable[..., t.Any]) -> GraphHandle:
        _SOURCE_REGISTRY.register(function, kind='graph')
        return GraphHandle(function, identifier=identifier)

    if function is not None:
        return decorator(function)

    return decorator


@dataclass(frozen=True)
class _Reference:
    """A parsed reference to a leaf or fixed input namespace."""

    task: str | None  # None denotes a graph input.
    port: str
    shape: Shape


@dataclass
class _LoweringState:
    definition: _SourceDefinition
    stack: tuple[str, ...]
    tasks: list[ProcessTask] = field(default_factory=list)
    dependencies: list[Dependency] = field(default_factory=list)
    inputs: dict[str, list[Route]] = field(default_factory=dict)
    names: dict[str, _Reference] = field(default_factory=dict)
    used: Counter[str] = field(default_factory=Counter)

    @property
    def key(self) -> str:
        return self.definition.key


def _parse_function(definition: _SourceDefinition) -> ast.FunctionDef:
    module = ast.parse(definition.source)
    if len(module.body) != 1 or not isinstance(module.body[0], ast.FunctionDef):
        msg = f'{definition.key}: expected one function definition'
        raise UnsupportedSyntax(msg)
    return module.body[0]


def _check_signature(state: _LoweringState, function: ast.FunctionDef) -> None:
    """Reject parameter kinds the graph compiler cannot represent."""
    if function.args.posonlyargs or function.args.kwonlyargs or function.args.vararg or function.args.kwarg:
        msg = f'{state.key}: only ordinary positional parameters are supported'
        raise UnsupportedSyntax(msg)
    if function.args.defaults or any(default is not None for default in function.args.kw_defaults):
        msg = f'{state.key}: parameter defaults are not supported'
        raise UnsupportedSyntax(msg)


def _declare_graph_inputs(state: _LoweringState, function: ast.FunctionDef) -> NamespaceShape:
    """Route every graph parameter to its input shape."""
    boundary = shape_for_annotations(state.definition.hints, tuple(arg.arg for arg in function.args.args))
    for arg in function.args.args:
        state.inputs[arg.arg] = []
        shape = boundary.select(arg.arg)
        state.names[arg.arg] = _Reference(None, arg.arg, shape)
    return boundary


def _lower_function(state: _LoweringState) -> GraphSpec:
    function = _parse_function(state.definition)
    _check_signature(state, function)
    boundary = _declare_graph_inputs(state, function)
    statements = function.body
    if statements and isinstance(statements[0], ast.Expr) and isinstance(statements[0].value, ast.Constant):
        if isinstance(statements[0].value.value, str):
            statements = statements[1:]
    if not statements or not isinstance(statements[-1], ast.Return):
        msg = f'{state.key}: graph must end in a return'
        raise UnsupportedSyntax(msg)
    for statement in statements[:-1]:
        if isinstance(statement, ast.If):
            _reject(state, statement, 'conditional branches are not supported')
        elif isinstance(statement, ast.While):
            _reject(state, statement, 'loops are not supported')
        else:
            _lower_assignment(state, statement)
    result = statements[-1].value
    if result is None:
        _reject(state, statements[-1], 'return must name a task or graph input')
    outputs, output_typehints = _lower_outputs(state, result)
    return GraphSpec(
        tasks=tuple(state.tasks),
        dependencies=tuple(state.dependencies),
        inputs={name: tuple(targets) for name, targets in state.inputs.items()},
        outputs=outputs,
        identifier=state.key.partition(':')[2],
        result_path=next(iter(outputs)) if len(outputs) == 1 else '',
        output_typehints=output_typehints,
        input_namespace=dump_shape(boundary),
    )


def _lower_outputs(state: _LoweringState, result: ast.expr) -> tuple[dict[str, Endpoint], dict[str, tuple[type, ...]]]:
    """Lower the return statement to named endpoints and their type hints."""
    hints = state.definition.hints
    references = _lower_return(state, result)
    returned = shape_for_annotation(hints.get('return'))
    if isinstance(returned, NamespaceShape):
        _reject(state, result, 'graph output namespaces are not supported')
    outputs = {name: Endpoint(task=reference.task, port=reference.port) for name, reference in references.items()}
    typehints = {next(iter(outputs)): returned.types} if len(outputs) == 1 and returned.types else {}
    return outputs, typehints


def _lower_return(state: _LoweringState, expression: ast.expr) -> dict[str, _Reference]:
    """Return a leaf reference or an explicit mapping of named leaf outputs."""
    if isinstance(expression, ast.Dict):
        outputs = {}
        for key, value in zip(expression.keys, expression.values, strict=True):
            if not isinstance(key, ast.Constant) or not isinstance(key.value, str) or not key.value.isidentifier():
                _reject(state, expression, 'output names must be identifier string literals')
            if key.value in outputs:
                _reject(state, expression, 'duplicate graph output')
            reference = _lower_value(state, value, allow_call=True)
            if not isinstance(reference, _Reference) or isinstance(reference.shape, NamespaceShape):
                _reject(state, value, 'graph outputs must select static leaves')
            outputs[key.value] = reference
        return outputs
    reference = _lower_value(state, expression, allow_call=True)
    if not isinstance(reference, _Reference) or not reference.port or isinstance(reference.shape, NamespaceShape):
        _reject(state, expression, 'return must select a task output or graph input leaf')
    return {reference.port.split('.')[-1]: reference}


def _lower_assignment(state: _LoweringState, statement: ast.stmt) -> str:
    if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
        _reject(state, statement, 'only single-name assignments are supported')
    target = statement.targets[0]
    if not isinstance(target, ast.Name) or target.id in state.names:
        _reject(state, statement, 'assignment must bind a new name')
    if not isinstance(statement.value, ast.Call):
        _reject(state, statement.value, 'graph assignments must call a registered task or graph')
    state.names[target.id] = _lower_call(state, statement.value)
    return target.id


def _lower_call(state: _LoweringState, expression: ast.expr) -> _Reference:
    if not isinstance(expression, ast.Call) or not isinstance(expression.func, ast.Name):
        _reject(state, expression, 'only direct calls to registered tasks or graphs are supported')
    if expression.args or any(keyword.arg is None for keyword in expression.keywords):
        _reject(state, expression, 'calls require named arguments without unpacking')
    name = expression.func.id
    if name in state.names:
        _reject(state, expression, f'call target {name!r} is shadowed')
    target = _resolve_binding(state.definition.function, name)
    if isinstance(target, GraphHandle):
        _reject(state, expression, 'nested graphs are not supported')
    spec = _task_spec_for(target)
    if spec is None:
        _reject(state, expression, f'unregistered call {name!r}')
    assert spec is not None
    inputs = spec.input_shape
    result_port = spec.result_port
    result_shape = spec.result_shape
    state.used[name] += 1
    count = state.used[name]
    instance = name if count == 1 else f'{name}_{count}'
    taken = {task.name for task in state.tasks}
    while instance in taken:
        count += 1
        instance = f'{name}_{count}'
    state.used[name] = count

    given = _lower_keywords(state, instance, name, inputs, expression.keywords)
    missing = _required_missing(state, instance, inputs, given)
    if missing:
        _reject(state, expression, f'task {name!r} is missing required inputs: {missing}')
    state.tasks.append(ProcessTask(name=instance, inputs=given, spec=spec))
    return _Reference(instance, result_port, result_shape)


def _lower_keywords(
    state: _LoweringState, instance: str, name: str, inputs: NamespaceShape, keywords: list[ast.keyword]
) -> dict[str, t.Any]:
    """Wire one call's arguments to literals, references, and ordering edges."""
    given: dict[str, t.Any] = {}
    seen = set()
    for keyword in keywords:
        port = keyword.arg
        assert port is not None
        if port in seen:
            _reject(state, keyword, f'duplicate input {port!r}')
        seen.add(port)
        if port == 'after':
            ordered = keyword.value.elts if isinstance(keyword.value, (ast.Tuple, ast.List)) else [keyword.value]
            for predecessor in ordered:
                reference = _lower_value(state, predecessor)
                if not isinstance(reference, _Reference) or reference.task is None:
                    _reject(state, predecessor, 'after must name a previously placed task')
                state.dependencies.append(Dependency(reference.task, instance))
            continue
        if port in given:
            _reject(state, keyword, f'duplicate or unknown input {port!r} of {name!r}')
        try:
            shape = inputs.select(port)
        except KeyError:
            _reject(state, keyword, f'duplicate or unknown input {port!r} of {name!r}')
        _lower_input(state, instance, port, keyword.value, shape, given)
    return given


def _required_missing(
    state: _LoweringState, instance: str, shape: NamespaceShape, given: t.Any, prefix: str = ''
) -> list[str]:
    """Return the required task inputs that are neither wired nor routed from graph inputs."""
    missing = []
    mapping = given if isinstance(given, Mapping) else {}
    for field_name, child in shape.fields:
        path = f'{prefix}.{field_name}' if prefix else field_name
        if isinstance(child, NamespaceShape):
            missing.extend(_required_missing(state, instance, child, mapping.get(field_name), path))
        elif child.required and field_name not in mapping and not _routed(state, instance, path):
            missing.append(path)
    return missing


def _routed(state: _LoweringState, instance: str, path: str) -> bool:
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
    if not isinstance(value, _Reference):
        place(given, port, value)
    elif value.task is None:
        state.inputs.setdefault(value.port, []).append(Route(instance, port))
    else:
        state.dependencies.append(Dependency(value.task, instance, value.port, port))


def _lower_input(
    state: _LoweringState, instance: str, path: str, expression: ast.expr, shape: Shape, given: dict[str, t.Any]
) -> None:
    """Expand dictionary syntax only for declared fixed input namespaces."""
    if isinstance(expression, ast.Dict) and isinstance(shape, NamespaceShape):
        place(given, path, {})
        seen = set()
        for key, value in zip(expression.keys, expression.values, strict=True):
            if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
                _reject(state, expression, 'namespace keys must be string literals without unpacking')
            name = key.value
            if name in seen:
                _reject(state, expression, f'duplicate or unknown namespace input {name!r}')
            try:
                child = shape.select(name)
            except KeyError:
                _reject(state, expression, f'duplicate or unknown namespace input {name!r}')
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
    if isinstance(expression, ast.Attribute):
        return _lower_selection(state, expression, allow_call=allow_call)
    if isinstance(expression, ast.Name):
        if expression.id not in state.names:
            _reject(state, expression, f'unbound name {expression.id!r}')
        return state.names[expression.id]
    if isinstance(expression, ast.Constant) and (
        expression.value is None or isinstance(expression.value, (int, float, str, bool))
    ):
        return expression.value
    if allow_call and isinstance(expression, ast.Call):
        return _lower_call(state, expression)
    _reject(state, expression, 'unsupported expression')


def _lower_selection(state: _LoweringState, expression: ast.Attribute, *, allow_call: bool = False) -> _Reference:
    """Resolve dotted access to a task output or a declared namespace field."""
    parent = _lower_value(state, expression.value, allow_call=allow_call)
    if not isinstance(parent, _Reference):
        _reject(state, expression, 'selection must name a task output or declared input namespace')
    if not isinstance(parent.shape, NamespaceShape):
        if parent.task is not None and parent.port == expression.attr:
            return parent
        _reject(state, expression, 'selection requires a declared namespace')
    path = f'{parent.port}.{expression.attr}' if parent.port else expression.attr
    try:
        shape = parent.shape.select(expression.attr)
    except KeyError:
        _reject(state, expression, f'unknown or undeclared namespace field {path!r}')
    return _Reference(parent.task, path, shape)


def _reject(state: _LoweringState, node: ast.AST, reason: str) -> t.NoReturn:
    """Point at the offending node in the original file, not just the extracted function."""
    source = state.definition.source.splitlines()
    location = state.definition
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
    definition = _SOURCE_REGISTRY.get_graph(key)
    if key in stack:
        msg = f'Recursive graph call: {" -> ".join((*stack, key))}'
        raise UnsupportedSyntax(msg)
    return _lower_function(_LoweringState(definition, (*stack, key)))


def build_from_source(function: Callable[..., t.Any]) -> GraphSpec:
    """Build a GraphSpec from a registered graph's source and its registered callees."""
    if isinstance(function, GraphHandle):
        function = function._function
    return _lower_registered_graph(_key(function), ())
