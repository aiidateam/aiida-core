###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Bind execution inputs without changing the scientific graph wiring."""

from __future__ import annotations

import typing as t
from collections.abc import Iterator, Mapping

from aiida.common.exceptions import GraphValidationError
from aiida.engine.processes.generic.ports import UNSPECIFIED
from aiida.engine.processes.graphs.ir import (
    BranchControl,
    GraphIR,
    LoopControl,
    MapControl,
    ProcessTask,
    SubgraphTask,
)
from aiida.engine.processes.ports import InputPort, PortNamespace


def _copy_config(value: t.Any) -> t.Any:
    """Snapshot containers while retaining node and entity identities."""
    if isinstance(value, Mapping):
        return {key: _copy_config(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return type(value)(_copy_config(child) for child in value)
    return value


def _runtime_placements(
    graph: GraphIR, prefix: tuple[str, ...] = ()
) -> Iterator[tuple[tuple[str, ...], ProcessTask, GraphIR]]:
    """Visit static process addresses, independently of control-flow execution."""
    for task in graph.tasks:
        if isinstance(task, ProcessTask):
            yield (*prefix, task.name), task, graph
        elif isinstance(task, SubgraphTask):
            yield from _runtime_placements(task.body, (*prefix, task.name))
        elif isinstance(task, BranchControl):
            for branch in task.branches:
                yield from _runtime_placements(branch, prefix)
        elif isinstance(task, LoopControl):
            yield from _runtime_placements(task.body, prefix)
        elif isinstance(task, MapControl) and task.body is not None:
            yield from _runtime_placements(task.body, prefix)


def _wired_paths(graph: GraphIR, task: ProcessTask) -> set[str]:
    """Include reserved wires even when their eventual value is absent."""
    paths = {path for routes in graph.inputs.values() for name, path in routes if name == task.name}
    paths.update(
        edge.target_port for edge in graph.dependencies if edge.target == task.name and edge.target_port is not None
    )

    def visit(values: Mapping[str, t.Any], ports: PortNamespace, prefix: str = '') -> None:
        for name, value in values.items():
            path = f'{prefix}.{name}' if prefix else name
            port = ports.get(name)
            if isinstance(port, PortNamespace) and isinstance(value, Mapping):
                visit(value, port, path)
            else:
                paths.add(path)

    visit(task.inputs, task.spec.process_class.spec().inputs)
    return paths


def _fail(placement: str, path: str, reason: str) -> t.NoReturn:
    msg = f'runtime_config placement `{placement}`, input `{path}`: {reason}'
    raise GraphValidationError(msg)


def _merge_runtime_inputs(
    task: ProcessTask, configured: Mapping[str, t.Any], inputs: Mapping[str, t.Any]
) -> dict[str, t.Any]:
    """Combine disjoint bindings, treating dictionary-valued leaves as atomic."""

    def merge(
        ports: PortNamespace, left: Mapping[str, t.Any], right: Mapping[str, t.Any], prefix: str
    ) -> dict[str, t.Any]:
        result = dict(left)
        for name, value in right.items():
            path = f'{prefix}.{name}' if prefix else name
            port = ports.get(name)
            if name not in result:
                result[name] = _copy_config(value)
            elif isinstance(port, PortNamespace) and isinstance(result[name], Mapping) and isinstance(value, Mapping):
                result[name] = merge(port, result[name], value, path)
            else:
                _fail(task.name, path, 'already explicitly wired by the graph.')
        return result

    return merge(task.spec.process_class.spec().inputs, inputs, configured, '')


def _bind_runtime_config(graph: GraphIR, provided: object) -> dict[str, t.Any]:
    """Validate every static address and prepare external bindings using process ports."""
    if not isinstance(provided, Mapping):
        msg = '`runtime_config` must be a mapping keyed by placement path.'
        raise GraphValidationError(msg)
    result = _copy_config(provided)
    placements = list(_runtime_placements(graph))
    addresses = {address for address, _, _ in placements}

    def check_addresses(values: Mapping[str, t.Any], prefix: tuple[str, ...] = ()) -> None:
        for name, value in values.items():
            if not isinstance(name, str):
                _fail('.'.join(prefix), repr(name), 'placement names must be strings.')
            address = (*prefix, name)
            label = '.'.join(address)
            if not isinstance(value, Mapping):
                _fail(label, '', 'expected a mapping.')
            if address in addresses:
                if any(other[: len(address)] == address and len(other) > len(address) for other in addresses):
                    _fail(label, '', 'ambiguous process and nested graph placement.')
            elif any(other[: len(address)] == address for other in addresses):
                check_addresses(value, address)
            else:
                _fail(label, '', 'unknown placement path.')

    check_addresses(provided)
    for address, task, owner in placements:
        label = '.'.join(address)
        values: Mapping[str, t.Any] = provided
        for part in address:
            values = values.get(part, {})
        ports = task.spec.process_class.spec().inputs
        allowed = task.spec.runtime_input_paths()
        wired = _wired_paths(owner, task)

        def check(namespace: PortNamespace, mapping: Mapping[str, t.Any], prefix: str = '') -> None:
            for name, value in mapping.items():
                if not isinstance(name, str):
                    _fail(label, repr(name), 'input names must be strings.')
                path = f'{prefix}.{name}' if prefix else name
                port = namespace.get(name)
                classified = any(path == root or path.startswith(f'{root}.') for root in allowed)
                if not classified and not any(root.startswith(f'{path}.') for root in allowed):
                    _fail(label, path, 'not an inferred execution input; wire it in the graph instead.')
                if any(path == wire or path.startswith(f'{wire}.') for wire in wired):
                    _fail(label, path, 'already explicitly wired by the graph.')
                if path == 'metadata.call_link_label':
                    _fail(label, path, 'call link labels are owned by the graph.')
                prepared = (
                    port.prepare(value).runtime
                    if path in ('metadata.store_provenance', 'metadata.dry_run') and isinstance(port, InputPort)
                    else value
                )
                if path == 'metadata.store_provenance' and prepared is False:
                    _fail(label, path, 'child provenance cannot be disabled.')
                if path == 'metadata.dry_run' and prepared:
                    _fail(label, path, 'dry runs cannot satisfy graph output contracts.')
                if isinstance(port, PortNamespace):
                    if not isinstance(value, Mapping):
                        _fail(label, path, 'expected a namespace mapping.')
                    check(port, value, path)
                elif port is None and not namespace.dynamic:
                    _fail(label, path, 'unknown process input.')
                elif any(wire.startswith(f'{path}.') for wire in wired):
                    _fail(label, path, 'contains inputs explicitly wired by the graph.')

        check(ports, values)
        # Use full original ports: serializers, defaults and namespace validators must survive inference.
        serialized = ports.serialize(dict(values)) or {}
        combined = _merge_runtime_inputs(task, serialized, task.inputs)
        filled = ports.pre_process(combined)

        def validate_config(namespace: PortNamespace, given: Mapping[str, t.Any], prefix: str = '') -> None:
            for name, port in namespace.items():
                path = f'{prefix}.{name}' if prefix else name
                if any(path == wire or path.startswith(f'{wire}.') or wire.startswith(f'{path}.') for wire in wired):
                    if isinstance(port, PortNamespace) and name in given:
                        validate_config(port, given[name], path)
                    continue
                if path in allowed:
                    if name not in given:
                        error = port.validate(UNSPECIFIED)
                        if error:
                            _fail(label, path, str(error))
                        continue
                    value = given[name]
                    if isinstance(port, PortNamespace):
                        if value is None and not port.required:
                            continue
                        value = {} if value is None else value
                        runtime = port.prepare(value).runtime
                        if path == 'metadata' and isinstance(runtime, Mapping):
                            if runtime.get('store_provenance') is False:
                                _fail(label, 'metadata.store_provenance', 'child provenance cannot be disabled.')
                            if runtime.get('dry_run'):
                                _fail(label, 'metadata.dry_run', 'dry runs cannot satisfy graph output contracts.')
                    else:
                        assert isinstance(port, InputPort)
                        runtime = port.prepare(value).runtime
                    error = port.validate(runtime)
                    if error:
                        _fail(label, path, str(error))
                elif isinstance(port, PortNamespace) and name in given:
                    validate_config(port, given[name], path)

        validate_config(ports, filled)
        # If there are no deferred wires, ordinary full-input validation is already possible.
        if not any(name == task.name for routes in owner.inputs.values() for name, _ in routes) and not any(
            edge.target == task.name for edge in owner.dependencies
        ):
            runtime = ports.prepare(filled).runtime
            assert isinstance(runtime, Mapping)
            error = ports.validate(runtime)
            if error:
                _fail(label, '', str(error))
        if values:
            target = result
            for part in address[:-1]:
                target = target[part]
            target[address[-1]] = serialized
    return result
