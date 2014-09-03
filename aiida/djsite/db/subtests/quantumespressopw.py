# -*- coding: utf-8 -*-
"""
Tests for the pw input plugin.

TODO: to test:
- association species->pseudos
- two pseudos with the same filename
- IFPOS (FIXED_COORDS in SETTINGS)
- automatic namelists
- manually specified namelists
- empty namelists
- content for non-existent namelists specified
"""
import os

from aiida.djsite.db.testbase import AiidaTestCase
from aiida.orm import CalculationFactory
from aiida.orm import DataFactory
from aiida.common.folders import SandboxFolder
from aiida.common.exceptions import InputValidationError
import aiida

__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = u"Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

QECalc = CalculationFactory('quantumespresso.pw')
StructureData = DataFactory('structure')
ParameterData = DataFactory('parameter')
UpfData = DataFactory('upf')
KpointsData = DataFactory('array.kpoints')

class QETestCase(AiidaTestCase):

    @classmethod
    def setUpClass(cls):
        super(QETestCase,cls).setUpClass()
        cls.calc_params = {
            'computer': cls.computer,
            'resources': {
                'num_machines': 1,
                'num_mpiprocs_per_machine': 1}
            }

class TestQEPWInputGeneration(QETestCase):
    """
    Test if the input is correctly generated
    """
    def test_inputs(self):        
        import logging
        cell = ((2.,0.,0.),(0.,2.,0.),(0.,0.,2.))

        input_params = {
            'CONTROL': {
                'calculation': 'vc-relax',
                'restart_mode': 'from_scratch',
                'wf_collect': True,
                },
            'SYSTEM': {
                'ecutwfc': 47.,
                'ecutrho': 568.,
                },
            'ELECTRONS': {
                'conv_thr': 1.e-10,
                },
            }
        
        c = QECalc(**self.calc_params).store()
        
        s = StructureData(cell=cell)
        s.append_atom(position=(0.,0.,0.),symbols=['Ba'])
        s.store()
        
        p = ParameterData(dict=input_params).store()
        
        k = KpointsData()
        k.set_kpoints_mesh([4,4,4])
        k.store()
        
        pseudo_dir = os.path.join(os.path.split(aiida.__file__)[0],
                                  os.pardir,'examples',
                                  'testdata','qepseudos')
        
        raw_pseudos = [
            ("Ba.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF", 'Ba'),
            ("Ti.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF", 'Ti'),
            ("O.pbesol-n-rrkjus_psl.0.1-tested-pslib030.UPF", 'O'),
            ]

        pseudos = {}
        # suppress debug messages
        logging.disable(logging.ERROR)
        for fname, elem in raw_pseudos:
            absname = os.path.realpath(os.path.join(pseudo_dir,fname))
            pseudo, _ = UpfData.get_or_create(
                absname, use_first=True)
            pseudos[elem] = pseudo
        # Reset logging level
        logging.disable(logging.NOTSET)

        inputdict = c.get_inputdata_dict()
        
        with SandboxFolder() as f:
            # I use the same SandboxFolder more than once because nothing
            # should be written for these failing tests

            # Missing required input nodes
            with self.assertRaises(InputValidationError):
                c._prepare_for_submission(f, inputdict)
            c.use_parameters(p)
            inputdict = c.get_inputdata_dict()
            with self.assertRaises(InputValidationError):
                c._prepare_for_submission(f, inputdict)
            c.use_structure(s)
            inputdict = c.get_inputdata_dict()
            with self.assertRaises(InputValidationError):
                c._prepare_for_submission(f, inputdict)
            c.use_kpoints(k)
            inputdict = c.get_inputdata_dict()
            with self.assertRaises(InputValidationError):
                c._prepare_for_submission(f, inputdict)
            c.use_pseudo(pseudos['Ba'], 'Ba')
            inputdict = c.get_inputdata_dict()
            c._prepare_for_submission(f, inputdict)

            # TODO: split this test in more than one
            c.use_pseudo(pseudos['Ti'], 'Ti')
            inputdict = c.get_inputdata_dict()
            # Too many pseudos
            with self.assertRaises(InputValidationError):
                c._prepare_for_submission(f, inputdict)
            
