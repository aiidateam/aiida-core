###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file      #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Check static graph declarations before scheduling."""

from __future__ import annotations

import typing as t

from aiida.common.exceptions import GraphTypeCheckError
from aiida.engine.processes.graphs.ir import (
    BranchControl,
    Endpoint,
    InlineOperation,
    LoopControl,
    MapControl,
    OutputTree,
    _input_ports_at,
    _port_at,
    branch_shapes_agree,
)
from aiida.engine.processes.graphs.operations import (
    BINARY_OPERATIONS,
    LEFT_PORT,
    OPERAND_PORT,
    RIGHT_PORT,
    infer_operation_shape,
)
from aiida.engine.processes.ports import OutputPort, PortNamespace, _infer_node_types
from aiida.orm.nodes.data.datanode import DataNode

if t.TYPE_CHECKING:
    from aiida.engine.processes.graphs.ir import Dependency, GraphIR, GraphTask, Route


def validate_graph(graph: GraphIR) -> None:
    """Check names, inputs, dependencies, regions, outputs, and acyclicity."""
    if len(set(graph.task_names)) != len(graph.task_names):
        duplicates = sorted({name for name in graph.task_names if graph.task_names.count(name) > 1})
        msg = f'task names must be unique; duplicated: {", ".join(duplicates)}.'
        raise GraphTypeCheckError(msg)
    boundary = graph.build_input_namespace()
    _validate_inputs(graph, boundary)
    _validate_dependencies(graph)
    for task in graph.tasks:
        try:
            task.input_ports()
            task.output_ports()
        except GraphTypeCheckError as exception:
            msg = f'task `{task.name}` declares ports the spec cannot represent.'
            raise GraphTypeCheckError(msg) from exception
        _validate_region(task)
        if isinstance(task, InlineOperation):
            _validate_operation(task)
    _validate_outputs(graph, boundary)
    _validate_acyclic(graph)


def _validate_inputs(graph: GraphIR, boundary: PortNamespace) -> None:
    """Check that routed graph inputs name known task inputs of compatible types."""
    for name, targets in graph.inputs.items():
        for route in targets:
            _validate_routed_input(graph, boundary, name, route)


def _task_at(graph: GraphIR, name: str, context: str) -> GraphTask:
    """Return the named task, raising a diagnostic for dangling references."""
    try:
        return graph.task(name)
    except KeyError as exception:
        msg = f'{context} refers to unknown task `{name}`.'
        raise GraphTypeCheckError(msg) from exception


def _validate_routed_input(graph: GraphIR, boundary: PortNamespace, name: str, route: Route) -> None:
    """Check that one routed graph input names a known task input of compatible type."""
    task = _task_at(graph, route.task, f'input `{name}`')
    ports = _input_ports_at(task, route.port)
    if not ports and not _accepts_condition(task, route.port):
        msg = f'input `{name}` refers to unknown input `{route.task}.{route.port}`.'
        raise GraphTypeCheckError(msg)
    origin = _port_at(boundary, name)
    if origin is None:
        msg = f'input `{name}` refers to unknown graph input.'
        raise GraphTypeCheckError(msg)
    for target in ports:
        _check_types(origin, target, f'graph input `{name}`')


def _validate_dependencies(graph: GraphIR) -> None:
    """Check that valued dependencies connect known outputs to compatible inputs."""
    for edge in graph.dependencies:
        _validate_edge(graph, edge)


def _validate_edge(graph: GraphIR, edge: Dependency) -> None:
    """Check that one valued dependency connects a known output to compatible inputs."""
    source = _task_at(graph, edge.source, 'dependency')
    target = _task_at(graph, edge.target, 'dependency')
    if edge.carried_between is None:
        return
    origin = _port_at(source.output_ports(), edge.source_port or '')
    ports = _input_ports_at(target, edge.target_port or '')
    if origin is None:
        msg = f'dependency refers to unknown output `{edge.source}.{edge.source_port}`.'
        raise GraphTypeCheckError(msg)
    if (
        isinstance(origin, PortNamespace)
        and not _accepts_region(target, edge.target_port)
        and not any(isinstance(port, PortNamespace) for port in ports)
        and (not ports or _accepts_condition(target, edge.target_port))
    ):
        # A whole namespace always names stored outputs; without a namespace
        # to land in, the type check below reports the mismatch instead.
        # Unwired conditions keep the unknown-output rejection.
        msg = f'dependency refers to unknown output `{edge.source}.{edge.source_port}`.'
        raise GraphTypeCheckError(msg)
    if not ports and not _accepts_condition(target, edge.target_port):
        msg = f'dependency refers to unknown input `{edge.target}.{edge.target_port}`.'
        raise GraphTypeCheckError(msg)
    for port in ports:
        _check_types(origin, port, f'dependency `{edge.source}` to `{edge.target}`')


def _validate_region(task: GraphTask) -> None:
    """Check that control-flow bodies agree on their condition and outputs."""
    if isinstance(task, BranchControl):
        if task.condition_port in task.body.inputs or task.condition_port in task.otherwise.inputs:
            msg = f'branch `{task.name}` condition conflicts with a body input.'
            raise GraphTypeCheckError(msg)
        if task.body.outputs.keys() != task.otherwise.outputs.keys():
            msg = (
                f'both branches of `{task.name}` must return the same outputs; '
                'convert outputs to a shared type in a task instead.'
            )
            raise GraphTypeCheckError(msg)
        _check_compatible(
            task.body.build_output_namespace(), task.otherwise.build_output_namespace(), f'branch `{task.name}`'
        )
        if not branch_shapes_agree(task.body.result_shape, task.otherwise.result_shape):
            msg = (
                f'branch `{task.name}` has incompatible collection members; '
                'both arms must return the same member types.'
            )
            raise GraphTypeCheckError(msg)
    if isinstance(task, MapControl):
        _validate_map(task)
    if isinstance(task, LoopControl) and type(task.max_iterations) is not int:
        msg = f'loop `{task.name}` needs an integer `max_iterations`.'
        raise GraphTypeCheckError(msg)
    if isinstance(task, LoopControl) and (
        task.condition_port not in task.body.outputs
        or task.condition_port not in task.body.inputs
        or task.max_iterations < 1
    ):
        msg = (
            f'loop `{task.name}` must take its condition as state and return it updated, '
            'allowing at least one iteration.'
        )
        raise GraphTypeCheckError(msg)


def _validate_map(task: MapControl) -> None:
    """Check that a map carries one unary callable with a single leaf output."""

    if (task.spec is None) == (task.body is None):
        msg = f'map `{task.name}` carries exactly one mapped callable: a task `spec` or a nested graph `body`.'
        raise GraphTypeCheckError(msg)
    if task.body is not None:
        validate_graph(task.body)
    fields = task.mapped_inputs.fields
    if len(fields) != 1:
        msg = (
            f'map `{task.name}` wires one element into one input, so the callable takes exactly one input; '
            'map a unary task or graph instead.'
        )
        raise GraphTypeCheckError(msg)
    if not task.mapped_result_port:
        msg = (
            f'map `{task.name}` collects one output per element, so the callable returns exactly one value; '
            'map a unary task or graph with one output instead.'
        )
        raise GraphTypeCheckError(msg)


def _validate_operation(task: InlineOperation) -> None:
    """Check that an inline operation declares the operand contracts and result its operator infers."""
    if task.operation in ('const', 'expression'):
        # `InlineOperation.__post_init__` already checks the bound value, its port, and the
        # result contract; inference below would re-derive the same identity shape.
        return
    by_name = dict(task.input_shape.fields)
    operands = (
        (by_name[LEFT_PORT], by_name[RIGHT_PORT]) if task.operation in BINARY_OPERATIONS else (by_name[OPERAND_PORT],)
    )
    try:
        inferred = infer_operation_shape(task.operation, operands)
    except GraphTypeCheckError as exception:
        msg = f'inline operation `{task.name}` misdeclares its operands: {exception}.'
        raise GraphTypeCheckError(msg) from exception
    declared = task.result_shape.types or ()
    produced = inferred.types or ()
    if tuple(declared) != tuple(produced):
        declared_names = _type_names(tuple(declared)) if declared else 'unconstrained types'
        msg = (
            f'inline operation `{task.name}` declares result {declared_names} '
            f'but `{task.operation}` produces {_type_names(tuple(produced))}.'
        )
        raise GraphTypeCheckError(msg)


def _validate_outputs(graph: GraphIR, boundary: PortNamespace) -> None:
    """Check that graph outputs reference declared leaves of compatible types."""
    outputs = graph.build_output_namespace()
    for name, tree in graph.outputs.items():
        port = outputs[name]
        assert isinstance(port, (OutputPort, PortNamespace))
        _validate_output_tree(graph, boundary, tree, port, f'graph output `{name}`')


def _validate_output_tree(
    graph: GraphIR, boundary: PortNamespace, tree: OutputTree, port: OutputPort | PortNamespace, context: str
) -> None:
    """Check one output leaf or nested mapping against its declared contracts."""
    if isinstance(tree, dict):
        assert isinstance(port, PortNamespace)  # `build_output_namespace` mirrors the output tree
        for field, child in tree.items():
            child_port = port[field]
            assert isinstance(child_port, (OutputPort, PortNamespace))
            _validate_output_tree(graph, boundary, child, child_port, f'{context}.{field}')
        return
    assert isinstance(tree, Endpoint)
    origin = (
        _port_at(boundary, tree.port)
        if tree.task is None
        else _port_at(graph.task(tree.task).output_ports(), tree.port)
    )
    _check_types(origin, port, context)


def _validate_acyclic(graph: GraphIR) -> None:
    """Check that the dependencies order every task."""
    remaining = {name: graph.predecessors(name) for name in graph.task_names}
    while remaining:
        free = [name for name, waiting in remaining.items() if not waiting & remaining.keys()]
        if not free:
            msg = f'the dependencies contain a cycle between {sorted(remaining)}.'
            raise GraphTypeCheckError(msg)
        for name in free:
            del remaining[name]


def _check_types(source: t.Any, target: t.Any, context: str) -> None:
    """Check that a produced value fits the accepting port, descending into namespaces."""
    if isinstance(source, PortNamespace) or isinstance(target, PortNamespace):
        if not isinstance(source, PortNamespace) or not isinstance(target, PortNamespace):
            msg = f'{context} has incompatible value and namespace shapes.'
            raise GraphTypeCheckError(msg)
        _check_namespaces(source, target, context)
        return

    produced, accepted = _stored_types(source), _stored_types(target)
    if (
        produced
        and accepted
        and DataNode not in produced
        and not all(any(issubclass(kind, expected) for expected in accepted) for kind in produced)
    ):
        msg = f'{context} has incompatible types: {_type_names(produced)} cannot feed {_type_names(accepted)}.'
        raise GraphTypeCheckError(msg)


def _check_compatible(first: PortNamespace, second: PortNamespace, context: str) -> None:
    """Check that two output contracts accept each other."""
    _check_types(first, second, context)
    _check_types(second, first, context)


def _check_namespaces(source: PortNamespace, target: PortNamespace, context: str) -> None:
    """Check that shared fields agree, required fields exist, and a static target declares every field."""
    for name, child in target.items():
        if name in source:
            _check_types(source[name], child, context)
        elif child.required:
            msg = f'{context} is missing required field `{name}`.'
            raise GraphTypeCheckError(msg)
    if target.dynamic:
        return
    for name in source:
        if name not in target:
            msg = f'{context} has unexpected field `{name}`.'
            raise GraphTypeCheckError(msg)


def _accepts_region(task: GraphTask, port: str | None) -> bool:
    """Return whether a placement wires a whole namespace into a control-flow region.

    Branch and loop bodies select fields from region inputs themselves, so the
    enclosing graph routes the whole namespace instead of one leaf.
    Task-to-task edges accept whole namespaces only into matching namespaces.
    """
    return isinstance(task, (BranchControl, LoopControl)) and port is not None and port != task.condition_port


def _accepts_condition(task: GraphTask, port: str | None) -> bool:
    """Return whether a branch wires its synthetic condition outside declared inputs.

    Graph-input-wired conditions bypass lowering-time type checks (the input's declared
    type is trusted); the runtime `_holds` check still rejects non-`bool`/`Bool` values loudly.
    """
    return isinstance(task, BranchControl) and port == task.condition_port


def _type_names(kinds: tuple[type, ...]) -> str:
    """Return the class names of alternative types, as a user reads them in an annotation."""
    return ' or '.join(f'`{kind.__name__}`' for kind in kinds)


def _stored_types(port: t.Any) -> tuple[type, ...]:
    """Return the stored types a port accepts, without nullability."""
    kinds = port.valid_type or ()
    kinds = (kinds,) if isinstance(kinds, type) else kinds
    return tuple(kind for declared in kinds if declared is not type(None) for kind in _infer_node_types(declared))
