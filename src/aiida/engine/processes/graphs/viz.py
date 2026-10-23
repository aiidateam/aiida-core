###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file       #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Render static graphs as Mermaid flowcharts for development."""

from __future__ import annotations

import re

from aiida.engine.processes.graphs.ir import BodyTask, GraphIR

__all__ = ('to_mermaid',)


def _node_id(*path: str) -> str:
    """Return a Mermaid-safe node id for a placement path."""
    return re.sub(r'\W', '_', '__'.join(path))


def _label(text: str) -> str:
    """Quote a label for Mermaid, neutralizing quotes and edge syntax."""
    return text.replace('\\', '\\\\').replace('"', "'").replace('|', '/')


def _edge(source: str, target: str, label: str = '') -> str:
    """Return one flowchart edge, dashed without a label for region inputs."""
    if label:
        return f'    {source} -->|{_label(label)}| {target}'
    return f'    {source} --> {target}'


def to_mermaid(spec: GraphIR) -> str:
    """Return the graph template as a Mermaid flowchart.

    Placements render flat with path-prefixed ids, so nested regions need no
    subgraph semantics: region inputs hang off their control task with dashed
    edges, and only top-level outputs render. Literal task inputs and ordering
    edges without ports render without labels.

    :param spec: the graph template to draw.
    :return: the flowchart source, pasteable into issues, reviews, and docs.
    """
    lines = ['flowchart TD']
    _render_body(spec, (), lines)
    return '\n'.join(lines) + '\n'


def _render_body(spec: GraphIR, prefix: tuple[str, ...], lines: list[str]) -> None:
    """Draw one template level: inputs, placements, wirings, and nested bodies."""
    for name, targets in spec.inputs.items():
        lines.append('    ' + _node_id(*prefix, 'in', name) + '{{' + _label(name) + '}}')
        for route in targets:
            lines.append(_edge(_node_id(*prefix, 'in', name), _node_id(*prefix, route.task), route.port))
    for task in spec.tasks:
        ident = _node_id(*prefix, task.name)
        name_label = _label('/'.join((*prefix, task.name)))
        lines.append(f'    {ident}["{name_label}"]')
        if isinstance(task, BodyTask):
            for name in task.body.inputs:
                region = _node_id(*prefix, task.name, 'in', name)
                lines.append('    ' + region + '{{' + _label(name) + '}}')
                lines.append(f'    {ident} -.-> {region}')
            _render_body(task.body, (*prefix, task.name), lines)
    for edge in spec.dependencies:
        if edge.source_port is None or edge.target_port is None:
            lines.append(_edge(_node_id(*prefix, edge.source), _node_id(*prefix, edge.target)))
        else:
            lines.append(
                _edge(
                    _node_id(*prefix, edge.source),
                    _node_id(*prefix, edge.target),
                    f'{edge.source_port} -> {edge.target_port}',
                )
            )
    if not prefix:
        for name, endpoint in spec.outputs.items():
            output = _node_id('out', name)
            lines.append(f'    {output}[/{_label(name)}/]')
            if endpoint.task is None:
                lines.append(_edge(_node_id('in', endpoint.port.split('.')[0]), output, endpoint.port))
            else:
                lines.append(_edge(_node_id(endpoint.task), output, endpoint.port))
