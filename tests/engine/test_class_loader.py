###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""A module to test class loader factories."""

import pytest

import aiida
from aiida.engine import Process
from aiida.plugins import CalculationFactory


class TestCalcJob:
    """Test CalcJob."""

    @pytest.fixture(autouse=True)
    def init_profile(self):
        """Initialize the profile."""
        assert Process.current() is None
        yield
        assert Process.current() is None

    def test_class_loader(self):
        """Test that CalculationFactory works."""
        process = CalculationFactory('core.templatereplacer')
        loader = aiida.engine.persistence.get_object_loader()

        class_name = loader.identify_object(process)
        loaded_class = loader.load_object(class_name)

        assert process.__name__ == loaded_class.__name__
        assert class_name == loader.identify_object(loaded_class)
