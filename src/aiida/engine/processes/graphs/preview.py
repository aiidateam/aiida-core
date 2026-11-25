###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core   #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""A static, launch-bound view of a graph before any placement is executed."""

from __future__ import annotations

import typing as t
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from types import MappingProxyType

from aiida.engine.execution import RetryPolicy
from aiida.engine.processes.graphs.ir import (
    BranchControl,
    GraphIR,
    GraphTask,
    LoopControl,
    MapControl,
    ProcessTask,
    SubgraphTask,
)
from aiida.engine.processes.graphs.recovery import _at_placement, _decode_policy
from aiida.engine.processes.ports import PortNamespace

__all__ = ('DeferredGraphInput', 'GraphLaunchPreview', 'GraphPlacementPreview', 'ResolvedGraphInput')


@dataclass(frozen=True, slots=True)
class ResolvedGraphInput:
    """An explicit input or graph-level default known before execution."""

    value: object

    @property
    def state(self) -> t.Literal['resolved']:
        """Identify a resolved binding."""
        return 'resolved'


@dataclass(frozen=True, slots=True)
class DeferredGraphInput:
    """A binding supplied by an upstream placement or a runtime control region."""

    source: str

    @property
    def state(self) -> t.Literal['deferred']:
        """Identify a binding that cannot be resolved before execution."""
        return 'deferred'


@dataclass(frozen=True, slots=True)
class GraphPlacementPreview:
    """A process or map placement in a static launch preview.

    :param address: Placement address, including enclosing subgraph aliases.
    :param regions: Enclosing branch, loop and mapped regions, outermost first.
    :param inputs: Explicit bindings by port path; missing keys have no preview binding.
    :param retry_policy: The validated execution policy, if configured.
    """

    address: str
    regions: tuple[str, ...]
    inputs: Mapping[str, ResolvedGraphInput | DeferredGraphInput]
    retry_policy: RetryPolicy | None = None


@dataclass(frozen=True, slots=True)
class GraphLaunchPreview:
    """Static placements for one validated launch, without predicting execution order within control regions."""

    placements: tuple[GraphPlacementPreview, ...]

    def __str__(self) -> str:
        lines = []
        for placement in self.placements:
            region = f' [{", ".join(placement.regions)}]' if placement.regions else ''
            lines.append(f'{placement.address}{region}')
            for path, binding in placement.inputs.items():
                value = (
                    str(binding.value) if isinstance(binding, ResolvedGraphInput) else f'deferred — {binding.source}'
                )
                lines.append(f'  {path}: {value}')
            if placement.retry_policy is not None:
                lines.append(f'  max attempts: {placement.retry_policy.max_attempts}')
        return '\n'.join(lines)


_Binding = ResolvedGraphInput | DeferredGraphInput


def _leaves(
    values: Mapping[str, object], ports: PortNamespace, prefix: str = ''
) -> Iterator[tuple[str, ResolvedGraphInput]]:
    """Flatten namespaces without flattening dictionary-valued leaf inputs."""
    for name, value in values.items():
        path = f'{prefix}.{name}' if prefix else name
        port = ports.get(name)
        if isinstance(port, PortNamespace) and isinstance(value, Mapping):
            yield from _leaves(value, port, path)
        else:
            yield path, ResolvedGraphInput(value)


def _bindings_for(
    graph: GraphIR, task: GraphTask, given: Mapping[str, _Binding], prefix: tuple[str, ...]
) -> dict[str, _Binding]:
    """Describe one placement's input routes, leaving upstream results unresolved."""
    result: dict[str, _Binding] = {}
    for name, routes in graph.inputs.items():
        for target, path in routes:
            if target != task.name:
                continue
            if name in given:
                result[path] = given[name]
            else:
                for leaf, binding in given.items():
                    if leaf.startswith(f'{name}.'):
                        result[f'{path}{leaf[len(name) :]}'] = binding
                    elif name.startswith(f'{leaf}.') and isinstance(binding, DeferredGraphInput):
                        result[path] = DeferredGraphInput(f'{binding.source}{name[len(leaf) :]}')
    for edge in graph.dependencies:
        if edge.target == task.name and edge.carried_between is not None:
            source, target_port = edge.carried_between
            location = '.'.join((*prefix, edge.source))
            result[target_port] = DeferredGraphInput(f'{location}.{source}' if source else location)
    return result


def _preview(
    graph: GraphIR, inputs: Mapping[str, object], config: Mapping[str, object], policies: Mapping[str, object]
) -> GraphLaunchPreview:
    """Walk the declaration once per static region, without evaluating control flow."""

    def visit(
        body: GraphIR, given: Mapping[str, _Binding], prefix: tuple[str, ...], regions: tuple[str, ...]
    ) -> Iterator[GraphPlacementPreview]:
        for task in body.tasks:
            address = (*prefix, task.name)
            label = '.'.join(address)
            wired = _bindings_for(body, task, given, prefix)
            if isinstance(task, ProcessTask):
                ports = task.spec.process_class.spec().inputs
                bindings: dict[str, _Binding] = dict(_leaves(task.inputs, ports))
                bindings.update(_leaves(_at_placement(config, address), ports))
                bindings.update(wired)
                policy = _at_placement(policies, address)
                yield GraphPlacementPreview(
                    label, regions, MappingProxyType(bindings), _decode_policy(policy) if policy else None
                )
            elif isinstance(task, SubgraphTask):
                ports = task.body.build_input_namespace()
                yield from visit(task.body, dict(_leaves(task.inputs, ports)) | wired, address, regions)
            elif isinstance(task, BranchControl):
                for arm, side in zip(task.branches, ('if', 'else'), strict=True):
                    yield from visit(arm, wired, prefix, (*regions, f'{label}:{side}'))
            elif isinstance(task, LoopControl):
                carried = {name: DeferredGraphInput(f'{label} loop state: {name}') for name in task.body.outputs}
                yield from visit(task.body, wired | carried, prefix, (*regions, f'{label}:loop'))
            elif isinstance(task, MapControl):
                yield GraphPlacementPreview(label, regions, MappingProxyType(wired))
                if task.body is not None:
                    element = task.element or next(iter(task.body.inputs))
                    item = {element: DeferredGraphInput(f'{label} collection element')}
                    fixed = dict(_leaves(task.inputs, task.body.build_input_namespace()))
                    yield from visit(task.body, fixed | wired | item, prefix, (*regions, f'{label}:map'))

    given = dict(_leaves(inputs, graph.build_input_namespace()))
    return GraphLaunchPreview(tuple(visit(graph, given, (), ())))
