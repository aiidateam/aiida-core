###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the workfunction decorator and WorkFunctionNode."""

import pytest

from aiida.common.links import LinkType
from aiida.engine import Process, calcfunction, workfunction
from aiida.manage.caching import enable_caching
from aiida.orm import CalcFunctionNode, Int, WorkFunctionNode


@pytest.mark.requires_rmq
class TestWorkFunction:
    """Tests for workfunctions.

    .. note: tests common to all process functions should go in `tests.engine.test_process_function.py`
    """

    @pytest.fixture(autouse=True)
    def init_profile(self):
        """Initialize the profile."""
        assert Process.current() is None
        self.default_int = Int(256)

        @workfunction
        def test_workfunction(data):
            return data

        self.test_workfunction = test_workfunction

        yield
        assert Process.current() is None

    def test_workfunction_node_type(self):
        """Verify that a workfunction gets a WorkFunctionNode as node instance."""
        _, node = self.test_workfunction.run_get_node(self.default_int)
        assert isinstance(node, WorkFunctionNode)

    def test_workfunction_links(self):
        """Verify that a workfunction can only get RETURN links and no CREATE links."""
        _, node = self.test_workfunction.run_get_node(self.default_int)

        assert len(node.base.links.get_outgoing(link_type=LinkType.RETURN).all()) == 1
        assert len(node.base.links.get_outgoing(link_type=LinkType.CREATE).all()) == 0

    def test_workfunction_return_unstored(self):
        """Verify that a workfunction will raise when an unstored node is returned."""

        @workfunction
        def test_workfunction():
            return Int(2)

        with pytest.raises(ValueError):
            test_workfunction.run_get_node()

    def test_workfunction_default_linkname(self):
        """Verify that a workfunction that returns a single Data node gets a default link label."""
        _, node = self.test_workfunction.run_get_node(self.default_int)

        assert node.outputs.result == self.default_int
        assert getattr(node.outputs, Process.SINGLE_OUTPUT_LINKNAME) == self.default_int
        assert node.outputs[Process.SINGLE_OUTPUT_LINKNAME] == self.default_int

    def test_workfunction_caching(self):
        """Verify that a workfunction cannot be cached."""
        _ = self.test_workfunction(self.default_int)

        # Caching should always be disabled for a WorkFunctionNode
        with enable_caching():
            _, cached = self.test_workfunction.run_get_node(self.default_int)
            assert not cached.base.caching.is_created_from_cache

    def test_call_link_label(self):
        """Verify that setting a `call_link_label` on a `calcfunction` called from a `workfunction` works."""
        link_label = 'non_default_call_link_label'

        @calcfunction
        def calculation():
            return

        @workfunction
        def caller():
            calculation(metadata={'call_link_label': link_label})

        _, node = caller.run_get_node()

        # Verify that the `CALL` link of the calculation function is there with the correct label
        link_triple = node.base.links.get_outgoing(link_type=LinkType.CALL_CALC, link_label_filter=link_label).one()
        assert isinstance(link_triple.node, CalcFunctionNode)
