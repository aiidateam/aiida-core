###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

"""Track write permission on graph bindings independently of node identity."""

from __future__ import annotations

import typing as t
from collections.abc import Callable, Mapping
from functools import reduce

from aiida.common.exceptions import GraphRuntimeError, GraphTypeCheckError
from aiida.engine.processes.graphs.ir import (
    BranchControl,
    Endpoint,
    GraphIR,
    GraphTask,
    InlineOperation,
    LoopControl,
    MapControl,
    OptionalOutputNamespace,
    OutputTree,
    ProcessTask,
    SubgraphTask,
)
from aiida.engine.processes.ports import InputPort, PortNamespace
from aiida.orm import CalculationNode

# A bool applies to every leaf below it. None represents a binding not yet known at build time.
Permission: t.TypeAlias = 'bool | dict[str, Permission] | None'


def select_permission(permission: Permission, path: str) -> Permission:
    """Return the permission at a dotted path, inheriting a whole-tree permission."""
    for part in path.split('.') if path else ():
        if not isinstance(permission, dict):
            break
        permission = permission.get(part, permission.get('', True))
    return permission


def declared_permissions(ports: PortNamespace) -> dict[str, Permission]:
    """Start an explicitly declared graph boundary with its own input contract."""
    return {
        name: declared_permissions(port) if isinstance(port, PortNamespace) else port.mutable
        for name, port in ports.items()
        if isinstance(port, (InputPort, PortNamespace))
    }


def _place_permission(inputs: dict[str, Permission], path: str, permission: Permission) -> None:
    """Override one subpath while retaining the inherited permission for its siblings."""
    *parents, leaf = path.split('.')
    for name in parents:
        child = select_permission(inputs, name)
        if not isinstance(child, dict):
            child = {'': child}
        else:
            child = dict(child)
        inputs[name] = child
        inputs = child
    inputs[leaf] = permission


def wired_permissions(
    graph: GraphIR, task: GraphTask, given: Permission, output: Callable[[str], Permission]
) -> dict[str, Permission]:
    """Follow the same graph routes as values, without using the values as keys."""
    inputs: dict[str, Permission] = {}
    for name, routes in graph.inputs.items():
        for target, path in routes:
            if target == task.name:
                _place_permission(inputs, path, select_permission(given, name))
    for edge in graph.dependencies:
        if edge.target == task.name and edge.carried_between is not None:
            source, target = edge.carried_between
            _place_permission(inputs, target, select_permission(output(edge.source), source))
    return inputs


def output_permissions(tree: OutputTree, resolve: Callable[[Endpoint], Permission]) -> Permission:
    """Regroup output bindings without granting permission at a scope exit."""
    if isinstance(tree, Endpoint):
        return resolve(tree)
    fields = tree.fields if isinstance(tree, OptionalOutputNamespace) else tree
    return {name: output_permissions(child, resolve) for name, child in fields.items()}


def check_permissions(
    ports: PortNamespace, given: Permission, path: str, *, values: Mapping[str, object] | None = None
) -> None:
    """Reject a read-only binding at a writable port."""
    for name, port in ports.items():
        value = values.get(name) if values is not None else None
        if values is not None and value is None:
            continue
        permission = select_permission(given, name)
        label = f'{path}.{name}'
        if isinstance(port, PortNamespace):
            if values is None:
                check_permissions(port, permission, label)
            elif isinstance(value, Mapping):
                check_permissions(port, permission, label, values=value)
        elif isinstance(port, InputPort) and port.mutable and permission is False:
            msg = f'cannot wire a read-only binding to mutable input `{label}`; opt in with PortField(mutable=True).'
            if values is not None:
                raise GraphRuntimeError(msg)
            raise GraphTypeCheckError(msg)


def process_permissions(task: ProcessTask) -> bool:
    """Calculation outputs are fresh sources; workflow outputs are references."""
    return issubclass(task.spec.process_class._node_class, CalculationNode)


def inline_permissions(task: InlineOperation, inputs: Permission) -> Permission:
    """Keep the source permission when an inline selection projects an existing binding."""
    if task.operation != 'expression' or task.expression is None:
        return True

    def origin(expression: Mapping[str, t.Any]) -> Permission:
        match expression['tag']:
            case 'ref':
                return select_permission(inputs, expression['port'])
            case 'index' | 'attribute':
                return origin(expression['target'])
            case _:
                return True

    return {task.result_port: origin(task.expression)}


def _merge(left: Permission, right: Permission) -> Permission:
    """Retain what is known on both paths, deferring disagreements to dispatch."""
    if left == right:
        return left
    if isinstance(left, dict) or isinstance(right, dict):
        keys = (left.keys() if isinstance(left, dict) else set()) | (right.keys() if isinstance(right, dict) else set())
        fallback_left = left.get('', True) if isinstance(left, dict) else left
        fallback_right = right.get('', True) if isinstance(right, dict) else right
        return {
            '': _merge(fallback_left, fallback_right),
            **{key: _merge(select_permission(left, key), select_permission(right, key)) for key in keys - {''}},
        }
    return None


class _StaticBindings:
    """Resolve statically known bindings, without evaluating branch conditions."""

    def __init__(self, graph: GraphIR, given: Permission) -> None:
        self.graph = graph
        self.given = given
        self.results: dict[str, Permission] = {}
        self.early_returns: list[Permission] = []

    def outputs(self) -> Permission:
        """Check even unused placements and resolve the possible output bindings."""
        for task in self.graph.tasks:
            self.placement(task.name)
        if self.graph.return_outputs is not None:
            self.early_returns.append(self.resolve(self.graph.return_outputs))
        return self.resolve(self.graph.outputs)

    def invocation_outputs(self) -> Permission:
        """Merge the binding at every successful return site of a named graph."""
        normal = self.outputs()
        candidates = self.early_returns if self.graph.always_returns else [normal, *self.early_returns]
        return reduce(_merge, candidates) if candidates else None

    def resolve(self, tree: dict[str, OutputTree]) -> Permission:
        return output_permissions(
            tree, lambda end: select_permission(self.given if end.task is None else self.placement(end.task), end.port)
        )

    def placement(self, name: str) -> Permission:
        if name not in self.results:
            task = self.graph.task(name)
            inputs = wired_permissions(self.graph, task, self.given, self.placement)
            self.results[name] = self._placement(task, inputs)
        return self.results[name]

    def _placement(self, task: GraphTask, inputs: dict[str, Permission]) -> Permission:
        if isinstance(task, (ProcessTask, SubgraphTask, MapControl)):
            for ports in task.input_ports():
                check_permissions(ports, inputs, task.name)
        if isinstance(task, ProcessTask):
            return process_permissions(task)
        if isinstance(task, SubgraphTask):
            result = _StaticBindings(
                task.body, declared_permissions(task.body.build_input_namespace())
            ).invocation_outputs()
            if task.capture_error:
                return {'value': select_permission(result, task.body.result_port), 'error': True}
            return result
        if isinstance(task, InlineOperation):
            return inline_permissions(task, inputs)
        if isinstance(task, BranchControl):
            continuing = []
            for arm in task.branches:
                bindings = _StaticBindings(arm, inputs)
                result = bindings.outputs()
                self.early_returns.extend(bindings.early_returns)
                if not arm.always_returns:
                    continuing.append(result)
            return reduce(_merge, continuing) if continuing else None
        if isinstance(task, LoopControl):
            bindings = _StaticBindings(task.body, inputs)
            result = bindings.outputs()
            self.early_returns.extend(bindings.early_returns)
            zero = {name: select_permission(inputs, name) for name in task.body.outputs}
            return _merge(zero, result)
        if isinstance(task, MapControl):
            element = task.element or task.mapped_inputs.fields[0][0]
            item = {**inputs, element: select_permission(inputs, 'collection')}
            ports = task.mapped_input_ports()
            check_permissions(ports, item, task.name)
        return True


def validate_bindings(graph: GraphIR) -> None:
    """Validate known write permissions after structural and cycle checks."""
    given = declared_permissions(graph.build_input_namespace()) if graph.identifier is not None else None
    _StaticBindings(graph, given).outputs()
