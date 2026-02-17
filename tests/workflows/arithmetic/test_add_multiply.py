###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `aiida.workflows.arithmetic.add_multiply` work function."""

import pytest

from aiida.orm import Int
from aiida.plugins import WorkflowFactory
from aiida.workflows.arithmetic.add_multiply import add_multiply


def test_factory():
    """Test that the work function can be loaded through the factory."""
    loaded = WorkflowFactory('core.arithmetic.add_multiply')
    assert loaded.is_process_function


def test_run():
    """Test running the work function."""
    x = Int(1)
    y = Int(2)
    z = Int(3)

    result = add_multiply(x, y, z)

    assert isinstance(result, Int)
    assert result == (x + y) * z
