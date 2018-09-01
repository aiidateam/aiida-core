# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from __future__ import absolute_import
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

    def test_exit_code(self):
        """
        Test the definition of error codes through the ProcessSpec
        """
        label = 'SOME_EXIT_CODE'
        status = 418
        message = 'I am a teapot'

        self.spec.exit_code(status, label, message)

        self.assertEquals(self.spec.exit_codes.SOME_EXIT_CODE.status, status)
        self.assertEquals(self.spec.exit_codes.SOME_EXIT_CODE.message, message)

        self.assertEquals(self.spec.exit_codes['SOME_EXIT_CODE'].status, status)
        self.assertEquals(self.spec.exit_codes['SOME_EXIT_CODE'].message, message)

        self.assertEquals(self.spec.exit_codes[label].status, status)
        self.assertEquals(self.spec.exit_codes[label].message, message)

    def test_exit_code_invalid(self):
        """
        Test type validation for registering new error codes
        """
        status = 418
        label = 'SOME_EXIT_CODE'
        message = 'I am a teapot'

        with self.assertRaises(TypeError):
            self.spec.exit_code(status, 256, message)

        with self.assertRaises(TypeError):
            self.spec.exit_code('string', label, message)

        with self.assertRaises(ValueError):
            self.spec.exit_code(-256, label, message)

        with self.assertRaises(TypeError):
            self.spec.exit_code(status, label, 8)
