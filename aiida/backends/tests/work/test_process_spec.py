# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.backends.testbase import AiidaTestCase
from aiida.work import Process


class TestProcessSpec(AiidaTestCase):

    def setUp(self):
        super(TestProcessSpec, self).setUp()
        self.assertIsNone(Process.current())
        self.spec = Process.spec()

    def tearDown(self):
        super(TestProcessSpec, self).tearDown()
        self.assertIsNone(Process.current())

    def test_dynamic_input(self):
        from aiida.orm import Node
        from aiida.orm.data import Data

        n = Node()
        d = Data()
        self.assertFalse(self.spec.validate_inputs({'key': 'foo'})[0])
        self.assertFalse(self.spec.validate_inputs({'key': 5})[0])
        self.assertFalse(self.spec.validate_inputs({'key': n})[0])
        self.assertTrue(self.spec.validate_inputs({'key': d})[0])

    def test_dynamic_output(self):
        from aiida.orm import Node
        from aiida.orm.data import Data

        n = Node()
        d = Data()
        self.assertFalse(self.spec.validate_outputs({'key': 'foo'})[0])
        self.assertFalse(self.spec.validate_outputs({'key': 5})[0])
        self.assertFalse(self.spec.validate_outputs({'key': n})[0])
        self.assertTrue(self.spec.validate_outputs({'key': d})[0])
