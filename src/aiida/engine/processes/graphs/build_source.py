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
import copy
import inspect
import typing as t
from collections import Counter
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace

from aiida.common.exceptions import UnsupportedSyntax
from aiida.engine.processes.graphs.inputs import place
from aiida.engine.processes.graphs.interface import GraphHandle
from aiida.engine.processes.graphs.shapes import (
    NamespaceShape,
    Shape,
    dump_shape,
    json_default,
    shape_for_annotation,
    shape_for_annotations,
)
from aiida.engine.processes.graphs.spec import (
    CONDITION_PORT,
    BranchControl,
    Dependency,
    Endpoint,
    GraphSpec,
    LoopControl,
    ProcessTask,
    Route,
    SubgraphTask,
    TaskSpec,
)
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
        """Register the task source without executing its body."""
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
        """Register the graph source without executing its body."""
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
    """The placements, wirings, and references collected while lowering one graph body."""

    definition: _SourceDefinition
    stack: tuple[str, ...]
    tasks: list[ProcessTask | SubgraphTask | BranchControl | LoopControl] = field(default_factory=list)
    dependencies: list[Dependency] = field(default_factory=list)
    inputs: dict[str, list[Route]] = field(default_factory=dict)
    names: dict[str, _Reference] = field(default_factory=dict)
    used: Counter[str] = field(default_factory=Counter)

    @property
    def key(self) -> str:
        """Return the registry key of the lowered graph."""
        return self.definition.key


def _parse_function(definition: _SourceDefinition) -> ast.FunctionDef:
    module = ast.parse(definition.source)
    if len(module.body) != 1 or not isinstance(module.body[0], ast.FunctionDef):
        msg = f'{definition.key}: expected one function definition'
        raise UnsupportedSyntax(msg)
    return module.body[0]


def _check_signature(state: _LoweringState, function: ast.FunctionDef) -> None:
    """Reject parameter kinds the graph compiler cannot represent."""
    if function.args.vararg or function.args.kwarg:
        _reject(state, function, 'variadic parameters are not supported')


def _parameter_defaults(state: _LoweringState, function: ast.FunctionDef) -> dict[str, t.Any]:
    """Read literal parameter defaults, like the explicit model defaults."""
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
            value = ast.literal_eval(default)
        except (ValueError, TypeError, SyntaxError):
            _reject(state, default, f'parameter default for `{parameter.arg}` must be a literal')
        try:
            json_default(value)
        except TypeError:
            _reject(state, default, f'parameter default for `{parameter.arg}` must be a finite JSON value')
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
            _lower_branch(state, statement)
        elif isinstance(statement, ast.While):
            _lower_loop(state, statement)
        elif isinstance(statement, (ast.For, ast.AsyncFor)):
            _reject(state, statement, 'for loops are not supported; unroll the placements or use a while loop')
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


def _lower_assignment(state: _LoweringState, statement: ast.stmt, *, rebind: bool = False) -> str:
    if not isinstance(statement, ast.Assign) or not statement.targets:
        _reject(state, statement, 'only single-name assignments are supported')
    names = [target.id for target in statement.targets if isinstance(target, ast.Name)]
    if len(names) != len(statement.targets):
        _reject(state, statement, 'only single-name assignments are supported')
    for name in names:
        if name in state.names and not rebind:
            _reject(state, statement, 'assignment must bind a new name')
    if not isinstance(statement.value, ast.Call):
        _reject(state, statement.value, 'graph assignments must call a registered task or graph')
    ref = _lower_call(state, statement.value)
    for name in names:
        state.names[name] = ref
    return names[0]


def _lower_unpack(state: _LoweringState, statement: ast.Assign) -> None:
    """Bind each tuple element to one output of a multi-output call."""
    target = statement.targets[0]
    assert isinstance(target, ast.Tuple)
    names = [elt.id for elt in target.elts if isinstance(elt, ast.Name)]
    if not names or len(names) != len(target.elts) or any(name in state.names for name in names):
        _reject(state, statement, 'tuple assignment must bind new names')
    if not isinstance(statement.value, ast.Call):
        _reject(state, statement.value, 'graph assignments must call a registered task or graph')
    ref = _lower_call(state, statement.value)
    if not isinstance(ref.shape, NamespaceShape):
        if len(names) == 1:
            state.names[names[0]] = ref
            return
        _reject(state, statement.value, 'tuple assignment needs multiple outputs')
    fields = ref.shape.fields
    if len(names) != len(fields):
        _reject(state, statement, f'tuple assignment needs exactly {len(fields)} names for {len(fields)} outputs')
    for name, (field_name, field_shape) in zip(names, fields):
        state.names[name] = _Reference(ref.task, field_name, field_shape)


def _region_input_namespace(state: _LoweringState) -> dict[str, t.Any] | None:
    """Snapshot region boundaries only when routing a declared namespace field."""
    if not any('.' in path for path in state.inputs):
        return None
    names = tuple(name for name in state.inputs if '.' not in name)
    return dump_shape(NamespaceShape(fields=tuple((name, state.names[name].shape) for name in names)))


def _body(state: _LoweringState, outputs: dict[str, _Reference]) -> GraphSpec:
    if any(isinstance(reference.shape, NamespaceShape) for reference in outputs.values()):
        msg = 'control-flow outputs must be static leaves, not namespaces.'
        raise UnsupportedSyntax(msg)
    endpoints = {name: Endpoint(task=reference.task, port=reference.port) for name, reference in outputs.items()}
    return GraphSpec(
        tasks=tuple(state.tasks),
        dependencies=tuple(state.dependencies),
        inputs={name: tuple(targets) for name, targets in state.inputs.items()},
        outputs=endpoints,
        input_namespace=_region_input_namespace(state),
    )


def _region(state: _LoweringState, statements: list[ast.stmt]) -> _LoweringState:
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
        and id(node) not in callees
    }
    names = reads
    child = _LoweringState(state.definition, state.stack)
    for name in sorted(names):
        if name not in state.names:
            _reject(state, statements[0], f'unbound name {name!r}')
        child.inputs[name] = []
        shape = state.names[name].shape
        child.names[name] = _Reference(None, name, shape)
    return child


def _place(state: _LoweringState, child: _LoweringState, instance: str, given: dict[str, t.Any]) -> None:
    for name in child.inputs:
        if name in state.names:
            _wire(state, instance, name, state.names[name], given)


def _bind_condition(state: _LoweringState, test: ast.expr) -> ast.Name | None:
    """Lower a call condition to a fresh binding, like its explicit assignment form."""
    if not isinstance(test, ast.Call):
        return None
    name = 'condition'
    count = 2
    while name in state.names:
        name = f'condition_{count}'
        count += 1
    bound = ast.Assign(targets=[ast.Name(id=name)], value=test)
    ast.copy_location(bound, test)
    ast.copy_location(bound.targets[0], test)
    _lower_assignment(state, bound)
    return ast.Name(id=name)


def _lower_branch(state: _LoweringState, statement: ast.If) -> None:
    bound = _bind_condition(state, statement.test)
    if bound is not None:
        statement.test = bound
    if not statement.orelse or len(statement.body) != 1 or len(statement.orelse) != 1:
        _reject(state, statement, 'if requires one assignment to the same name on each side')
    sides = []
    for statements in (statement.body, statement.orelse):
        child = _region(state, statements)
        name = _lower_assignment(child, statements[0])
        reference = child.names[name]
        body = _body(child, {reference.port: reference})
        sides.append((name, child, body))
    if sides[0][0] != sides[1][0] or sides[0][0] in state.names:
        _reject(state, statement, 'if requires one new name shared by both sides')
    if CONDITION_PORT in sides[0][2].inputs or CONDITION_PORT in sides[1][2].inputs:
        _reject(state, statement, 'condition conflicts with a branch input')
    instance = f'branch_{len(state.tasks) + 1}'
    given: dict[str, t.Any] = {}
    _wire(state, instance, CONDITION_PORT, _lower_value(state, statement.test), given)
    for name in sorted({path.split('.')[0] for _, child, _ in sides for path in child.inputs}):
        _wire(state, instance, name, state.names[name], given)
    state.tasks.append(BranchControl(name=instance, inputs=given, body=sides[0][2], otherwise=sides[1][2]))
    selected = sides[0][1].names[sides[0][0]]
    state.names[sides[0][0]] = _Reference(instance, selected.port, selected.shape)


def _lower_loop(state: _LoweringState, statement: ast.While) -> None:
    bound = _bind_condition(state, statement.test)
    if bound is not None:
        update = ast.Assign(targets=[ast.Name(id=bound.id)], value=copy.deepcopy(statement.test))
        ast.copy_location(update, statement.test)
        ast.copy_location(update.targets[0], statement.test)
        statement.body.append(update)
        statement.test = bound
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
        child.names[name] = _Reference(None, name, state.names[name].shape)
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
        state.names[name] = _Reference(instance, name, child.names[name].shape)


def _lower_call(state: _LoweringState, expression: ast.expr) -> _Reference:
    if not isinstance(expression, ast.Call) or not isinstance(expression.func, ast.Name):
        _reject(state, expression, 'only direct calls to registered tasks or graphs are supported')
    name = expression.func.id
    if name in state.names:
        _reject(state, expression, f'call target {name!r} is shadowed')
    target = _resolve_binding(state.definition.function, name)
    spec = _task_spec_for(target)
    if spec is None and not isinstance(target, GraphHandle):
        _reject(state, expression, f'unregistered call {name!r}')
    state.used[name] += 1
    count = state.used[name]
    instance = name if count == 1 else f'{name}_{count}'
    taken = {placed.name for placed in state.tasks}
    while instance in taken:
        count += 1
        instance = f'{name}_{count}'
    state.used[name] = count
    inputs: NamespaceShape
    result_port: str
    result_shape: Shape
    if isinstance(target, GraphHandle):
        body = _lower_registered_graph(_key(target._function), state.stack)
        inputs = body.input_shape
        result_port = body.result_port
        result_shape = body.result_shape
        task: ProcessTask | SubgraphTask = SubgraphTask(name=instance, inputs={}, body=body)
    else:
        assert spec is not None
        inputs = spec.input_shape
        result_port = spec.result_port
        result_shape = spec.result_shape
        task = ProcessTask(name=instance, inputs={}, spec=spec)

    keywords = _named_keywords(state, expression, name, inputs)
    task = replace(task, inputs=_lower_keywords(state, instance, name, inputs, keywords))
    missing = _required_missing(state, instance, inputs, task.inputs)
    if missing:
        _reject(state, expression, f'task {name!r} is missing required inputs: {missing}')
    state.tasks.append(task)
    return _Reference(instance, result_port, result_shape)


def _named_keywords(
    state: _LoweringState, expression: ast.Call, name: str, inputs: NamespaceShape
) -> list[ast.keyword]:
    """Bind positional arguments through declared input order, like the explicit keywords."""
    if not expression.args:
        keywords = list(expression.keywords)
    else:
        order = [field for field, _ in inputs.fields]
        if len(expression.args) > len(order):
            _reject(state, expression, f'too many positional arguments for `{name}`')
        keywords = [ast.keyword(arg=field, value=arg) for field, arg in zip(order, expression.args)]
        keywords.extend(expression.keywords)
    if any(keyword.arg is None for keyword in keywords):
        _reject(state, expression, 'calls require named arguments without unpacking')
    return keywords


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
