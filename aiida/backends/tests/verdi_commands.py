# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Tests for nodes, attributes and links
"""

import mock

from aiida.backends.testbase import AiidaTestCase
from aiida.utils.capturing import Capturing

computer_name_1 = "torquessh1"
computer_setup_input_1 = [computer_name_1,
                          "localhost",
                          "",
                          "True",
                          "ssh",
                          "torque",
                          "/scratch/{username}/aiida_run",
                          "mpirun -np {tot_num_mpiprocs}",
                          "1",
                          EOFError,
                          EOFError,
                          ]


computer_name_2 = "torquessh2"
computer_setup_input_2 = [computer_name_2,
                          "localhost",
                          "",
                          "True",
                          "ssh",
                          "torque",
                          "/scratch/{username}/aiida_run",
                          "mpirun -np {tot_num_mpiprocs}",
                          "1",
                          EOFError,
                          EOFError,
                          ]

code_name_1 = "doubler_1"
code_setup_input_1 = [code_name_1,
                      "simple script that doubles a number "
                      "and sleeps for a given number of seconds",
                      "False",
                      "simpleplugins.templatereplacer",
                      computer_name_1,
                      "/usr/local/bin/doubler.sh",
                      EOFError,
                      EOFError,
                      ]

code_name_2 = "doubler_2"
code_setup_input_2 = [code_name_2,
                      "simple script that doubles a number "
                      "and sleeps for a given number of seconds",
                      "False",
                      "simpleplugins.templatereplacer",
                      computer_name_2,
                      "/usr/local/bin/doubler.sh",
                      EOFError,
                      EOFError,
                      ]


class TestVerdiCommands(AiidaTestCase):
    """
    Bla bla bla
    """

    def ttest_calculation_list(self):
        from aiida.cmdline.commands.calculation import Calculation
        calcCmd = Calculation()

        with captured_output() as (out, err):
            calcCmd.calculation_list()

        output = out.getvalue().strip()
        print "----->", output
        # self.assertEqual(output, 'hello world!')


class TestVerdiCodeCommands(AiidaTestCase):

    @classmethod
    def setUpClass(cls):
        """
        Create the computers and setup a codes
        """
        super(TestVerdiCodeCommands, cls).setUpClass()

        # Setup computer #1
        from aiida.cmdline.commands.computer import Computer
        cmd_comp = Computer()
        with mock.patch('__builtin__.raw_input',
                        side_effect=computer_setup_input_1):
            cmd_comp.computer_setup()

        # Setup a code for computer #1
        from aiida.cmdline.commands.code import Code
        code_cmd = Code()
        with mock.patch('__builtin__.raw_input',
                        side_effect=code_setup_input_1):
            code_cmd.code_setup()

        # Setup computer #2
        with mock.patch('__builtin__.raw_input',
                        side_effect=computer_setup_input_2):
            cmd_comp.computer_setup()

        # Setup a code for computer #2
        with mock.patch('__builtin__.raw_input',
                        side_effect=code_setup_input_2):
            code_cmd.code_setup()

    def test_code_list(self):
        """
        Do some code listing test to ensure the correct behaviour of
        verdi code list
        """
        from aiida.cmdline.commands.code import Code
        code_cmd = Code()

        # Run a simple verdi code list, capture the output and check the result
        with Capturing() as output:
            code_cmd.code_list()
        out_str_1 = ''.join(output)
        self.assertTrue(computer_name_1 in out_str_1,
                        "The computer 1 name should be included into "
                        "this list")
        self.assertTrue(code_name_1 in out_str_1,
                        "The code 1 name should be included into this list")
        self.assertTrue(computer_name_2 in out_str_1,
                        "The computer 2 name should be included into "
                        "this list")
        self.assertTrue(code_name_2 in out_str_1,
                        "The code 2 name should be included into this list")

        # Run a verdi code list -a, capture the output and check if the result
        # is the same as the previous one
        with Capturing() as output:
            code_cmd.code_list(*['-a'])
        out_str_2 = ''.join(output)
        self.assertEqual(out_str_1, out_str_2,
                         "verdi code list & verdi code list -a should provide "
                         "the same output in this experiment.")

        # Run a verdi code list -c, capture the output and check the result
        with Capturing() as output:
            code_cmd.code_list(*['-c', computer_name_1])
        out_str = ''.join(output)
        self.assertTrue(computer_name_1 in out_str,
                        "The computer 1 name should be included into "
                        "this list")
        self.assertFalse(computer_name_2 in out_str,
                         "The computer 2 name should not be included into "
                         "this list")
