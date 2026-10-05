###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Build a GraphSpec from restricted graph source without executing graph bodies.

Only the source decorators populate this module's registry; execution authoring does not use it.
Lowering retrieves each graph definition once and passes it through the parser without further registry reads.
Source-based building never executes graph bodies.
"""

from __future__ import annotations

import ast
import inspect
import textwrap
import typing as t
from collections import Counter
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from aiida.engine.processes.graphs.build_execution import ProcessHandle
from aiida.engine.processes.graphs.build_execution import task as build_task
from aiida.engine.processes.graphs.inputs import dump_port, namespace_for_annotations, namespace_for_outputs
from aiida.engine.processes.graphs.interface import GraphHandle
from aiida.engine.processes.graphs.run import place
from aiida.engine.processes.graphs.source_bindings import resolve_binding, task_spec_for
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
from aiida.engine.processes.port_model import fields_of, without_marks
from aiida.engine.processes.ports import OutputPort, PortNamespace, infer_valid_type_from_type_annotation

# The source decorators are imported explicitly from this module, since ``graph``
# would otherwise shadow the graph-builder decorator exported by ``aiida.engine``.
__all__ = ('SourceGraphHandle', 'UnsupportedSyntax', 'build_from_source')


class UnsupportedSyntax(ValueError):  # noqa: N818 - keep the prototype's exception name
    """A registered graph contains syntax the source parser cannot represent."""


@dataclass(frozen=True)
class _SourceDefinition:
    """A source decorator's captured definition, owned independently of registry lookups."""

    key: str
    kind: t.Literal['graph', 'task']
    function: Callable[..., t.Any]
    source: str
    filename: str
    first_line: int
    hints: Mapping[str, t.Any]


class _SourceRegistry:
    """Own definitions registered exclusively by ``graph_source`` and ``task_source``."""

    def __init__(self) -> None:
        self._definitions: dict[str, _SourceDefinition] = {}

    def register(self, function: Callable[..., t.Any], *, kind: t.Literal['graph', 'task']) -> None:
        """Capture a definition atomically, without executing its body."""
        key = _key(function)
        if key in self._definitions:
            msg = f'Duplicate registered function {key}'
            raise UnsupportedSyntax(msg)
        lines, first_line = inspect.getsourcelines(function)
        definition = _SourceDefinition(
            key=key,
            kind=kind,
            function=function,
            source=textwrap.dedent(''.join(lines)),
            filename=inspect.getsourcefile(function) or '<unknown>',
            first_line=first_line,
            hints=MappingProxyType(t.get_type_hints(function, include_extras=True)),
        )
        self._definitions[key] = definition

    def get_graph(self, key: str) -> _SourceDefinition:
        """Retrieve a source graph once, at the entry to its lowering pipeline."""
        definition = self._definitions.get(key)
        if definition is None or definition.kind != 'graph':
            msg = f'Graph {key} is not registered'
            raise UnsupportedSyntax(msg)
        return definition


_SOURCE_REGISTRY = _SourceRegistry()
"""The source authoring module owns the single production registry instance."""


def _key(function: Callable[..., t.Any]) -> str:
    if function.__qualname__ != function.__name__:
        raise UnsupportedSyntax('Registered functions must be defined at module scope')
    return f'{function.__module__}:{function.__name__}'


class SourceGraphHandle(GraphHandle):
    """A graph that builds by lowering its registered source, without executing its body."""

    def build(self) -> GraphSpec:
        """Return the graph that the function declares, lowered from its registered source."""
        return build_from_source(self._function)


def task(function: Callable[..., t.Any]) -> t.Any:
    """Register a Python function as an AiiDA task and save its source."""
    try:
        inspect.get_annotations(function, eval_str=True)
    except (NameError, AttributeError) as exception:
        msg = f'Cannot resolve type hints for task `{function.__qualname__}`: {exception}'
        raise TypeError(msg) from exception
    _SOURCE_REGISTRY.register(function, kind='task')
    return build_task(function)


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
        _SOURCE_REGISTRY.register(function, kind='graph')
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
    definition: _SourceDefinition
    stack: tuple[str, ...]
    tasks: list[ProcessTask | SubgraphTask | BranchControl | LoopControl | MapGraphControl] = field(
        default_factory=list
    )
    dependencies: list[Dependency] = field(default_factory=list)
    inputs: dict[str, list[tuple[str, str]]] = field(default_factory=dict)
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


def _lower_function(state: _LoweringState) -> GraphSpec:
    function = _parse_function(state.definition)
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
    hints = state.definition.hints
    outputs = _lower_return(state, result, hints.get('return'))
    output_hint = infer_valid_type_from_type_annotation(hints.get('return'))
    output_namespace = namespace_for_outputs(hints.get('return'))
    return GraphSpec(
        tasks=tuple(state.tasks),
        dependencies=tuple(state.dependencies),
        inputs={name: tuple(targets) for name, targets in state.inputs.items()},
        outputs=outputs,
        identifier=state.key.partition(':')[2],
        input_typehints={
            name: hint for name in state.inputs if (hint := infer_valid_type_from_type_annotation(hints.get(name)))
        },
        output_typehints=dict.fromkeys(outputs, output_hint) if len(outputs) == 1 and output_hint else {},
        output_namespace=dump_port(output_namespace, defaults=False) if output_namespace is not None else None,
        input_namespace=dump_port(namespace_for_annotations(hints, tuple(arg.arg for arg in function.args.args))),
    )


def _lower_return(
    state: _LoweringState, expression: ast.expr, annotation: t.Any = None, prefix: str = ''
) -> dict[str, Endpoint]:
    """Wire returned values against namespaces declared exclusively by PortModel annotations."""
    fields = fields_of(annotation)
    members: list[tuple[str, ast.expr]] | None = None
    if isinstance(expression, ast.Dict):
        _reject(
            state,
            expression,
            'graph namespace returns require PortModel values and a PortModel return annotation, not dictionaries',
        )
    if fields is not None and isinstance(expression, ast.Call) and isinstance(expression.func, ast.Name):
        if expression.func.id == annotation.__name__:
            if expression.args or any(keyword.arg is None for keyword in expression.keywords):
                _reject(state, expression, 'structured returns require named fields')
            members = [(t.cast(str, keyword.arg), keyword.value) for keyword in expression.keywords]
    if members is not None:
        outputs: dict[str, Endpoint] = {}
        annotations = {field.name: field.annotation for field in fields or ()}
        for name, value in members:
            if name not in annotations:
                _reject(
                    state,
                    expression,
                    f'graph output {prefix}{name!r} is not declared by its PortModel return annotation',
                )
            lowered = _lower_return(state, value, annotations.get(name), f'{prefix}{name}.')
            if outputs.keys() & lowered.keys():
                _reject(state, expression, 'duplicate graph output')
            outputs.update(lowered)
        return outputs
    reference = _lower_value(state, expression, allow_call=True)
    if not isinstance(reference, _Reference) or (not reference.port and fields is None):
        _reject(state, expression, 'return must select a task output or graph input')
    if fields is not None:

        def expand(annotation: t.Any, target: str, source: str) -> dict[str, Endpoint]:
            children = fields_of(annotation)
            if children is None:
                return {target: Endpoint(task=reference.task, port=source)}
            expanded = {}
            for child in children:
                expanded.update(
                    expand(
                        child.annotation,
                        f'{target}.{child.name}' if target else child.name,
                        f'{source}.{child.name}' if source else child.name,
                    )
                )
            return expanded

        source_path = reference.port
        if reference.task is not None and isinstance(expression, (ast.Name, ast.Call)):
            task = next(task for task in state.tasks if task.name == reference.task)
            declared = task.spec.outputs if isinstance(task, ProcessTask) else task.body.output_spec()
            if declared.keys() == {field.name for field in fields}:
                source_path = ''
        return expand(annotation, prefix.rstrip('.'), source_path)
    name = prefix.rstrip('.') if prefix else reference.port
    return {name: Endpoint(task=reference.task, port=reference.port)}


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


def _region_input_namespace(state: _LoweringState) -> dict[str, t.Any] | None:
    """Snapshot region boundaries only when routing a declared namespace field."""
    if not any('.' in path for path in state.inputs):
        return None
    names = tuple(name for name in state.inputs if '.' not in name)
    return dump_port(namespace_for_annotations(state.definition.hints, names))


def _body(state: _LoweringState, outputs: dict[str, _Reference]) -> GraphSpec:
    return GraphSpec(
        tasks=tuple(state.tasks),
        dependencies=tuple(state.dependencies),
        inputs={name: tuple(targets) for name, targets in state.inputs.items()},
        outputs={name: Endpoint(task=ref.task, port=ref.port) for name, ref in outputs.items()},
        input_namespace=_region_input_namespace(state),
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
    child = _LoweringState(state.definition, state.stack)
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
    value: _Reference | int | float | str | bool | None,
    given: dict[str, t.Any],
) -> None:
    if not isinstance(value, _Reference):
        place(given, port, value)
    elif value.task is None:
        state.inputs.setdefault(value.port, []).append((instance, port))
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
        reference = child.names[name]
        task = next(task for task in child.tasks if task.name == reference.task)
        namespace = task.spec.outputs if isinstance(task, ProcessTask) else task.body.output_spec()
        if isinstance(task, SubgraphTask) and task.body.output_namespace is None:
            namespace = PortNamespace('outputs')
            for path in task.body.outputs:
                namespace[path] = OutputPort(path, valid_type=task.body.output_typehints.get(path))

        def expand(port: PortNamespace, prefix: str = '') -> dict[str, Endpoint]:
            outputs = {}
            for field_name, field_port in port.items():
                path = f'{prefix}.{field_name}' if prefix else field_name
                if isinstance(field_port, PortNamespace) and not field_port.dynamic and field_port:
                    outputs.update(expand(field_port, path))
                else:
                    outputs[path] = Endpoint(task=reference.task, port=path)
            return outputs

        body = GraphSpec(
            tasks=tuple(child.tasks),
            dependencies=tuple(child.dependencies),
            inputs={name: tuple(targets) for name, targets in child.inputs.items()},
            outputs=expand(namespace),
            output_namespace=dump_port(namespace, defaults=False),
            input_namespace=_region_input_namespace(child),
        )
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
    namespace = sides[0][2].output_spec()
    scalar = set(namespace) == {'result'} and not isinstance(namespace['result'], PortNamespace)
    state.names[sides[0][0]] = _Reference(instance, 'result' if scalar else '')


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
    if name in state.names:
        _reject(state, expression, f'call target {name!r} is shadowed')
    target = resolve_binding(state.definition.function, name)
    if isinstance(target, ProcessHandle) and target.is_prepared:
        _reject(state, expression, 'inject prepared handles with GraphHandle.bind_tasks instead of module globals')
    spec = task_spec_for(target)
    if spec is None and not isinstance(target, SourceGraphHandle):
        _reject(state, expression, f'unregistered call {name!r}')
    state.used[name] += 1
    instance = name if state.used[name] == 1 else f'{name}_{state.used[name]}'
    inputs: t.Collection[str]
    outputs: t.Collection[str]
    if isinstance(target, SourceGraphHandle):
        body = _lower_registered_graph(_key(target._function), state.stack)
        inputs = body.inputs
        outputs = body.outputs

        def make_task(inputs: dict[str, t.Any]) -> ProcessTask | SubgraphTask:
            return SubgraphTask(name=instance, inputs=inputs, body=body)
    else:
        assert spec is not None
        inputs = spec.inputs
        outputs = spec.outputs

        def make_task(inputs: dict[str, t.Any]) -> ProcessTask | SubgraphTask:
            return ProcessTask(name=instance, inputs=inputs, spec=spec)

    given: dict[str, t.Any] = {}
    for keyword in expression.keywords:
        port = keyword.arg
        assert port is not None
        if port in given or port not in inputs:
            _reject(state, keyword, f'duplicate or unknown input {port!r} of {name!r}')
        port_spec = inputs.get(port) if isinstance(inputs, PortNamespace) else None
        _lower_input(state, instance, port, keyword.value, port_spec, given)
    state.tasks.append(make_task(given))
    return _Reference(instance, next(iter(outputs)) if len(outputs) == 1 else '')


def _lower_input(
    state: _LoweringState, instance: str, path: str, expression: ast.expr, port: t.Any, given: dict[str, t.Any]
) -> None:
    """Expand dictionary syntax only where the process declares a namespace."""
    if isinstance(expression, ast.Dict) and isinstance(port, PortNamespace):
        place(given, path, {})
        seen = set()
        for key, value in zip(expression.keys, expression.values, strict=True):
            if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
                _reject(state, expression, 'namespace keys must be string literals without unpacking')
            name = key.value
            if name in seen or (name not in port and not port.dynamic):
                _reject(state, expression, f'duplicate or unknown namespace input {name!r}')
            seen.add(name)
            _lower_input(state, instance, f'{path}.{name}', value, port.get(name), given)
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
        parent = _lower_value(state, expression.value, allow_call=allow_call)
        if not isinstance(parent, _Reference):
            _reject(state, expression, 'selection must name a task output or declared input namespace')
        path = f'{parent.port}.{expression.attr}' if parent.port else expression.attr
        if parent.task is None:
            root, *segments = path.split('.')
            annotation = state.definition.hints.get(root)
            for segment in segments:
                fields = fields_of(without_marks(annotation))
                selected = next((field for field in fields or () if field.name == segment), None)
                if selected is None:
                    _reject(state, expression, f'unknown or undeclared input namespace field {path!r}')
                annotation = selected.annotation
        elif isinstance(expression.value, ast.Name) and parent.port == expression.attr:
            path = parent.port
        return _Reference(parent.task, path)
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
    if isinstance(function, SourceGraphHandle):
        function = function._function
    return _lower_registered_graph(_key(function), ())
