###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Human-readable view of a graph declaration, without launching its tasks."""

from __future__ import annotations

from aiida.engine.processes.graphs.spec import (
    BodyTask,
    BranchControl,
    GraphSpec,
    GraphTask,
    LoopControl,
    MapGraphControl,
    MapTask,
    ProcessTask,
)


def format_graph(graph: GraphSpec) -> str:
    """Return a nested, readable view of a graph's tasks and their port wiring.

    :param graph: The declaration to display. No graph or task bodies are executed.
    :return: A multiline description including nested branches, loops and maps.
    """
    lines: list[str] = []
    _format_graph(graph, lines, depth=0)
    return '\n'.join(lines)


def _task_label(task: GraphTask) -> str:
    if isinstance(task, BranchControl):
        return f'branch on {task.condition_port}'
    if isinstance(task, LoopControl):
        return f'loop while {task.condition_port}'
    if isinstance(task, (MapTask, MapGraphControl)):
        return f'map over {task.item_port}'
    if isinstance(task, ProcessTask):
        return f'process {task.spec.identifier}'
    return task.kind


def _format_graph(graph: GraphSpec, lines: list[str], *, depth: int) -> None:
    indent = '  ' * depth
    lines.append(f'{indent}graph {graph.identifier or "<body>"}({", ".join(graph.inputs)}):')

    # A task's arguments may come from literals, graph inputs, or preceding tasks.
    wiring: dict[str, dict[str, str]] = {task.name: {} for task in graph.tasks}
    for name, targets in graph.inputs.items():
        for task_name, port in targets:
            wiring[task_name][port] = name
    for edge in graph.dependencies:
        if (carried := edge.carried_between) is not None:
            source_port, target_port = carried
            wiring[edge.target][target_port] = f'{edge.source}.{source_port}'

    for task in graph.tasks:
        arguments = {key: repr(value) for key, value in task.inputs.items()}
        arguments.update(wiring[task.name])
        written = ', '.join(f'{port}={value}' for port, value in sorted(arguments.items()))
        lines.append(f'{indent}  {task.name} [{_task_label(task)}]({written})')
        for edge in graph.dependencies:
            if edge.target == task.name and edge.carried_between is None:
                lines.append(f'{indent}    after {edge.source}')

        if isinstance(task, BranchControl):
            lines.append(f'{indent}    then:')
            _format_graph(task.body, lines, depth=depth + 3)
            if task.otherwise is not None:
                lines.append(f'{indent}    otherwise:')
                _format_graph(task.otherwise, lines, depth=depth + 3)
        elif isinstance(task, BodyTask):
            _format_graph(task.body, lines, depth=depth + 2)

    outputs = ', '.join(
        f'{name}={source.task}.{source.port}' if source.task is not None else f'{name}={source.port}'
        for name, source in graph.outputs.items()
    )
    lines.append(f'{indent}  return {outputs}')
