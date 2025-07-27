###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Unit tests for REST API statistics."""

from threading import Thread

import pytest
import requests


def linearize_namespace(tree_namespace, linear_namespace=None):
    """Linearize a branched namespace with full_type, count, and subspaces"""
    if linear_namespace is None:
        linear_namespace = {}

    full_type = tree_namespace['full_type']
    while full_type[-1] != '.':
        full_type = full_type[0:-1]

    counter = tree_namespace['counter']
    subspaces = tree_namespace['subspaces']

    linear_namespace[full_type] = counter
    for subspace in subspaces:
        linearize_namespace(subspace, linear_namespace)

    return linear_namespace


@pytest.mark.usefixtures('populate_restapi_database')
def test_count_consistency(restapi_server, server_url):
    """Test the consistency in values between full_type_count and statistics"""
    server = restapi_server()
    server_thread = Thread(target=server.serve_forever)

    _server_url = server_url(port=server.server_port)

    try:
        server_thread.start()
        type_count_response = requests.get(f'{_server_url}/nodes/full_types_count', timeout=10)
        statistics_response = requests.get(f'{_server_url}/nodes/statistics', timeout=10)
    finally:
        server.shutdown()

    type_count_dict = linearize_namespace(type_count_response.json()['data'])
    statistics_dict = statistics_response.json()['data']['types']

    for full_type, count in statistics_dict.items():
        if full_type in type_count_dict:
            assert count == type_count_dict[full_type], f'Found inconsistency for full_type {full_type!r}'
