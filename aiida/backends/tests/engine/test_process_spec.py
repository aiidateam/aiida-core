# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `ProcessSpec` class."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.backends.testbase import AiidaTestCase
from aiida.engine import Process
from aiida.orm import Node, Data


class TestProcessSpec(AiidaTestCase):
    """Tests for the `ProcessSpec` class."""

    def setUp(self):
        super(TestProcessSpec, self).setUp()
        self.assertIsNone(Process.current())
        self.spec = Process.spec()

    def tearDown(self):
        super(TestProcessSpec, self).tearDown()
        self.assertIsNone(Process.current())

    def test_dynamic_input(self):
        """Test a process spec with dynamic input enabled."""
        node = Node()
        data = Data()
        self.assertIsNotNone(self.spec.validate_inputs({'key': 'foo'}))
        self.assertIsNotNone(self.spec.validate_inputs({'key': 5}))
        self.assertIsNotNone(self.spec.validate_inputs({'key': node}))
        self.assertIsNone(self.spec.validate_inputs({'key': data}))

    def test_dynamic_output(self):
        """Test a process spec with dynamic output enabled."""
        node = Node()
        data = Data()
        self.assertIsNotNone(self.spec.validate_outputs({'key': 'foo'}))
        self.assertIsNotNone(self.spec.validate_outputs({'key': 5}))
        self.assertIsNotNone(self.spec.validate_outputs({'key': node}))
        self.assertIsNone(self.spec.validate_outputs({'key': data}))

    def test_exit_code(self):
        """Test the definition of error codes through the ProcessSpec."""
        label = 'SOME_EXIT_CODE'
        status = 418
        message = 'I am a teapot'

        self.spec.exit_code(status, label, message)

        self.assertEqual(self.spec.exit_codes.SOME_EXIT_CODE.status, status)
        self.assertEqual(self.spec.exit_codes.SOME_EXIT_CODE.message, message)

        self.assertEqual(self.spec.exit_codes['SOME_EXIT_CODE'].status, status)
        self.assertEqual(self.spec.exit_codes['SOME_EXIT_CODE'].message, message)

        self.assertEqual(self.spec.exit_codes[label].status, status)
        self.assertEqual(self.spec.exit_codes[label].message, message)

    def test_exit_code_invalid(self):
        """Test type validation for registering new error codes."""
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
