###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Render node contraction for differently connected selections.

For every scenario, the script creates an independent copy of this graph::

                            +-> W1 -> C1 -> D1 -+
                            |                    |
    D0 -> W0 ---------------+                    +-> returned by W0
                            |                    |
                            +-> W2 -> C2 -> D2 -+

``D0`` is also an explicit input of each child workflow and calculation.
Each scenario contracts a different set of process nodes.
Connected selected nodes produce one contraction marker, while disconnected selected regions produce one marker each.
"""

from __future__ import annotations

import argparse
import heapq
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from plumpy import ProcessState

from aiida import load_profile
from aiida.common import LinkType
from aiida.orm import CalculationNode, Data, LinkPair, Node, WorkflowNode, load_node
from aiida.tools import contract_nodes
from aiida.tools.visualization import Graph


@dataclass(frozen=True)
class Scenario:
    """A node-contraction scenario rendered by the demo."""

    name: str
    description: str
    selected_names: tuple[str, ...]
    expected_markers: int


@dataclass(frozen=True)
class DemoGraph:
    """The nodes needed to execute and render a scenario."""

    origin_pk: int
    node_pks: dict[str, int]

    def select(self, names: tuple[str, ...]) -> tuple[int, ...]:
        """Return PKs for the named nodes."""
        return tuple(self.node_pks[name] for name in names)


def finish(process: CalculationNode | WorkflowNode) -> None:
    """Mark a process as successfully finished and seal it."""
    process.set_process_state(ProcessState.FINISHED)
    process.set_exit_status(0)
    process.seal()


def create_branch(input_node: Data, caller: WorkflowNode, *, suffix: str) -> tuple[WorkflowNode, CalculationNode, Data]:
    """Create a called workflow containing one called calculation."""
    safe_suffix = suffix.replace(' ', '_')
    workflow = WorkflowNode(label=f'workflow {suffix}')
    workflow.base.links.add_incoming(input_node, LinkType.INPUT_WORK, 'input')
    workflow.base.links.add_incoming(caller, LinkType.CALL_WORK, f'workflow_{safe_suffix}')
    workflow.store()

    calculation = CalculationNode(label=f'calculation {suffix}')
    calculation.base.links.add_incoming(input_node, LinkType.INPUT_CALC, 'input')
    calculation.base.links.add_incoming(workflow, LinkType.CALL_CALC, f'calculation_{safe_suffix}')
    calculation.store()

    output = Data(label=f'output {suffix}').store()
    output.base.links.add_incoming(calculation, LinkType.CREATE, 'result')
    output.base.links.add_incoming(workflow, LinkType.RETURN, 'result')

    finish(calculation)
    finish(workflow)
    return workflow, calculation, output


def create_demo_graph(prefix: str) -> DemoGraph:
    """Create one independent copy of the branched provenance graph."""
    input_node = Data(label=f'{prefix}: input').store()

    root = WorkflowNode(label=f'{prefix}: root workflow')
    root.base.links.add_incoming(input_node, LinkType.INPUT_WORK, 'input')
    root.store()

    workflow_one, calculation_one, output_one = create_branch(input_node, root, suffix=f'{prefix} one')
    workflow_two, calculation_two, output_two = create_branch(input_node, root, suffix=f'{prefix} two')

    output_one.base.links.add_incoming(root, LinkType.RETURN, 'result_one')
    output_two.base.links.add_incoming(root, LinkType.RETURN, 'result_two')
    finish(root)

    nodes = {
        'input': input_node.pk,
        'root': root.pk,
        'workflow_one': workflow_one.pk,
        'calculation_one': calculation_one.pk,
        'output_one': output_one.pk,
        'workflow_two': workflow_two.pk,
        'calculation_two': calculation_two.pk,
        'output_two': output_two.pk,
    }
    assert all(pk is not None for pk in nodes.values())
    assert input_node.pk is not None
    return DemoGraph(input_node.pk, {name: cast(int, pk) for name, pk in nodes.items()})


def collect_graph(origin_pk: int) -> tuple[dict[int, Node], set[tuple[int, int, LinkType, str]]]:
    """Collect descendants in deterministic PK order."""
    origin = load_node(origin_pk)
    assert origin.pk is not None
    nodes = {origin.pk: origin}
    edges: set[tuple[int, int, LinkType, str]] = set()
    pending = [origin.pk]
    visited: set[int] = set()

    while pending:
        source_pk = heapq.heappop(pending)
        if source_pk in visited:
            continue
        visited.add(source_pk)
        source = nodes[source_pk]
        links = sorted(
            source.base.links.get_outgoing(link_type=tuple(LinkType)),
            key=lambda link: (link.node.pk, link.link_type.value, link.link_label),
        )
        for link in links:
            target_pk = link.node.pk
            assert target_pk is not None
            edges.add((source_pk, target_pk, link.link_type, link.link_label))
            if target_pk not in nodes:
                nodes[target_pk] = link.node
                heapq.heappush(pending, target_pk)

    return nodes, edges


def render_graph(origin_pk: int, path: Path, *, marked_for_deletion: set[int] | None = None) -> Path:
    """Render descendants by adding sorted nodes and links explicitly."""
    nodes, edges = collect_graph(origin_pk)
    marked_for_deletion = marked_for_deletion or set()
    graph = Graph(
        graph_attr={'rankdir': 'LR'},
        global_node_style={'ordering': 'out'},
        node_id_type='pk',
    )

    for pk, node in sorted(nodes.items()):
        style = None
        if pk in marked_for_deletion:
            style = {'xlabel': 'DELETE', 'color': '#d62728', 'fontcolor': '#d62728', 'penwidth': 3}
        graph.add_node(node, style_override=style)

    for source_pk, target_pk, link_type, link_label in sorted(
        edges, key=lambda edge: (edge[0], edge[1], edge[2].value, edge[3])
    ):
        style = {'label': f'{link_type.value}: {link_label}'}
        if link_type is LinkType.CONTRACTED:
            style.update({'style': 'dashed', 'color': '#7f3c8d'})
        graph.add_edge(
            nodes[source_pk],
            nodes[target_pk],
            link_pair=LinkPair(link_type, link_label),
            style=style,
        )

    rendered = graph.graphviz.render(filename=path.stem, directory=path.parent, format='png', cleanup=True)
    return Path(rendered)


def run_scenario(
    scenario: Scenario, demo: DemoGraph, index: int, output_directory: Path
) -> tuple[Path, Path, set[int]]:
    """Render, contract, and render one previously created scenario."""
    stem = f'{index:02d}_{scenario.name}'
    selected_pks = demo.select(scenario.selected_names)
    planned, was_applied = contract_nodes(selected_pks, dry_run=True)
    if was_applied:
        raise RuntimeError(f'dry run unexpectedly changed the graph for scenario {scenario.name}')
    before = render_graph(
        demo.origin_pk,
        output_directory / f'{stem}_before.png',
        marked_for_deletion=planned,
    )

    removed, was_applied = contract_nodes(selected_pks, dry_run=False)
    if not was_applied:
        raise RuntimeError(f'operation was not applied for scenario {scenario.name}')

    after = render_graph(demo.origin_pk, output_directory / f'{stem}_after.png')
    nodes, _ = collect_graph(demo.origin_pk)
    marker_count = sum(node.node_type.startswith('contracted.') for node in nodes.values())
    if marker_count != scenario.expected_markers:
        raise RuntimeError(f'expected {scenario.expected_markers} contraction markers, found {marker_count}')
    return before, after, removed


def main() -> None:
    """Run all contraction scenarios and produce before-and-after PNGs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--output-directory',
        type=Path,
        default=Path.cwd() / 'node-contraction-regions',
        help='Directory for generated PNG files.',
    )
    args = parser.parse_args()

    if shutil.which('dot') is None:
        raise RuntimeError('Graphviz is required: install it and ensure the `dot` executable is on PATH')

    load_profile()
    args.output_directory.mkdir(parents=True, exist_ok=True)

    scenarios = (
        Scenario(
            name='single_branch',
            description='Contracting connected W1 and C1 creates one marker.',
            selected_names=('workflow_one', 'calculation_one'),
            expected_markers=1,
        ),
        Scenario(
            name='two_disconnected_branches',
            description='Contracting both branches without the root creates two markers.',
            selected_names=('workflow_one', 'calculation_one', 'workflow_two', 'calculation_two'),
            expected_markers=2,
        ),
        Scenario(
            name='branches_connected_by_root',
            description='Including the root connects both selected branches and creates one marker.',
            selected_names=('root', 'workflow_one', 'calculation_one', 'workflow_two', 'calculation_two'),
            expected_markers=1,
        ),
    )

    # Create every graph before deleting anything.
    # SQLite can reuse deleted integer primary keys, and reusing them while the
    # long-lived SQLAlchemy session still contains old objects triggers identity-map warnings.
    demos = tuple(create_demo_graph(scenario.name) for scenario in scenarios)

    for index, (scenario, demo) in enumerate(zip(scenarios, demos, strict=True), 1):
        before, after, deleted = run_scenario(scenario, demo, index, args.output_directory)
        print(f'[{scenario.name}] {scenario.description}')
        print(f'  selected nodes: {scenario.selected_names}')
        print(f'  contraction markers: {scenario.expected_markers}')
        print(f'  removed PKs: {sorted(deleted)}')
        print(f'  before: {before}')
        print(f'  after:  {after}')


if __name__ == '__main__':
    main()
