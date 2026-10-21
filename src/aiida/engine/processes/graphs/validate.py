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
from aiida.engine.processes.graphs.ir import BranchControl, LoopControl, input_ports_at, port_at
from aiida.engine.processes.ports import PortNamespace, infer_node_types
from aiida.orm import Data

if t.TYPE_CHECKING:
    from aiida.engine.processes.graphs.ir import Dependency, GraphIR, GraphTask, Route


def validate_graph(graph: GraphIR) -> None:
    """Check names, inputs, dependencies, regions, outputs, and acyclicity."""
    if len(set(graph.task_names)) != len(graph.task_names):
        msg = 'task names must be unique.'
        raise GraphTypeCheckError(msg)
    boundary = graph.input_spec()
    _validate_inputs(graph, boundary)
    _validate_dependencies(graph)
    for task in graph.tasks:
        # Touch the port views: they raise on dynamic or namespaced outputs the spec cannot represent.
        task.input_ports()
        task.output_ports()
        _validate_region(graph, task)
    _validate_outputs(graph, boundary)
    _validate_acyclic(graph)


def _validate_inputs(graph: GraphIR, boundary: PortNamespace) -> None:
    """Check that routed graph inputs name known task inputs of compatible types."""
    for name, targets in graph.inputs.items():
        for route in targets:
            _validate_routed_input(graph, boundary, name, route)


def _validate_routed_input(graph: GraphIR, boundary: PortNamespace, name: str, route: Route) -> None:
    """Check that one routed graph input names a known task input of compatible type."""
    task = graph.task(route.task)
    ports = input_ports_at(task, route.port)
    if not ports and not _accepts_condition(task, route.port):
        msg = f'input `{name}` refers to unknown input `{route.task}.{route.port}`.'
        raise GraphTypeCheckError(msg)
    origin = port_at(boundary, name)
    for target in ports:
        _check_types(origin, target, f'graph input `{name}`')


def _validate_dependencies(graph: GraphIR) -> None:
    """Check that valued dependencies connect known outputs to compatible inputs."""
    for edge in graph.dependencies:
        _validate_edge(graph, edge)


def _validate_edge(graph: GraphIR, edge: Dependency) -> None:
    """Check that one valued dependency connects a known output to compatible inputs."""
    source, target = graph.task(edge.source), graph.task(edge.target)
    if edge.carried_between is None:
        return
    origin = port_at(source.output_ports(), edge.source_port or '')
    ports = input_ports_at(target, edge.target_port or '')
    if origin is None or isinstance(origin, PortNamespace):
        msg = f'dependency refers to unknown output `{edge.source}.{edge.source_port}`.'
        raise GraphTypeCheckError(msg)
    if not ports and not _accepts_condition(target, edge.target_port):
        msg = f'dependency refers to unknown input `{edge.target}.{edge.target_port}`.'
        raise GraphTypeCheckError(msg)
    for port in ports:
        _check_types(origin, port, f'dependency `{edge.source}` to `{edge.target}`')


def _validate_region(graph: GraphIR, task: GraphTask) -> None:
    """Check that control-flow bodies agree on their condition and outputs."""
    if isinstance(task, BranchControl):
        if task.condition_port in task.body.inputs or task.condition_port in task.otherwise.inputs:
            msg = 'branch condition conflicts with a body input.'
            raise GraphTypeCheckError(msg)
        if task.body.outputs.keys() != task.otherwise.outputs.keys():
            msg = 'both branches must return the same outputs.'
            raise GraphTypeCheckError(msg)
        _check_compatible(task.body.output_spec(), task.otherwise.output_spec(), 'branch outputs')
    if isinstance(task, LoopControl) and (task.condition_port not in task.body.outputs or task.max_iterations < 1):
        msg = 'a loop must return its condition and allow at least one iteration.'
        raise GraphTypeCheckError(msg)


def _validate_outputs(graph: GraphIR, boundary: PortNamespace) -> None:
    """Check that graph outputs reference declared leaves of compatible types."""
    outputs = graph.output_spec()
    for name, endpoint in graph.outputs.items():
        origin = (
            port_at(boundary, endpoint.port)
            if endpoint.task is None
            else port_at(graph.task(endpoint.task).output_ports(), endpoint.port)
        )
        _check_types(origin, outputs[name], f'graph output `{name}`')


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
        and Data not in produced
        and not all(any(issubclass(kind, expected) for expected in accepted) for kind in produced)
    ):
        msg = f'{context} has incompatible types: {produced} cannot feed {accepted}.'
        raise GraphTypeCheckError(msg)


def _check_compatible(first: PortNamespace, second: PortNamespace, context: str) -> None:
    """Check that two output contracts accept each other."""
    _check_types(first, second, context)
    _check_types(second, first, context)


def _check_namespaces(source: PortNamespace, target: PortNamespace, context: str) -> None:
    """Check that shared fields agree and required fields exist."""
    for name, child in target.items():
        if name in source:
            _check_types(source[name], child, context)
        elif child.required:
            msg = f'{context} is missing required field `{name}`.'
            raise GraphTypeCheckError(msg)


def _accepts_condition(task: GraphTask, port: str | None) -> bool:
    """Return whether a control task wires its condition outside declared inputs."""
    return isinstance(task, (BranchControl, LoopControl)) and port == task.condition_port


def _stored_types(port: t.Any) -> tuple[type, ...]:
    """Return the stored types a port accepts, without nullability."""
    kinds = port.valid_type or ()
    kinds = (kinds,) if isinstance(kinds, type) else kinds
    return tuple(kind for declared in kinds if declared is not type(None) for kind in infer_node_types(declared))
