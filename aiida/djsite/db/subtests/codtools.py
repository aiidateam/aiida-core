# -*- coding: utf-8 -*-
"""
Tests for the codtools input plugins.
"""
import os

from aiida.djsite.db.testbase import AiidaTestCase
from aiida.common.folders import SandboxFolder
from aiida.orm.calculation.codtools import CodtoolsCalculation
from aiida.parsers.plugins.codtools import CodtoolsParser
import aiida

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.2.1"

class TestCodtools(AiidaTestCase):

    def test_1(self):
        import tempfile
        from aiida.orm.data.cif import CifData
        from aiida.orm.data.folder import FolderData
        from aiida.orm.data.parameter import ParameterData
        from aiida.common.exceptions import InputValidationError
        from aiida.common.datastructures import calc_states

        file_content = "data_test _cell_length_a 10(1)"
        with tempfile.NamedTemporaryFile() as f:
            f.write(file_content)
            f.flush()
            cif = CifData(file=f.name)

        p = ParameterData(dict={
                    'start-data-block-number': '1234567',
                    'extra-tag-list': [ 'cod.lst', 'tcod.lst' ],
                    'reformat-spacegroup': True,
                    's': True,
            })

        c = CodtoolsCalculation(computer=self.computer,
                                resources={
                                    'num_machines': 1,
                                    'num_mpiprocs_per_machine': 1}
                                )
        f = SandboxFolder()

        with self.assertRaises(InputValidationError):
            c._prepare_for_submission(f, c.get_inputdata_dict())

        with self.assertRaises(TypeError):
            c.use_cif(None)

        c.use_cif(cif)

        calc = c._prepare_for_submission(f, c.get_inputdata_dict())
        self.assertEquals(calc['cmdline_params'], [])

        with self.assertRaises(TypeError):
            c.use_parameters(None)

        c.use_parameters(p)

        calc = c._prepare_for_submission(f, c.get_inputdata_dict())

        self.assertEquals(calc['cmdline_params'],
                          ['--extra-tag-list cod.lst',
                           '--extra-tag-list tcod.lst',
                           '-s', '--reformat-spacegroup',
                           '--start-data-block-number 1234567'])

        self.assertEquals(calc['stdout_name'], c._DEFAULT_OUTPUT_FILE)
        self.assertEquals(calc['stderr_name'], c._DEFAULT_ERROR_FILE)

        with open("{}/{}".format(f.abspath,calc['stdin_name'])) as i:
            self.assertEquals(i.read(), file_content)

        c.store()
        c._set_state(calc_states.PARSING)

        fd = FolderData()
        fd.store()

        fd._add_link_from(c, label="retrieved")

        with open("{}/{}".format(fd._get_folder_pathsubfolder.abspath,
                                 calc['stdout_name']), 'w') as o:
            o.write(file_content)
            o.flush()

        parser = CodtoolsParser(c)
        success, nodes = parser.parse_from_calc()

        self.assertEquals(success, True)
        self.assertEquals(len(nodes), 1)
        self.assertEquals(nodes[0][0], 'cif')
        self.assertEquals(isinstance(nodes[0][1], CifData), True)
        self.assertEquals(nodes[0][1].generate_md5(),
                          'b5bb739a254514961a157503daf715eb')

    def test_2(self):
        import tempfile
        from aiida.orm.data.cif import CifData
        from aiida.orm.data.folder import FolderData
        from aiida.orm.data.parameter import ParameterData
        from aiida.common.exceptions import InputValidationError
        from aiida.common.datastructures import calc_states

        file_content = "data_test _cell_length_a 10(1)"
        errors = "first line\nlast line"
        with tempfile.NamedTemporaryFile() as f:
            f.write(file_content)
            f.flush()
            cif = CifData(file=f.name)
        c = CodtoolsCalculation(computer=self.computer,
                                resources={
                                    'num_machines': 1,
                                    'num_mpiprocs_per_machine': 1}
                                )
        f = SandboxFolder()

        c.use_cif(cif)

        calc = c._prepare_for_submission(f, c.get_inputdata_dict())
        c.store()
        c._set_state(calc_states.PARSING)

        fd = FolderData()
        fd.store()

        fd._add_link_from(c, label="retrieved")

        with open("{}/{}".format(fd._get_folder_pathsubfolder.abspath,
                                 calc['stdout_name']), 'w') as o:
            o.write(file_content)
            o.flush()

        with open("{}/{}".format(fd._get_folder_pathsubfolder.abspath,
                                 calc['stderr_name']), 'w') as o:
            o.write(errors)
            o.flush()

        parser = CodtoolsParser(c)
        success, nodes = parser.parse_from_calc()

        self.assertEquals(success, True)
        self.assertEquals(len(nodes), 2)
        self.assertEquals(nodes[0][0], 'cif')
        self.assertEquals(isinstance(nodes[0][1], CifData), True)
        self.assertEquals(nodes[0][1].generate_md5(),
                          'b5bb739a254514961a157503daf715eb')
        self.assertEquals(nodes[1][0], 'messages')
        self.assertEquals(isinstance(nodes[1][1], ParameterData), True)

    def test_3(self):
        import tempfile
        from aiida.parsers.plugins.codtools.cifcodcheck import CifcodcheckParser
        from aiida.orm.data.cif import CifData
        from aiida.orm.data.folder import FolderData
        from aiida.orm.data.parameter import ParameterData
        from aiida.common.exceptions import InputValidationError
        from aiida.common.datastructures import calc_states

        file_content = "data_test _cell_length_a 10(1)"
        errors = "first line\nlast line"
        with tempfile.NamedTemporaryFile() as f:
            f.write(file_content)
            f.flush()
            cif = CifData(file=f.name)
        c = CodtoolsCalculation(computer=self.computer,
                                resources={
                                    'num_machines': 1,
                                    'num_mpiprocs_per_machine': 1}
                                )
        f = SandboxFolder()

        c.use_cif(cif)

        calc = c._prepare_for_submission(f, c.get_inputdata_dict())
        c.store()
        c._set_state(calc_states.PARSING)

        fd = FolderData()
        fd.store()

        fd._add_link_from(c, label="retrieved")

        stdout_messages = [ "NOTE, symmetry operator '-x,-y,-z' is missing" ]
        with open("{}/{}".format(fd._get_folder_pathsubfolder.abspath,
                                 calc['stdout_name']), 'w') as o:
            o.write("aiida.in: OK\n")
            o.write("\n".join(stdout_messages))
            o.flush()

        stderr_messages = [ "ERROR, tag '_refine_ls_shift/esd_max' value '0.25' is > 0.2." ]
        with open("{}/{}".format(fd._get_folder_pathsubfolder.abspath,
                                 calc['stderr_name']), 'w') as o:
            o.write("\n".join(stderr_messages))
            o.flush()

        parser = CifcodcheckParser(c)
        success, nodes = parser.parse_from_calc()

        self.assertEquals(success, True)
        self.assertEquals(len(nodes), 1)
        self.assertEquals(nodes[0][0], 'messages')
        self.assertEquals(isinstance(nodes[0][1], ParameterData), True)
        self.assertEquals(nodes[0][1].get_dict()['output_messages'],
                          stdout_messages + stderr_messages)
