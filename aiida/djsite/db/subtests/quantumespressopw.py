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

QECalc = CalculationFactory('quantumespresso.pw')
StructureData = DataFactory('structure')
ParameterData = DataFactory('parameter')
UpfData = DataFactory('upf')

class QETestCase(AiidaTestCase):

    @classmethod
    def setUpClass(cls):
        super(QETestCase,cls).setUpClass()
        cls.calc_params = {
            'computer': cls.computer,
            'resources': {
                'num_machines': 1,
                'num_cpus_per_machine': 1}
            }

class TestQEPWInputGeneration(QETestCase):
    """
    Test if the input is correctly generated
    """
    def test_inputs(self):        
        import logging
        cell = ((2.,0.,0.),(0.,2.,0.),(0.,0.,2.))

        k_points = {
            'type': 'automatic',
            'points': [4, 4, 4, 0, 0, 0],
            }
        
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
        
        k = ParameterData(dict=k_points).store()
        
        pseudo_dir = os.path.join(aiida.__file__, os.pardir,os.pardir,
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

        
        with SandboxFolder() as f:
            # I use the same SandboxFolder more than once because nothing
            # should be written for these failing tests

            # Missing required input nodes
            with self.assertRaises(InputValidationError):
                c._prepare_for_submission(f)
            c.use_parameters(p)
            with self.assertRaises(InputValidationError):
                c._prepare_for_submission(f)
            c.use_structure(s)
            with self.assertRaises(InputValidationError):
                c._prepare_for_submission(f)
            c.use_kpoints(k)            
            with self.assertRaises(InputValidationError):
                c._prepare_for_submission(f)
            c.use_pseudo(pseudos['Ba'], 'Ba')
            c._prepare_for_submission(f)

            # TODO: split this test in more than one
            c.use_pseudo(pseudos['Ti'], 'Ti')
            # Too many pseudos
            with self.assertRaises(InputValidationError):
                c._prepare_for_submission(f)
            
