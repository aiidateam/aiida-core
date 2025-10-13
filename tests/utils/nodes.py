###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utilities for testing memory leakage."""

import uuid

from aiida import orm
from aiida.common import timezone
from aiida.manage import get_manager


def create_int_nodes(num_nodes, backend=None):
    """Create a specified number of Int nodes efficiently using bulk_insert.

    :param num_nodes: Number of nodes to create
    :param backend: Optional backend instance. If None, uses default profile storage.
    :returns: List of PKs of orm.Int nodes created in profile storage
    """
    if backend is None:
        backend = get_manager().get_profile_storage()

    assert backend.default_user is not None

    current_time = timezone.now()

    nodes_data = []
    for i in range(num_nodes):
        node_data = {
            'uuid': str(uuid.uuid4()),
            'node_type': 'data.core.int.Int.',
            'process_type': None,
            'label': f'test_node_{i}',
            'description': 'Test node for integration testing',
            'user_id': backend.default_user.pk,
            'dbcomputer_id': None,
            'ctime': current_time,
            'mtime': current_time,
            'attributes': {'value': i},
            'extras': {},
            'repository_metadata': {},
        }
        nodes_data.append(node_data)

    return backend.bulk_insert(entity_type=orm.entities.EntityTypes.NODE, rows=nodes_data)
