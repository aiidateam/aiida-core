# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=unused-argument,protected-access
"""Performance benchmark tests for single nodes.

The purpose of these tests is to benchmark and compare basic node interactions,
such as storage and deletion from the database and repository.
"""
from io import StringIO

import pytest

from aiida.orm import Data

GROUP_NAME = 'node'


def get_data_node(store=True):
    """A function to create a simple data node."""
    data = Data()
    data.set_attribute_many({str(i): i for i in range(10)})
    if store:
        data.store()
    return (), {'node': data}


def get_data_node_and_object(store=True):
    """A function to create a simple data node, with an object."""
    data = Data()
    data.set_attribute_many({str(i): i for i in range(10)})
    data.put_object_from_filelike(StringIO('a' * 10000), 'key')
    if store:
        data.store()
    return (), {'node': data}


@pytest.mark.usefixtures('clear_database_before_test')
@pytest.mark.benchmark(group=GROUP_NAME, min_rounds=100)
def test_store_backend(benchmark):
    """Benchmark for creating and storing a node directly,
    via the backend storage mechanism.
    """

    def _run():
        data = Data()
        data.set_attribute_many({str(i): i for i in range(10)})
        return data._backend_entity.store(clean=False)

    benchmark(_run)


@pytest.mark.usefixtures('clear_database_before_test')
@pytest.mark.benchmark(group=GROUP_NAME, min_rounds=100)
def test_store(benchmark):
    """Benchmark for creating and storing a node,
    via the full ORM mechanism.
    """
    benchmark(get_data_node)


@pytest.mark.usefixtures('clear_database_before_test')
@pytest.mark.benchmark(group=GROUP_NAME, min_rounds=100)
def test_store_with_object(benchmark):
    """Benchmark for creating and storing a node,
    including an object to be stored in the repository.
    """
    benchmark(get_data_node_and_object)


@pytest.mark.usefixtures('clear_database_before_test')
@pytest.mark.benchmark(group=GROUP_NAME)
def test_delete_backend(benchmark):
    """Benchmark for deleting a stored node directly,
    via the backend deletion mechanism.
    """

    def _run(node):
        Data.objects._backend.nodes.delete(node.pk)  # pylint: disable=no-member

    benchmark.pedantic(_run, setup=get_data_node, iterations=1, rounds=100, warmup_rounds=1)


@pytest.mark.usefixtures('clear_database_before_test')
@pytest.mark.benchmark(group=GROUP_NAME)
def test_delete(benchmark):
    """Benchmark for deleting a node,
    via the full ORM mechanism.
    """

    def _run(node):
        Data.objects.delete(node.pk)  # pylint: disable=no-member

    benchmark.pedantic(_run, setup=get_data_node, iterations=1, rounds=100, warmup_rounds=1)


@pytest.mark.usefixtures('clear_database_before_test')
@pytest.mark.benchmark(group=GROUP_NAME)
def test_delete_with_object(benchmark):
    """Benchmark for deleting a node,
    including an object stored in the repository
    """

    def _run(node):
        Data.objects.delete(node.pk)  # pylint: disable=no-member

    benchmark.pedantic(_run, setup=get_data_node_and_object, iterations=1, rounds=100, warmup_rounds=1)
