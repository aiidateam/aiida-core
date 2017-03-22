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
Tests for ``aiida.tools.codespecific.quantumespresso.pwinputparser``.

Since the AiiDA-specific methods of PwInputFile generates (unstored) Node
objects, this  has to be run with a temporary database.

The directory, ``./pwtestjobs/``, contains small QE jobs that are used to test
the parsing and units conversion. The test jobs should all contain the same
structure, input parameters, ect., but the units of the input files differ,
in order to test the unit and coordinate transformations of the PwInputTools
methods. The only thing that should vary between some of them is the type of
k-points (manual, gamma, and automatic). For this reason, the testing of
get_kpointsdata is split up into three different test methods.
"""
import os

import numpy as np

from aiida.tools.codespecific.quantumespresso import pwinputparser
from aiida.orm.data.structure import StructureData
from aiida.backends.testbase import AiidaTestCase


# File names: a_celldm(1)_kpoints_cellparameters_atomicposition

# Define the path to the directory containing the test PW runs.
TEST_JOB_DIR = os.path.join(os.path.dirname(__file__), 'pwtestjobs')
# Get the paths of all the input files.
INPUT_FILES = [os.path.join(TEST_JOB_DIR, x) for x in os.listdir(TEST_JOB_DIR)
               if x.endswith('.in')]


class TestPwInputFile(AiidaTestCase):
    """
    Unittest for testing the PwInputFile class of pwinputparser.

    The tests involve looping over the test PW runs, creating a PwInputFile
    object for each, and verifying its parsed attributes and the output of
    its AiiDa-specific methods.

    The test jobs should all contain the same structure, input parameters,
    ect., but the units of the input files differ, in order to test the unit
    and coordinate transformations of the PwInputTools methods.

    The only thing that should vary between some of them is the type of
    k-points (manual, gamma, and automatic). For this reason, the testing of
    get_kpointsdata is split up into three different test methods.
    """

    def test_get_structuredata(self):
        """Test the get_structuredata method of PwInputFile"""

        # Create a reference StructureData object for the structure contained
        # in all the input files.
        ref_structure = StructureData()
        ref_structure.set_cell(
            ((2.456, 0., 0.),
             (-1.228, 2.12695, 0.),
             (0., 0., 6.69604))
        )
        ref_structure.append_atom(
            name='C', symbols='C', position=(0., 0., 0.), mass=12.
        )
        ref_structure.append_atom(
            name='C', symbols='C', position=(0., 1.41797, 0.), mass=12.
        )
        ref_structure.append_atom(
            name='C', symbols='C', position=(0., 0., 3.34802), mass=12.
        )
        ref_structure.append_atom(
            name='C', symbols='C', position=(1.228, 0.70899, 3.34802), mass=12.
        )

        # Check each input file for agreement with reference values.
        for input_file in INPUT_FILES:

            # Parse the input file and get the structuredata.
            pwinputfile = pwinputparser.PwInputFile(input_file)
            structure = pwinputfile.get_structuredata()

            # Check the name and the positions of each Kind.
            for ref_site, site in zip(ref_structure.sites, structure.sites):
                self.assertEqual(site.kind_name, ref_site.kind_name)
                for ref_q, q in zip(ref_site.position, site.position):
                    self.assertAlmostEqual(ref_q, q, 4)

            # Check the cell.
            for ref_row, row in zip(ref_structure.cell, structure.cell):
                for ref_q, q in zip(ref_row, row):
                    self.assertAlmostEqual(ref_q, q, 4)

            # Check the mass of each Kind.
            for ref_kind, kind in zip(ref_structure.kinds, structure.kinds):
                self.assertEqual(ref_kind.mass, kind.mass)

    def test_namelists(self):
        """Test the parsing of the QE namelists and their key/value pairs."""

        # Define the reference namelists.
        # NOTE: Only the items important to the proper creation of an AiiDa
        # calculation are included here and checked below.
        ref_namelists = {
            'CONTROL':
                {'calculation': 'scf',
                 'restart_mode': 'from_scratch',
                 'outdir': './tmp'},
            'ELECTRONS':
                {'conv_thr': 1e-05},
            'SYSTEM':
                {'ecutwfc': 30.0,
                 'occupations': 'fixed',
                 'ibrav': 0,
                 'degauss': 0.02,
                 'smearing': 'methfessel-paxton',
                 'nat': 4,
                 'ntyp': 1,
                 'ecutrho': 180.0}
        }

        # Check each input file for agreement with reference values.
        for input_file in INPUT_FILES:

            # Parse the input file
            pwinputfile = pwinputparser.PwInputFile(input_file)

            # Check the key/value pairs for each namelist in ref_namelists.
            for namelist_key, namelist in ref_namelists.items():
                for key, ref_value in namelist.items():
                    self.assertEqual(pwinputfile.namelists[namelist_key][key],
                                     ref_value)

    def test_get_kpointsdata_manual(self):
        """Test get_kpointsdata for all inputs w/ manually specified kpoints."""

        # Define reference cell.
        ref_cell = np.array([[2.456, 0., 0.],
                             [-1.228, 2.12695, 0.],
                             [0., 0., 6.69604]])
        # Define reference kpoints.
        ref_kpoints = np.array([[0., 0., 0.],
                                [0.25, 0., 0.],
                                [0.5, 0., 0.],
                                [0.3333333, 0.3333333, 0.],
                                [0.1666667, 0.1666667, 0.],
                                [0., 0., 0.],
                                [0., 0., 0.25],
                                [0., 0., 0.5],
                                [0.5, 0., 0.5],
                                [0.3333333, 0.3333333, 0.5],
                                [0., 0., 0.5],
                                [0.5, 0., 0.5],
                                [0.5, 0., 0.],
                                [0.3333333, 0.3333333, 0.],
                                [0.3333333, 0.3333333, 0.5]])
        # Define reference weights.
        ref_weights = np.array(
            [1., 1., 5., 2., 2., 4., 4., 1., 5., 2., 4., 5., 2., 4., 2.]
        )

        # Filter out all input files with manually specified kpoints.
        manual_input_files = filter(
            lambda x: 'automatic' not in x and 'gamma' not in x,
            INPUT_FILES
        )

        # Check each input file for agreement with reference values.
        tol = 0.0001
        for input_file in manual_input_files:
            # Parse the input file and get the kpointsdata.
            pwinputfile = pwinputparser.PwInputFile(input_file)
            kpointsdata = pwinputfile.get_kpointsdata()

            # Check the cell.
            self.assertTrue(np.all(np.abs(kpointsdata.cell - ref_cell) < tol))

            # Check the kpoints and weights.
            kpoints, weights = kpointsdata.get_kpoints(also_weights=True)
            self.assertTrue(np.all(np.abs(kpoints - ref_kpoints) < tol))
            self.assertTrue(np.all(np.abs(weights - ref_weights) < tol))

    def test_get_kpointsdata_automatic(self):
        """Test get_kpointsdata for all inputs w/ automatic kpoints."""

        # Define reference cell.
        ref_cell = np.array([[2.456, 0., 0.],
                             [-1.228, 2.12695, 0.],
                             [0., 0., 6.69604]])
        # Define reference kpoints mesh.
        ref_mesh = np.array([5, 5, 6])
        # Define reference offset.
        ref_offset = np.array([0.5, 0.5, 0.])

        # Filter out all input files with automatic kpoints.
        automatic_input_files = filter(lambda x: 'automatic' in x, INPUT_FILES)

        # Check each input file for agreement with reference values.
        tol = 0.0001
        for input_file in automatic_input_files:
            # Parse the input file and get the kpointsdata.
            pwinputfile = pwinputparser.PwInputFile(input_file)
            kpointsdata = pwinputfile.get_kpointsdata()

            # Check the cell.
            self.assertTrue(np.all(np.abs(kpointsdata.cell - ref_cell) < tol))

            # Check the mesh and offset.
            mesh, offset = kpointsdata.get_kpoints_mesh()
            self.assertTrue(np.all(np.abs(np.array(mesh) - ref_mesh) < tol))
            self.assertTrue(np.all(np.abs(np.array(offset) - ref_offset) < tol))

    def test_get_kpointsdata_gamma(self):
        """Test get_kpointsdata for all inputs w/ gamma kpoints."""

        # Define reference cell.
        ref_cell = np.array([[2.456, 0., 0.],
                             [-1.228, 2.12695, 0.],
                             [0., 0., 6.69604]])
        # Define reference kpoints mesh.
        ref_mesh = np.array([1, 1, 1])
        # Define reference offset.
        ref_offset = np.array([0., 0., 0.])

        # Filter out all input files with gamma kpoints.
        gamma_input_files = filter(lambda x: 'gamma' in x, INPUT_FILES)

        # Check each input file for agreement with reference values.
        tol = 0.0001
        for input_file in gamma_input_files:
            # Parse the input file and get the kpointsdata.
            pwinputfile = pwinputparser.PwInputFile(input_file)
            kpointsdata = pwinputfile.get_kpointsdata()

            # Check the cell.
            self.assertTrue(np.all(np.abs(kpointsdata.cell - ref_cell) < tol))

            # Check the mesh and offset.
            mesh, offset = kpointsdata.get_kpoints_mesh()
            self.assertTrue(np.all(np.abs(np.array(mesh) - ref_mesh) < tol))
            self.assertTrue(np.all(np.abs(np.array(offset) - ref_offset) < tol))

    def test_atomic_species(self):
        """Test the parsing of the ATOMIC_SPECIES card."""

        # Define the reference atomic species dictionary.
        ref_atomic_species = {'masses': [12.0],
                              'names': ['C'],
                              'pseudo_file_names': ['C.pbe-rrkjus.UPF']}

        # Check each input file for agreement with reference values.
        for input_file in INPUT_FILES:
            # Parse the input file
            pwinputfile = pwinputparser.PwInputFile(input_file)

            # Check the atomic_species attribute against the reference
            # dictionary.
            self.assertDictEqual(ref_atomic_species, pwinputfile.atomic_species)
