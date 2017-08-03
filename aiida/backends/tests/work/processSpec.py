# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################


from collections import Mapping
from aiida.backends.testbase import AiidaTestCase
from aiida.work.process import Process, ProcessSpec
import aiida.work.util as util


class TestProcessSpec(AiidaTestCase):
    def setUp(self):
        super(TestProcessSpec, self).setUp()
        self.assertEquals(len(util.ProcessStack.stack()), 0)
        self.spec = Process.spec()

    def tearDown(self):
        super(TestProcessSpec, self).tearDown()
        self.assertEquals(len(util.ProcessStack.stack()), 0)

    def test_get_inputs_template(self):
        s = ProcessSpec()
        s.input('a')
        s.input('b', default=5)

        template = s.get_inputs_template()
        self.assertIsInstance(template, Mapping)
        self._test_template(template)
        for attr in ['b']:
            self.assertTrue(
                attr in template,
                "Attribute '{}' not found in template".format(attr))

    def test_dynamic_input(self):
        from aiida.orm import Node
        from aiida.orm.data import Data

        n = Node()
        d = Data()
        port = self.spec.get_dynamic_input()
        self.assertFalse(port.validate("foo")[0])
        self.assertFalse(port.validate(5)[0])
        self.assertFalse(port.validate(n)[0])
        self.assertTrue(port.validate(d)[0])

    def test_dynamic_output(self):
        from aiida.orm import Node
        from aiida.orm.data import Data

        n = Node()
        d = Data()
        port = self.spec.get_dynamic_output()
        self.assertFalse(port.validate("foo")[0])
        self.assertFalse(port.validate(5)[0])
        self.assertFalse(port.validate(n)[0])
        self.assertTrue(port.validate(d)[0])

    def _test_template(self, template):
        template.a = 2
        self.assertEqual(template.a, 2)
        # Check the default is what we expect
        self.assertEqual(template.b, 5)
        with self.assertRaises(AttributeError):
            template.c = 6

        # Check that we can unpack
        self.assertEqual(dict(**template)['a'], 2)

