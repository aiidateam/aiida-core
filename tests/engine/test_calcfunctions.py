###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the calcfunction decorator and CalcFunctionNode."""

import pytest

from aiida.common import exceptions
from aiida.common.links import LinkType
from aiida.engine import Process, calcfunction
from aiida.manage.caching import enable_caching
from aiida.orm import CalcFunctionNode, Int

# Global required for one of the caching tests to keep track of the number of times the calculation function is executed
EXECUTION_COUNTER = 0


@calcfunction
def add_calcfunction(data):
    return Int(data.value + 1)


@calcfunction
def return_stored_calcfunction():
    return Int(2).store()


@calcfunction
def execution_counter_calcfunction(data):
    global EXECUTION_COUNTER  # noqa: PLW0603
    EXECUTION_COUNTER += 1
    return Int(data.value + 1)


class TestCalcFunction:
    """Tests for calcfunctions.

    .. note: tests common to all process functions should go in `tests.engine.test_process_function.py`
    """

    @pytest.fixture(autouse=True)
    def init_profile(self):
        """Initialize the profile."""
        assert Process.current() is None
        self.default_int = Int(256)
        self.test_calcfunction = add_calcfunction
        yield
        assert Process.current() is None

    def test_calcfunction_node_type(self):
        """Verify that a calcfunction gets a CalcFunctionNode as node instance."""
        _, node = self.test_calcfunction.run_get_node(self.default_int)
        assert isinstance(node, CalcFunctionNode)

    def test_calcfunction_links(self):
        """Verify that a calcfunction can only get CREATE links and no RETURN links."""
        _, node = self.test_calcfunction.run_get_node(self.default_int)

        assert len(node.base.links.get_outgoing(link_type=LinkType.CREATE).all()) == 1
        assert len(node.base.links.get_outgoing(link_type=LinkType.RETURN).all()) == 0

    def test_calcfunction_return_stored(self):
        """Verify that a calcfunction will raise when a stored node is returned."""
        with pytest.raises(ValueError):
            return_stored_calcfunction.run_get_node()

    def test_calcfunction_default_linkname(self):
        """Verify that a calcfunction that returns a single Data node gets a default link label."""
        _, node = self.test_calcfunction.run_get_node(self.default_int)

        assert node.outputs.result == self.default_int.value + 1
        assert getattr(node.outputs, Process.SINGLE_OUTPUT_LINKNAME) == self.default_int.value + 1
        assert node.outputs[Process.SINGLE_OUTPUT_LINKNAME] == self.default_int.value + 1

    def test_calcfunction_caching(self):
        """Verify that a calcfunction can be cached."""
        assert EXECUTION_COUNTER == 0
        _, original = execution_counter_calcfunction.run_get_node(Int(5))
        assert EXECUTION_COUNTER == 1

        # Caching a CalcFunctionNode should be possible
        with enable_caching(identifier='*.execution_counter_calcfunction'):
            input_node = Int(5)
            result, cached = execution_counter_calcfunction.run_get_node(input_node)

            assert EXECUTION_COUNTER == 1  # Calculation function body should not have been executed
            assert result.is_stored
            assert cached.base.caching.is_created_from_cache
            assert cached.base.caching.get_cache_source() in original.uuid
            assert cached.base.links.get_incoming().one().node.uuid == input_node.uuid

    def test_calcfunction_caching_change_code(self):
        """Verify that changing the source code of a calcfunction invalidates any existing cached nodes.

        The ``add_calcfunction`` of the ``calcfunctions`` module uses the exact same name as the one defined in this
        test module, however, it has a slightly different implementation. Note that we have to define the duplicate in
        a different module, because we cannot define it in the same module (as the name clashes, on purpose) and we
        cannot inline the calcfunction in this test, since inlined process functions are not valid cache sources.
        """
        from .calcfunctions import add_calcfunction

        result_original = self.test_calcfunction(self.default_int)

        with enable_caching(identifier='*.add_calcfunction'):
            result_cached, cached = add_calcfunction.run_get_node(self.default_int)
            assert result_original != result_cached
            assert not cached.base.caching.is_created_from_cache
            assert cached.base.caching.is_valid_cache

            # Test that the locally-created calcfunction can be cached in principle
            result2_cached, cached2 = add_calcfunction.run_get_node(self.default_int)
            assert result2_cached != result_original
            assert result2_cached == result_cached
            assert cached2.base.caching.is_created_from_cache

    def test_calcfunction_do_not_store_provenance(self):
        """Run the function without storing the provenance."""
        data = Int(1)
        result, node = self.test_calcfunction.run_get_node(data, metadata={'store_provenance': False})
        assert not result.is_stored
        assert not data.is_stored
        assert not node.is_stored
        assert result == data + 1

    def test_calculation_cannot_call(self):
        """Verify that calling another process from within a calcfunction raises as it is forbidden."""

        @calcfunction
        def test_calcfunction_caller(data):
            self.test_calcfunction(data)

        with pytest.raises(exceptions.InvalidOperation):
            test_calcfunction_caller(self.default_int)

    def test_calculation_call_store_provenance_false(self):
        """Verify that a `calcfunction` can call another calcfunction as long as `store_provenance`  is False."""

        @calcfunction
        def test_calcfunction_caller(data):
            return self.test_calcfunction(data, metadata={'store_provenance': False})

        result, node = test_calcfunction_caller.run_get_node(self.default_int)

        assert isinstance(result, Int)
        assert isinstance(node, CalcFunctionNode)

        # The node of the outermost `calcfunction` should have a single `CREATE` link and no `CALL_CALC` links
        assert len(node.base.links.get_outgoing(link_type=LinkType.CREATE).all()) == 1
        assert len(node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).all()) == 0
