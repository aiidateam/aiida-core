###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Run-specific values carried alongside, never inside, graph declarations."""

from __future__ import annotations

import contextvars
import typing as t
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import replace

from aiida.engine.processes.graphs.inputs import at, dump_port, load_port, prepare_inputs
from aiida.engine.processes.graphs.run import place
from aiida.engine.processes.graphs.spec import GraphSpec, ProcessTask
from aiida.engine.processes.ports import InputPort, PortNamespace
from aiida.orm import Node

LAUNCH_BINDINGS: contextvars.ContextVar[dict[str, t.Any] | None] = contextvars.ContextVar(
    'graph_launch_bindings', default=None
)


def copy_containers(value: t.Any) -> t.Any:
    """Snapshot containers without copying node identities."""
    if isinstance(value, Node):
        return value
    if isinstance(value, Mapping):
        return {key: copy_containers(item) for key, item in value.items()}
    if isinstance(value, list):
        return [copy_containers(item) for item in value]
    if isinstance(value, tuple):
        return tuple(copy_containers(item) for item in value)
    if isinstance(value, set):
        return {copy_containers(item) for item in value}
    return value


def merge_inputs(bound: Mapping[str, t.Any], supplied: Mapping[str, t.Any], ports: PortNamespace) -> dict[str, t.Any]:
    """Merge only declared namespaces, replacing dictionary-valued leaves whole."""
    result = copy_containers(bound)
    for name, value in supplied.items():
        port = ports.get(name)
        if isinstance(port, PortNamespace) and isinstance(value, Mapping) and isinstance(result.get(name), Mapping):
            result[name] = merge_inputs(result[name], value, port)
        else:
            result[name] = copy_containers(value)
    return result


def leaves(values: Mapping[str, t.Any], ports: PortNamespace, prefix: str = '') -> t.Iterator[tuple[str, t.Any]]:
    """Walk namespaces by their specification, not by the type of their values."""
    for name, value in values.items():
        path = f'{prefix}{name}'
        port = ports.get(name)
        if isinstance(port, PortNamespace) and isinstance(value, Mapping) and value:
            yield from leaves(value, port, f'{path}.')
        else:
            yield path, value


def bind_declaration(body: GraphSpec, bindings: Mapping[str, t.Any]) -> GraphSpec:
    """Route captured leaves through private boundary inputs; explicit placements win."""
    inputs = dict(body.inputs)
    tasks = list(body.tasks)
    namespace = body.input_spec()
    collector = LAUNCH_BINDINGS.get()
    for task_name, handle in bindings.items():
        placed = body.task(task_name)
        if not isinstance(placed, ProcessTask) or placed.spec.executor != handle.task_spec.executor:
            msg = f"Prepared task `{task_name}` must use the declaration's process class."
            raise TypeError(msg)
        values = handle.get_launch_inputs(**placed.inputs)
        tasks[tasks.index(placed)] = replace(placed, inputs={}, validate_inputs=True)
        occupied = {path for targets in body.inputs.values() for name, path in targets if name == task_name}
        occupied.update(edge.target_port for edge in body.dependencies if edge.target == task_name and edge.target_port)
        captured_leaves = sorted(leaves(values, handle.process_class.spec().inputs), key=lambda item: item[0])
        for index, (path, value) in enumerate(captured_leaves):
            if any(path == other or path.startswith(f'{other}.') or other.startswith(f'{path}.') for other in occupied):
                continue
            name = f'prepared_{task_name}_{index}'
            if name in inputs:
                msg = f'Prepared input name `{name}` collides with a graph input.'
                raise ValueError(msg)
            inputs[name] = ((task_name, path),)
            port = handle.process_class.spec().inputs
            for segment in path.split('.'):
                if isinstance(port, PortNamespace) and segment in port:
                    port = port[segment]
                elif isinstance(port, PortNamespace) and port.dynamic:
                    port = InputPort(segment, valid_type=port.valid_type)
                else:
                    msg = f'Unknown prepared input `{task_name}.{path}`.'
                    raise ValueError(msg)
            namespace[name] = load_port(dump_port(port, defaults=False))
            if collector is not None:
                collector[name] = copy_containers(value)
    return replace(body, tasks=tuple(tasks), inputs=inputs, input_namespace=dump_port(namespace))


def _copy_ports(namespace: PortNamespace) -> PortNamespace:
    """Copy validation structure without cloning defaults or callable collaborators."""
    memo: dict[int, t.Any] = {}

    def visit(port: InputPort | PortNamespace) -> None:
        if port.has_default():
            default = port.default
            memo[id(default)] = copy_containers(default)
        for callback in (port.validator, getattr(port, 'serializer', None)):
            if callback is not None:
                memo[id(callback)] = callback
        if isinstance(port, PortNamespace):
            for child in port.values():
                visit(child)

    visit(namespace)
    return deepcopy(namespace, memo)


def validate_bound_tasks(body: GraphSpec, given: Mapping[str, t.Any]) -> None:
    """Validate concrete inputs while treating checked graph edges as satisfied ports."""
    if not any(isinstance(task, ProcessTask) and task.validate_inputs for task in body.tasks):
        return
    body.validate_typehints()
    for task in body.tasks:
        if not isinstance(task, ProcessTask) or not task.validate_inputs:
            continue
        ports = task.spec.process_class.spec().inputs
        values = copy_containers(task.inputs)
        for name, targets in body.inputs.items():
            try:
                value = at(given, name)
            except KeyError:
                continue
            for task_name, path in targets:
                if task_name == task.name:
                    place(values, path, copy_containers(value))
        # Validators involving unresolved values run on the child at dispatch.
        concrete_ports = _copy_ports(ports)
        for edge in body.dependencies:
            if edge.target != task.name or edge.target_port is None:
                continue
            concrete_ports.validator = None
            parent: t.Any = concrete_ports
            segments = edge.target_port.split('.')
            supplied = values
            for segment in segments[:-1]:
                parent = parent.get(segment)
                if not isinstance(parent, PortNamespace):
                    break
                parent.required = False
                parent.validator = None
                supplied = supplied.setdefault(segment, {})
                if not isinstance(supplied, dict):
                    break
            else:
                if segments[-1] in parent:
                    del parent[segments[-1]]
        prepared = prepare_inputs(concrete_ports, concrete_ports.pre_process(values), task.name)
        serialized = concrete_ports.serialize(prepared)
        assert serialized is not None
        error = concrete_ports.validate(concrete_ports.prepare(serialized))
        if error is not None:
            raise ValueError(error)
