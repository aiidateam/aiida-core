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
from aiida.orm import Code



class TestExampleHelpers(AiidaTestCase):
    CODE_LABEL = 'test_code'
    INPUT_PLUGIN_NAME = 'test_input_plugin'

    def setUp(self):
        # Create some code nodes
        code = Code()
        code.set_remote_computer_exec((self.computer, '/bin/true'))
        code.label = self.CODE_LABEL
        code.set_input_plugin_name(self.INPUT_PLUGIN_NAME)
        code.store()

    def tearDown(self):
        from aiida.orm.code import delete_code

        code = Code.get_from_string(self.CODE_LABEL)
        delete_code(code)

    def test_test_and_get_code(self):
        """
        Checks that the test_and_get_code functions of the example_helpers
        file behaves as expected.
        """

        from aiida.common.example_helpers import test_and_get_code

        # When asking an existing code, the returned code
        # should be the right one
        code = test_and_get_code('test_code', 'test_input_plugin')
        self.assertEquals(code.label, self.CODE_LABEL,
                          "The code name is not the expected one.")
        self.assertEquals(code.get_input_plugin_name(), self.INPUT_PLUGIN_NAME,
                          "The input plugin name of the code is not the "
                          "expected one.")

        # Check the correct behaviour of the function when asking a code that
        # doesn't exist and when the input doesn't also exist
        with self.assertRaises(ValueError):
            test_and_get_code('no_code', 'no_input_plugin',
                              use_exceptions=True)

        with self.assertRaises(ValueError):
            test_and_get_code('no_code', self.INPUT_PLUGIN_NAME,
                              use_exceptions=True)

