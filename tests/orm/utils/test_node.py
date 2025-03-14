###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `Node` utils."""

import pytest

from aiida.orm import Data
from aiida.orm.utils.node import load_node_class


def test_load_node_class_fallback():
    """Verify that `load_node_class` will fall back to `Data` class if entry point cannot be loaded."""
    loaded_class = load_node_class('data.core.some.non.existing.plugin.')
    assert loaded_class == Data

    # For really unresolvable type strings, we fall back onto the `Data` class
    with pytest.warns(UserWarning):
        loaded_class = load_node_class('__main__.SubData.')
    assert loaded_class == Data
