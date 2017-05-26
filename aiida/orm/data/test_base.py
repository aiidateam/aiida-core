# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import unittest
from aiida.orm.data.base import Bool

class BoolTestCase(unittest.TestCase):
    def test_bool_conversion(self):
        for val in [True, False]:
            self.assertEqual(val, bool(Bool(val)))

    def test_int_conversion(self):
        for val in [True, False]:
            self.assertEqual(int(val), int(Bool(val)))
