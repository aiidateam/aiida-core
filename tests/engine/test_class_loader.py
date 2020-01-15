# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""A module to test class loader factories."""
import aiida

from aiida.backends.testbase import AiidaTestCase
from aiida.engine import Process
from aiida.plugins import CalculationFactory


class TestCalcJob(AiidaTestCase):
    """Test CalcJob."""

    def setUp(self):
        super().setUp()
        self.assertIsNone(Process.current())

    def tearDown(self):
        super().tearDown()
        self.assertIsNone(Process.current())

    def test_class_loader(self):
        """Test that CalculationFactory works."""
        process = CalculationFactory('templatereplacer')
        loader = aiida.engine.persistence.get_object_loader()

        class_name = loader.identify_object(process)
        loaded_class = loader.load_object(class_name)

        self.assertEqual(process.__name__, loaded_class.__name__)
        self.assertEqual(class_name, loader.identify_object(loaded_class))
