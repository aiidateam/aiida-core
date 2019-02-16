# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.backends.testbase import AiidaTestCase
from aiida.orm.nodes.data.frozendict import FrozenDict
from aiida.orm.nodes.data.int import Int
from aiida.orm.nodes.data.str import Str


class TestFrozenDict(AiidaTestCase):

    def test_create(self):
        FrozenDict(dict={})

    def test_create_invalid(self):
        with self.assertRaises(AssertionError):
            FrozenDict(dict={'a': 5})

    def test_get_value(self):
        inputs = {'a': Int(5).store()}
        dictionary = FrozenDict(dict=inputs)
        self.assertEqual(dictionary['a'], inputs['a'])

    def test_iterate(self):
        inputs = {'a': Int(5).store(), 'b': Str('testing').store()}
        dictionary = FrozenDict(dict=inputs)
        for key, value in dictionary.items():
            self.assertEqual(inputs[key], value)

    def test_length(self):
        inputs = {'a': Int(5).store(), 'b': Str('testing').store()}
        dictionary = FrozenDict(dict=inputs)
        self.assertEqual(len(inputs), len(dictionary))
