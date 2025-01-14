###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `run` functions."""

import pytest

from aiida.engine import run, run_get_node
from aiida.orm import Int, ProcessNode, Str
from tests.utils.processes import DummyProcess


@pytest.mark.requires_rmq
class TestRun:
    """Tests for the `run` functions."""

    @staticmethod
    def test_run():
        """Test the `run` function."""
        inputs = {'a': Int(2), 'b': Str('test')}
        run(DummyProcess, **inputs)

    def test_run_get_node(self):
        """Test the `run_get_node` function."""
        inputs = {'a': Int(2), 'b': Str('test')}
        result, node = run_get_node(DummyProcess, **inputs)
        assert isinstance(node, ProcessNode)
