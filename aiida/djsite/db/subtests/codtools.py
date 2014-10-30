# -*- coding: utf-8 -*-
"""
Tests for the codtools input plugins.
"""
import os

from aiida.djsite.db.testbase import AiidaTestCase
from aiida.common.folders import SandboxFolder
from aiida.orm.calculation.codtools import CodtoolsCalculation
import aiida

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.2.1"

class TestCodtools(AiidaTestCase):

    def test_inputs_1(self):
        import tempfile
        from aiida.orm.data.cif import CifData
        from aiida.orm.data.parameter import ParameterData

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

        c = CodtoolsCalculation()
        c.use_cif(cif)
        c.use_parameters(p)

        f = SandboxFolder()
        calc = c._prepare_for_submission(f, c.get_inputdata_dict())

        self.assertEquals(calc['cmdline_params'],
                          ['--extra-tag-list cod.lst',
                           '--extra-tag-list tcod.lst',
                           '-s', '--reformat-spacegroup',
                           '--start-data-block-number 1234567'])

        self.assertEquals(calc['stderr_name'], 'aiida.err')

        with open("{}/{}".format(f.abspath,calc['stdin_name'])) as i:
            self.assertEquals(i.read(), file_content)
