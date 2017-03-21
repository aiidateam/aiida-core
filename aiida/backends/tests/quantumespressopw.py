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

import aiida
from aiida.common.exceptions import InputValidationError
from aiida.common.folders import SandboxFolder
from aiida.orm import CalculationFactory, DataFactory
from aiida.backends.testbase import AiidaTestCase
from aiida.orm import Code

QECalc = CalculationFactory('quantumespresso.pw')
StructureData = DataFactory('structure')
ParameterData = DataFactory('parameter')
UpfData = DataFactory('upf')
KpointsData = DataFactory('array.kpoints')

class TestQEPWInputGeneration(AiidaTestCase):
    """
    Test if the input is correctly generated
    """
    @classmethod
    def setUpClass(cls):
        super(TestQEPWInputGeneration, cls).setUpClass()
        cls.calc_params = {
            'computer': cls.computer,
            'resources': {
                'num_machines': 1,
                'num_mpiprocs_per_machine': 1
            }
        }

        cls.code = Code()
        cls.code.set_remote_computer_exec((cls.computer, '/x.x'))
        cls.code.store()

    def test_inputs(self):
        import logging

        cell = ((2., 0., 0.), (0., 2., 0.), (0., 0., 2.))

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
        s.append_atom(position=(0., 0., 0.), symbols=['Ba'])
        s.store()

        p = ParameterData(dict=input_params).store()

        k = KpointsData()
        k.set_kpoints_mesh([4, 4, 4])
        k.store()

        pseudo_dir = os.path.join(os.path.split(aiida.__file__)[0],
                                  os.pardir, 'examples',
                                  'testdata', 'qepseudos')

        raw_pseudos = [
            ("Ba.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF", 'Ba'),
            ("Ti.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF", 'Ti'),
            ("O.pbesol-n-rrkjus_psl.0.1-tested-pslib030.UPF", 'O'),
        ]

        pseudos = {}
        # suppress debug messages
        logging.disable(logging.ERROR)
        for fname, elem in raw_pseudos:
            absname = os.path.realpath(os.path.join(pseudo_dir, fname))
            pseudo, _ = UpfData.get_or_create(
                absname, use_first=True)
            pseudos[elem] = pseudo
        # Reset logging level
        logging.disable(logging.NOTSET)

        inputdict = c.get_inputs_dict()
        inputdict.pop('code', None)

        with SandboxFolder() as f:
            # I use the same SandboxFolder more than once because nothing
            # should be written for these failing tests

            # Missing required input nodes
            with self.assertRaises(InputValidationError):
                c._prepare_for_submission(f, inputdict)
            c.use_parameters(p)
            inputdict = c.get_inputs_dict()
            with self.assertRaises(InputValidationError):
                c._prepare_for_submission(f, inputdict)
            c.use_structure(s)
            inputdict = c.get_inputs_dict()
            with self.assertRaises(InputValidationError):
                c._prepare_for_submission(f, inputdict)
            c.use_kpoints(k)
            inputdict = c.get_inputs_dict()
            with self.assertRaises(InputValidationError):
                c._prepare_for_submission(f, inputdict)
            c.use_pseudo(pseudos['Ba'], 'Ba')

            inputdict = c.get_inputs_dict()
            with self.assertRaises(InputValidationError):
                c._prepare_for_submission(f, inputdict)
            c.use_code(self.code)
            inputdict = c.get_inputs_dict()
            c._prepare_for_submission(f, inputdict)

            # TODO: split this test in more than one
            c.use_pseudo(pseudos['Ti'], 'Ti')
            inputdict = c.get_inputs_dict()
            # Too many pseudos
            with self.assertRaises(InputValidationError):
                c._prepare_for_submission(f, inputdict)

    def test_inputs_with_multiple_species(self):
        """
        Test the creation of the input file when there are two species
        associated to the same element, with different starting_magnetization
        values.
        """
        import logging

        s = StructureData(cell=[
            [2.871, 0., 0.],
            [0., 2.871, 0.],
            [0., 0., 2.871]])

        ## I leave this as a reference, but I use instead the
        ## append_atom method
        # from aiida.orm.data.structure import Kind, Site
        # s.append_kind(Kind(symbols='Ba', name='Ba1'))
        # s.append_kind(Kind(symbols='Ba', name='Ba2'))
        # s.append_site(Site(kind_name='Ba1', position=[0.,0.,0.]))
        # s.append_site(Site(kind_name='Ba2', position=[1.4355,1.4355,1.4355]))
        s.append_atom(symbols='Ba', position=[0., 0., 0.], name='Ba1')
        s.append_atom(symbols='Ba', position=[1.4355, 1.4355, 1.4355],
                      name='Ba2')

        input_params = {
            'CONTROL': {
                'calculation': 'vc-relax',
                'restart_mode': 'from_scratch',
                'wf_collect': True,
            },
            'SYSTEM': {
                'ecutwfc': 47.,
                'ecutrho': 568.,
                'nspin': 2,
                'starting_magnetization': {
                    'Ba1': 0.5,
                    'Ba2': -0.5
                    },
            },
            'ELECTRONS': {
                'conv_thr': 1.e-10,
            },
        }

        c = QECalc(**self.calc_params).store()
        c.use_code(self.code)

        p = ParameterData(dict=input_params).store()

        k = KpointsData()
        k.set_kpoints_mesh([4, 4, 4])
        k.store()

        pseudo_dir = os.path.join(os.path.split(aiida.__file__)[0],
                                  os.pardir, 'examples',
                                  'testdata', 'qepseudos')

        raw_pseudos = [
            ("Ba.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF", 'Ba'),
        ]

        pseudos = {}
        # suppress debug messages
        logging.disable(logging.ERROR)
        for fname, elem in raw_pseudos:
            absname = os.path.realpath(os.path.join(pseudo_dir, fname))
            pseudo, _ = UpfData.get_or_create(
                absname, use_first=True)
            pseudos[elem] = pseudo
        # Reset logging level
        logging.disable(logging.NOTSET)

        c.use_parameters(p)
        c.use_structure(s)
        c.use_kpoints(k)

        with SandboxFolder() as f:
            # I use the same SandboxFolder more than once because nothing
            # should be written for these failing tests

            # Same pseudo for two species
            c.use_pseudo(pseudos['Ba'], ['Ba1', 'Ba2'])
            inputdict = c.get_inputs_dict()
            c._prepare_for_submission(f, inputdict)

            with open(os.path.join(f.abspath, 'aiida.in')) as infile:
                lines = [_.strip() for _ in infile.readlines()]

            find_kind_ba1 = any('Ba1' in l and
                                'Ba.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF' in l
                                for l in lines)
            self.assertTrue(find_kind_ba1, "Unable to find the species line "
                                           "for Ba1")
            find_kind_ba2 = any('Ba2' in l and
                                'Ba.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF' in l
                                for l in lines)
            self.assertTrue(find_kind_ba2, "Unable to find the species line "
                                           "for Ba2")

            found1 = False
            found2 = False
            for l in lines:
                if 'starting_magnetization(1)' in l:
                    if found1:
                        raise ValueError(
                            "starting_magnetization(1) found multiple times")
                    found1 = True
                    self.assertAlmostEquals(
                        float(l.split('=')[1].replace('d', 'e')), 0.5)
                if 'starting_magnetization(2)' in l:
                    if found2:
                        raise ValueError(
                            "starting_magnetization(2) found multiple times")
                    found2 = True
                    self.assertAlmostEquals(
                        float(l.split('=')[1].replace('d', 'e')), -0.5)
