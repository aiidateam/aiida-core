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
from aiida.engine.processes.graphs.ir import input_ports_at, port_at
from aiida.engine.processes.ports import PortNamespace, _infer_node_types
from aiida.orm import Data

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
    ports = input_ports_at(task, route.port)
    if not ports:
        msg = f'input `{name}` refers to unknown input `{route.task}.{route.port}`.'
        raise GraphTypeCheckError(msg)
    origin = port_at(boundary, name)
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
    origin = port_at(source.output_ports(), edge.source_port or '')
    ports = input_ports_at(target, edge.target_port or '')
    if origin is None or isinstance(origin, PortNamespace):
        msg = f'dependency refers to unknown output `{edge.source}.{edge.source_port}`.'
        raise GraphTypeCheckError(msg)
    if not ports:
        msg = f'dependency refers to unknown input `{edge.target}.{edge.target_port}`.'
        raise GraphTypeCheckError(msg)
    for port in ports:
        _check_types(origin, port, f'dependency `{edge.source}` to `{edge.target}`')


def _validate_outputs(graph: GraphIR, boundary: PortNamespace) -> None:
    """Check that graph outputs reference declared leaves of compatible types."""
    outputs = graph.build_output_namespace()
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


def _check_namespaces(source: PortNamespace, target: PortNamespace, context: str) -> None:
    """Check that shared fields agree and required fields exist."""
    for name, child in target.items():
        if name in source:
            _check_types(source[name], child, context)
        elif child.required:
            msg = f'{context} is missing required field `{name}`.'
            raise GraphTypeCheckError(msg)


def _stored_types(port: t.Any) -> tuple[type, ...]:
    """Return the stored types a port accepts, without nullability."""
    kinds = port.valid_type or ()
    kinds = (kinds,) if isinstance(kinds, type) else kinds
    return tuple(kind for declared in kinds if declared is not type(None) for kind in _infer_node_types(declared))
