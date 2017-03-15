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
Tests for the codtools input plugins.
"""
import tempfile
import unittest
from aiida.common.folders import SandboxFolder
from aiida.orm.data.cif import CifData
from aiida.orm.data.parameter import ParameterData
from aiida.common.exceptions import FeatureNotAvailable
from aiida.orm.calculation.job.codtools.cifcellcontents import CifcellcontentsCalculation
from aiida.orm.calculation.job.codtools.cifcodcheck import CifcodcheckCalculation
from aiida.orm.calculation.job.codtools.ciffilter import CiffilterCalculation
from aiida.parsers.plugins.codtools.cifcellcontents import CifcellcontentsParser
from aiida.parsers.plugins.codtools.cifcodcheck import CifcodcheckParser
from aiida.parsers.plugins.codtools.ciffilter import CiffilterParser
from aiida.backends.testbase import AiidaTestCase



class TestCodtools(AiidaTestCase):
    from aiida.orm.data.cif import has_pycifrw

    @unittest.skipIf(not has_pycifrw(), "Unable to import PyCifRW")
    def test_1(self):
        stdout_messages = ["data_test _cell_length_a 10(1)"]
        stderr_messages = []

        f = SandboxFolder()
        stdout_file = "{}/{}".format(f.abspath, "aiida.out")
        stderr_file = "{}/{}".format(f.abspath, "aiida.err")

        with open(stdout_file, 'w') as of:
            of.write("\n".join(stdout_messages))
            of.flush()

        with open(stderr_file, 'w') as ef:
            ef.write("\n".join(stderr_messages))
            ef.flush()

        parser = CiffilterParser(CiffilterCalculation())
        success, nodes = parser._get_output_nodes(stdout_file, stderr_file)

        self.assertEquals(success, True)
        self.assertEquals(len(nodes), 2)
        self.assertEquals(nodes[0][0], 'cif')
        self.assertEquals(isinstance(nodes[0][1], CifData), True)
        self.assertEquals(nodes[0][1].generate_md5(),
                          'b5bb739a254514961a157503daf715eb')
        self.assertEquals(nodes[1][0], 'messages')
        self.assertEquals(len(nodes[1][1].get_dict()['output_messages']), 0)

    @unittest.skipIf(not has_pycifrw(), "Unable to import PyCifRW")
    def test_2(self):
        stdout_messages = ["data_test _cell_length_a 10(1)"]
        stderr_messages = ["first line", "last line"]

        f = SandboxFolder()
        stdout_file = "{}/{}".format(f.abspath, "aiida.out")
        stderr_file = "{}/{}".format(f.abspath, "aiida.err")

        with open(stdout_file, 'w') as of:
            of.write("\n".join(stdout_messages))
            of.flush()

        with open(stderr_file, 'w') as ef:
            ef.write("\n".join(stderr_messages))
            ef.flush()

        parser = CiffilterParser(CiffilterCalculation())
        success, nodes = parser._get_output_nodes(stdout_file, stderr_file)

        self.assertEquals(success, True)
        self.assertEquals(len(nodes), 2)
        self.assertEquals(nodes[0][0], 'cif')
        self.assertEquals(isinstance(nodes[0][1], CifData), True)
        self.assertEquals(nodes[0][1].generate_md5(),
                          'b5bb739a254514961a157503daf715eb')
        self.assertEquals(nodes[1][0], 'messages')
        self.assertEquals(isinstance(nodes[1][1], ParameterData), True)

    def test_3(self):
        stdout_messages = ["NOTE, symmetry operator '-x,-y,-z' is missing"]
        stderr_messages = ["ERROR, tag '_refine_ls_shift/esd_max' value '0.25' is > 0.2."]

        f = SandboxFolder()
        stdout_file = "{}/{}".format(f.abspath, "aiida.out")
        stderr_file = "{}/{}".format(f.abspath, "aiida.err")

        with open(stdout_file, 'w') as of:
            of.write("aiida.in: OK\n")
            of.write("\n".join(stdout_messages))
            of.flush()

        with open(stderr_file, 'w') as ef:
            ef.write("\n".join(stderr_messages))
            ef.flush()

        parser = CifcodcheckParser(CifcodcheckCalculation())
        success, nodes = parser._get_output_nodes(stdout_file, stderr_file)

        self.assertEquals(success, True)
        self.assertEquals(len(nodes), 1)
        self.assertEquals(nodes[0][0], 'messages')
        self.assertEquals(isinstance(nodes[0][1], ParameterData), True)
        self.assertEquals(nodes[0][1].get_dict()['output_messages'],
                          stdout_messages + stderr_messages)

    def test_4(self):
        from aiida.parsers.plugins.codtools.cifcellcontents import CifcellcontentsParser

        stdout = '''4000000	C26 H26 Fe
4000001	C24 H17 F5 Fe
4000002	C24 H17 F5 Fe
4000003	C24 H17 F5 Fe
4000004	C22 H8 F10 Fe
4000005	Sn3 Ti2
4000006	C10 H9 Cl0.603 N O1.397 S6
4000007	C30 H46 O3 S
4000008	C2 H10 F Mn N2 O9 V3
4000009	C4 H18 Mn N4 O12 V4
'''
        stderr = ''

        f = SandboxFolder()
        stdout_file = "{}/{}".format(f.abspath, "aiida.out")
        stderr_file = "{}/{}".format(f.abspath, "aiida.err")

        with open(stdout_file, 'w') as of:
            of.write(stdout)
            of.flush()
        with open(stderr_file, 'w') as ef:
            ef.write(stderr)
            ef.flush()

        parser = CifcellcontentsParser(CifcellcontentsCalculation())
        _, output_nodes = parser._get_output_nodes(stdout_file, stderr_file)
        self.assertEquals(output_nodes[0][1].get_dict(), {
            'formulae': {
                '4000003': 'C24 H17 F5 Fe',
                '4000002': 'C24 H17 F5 Fe',
                '4000001': 'C24 H17 F5 Fe',
                '4000000': 'C26 H26 Fe',
                '4000007': 'C30 H46 O3 S',
                '4000006': 'C10 H9 Cl0.603 N O1.397 S6',
                '4000005': 'Sn3 Ti2',
                '4000004': 'C22 H8 F10 Fe',
                '4000009': 'C4 H18 Mn N4 O12 V4',
                '4000008': 'C2 H10 F Mn N2 O9 V3'}})

    def test_5(self):
        from aiida.parsers.plugins.codtools.cifcoddeposit import CifcoddepositParser

        content = \
            """<!DOCTYPE html
                PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
                 "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
            <html xmlns="http://www.w3.org/1999/xhtml" lang="en-US" xml:lang="en-US">
            <head>
            <title>COD data deposition ERROR</title>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
            </head>
            <body>
            <p class="ERROR" style="color: red;font-size:large">cif-deposit.pl: password 'password' value from the upload form contains unallowed characters (not in '(.{4,64})')<br />
            </p>

            </body>
            </html>
            """
        status, message = CifcoddepositParser._deposit_result(content)
        self.assertEquals(status, 'INPUTERROR')
        self.assertEquals(message, 'password \'password\' value from the '
                                   'upload form contains unallowed '
                                   'characters (not in \'(.{4,64})\')<br />')

        content = \
            """cif-deposit.pl: The following structures seem to be already in COD:
            Structure from 1000000.cif (_chemical_formula_sum 'C5 H17 Al N2 O8 P2') is found in COD entry 2000041
            Will not deposit the structure(s) once more.
            """

        status, message = CifcoddepositParser._deposit_result(content)
        self.assertEquals(status, 'DUPLICATE')
        self.assertEquals(message, 'The following structures seem to be '
                                   'already in COD')

        content = \
            """cif-deposit.pl: upload from variable 'username' value '' contains unallowed characters (not in '[a-zA-Z0-9 ,.-'_()\\x{0080}-\\x{7FFFFFFF}]+')"""

        status, message = CifcoddepositParser._deposit_result(content)
        self.assertEquals(status, 'INPUTERROR')
        self.assertEquals(message, 'upload from variable \'username\' '
                                   'value \'\' contains unallowed characters '
                                   '(not in \'[a-zA-Z0-9 ,.-\'_()\\x{0080}-\\x{7FFFFFFF}]+\')')

        content = \
            """cif-deposit.pl: cif_cod_check: - data_4000000: _publ_section_title is undefined
cif_cod_check: - data_4000000: neither _journal_page_first nor _journal_article_reference is defined
cif_cod_check: - data_4000001: _publ_section_title is undefined"""

        status, message = CifcoddepositParser._deposit_result(content)
        self.assertEquals(status, 'INPUTERROR')
        self.assertEquals(message, 'cif_cod_check: - data_4000000: '
                                   '_publ_section_title is undefined\n'
                                   'cif_cod_check: - data_4000000: '
                                   'neither _journal_page_first nor '
                                   '_journal_article_reference is defined\n'
                                   'cif_cod_check: - data_4000001: '
                                   '_publ_section_title is undefined')

        content = \
            """cif-deposit.pl: structures 4300539 were successfully deposited into COD"""

        status, message = CifcoddepositParser._deposit_result(content)
        self.assertEquals(status, 'SUCCESS')
        self.assertEquals(message, 'structures 4300539 were successfully '
                                   'deposited into COD')

    def test_perl_error_detection(self):
        from aiida.parsers.plugins.codtools.cifcellcontents import CifcellcontentsParser
        from aiida.common.exceptions import PluginInternalError

        stdout = "4000000	C26 H26 Fe\n"

        stderr_1 = "Can't locate CIFSymmetryGenerator.pm in @INC (@INC contains: .) at cif_molecule line 61."
        stderr_2 = "BEGIN failed--compilation aborted at cif_molecule line 61."

        f = SandboxFolder()

        stdout_file = "{}/{}".format(f.abspath, "aiida.out")
        stderr_1_file = "{}/{}".format(f.abspath, "aiida_1.err")
        stderr_2_file = "{}/{}".format(f.abspath, "aiida_2.err")

        with open(stdout_file, 'w') as of:
            of.write(stdout)
            of.flush()
        with open(stderr_1_file, 'w') as ef:
            ef.write(stderr_1)
            ef.flush()
        with open(stderr_2_file, 'w') as ef:
            ef.write(stderr_2)
            ef.flush()

        parser = CifcellcontentsParser(CifcellcontentsCalculation())
        with self.assertRaises(PluginInternalError):
            parser._get_output_nodes(stdout_file, stderr_1_file)
        with self.assertRaises(PluginInternalError):
            parser._get_output_nodes(stdout_file, stderr_2_file)

    def test_cmdline_generation(self):
        from aiida.orm.calculation.job.codtools import commandline_params_from_dict

        dictionary = {
            'start-data-block-number': '1234567',
            'extra-tag-list': ['cod.lst', 'tcod.lst'],
            'reformat-spacegroup': True,
            's': True,
        }
        cmdline = commandline_params_from_dict(dictionary)

        self.assertEquals(cmdline,
                          ['--extra-tag-list', 'cod.lst',
                           '--extra-tag-list', 'tcod.lst',
                           '-s', '--reformat-spacegroup',
                           '--start-data-block-number', '1234567'])

    def test_resource_validation(self):
        calc = CiffilterCalculation()
        calc.use_cif(CifData())

        for key in ['num_machines', 'num_mpiprocs_per_machine',
                    'tot_num_mpiprocs']:
            with self.assertRaises(FeatureNotAvailable):
                calc.set_resources({key: 2})

            # Inner modification of resource parameters:
            calc._set_attr('jobresource_params', {key: 2})
            with self.assertRaises(FeatureNotAvailable):
                calc._validate_resources(**calc.get_resources())

            calc.set_resources({key: 1})

    @unittest.skipIf(not has_pycifrw(), "Unable to import PyCifRW")
    def test_status_assertion(self):
        nonempty = tempfile.NamedTemporaryFile()
        nonempty.write('data_test _tag value')
        nonempty.flush()

        empty = tempfile.NamedTemporaryFile()
        empty.write('')
        empty.flush()

        calc = CiffilterCalculation()
        parser = CiffilterParser(calc)

        status, nodes = parser._get_output_nodes(nonempty.name, empty.name)
        self.assertEquals(status, True)

        status, nodes = parser._get_output_nodes(empty.name, nonempty.name)
        self.assertEquals(status, False)

        calc = CifcellcontentsCalculation()
        parser = CifcellcontentsParser(calc)

        status, nodes = parser._get_output_nodes(nonempty.name, empty.name)
        self.assertEquals(status, True)

        status, nodes = parser._get_output_nodes(empty.name, nonempty.name)
        self.assertEquals(status, False)
