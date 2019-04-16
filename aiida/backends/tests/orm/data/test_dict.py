# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `Dict` class."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.backends.testbase import AiidaTestCase
from aiida.orm import Dict


class TestDict(AiidaTestCase):
    """Test for the `Dict` class."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super(TestDict, cls).setUpClass(*args, **kwargs)
        cls.dictionary = {'value': 1, 'nested': {'dict': 'ionary'}}
        cls.node = Dict(dict=cls.dictionary)

    def test_keys(self):
        """Test the `keys` method."""
        self.assertEqual(sorted(self.node.keys()), sorted(self.dictionary.keys()))

    def test_get_dict(self):
        """Test the `get_dict` method."""
        self.assertEqual(self.node.get_dict(), self.dictionary)

    def test_dict_property(self):
        """Test the `dict` property."""
        self.assertEqual(self.node.dict.value, self.dictionary['value'])
        self.assertEqual(self.node.dict.nested, self.dictionary['nested'])

    def test_get_item(self):
        """Test the `__getitem__` method."""
        self.assertEqual(self.node['value'], self.dictionary['value'])
        self.assertEqual(self.node['nested'], self.dictionary['nested'])
