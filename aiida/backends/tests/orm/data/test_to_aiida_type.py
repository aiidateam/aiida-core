# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
This module contains tests for the to_aiida_type serializer
"""
from aiida.orm.nodes.data.base import to_aiida_type
from aiida.orm import Dict, Int, Float, Bool, Str

from aiida.backends.testbase import AiidaTestCase


class TestToAiiDAType(AiidaTestCase):
    """
    Test the to_aiida_type serialize that converts
    python objects to AiiDA nodes
    """

    def test_dict(self):
        """Test converting dict to Dict"""

        data = {'foo': 'bar', 'bla': {'bar': 'foo'}}

        # pylint: disable=assignment-from-no-return
        aiida_dict = to_aiida_type(data)
        self.assertIsInstance(aiida_dict, Dict)
        self.assertEqual(aiida_dict.get_dict(), data)

    def test_int(self):
        """Test integer"""

        # pylint: disable=assignment-from-no-return
        aiida_int = to_aiida_type(1234567)
        self.assertEqual(aiida_int, 1234567)
        self.assertIsInstance(aiida_int, Int)

    def test_flot(self):
        """Test converting float to Float"""

        float_value = 3.14159265358
        # pylint: disable=assignment-from-no-return
        aiida_float = to_aiida_type(float_value)
        self.assertEqual(aiida_float, float_value)
        self.assertIsInstance(aiida_float, Float)

    def test_bool(self):
        """Test converting bool to Bool"""

        import numpy as np
        # pylint: disable=assignment-from-no-return
        aiida_bool = to_aiida_type(True)
        self.assertIsInstance(aiida_bool, Bool)
        self.assertEqual(aiida_bool, True)

        # pylint: disable=assignment-from-no-return
        aiida_bool = to_aiida_type(np.bool_(True))
        self.assertIsInstance(aiida_bool, Bool)
        self.assertEqual(np.bool_(True), True)

    def test_str(self):
        """Test converting string to Str"""
        string = 'hello world'
        # pylint: disable=assignment-from-no-return
        aiida_string = to_aiida_type(string)
        self.assertIsInstance(aiida_string, Str)
        self.assertEqual(aiida_string, string)
