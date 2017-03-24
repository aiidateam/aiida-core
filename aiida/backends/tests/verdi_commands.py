# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################


import mock

from aiida.backends.testbase import AiidaTestCase
from aiida.utils.capturing import Capturing
from aiida.common.datastructures import calc_states

# Common computer information
computer_common_info = ["localhost",
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

# Computer #1
computer_name_1 = "torquessh1"
computer_setup_input_1 = [computer_name_1] + computer_common_info

# Computer #2
computer_name_2 = "torquessh2"
computer_setup_input_2 = [computer_name_2] + computer_common_info


# Common code information
code_common_info_1 = ["simple script",
                      "False",
                      "simpleplugins.templatereplacer",]
code_common_info_2 = ["/usr/local/bin/doubler.sh",
                      EOFError,
                      EOFError,
                      ]

# Code #1
code_name_1 = "doubler_1"
code_setup_input_1 = ([code_name_1] + code_common_info_1 +
                      [computer_name_1] + code_common_info_2)
# Code #2
code_name_2 = "doubler_2"
code_setup_input_2 = ([code_name_2] + code_common_info_1 +
                      [computer_name_2] + code_common_info_2)


class TestVerdiCalculationCommands(AiidaTestCase):

    @classmethod
    def setUpClass(cls):
        """
        Create some calculations with various states
        """
        super(TestVerdiCalculationCommands, cls).setUpClass()

        from aiida.orm import JobCalculation

        # Create some calculation
        calc1 = JobCalculation(computer=cls.computer,
                               resources={
                                  'num_machines': 1,
                                  'num_mpiprocs_per_machine': 1}).store()
        calc1._set_state(calc_states.TOSUBMIT)
        calc2 = JobCalculation(computer=cls.computer.name,
                               resources={
                                   'num_machines': 1,
                                   'num_mpiprocs_per_machine': 1}).store()
        calc2._set_state(calc_states.COMPUTED)
        calc3 = JobCalculation(computer=cls.computer.id,
                               resources={
                                   'num_machines': 1,
                                   'num_mpiprocs_per_machine': 1}).store()
        calc3._set_state(calc_states.FINISHED)

    def test_calculation_list(self):
        """
        Do some calculation listing to ensure that verdi calculation list
        works and gives at least to some extent the expected results.
        """
        from aiida.cmdline.commands.calculation import Calculation
        calc_cmd = Calculation()

        with Capturing() as output:
            calc_cmd.calculation_list()

        out_str = ''.join(output)
        self.assertTrue(calc_states.TOSUBMIT in out_str,
                        "The TOSUBMIT calculations should be part fo the "
                        "simple calculation list.")
        self.assertTrue(calc_states.COMPUTED in out_str,
                        "The COMPUTED calculations should be part fo the "
                        "simple calculation list.")
        self.assertFalse(calc_states.FINISHED in out_str,
                         "The FINISHED calculations should not be part fo the "
                         "simple calculation list.")

        with Capturing() as output:
            calc_cmd.calculation_list(*['-a'])

        out_str = ''.join(output)
        self.assertTrue(calc_states.FINISHED in out_str,
                        "The FINISHED calculations should be part fo the "
                        "simple calculation list.")


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
            with Capturing():
                cmd_comp.computer_setup()

        # Setup a code for computer #1
        from aiida.cmdline.commands.code import Code
        code_cmd = Code()
        with mock.patch('__builtin__.raw_input',
                        side_effect=code_setup_input_1):
            with Capturing():
                code_cmd.code_setup()

        # Setup computer #2
        with mock.patch('__builtin__.raw_input',
                        side_effect=computer_setup_input_2):
            with Capturing():
                cmd_comp.computer_setup()

        # Setup a code for computer #2
        with mock.patch('__builtin__.raw_input',
                        side_effect=code_setup_input_2):
            with Capturing():
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
