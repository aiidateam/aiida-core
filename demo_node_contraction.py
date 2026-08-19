###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Create and render a provenance graph before and after node contraction.

The script creates this graph in the current profile::

    input -> calculation one -> intermediate -> calculation two -> output

It then contracts both calculations and the intermediate data node, leaving one
internal contraction marker between the input and output nodes.

The script requires the Graphviz ``dot`` executable and writes
``contraction_before.png`` and ``contraction_after.png``.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from plumpy import ProcessState

from aiida import load_profile
from aiida.common import LinkType
from aiida.orm import CalculationNode, Data, load_node
from aiida.tools import contract_nodes
from aiida.tools.visualization import Graph


def create_calculation(input_node: Data, *, label: str, output_label: str) -> tuple[CalculationNode, Data]:
    """Create a sealed calculation with one input and one output."""
    calculation = CalculationNode(label=label)
    calculation.base.links.add_incoming(input_node, LinkType.INPUT_CALC, 'input')
    calculation.store()

    output = Data(label=output_label).store()
    output.base.links.add_incoming(calculation, LinkType.CREATE, 'result')

    calculation.set_process_state(ProcessState.FINISHED)
    calculation.set_exit_status(0)
    calculation.seal()
    return calculation, output


def render_graph(origin: Data, path: Path) -> Path:
    """Render all descendants of ``origin``, including contracted links."""
    graph = Graph(graph_attr={'rankdir': 'LR'}, node_id_type='pk')
    graph.recurse_descendants(
        origin,
        origin_style=None,
        include_process_inputs=True,
        annotate_links='both',
        link_types=tuple(LinkType),
    )
    rendered = graph.graphviz.render(filename=path.stem, directory=path.parent, format='png', cleanup=True)
    return Path(rendered)


def main() -> None:
    """Create the example graph, contract it, and render both states."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--output-directory',
        type=Path,
        default=Path.cwd(),
        help='Directory for the generated PNG files.',
    )
    args = parser.parse_args()

    if shutil.which('dot') is None:
        raise RuntimeError('Graphviz is required: install it and ensure the `dot` executable is on PATH')

    load_profile()
    args.output_directory.mkdir(parents=True, exist_ok=True)

    input_node = Data(label='input').store()
    calculation_one, intermediate = create_calculation(
        input_node, label='calculation one', output_label='intermediate'
    )
    calculation_two, output = create_calculation(intermediate, label='calculation two', output_label='output')

    before_path = render_graph(input_node, args.output_directory / 'contraction_before.png')

    selected_pks = [calculation_one.pk, intermediate.pk, calculation_two.pk]
    contracted_pks, was_contracted = contract_nodes(selected_pks, dry_run=False)
    if not was_contracted or contracted_pks != set(selected_pks):
        raise RuntimeError(
            f'unexpected contraction result: contracted={contracted_pks}, applied={was_contracted}'
        )

    input_node = load_node(input_node.pk)
    output = load_node(output.pk)
    marker = input_node.base.links.get_outgoing(link_type=LinkType.CONTRACTED).one().node
    after_path = render_graph(input_node, args.output_directory / 'contraction_after.png')

    print(f'Before: {before_path}')
    print(f'After:  {after_path}')
    print(f'Marker: pk={marker.pk}, uuid={marker.uuid}')
    print(f'Output: pk={output.pk}, uuid={output.uuid}')


if __name__ == '__main__':
    main()
