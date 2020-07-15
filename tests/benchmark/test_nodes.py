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
"""Benchmark tests for nodes."""
import pytest

from aiida.orm import Data
from aiida.engine import calcfunction, run, WorkChain


def get_node(store=True):
    data = Data()
    data.set_attribute_many({str(i): i for i in range(10)})
    if store:
        data.store()
    return (), {"node": data}


@pytest.mark.usefixtures('clear_database_before_test')
@pytest.mark.benchmark(group='node', min_rounds=100)
def test_store_backend(benchmark):

    def _run():
        data = Data()
        data.set_attribute_many({str(i): i for i in range(10)})
        return data._backend_entity.store(clean=False)

    benchmark(_run)


@pytest.mark.usefixtures('clear_database_before_test')
@pytest.mark.benchmark(group='node', min_rounds=100)
def test_store(benchmark):
    """Store a node."""
    benchmark(get_node)


@pytest.mark.usefixtures('clear_database_before_test')
@pytest.mark.benchmark(group='node')
def test_delete_backend(benchmark):

    def _run(node):
        Data.objects._backend.nodes.delete(node.pk)  # pylint: disable=no-member

    benchmark.pedantic(_run, setup=get_node, iterations=1, rounds=100, warmup_rounds=1)


@pytest.mark.usefixtures('clear_database_before_test')
@pytest.mark.benchmark(group='node')
def test_delete(benchmark):
    """Delete a node."""
    def _run(node):
        Data.objects.delete(node.pk)  # pylint: disable=no-member

    benchmark.pedantic(_run, setup=get_node, iterations=1, rounds=100, warmup_rounds=1)


@pytest.mark.usefixtures('clear_database_before_test')
@pytest.mark.benchmark(group='engine')
def test_calcfunction(benchmark):
    """Run a simple calcfunction."""

    @calcfunction
    def _calcfunction(node):
        return get_node(store=False)[1]["node"]

    def _run(node):
        return _calcfunction(node)

    result = benchmark.pedantic(_run, setup=get_node, iterations=1, rounds=50, warmup_rounds=1)
    assert isinstance(result, Data)


@pytest.mark.usefixtures('clear_database_before_test')
@pytest.mark.benchmark(group='engine')
def test_workchain(benchmark):

    @calcfunction
    def _calcfunction(node):
        return get_node(store=False)[1]["node"]

    class _Wc(WorkChain):

        @classmethod
        def define(cls, spec):
            super().define(spec)
            spec.input('node')
            spec.output('node')
            spec.outline(cls.call_workfunction)

        def call_workfunction(self):
            self.out('node', _calcfunction(self.inputs.node))

    def _run(node):
        return run(_Wc({"node": node}))

    result = benchmark.pedantic(_run, setup=get_node, iterations=1, rounds=50, warmup_rounds=1)
    assert isinstance(result['node'], Data)
