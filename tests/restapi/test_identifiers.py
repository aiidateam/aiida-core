###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `aiida.restapi.common.identifiers` module."""

from threading import Thread

import pytest
import requests

from aiida import orm
from aiida.restapi.common.identifiers import FULL_TYPE_CONCATENATOR, LIKE_OPERATOR_CHARACTER, get_full_type_filters


def test_get_full_type_filters():
    """Coverage test for the `get_full_type_filters` function."""
    # Equals on both
    filters = get_full_type_filters(f'node_type{FULL_TYPE_CONCATENATOR}process_type')
    assert filters['node_type'] == {'==': 'node_type'}
    assert filters['process_type'] == {'==': 'process_type'}

    # Like on `node_type`
    filters = get_full_type_filters(f'node_type{LIKE_OPERATOR_CHARACTER}{FULL_TYPE_CONCATENATOR}process_type')
    assert filters['node_type'] == {'like': 'node\\_type%'}
    assert filters['process_type'] == {'==': 'process_type'}

    # Like on `process_type`
    filters = get_full_type_filters(f'node_type{FULL_TYPE_CONCATENATOR}process_type{LIKE_OPERATOR_CHARACTER}')
    assert filters['node_type'] == {'==': 'node_type'}
    assert filters['process_type'] == {'like': 'process\\_type%'}

    # Like on both
    filters = get_full_type_filters(
        'node_type{like}{concat}process_type{like}'.format(like=LIKE_OPERATOR_CHARACTER, concat=FULL_TYPE_CONCATENATOR)
    )
    assert filters['node_type'] == {'like': 'node\\_type%'}
    assert filters['process_type'] == {'like': 'process\\_type%'}

    # Test patologic case of process_type = '' / None
    filters = get_full_type_filters(f'node_type{FULL_TYPE_CONCATENATOR}')
    assert filters['node_type'] == {'==': 'node_type'}
    assert filters['process_type'] == {'or': [{'==': ''}, {'==': None}]}

    filters = get_full_type_filters(f'node_type{LIKE_OPERATOR_CHARACTER}{FULL_TYPE_CONCATENATOR}')
    assert filters['node_type'] == {'like': 'node\\_type%'}
    assert filters['process_type'] == {'or': [{'==': ''}, {'==': None}]}


def test_get_filters_errors():
    """Test the `get_full_type_filters` function."""
    with pytest.raises(TypeError):
        get_full_type_filters(10)

    with pytest.raises(ValueError):
        get_full_type_filters('string_without_full_type_concatenator')

    with pytest.raises(ValueError):
        get_full_type_filters(
            'too_many_{like}{like}{concat}process_type'.format(
                like=LIKE_OPERATOR_CHARACTER, concat=FULL_TYPE_CONCATENATOR
            )
        )

    with pytest.raises(ValueError):
        get_full_type_filters(
            'node_type{concat}too_many_{like}{like}'.format(like=LIKE_OPERATOR_CHARACTER, concat=FULL_TYPE_CONCATENATOR)
        )

    with pytest.raises(ValueError):
        get_full_type_filters(f'not_at_{LIKE_OPERATOR_CHARACTER}_the_end{FULL_TYPE_CONCATENATOR}process_type')

    with pytest.raises(ValueError):
        get_full_type_filters(f'node_type{FULL_TYPE_CONCATENATOR}not_at_{LIKE_OPERATOR_CHARACTER}_the_end')


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    'process_class', [orm.CalcFunctionNode, orm.CalcJobNode, orm.WorkFunctionNode, orm.WorkChainNode]
)
def test_full_type_unregistered(process_class, restapi_server, server_url):
    """Functionality test for the compatibility with old process_type entries.

    This will only check the integrity of the shape of the tree, there is no checking on how the
    data should be represented internally in term of full types, labels, etc. The only thing that
    must work correctly is the internal consistency of `full_type` as it is interpreted by the
    get_full_type_filters and the querybuilder.
    """
    calc_unreg11 = process_class()
    calc_unreg11.set_process_type('unregistered_type1.process1')
    calc_unreg11.store()

    calc_unreg21 = process_class()
    calc_unreg21.set_process_type('unregistered_type2.process1')
    calc_unreg21.store()

    calc_unreg22 = process_class()
    calc_unreg22.set_process_type('unregistered_type2.process2')
    calc_unreg22.store()

    server = restapi_server()
    server_thread = Thread(target=server.serve_forever)

    _server_url = server_url(port=server.server_port)

    try:
        server_thread.start()
        type_count_response = requests.get(f'{_server_url}/nodes/full_types', timeout=10)
    finally:
        server.shutdown()

    # All nodes = only processes
    # The main branch for all nodes does not currently return a queryable full_type
    current_namespace = type_count_response.json()['data']
    assert len(current_namespace['subspaces']) == 1

    # All processes = only one kind of process (Calculation/Workflow)
    current_namespace = current_namespace['subspaces'][0]
    query_all = orm.QueryBuilder().append(orm.Node, filters=get_full_type_filters(current_namespace['full_type']))
    assert len(current_namespace['subspaces']) == 1
    assert query_all.count() == 3

    # All subprocesses = only one kind of subprocess (calcfunc/workfunc or calcjob/workchain)
    current_namespace = current_namespace['subspaces'][0]
    query_all = orm.QueryBuilder().append(orm.Node, filters=get_full_type_filters(current_namespace['full_type']))
    assert len(current_namespace['subspaces']) == 1
    assert query_all.count() == 3

    # One branch for each registered plugin and one for all unregistered
    # (there are only unregistered here)
    current_namespace = current_namespace['subspaces'][0]
    query_all = orm.QueryBuilder().append(orm.Node, filters=get_full_type_filters(current_namespace['full_type']))
    assert len(current_namespace['subspaces']) == 1
    assert query_all.count() == 3

    # There are only two  process types: unregistered_type1 (1) and unregistered_type2 (2)
    # The unregistered branch does not currently return a queryable full_type
    current_namespace = current_namespace['subspaces'][0]
    assert len(current_namespace['subspaces']) == 2

    type_namespace = current_namespace['subspaces'][0]
    query_type = orm.QueryBuilder().append(orm.Node, filters=get_full_type_filters(type_namespace['full_type']))
    assert len(type_namespace['subspaces']) == 1
    assert query_type.count() == 1

    type_namespace = current_namespace['subspaces'][1]
    query_type = orm.QueryBuilder().append(orm.Node, filters=get_full_type_filters(type_namespace['full_type']))
    assert len(type_namespace['subspaces']) == 2
    assert query_type.count() == 2

    # Finally we check each specific subtype (1 for unregistered_type1 and 2 for unregistered_type2)
    # These are lead nodes without any further subspace
    type_namespace = current_namespace['subspaces'][0]['subspaces'][0]
    query_type = orm.QueryBuilder().append(orm.Node, filters=get_full_type_filters(type_namespace['full_type']))
    assert len(type_namespace['subspaces']) == 0
    assert query_type.count() == 1

    type_namespace = current_namespace['subspaces'][1]['subspaces'][0]
    query_type = orm.QueryBuilder().append(orm.Node, filters=get_full_type_filters(type_namespace['full_type']))
    assert len(type_namespace['subspaces']) == 0
    assert query_type.count() == 1

    type_namespace = current_namespace['subspaces'][1]['subspaces'][1]
    query_type = orm.QueryBuilder().append(orm.Node, filters=get_full_type_filters(type_namespace['full_type']))
    assert len(type_namespace['subspaces']) == 0
    assert query_type.count() == 1


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize('node_class', [orm.CalcFunctionNode, orm.Dict])
def test_full_type_backwards_compatibility(node_class, restapi_server, server_url):
    """Functionality test for the compatibility with old process_type entries.

    This will only check the integrity of the shape of the tree, there is no checking on how the
    data should be represented internally in term of full types, labels, etc. The only thing that
    must work correctly is the internal consistency of `full_type` as it is interpreted by the
    get_full_type_filters and the querybuilder.
    """
    node_empty = node_class()
    node_empty.process_type = ''
    node_empty.store()

    node_nones = node_class()
    node_nones.process_type = None
    node_nones.store()

    server = restapi_server()
    server_thread = Thread(target=server.serve_forever)

    _server_url = server_url(port=server.server_port)

    try:
        server_thread.start()
        type_count_response = requests.get(f'{_server_url}/nodes/full_types', timeout=10)
    finally:
        server.shutdown()

    # All nodes (contains either a process branch or data branch)
    # The main branch for all nodes does not currently return a queryable full_type
    current_namespace = type_count_response.json()['data']
    assert len(current_namespace['subspaces']) == 1

    # All subnodes (contains a workflow, calculation or data_type branch)
    current_namespace = current_namespace['subspaces'][0]
    query_all = orm.QueryBuilder().append(orm.Node, filters=get_full_type_filters(current_namespace['full_type']))
    assert len(current_namespace['subspaces']) == 1
    assert query_all.count() == 2

    current_namespace = current_namespace['subspaces'][0]
    query_all = orm.QueryBuilder().append(orm.Node, filters=get_full_type_filters(current_namespace['full_type']))
    assert len(current_namespace['subspaces']) == 1
    assert query_all.count() == 2
