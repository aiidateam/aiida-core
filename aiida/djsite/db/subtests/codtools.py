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
        self.assertEquals(nodes[0][0], 'cif')
        self.assertEquals(isinstance(nodes[0][1], CifData), True)
