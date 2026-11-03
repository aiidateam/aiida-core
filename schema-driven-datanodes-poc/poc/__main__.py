###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Run the schema-driven data-node PoC."""

from __future__ import annotations

from .orm.nodes.data import TrajectoryData, load_node
from .storage import load_profile

TYPE_NAMES = {
    0: 'string',
    1: 'int',
    2: 'float',
    3: 'bool',
    4: 'list[string]',
}



def run_example() -> None:
    """Run the user-facing data-node round trip."""
    format_version, schema = TrajectoryData._load_schema()

    print('stored data-node schema in SQLite as protobuf blob')
    print(f'  format version: {format_version}')
    print(f'  schema name:    {schema.name}')
    print('  fields:')
    for field in TrajectoryData.fields():
        validator = field.validator_name or '-'
        print(f'    - {field.name}: {TYPE_NAMES[field.scalar_type]}, validator={validator}')

    node = TrajectoryData(label='water-md', nsteps=1000, tags=['production', 'nvt'])
    node_id = node.store()
    del node
    rebuilt = load_node(node_id, TrajectoryData)

    print('\nuser-facing round trip')
    print("  created: TrajectoryData(label='water-md', nsteps=1000, tags=['production', 'nvt'])")
    print(f'  stored id: {node_id}')
    print(f'  loaded:    {rebuilt}')

    try:
        TrajectoryData(label='', nsteps=0).store()
    except ValueError as exception:
        print('\ninvalid payload is rejected during store()')
        print(f'  error: {exception}')


def main() -> None:
    load_profile(':memory:')
    run_example()


if __name__ == '__main__':
    main()
