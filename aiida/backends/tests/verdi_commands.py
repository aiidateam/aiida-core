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
import unittest

from aiida.backends.testbase import AiidaTestCase
from contextlib import contextmanager
from StringIO import StringIO
import sys
from aiida.common import utils
from aiida.utils.capturing import Capturing

@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


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

    def tearDown(self):
        utils.raw_input = None

    def test_code_list(self):
        # from aiida.orm.code import Code
        # # Create a code
        # code1 = Code()
        # code1.set_remote_computer_exec((self.computer, '/bin/true'))
        # code1.label = 'test_code1'
        # code1.store()

        from aiida.cmdline.commands.code import Code
        codeCmd = Code()
        # codeCmd.code_setup()
        code_setup_input = ["doubler",
                       "simple script that doubles a number "
                       "and sleeps for a given number of seconds",
                       "False",
                       "simpleplugins.templatereplacer",
                       "torquessh",
                       "/usr/local/bin/doubler.sh",
                       "",
                       ""]

        import mock
        with mock.patch('__builtin__.raw_input', side_effect=code_setup_input):
            codeCmd.code_setup()

        original_raw_input = __builtins__.raw_input
        __builtins__.raw_input = lambda _:  code_setup_input[ac.array_counter()]
        codeCmd.code_setup()
        __builtins__.raw_input = original_raw_input


        ac = utils.ArrayCounter()
        utils.raw_input = lambda _: code_setup_input[ac.array_counter()]
        # with Capturing():
        bk_vars = codeCmd.code_setup()



        # codeCmd.code_list()


