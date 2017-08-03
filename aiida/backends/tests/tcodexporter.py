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
Tests for TestTcodDbExporter
"""
import unittest

from aiida.backends.testbase import AiidaTestCase
from aiida.common.links import LinkType



class FakeObject(object):
    """
    A wrapper for dictionary, which can be used instead of object.
    Example use case: fake Calculation object ``calc``, having keys
    ``inp`` and ``out`` to access also fake NodeInputManager and
    NodeOutputManager.
    """

    def __init__(self, dictionary):
        self._dictionary = dictionary

    def __getattr__(self, name):
        if isinstance(self._dictionary[name], dict):
            return FakeObject(self._dictionary[name])
        else:
            return self._dictionary[name]


class TestTcodDbExporter(AiidaTestCase):
    """
    Tests for TcodDbExporter class.
    """
    from aiida.orm.data.structure import has_ase, has_spglib
    from aiida.orm.data.cif import has_pycifrw

    def test_contents_encoding_1(self):
        """
        Testing the logic of choosing the encoding and the process of
        encoding contents.
        """
        from aiida.tools.dbexporters.tcod import cif_encode_contents
        self.assertEquals(cif_encode_contents('simple line')[1],
                          None)
        self.assertEquals(cif_encode_contents(' ;\n ;')[1],
                          None)
        self.assertEquals(cif_encode_contents(';\n'),
                          ('=3B\n', 'quoted-printable'))
        self.assertEquals(cif_encode_contents('line\n;line'),
                          ('line\n=3Bline', 'quoted-printable'))
        self.assertEquals(cif_encode_contents('tabbed\ttext'),
                          ('tabbed=09text', 'quoted-printable'))
        self.assertEquals(cif_encode_contents('angstrom Å'),
                          ('angstrom =C3=85', 'quoted-printable'))
        self.assertEquals(cif_encode_contents('.'),
                          ('=2E', 'quoted-printable'))
        self.assertEquals(cif_encode_contents('?'),
                          ('=3F', 'quoted-printable'))
        self.assertEquals(cif_encode_contents('.?'), ('.?', None))
        # This one is particularly tricky: a long line is folded by the QP
        # and the semicolon sign becomes the first character on a new line.
        self.assertEquals(cif_encode_contents(
            "Å{};a".format("".join("a" for i in range(0, 69)))),
            ('=C3=85aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
             'aaaaaaaaaaaaaaaaaaaaaaaaaaaaa=\n=3Ba',
             'quoted-printable'))
        self.assertEquals(cif_encode_contents('angstrom ÅÅÅ'),
                          ('YW5nc3Ryb20gw4XDhcOF', 'base64'))
        self.assertEquals(cif_encode_contents(
            "".join("a" for i in range(0, 2048)))[1],
                          None)
        self.assertEquals(cif_encode_contents(
            "".join("a" for i in range(0, 2049)))[1],
                          'quoted-printable')
        self.assertEquals(cif_encode_contents('datatest')[1], None)
        self.assertEquals(cif_encode_contents('data_test')[1], 'base64')

    def test_collect_files(self):
        """
        Testing the collection of files from file tree.
        """
        from aiida.tools.dbexporters.tcod import _collect_files
        from aiida.common.folders import SandboxFolder
        import StringIO

        sf = SandboxFolder()
        sf.get_subfolder('out', create=True)
        sf.get_subfolder('pseudo', create=True)
        sf.get_subfolder('save', create=True)
        sf.get_subfolder('save/1', create=True)
        sf.get_subfolder('save/2', create=True)

        f = StringIO.StringIO("test")
        sf.create_file_from_filelike(f, 'aiida.in')
        f = StringIO.StringIO("test")
        sf.create_file_from_filelike(f, 'aiida.out')
        f = StringIO.StringIO("test")
        sf.create_file_from_filelike(f, '_aiidasubmit.sh')
        f = StringIO.StringIO("test")
        sf.create_file_from_filelike(f, '_.out')
        f = StringIO.StringIO("test")
        sf.create_file_from_filelike(f, 'out/out')
        f = StringIO.StringIO("test")
        sf.create_file_from_filelike(f, 'save/1/log.log')

        md5 = '098f6bcd4621d373cade4e832627b4f6'
        sha1 = 'a94a8fe5ccb19ba61c4c0873d391e987982fbbd3'
        self.assertEquals(
            _collect_files(sf.abspath),
            [{'name': '_.out', 'contents': 'test', 'md5': md5,
              'sha1': sha1, 'type': 'file'},
             {'name': '_aiidasubmit.sh', 'contents': 'test', 'md5': md5,
              'sha1': sha1, 'type': 'file'},
             {'name': 'aiida.in', 'contents': 'test', 'md5': md5,
              'sha1': sha1, 'type': 'file'},
             {'name': 'aiida.out', 'contents': 'test', 'md5': md5,
              'sha1': sha1, 'type': 'file'},
             {'name': 'out/', 'type': 'folder'},
             {'name': 'out/out', 'contents': 'test', 'md5': md5,
              'sha1': sha1, 'type': 'file'},
             {'name': 'pseudo/', 'type': 'folder'},
             {'name': 'save/', 'type': 'folder'},
             {'name': 'save/1/', 'type': 'folder'},
             {'name': 'save/1/log.log', 'contents': 'test', 'md5': md5,
              'sha1': sha1, 'type': 'file'},
             {'name': 'save/2/', 'type': 'folder'}])

    @unittest.skipIf(not has_ase(), "Unable to import ase")
    @unittest.skipIf(not has_spglib(), "Unable to import spglib")
    @unittest.skipIf(not has_pycifrw(), "Unable to import PyCifRW")
    def test_cif_structure_roundtrip(self):
        from aiida.tools.dbexporters.tcod import export_cif, export_values
        from aiida.orm import Code
        from aiida.orm import JobCalculation
        from aiida.orm.data.cif import CifData
        from aiida.orm.data.parameter import ParameterData
        from aiida.orm.data.upf import UpfData
        from aiida.orm.data.folder import FolderData
        from aiida.common.folders import SandboxFolder
        from aiida.common.datastructures import calc_states
        import tempfile

        with tempfile.NamedTemporaryFile() as f:
            f.write('''
                data_test
                _cell_length_a    10
                _cell_length_b    10
                _cell_length_c    10
                _cell_angle_alpha 90
                _cell_angle_beta  90
                _cell_angle_gamma 90
                loop_
                _atom_site_label
                _atom_site_fract_x
                _atom_site_fract_y
                _atom_site_fract_z
                C 0 0 0
                O 0.5 0.5 0.5
            ''')
            f.flush()
            a = CifData(file=f.name)

        c = a._get_aiida_structure()
        c.store()
        pd = ParameterData()

        code = Code(local_executable='test.sh')
        with tempfile.NamedTemporaryFile() as f:
            f.write("#/bin/bash\n\necho test run\n")
            f.flush()
            code.add_path(f.name, 'test.sh')

        code.store()

        calc = JobCalculation(computer=self.computer)
        calc.set_resources({'num_machines': 1,
                            'num_mpiprocs_per_machine': 1})
        calc.add_link_from(code, "code")
        calc.set_environment_variables({'PATH': '/dev/null', 'USER': 'unknown'})

        with tempfile.NamedTemporaryFile(prefix="Fe") as f:
            f.write("<UPF version=\"2.0.1\">\nelement=\"Fe\"\n")
            f.flush()
            upf = UpfData(file=f.name)
            upf.store()
            calc.add_link_from(upf, "upf")

        with tempfile.NamedTemporaryFile() as f:
            f.write("data_test")
            f.flush()
            cif = CifData(file=f.name)
            cif.store()
            calc.add_link_from(cif, "cif")

        calc.store()
        calc._set_state(calc_states.SUBMITTING)
        with SandboxFolder() as f:
            calc._store_raw_input_folder(f.abspath)

        fd = FolderData()
        with open(fd._get_folder_pathsubfolder.get_abs_path(
                calc._SCHED_OUTPUT_FILE), 'w') as f:
            f.write("standard output")
            f.flush()

        with open(fd._get_folder_pathsubfolder.get_abs_path(
                calc._SCHED_ERROR_FILE), 'w') as f:
            f.write("standard error")
            f.flush()

        fd.store()
        fd.add_link_from(calc, calc._get_linkname_retrieved(), LinkType.CREATE)

        pd.add_link_from(calc, "calc", LinkType.CREATE)
        pd.store()

        with self.assertRaises(ValueError):
            export_cif(c, parameters=pd)

        c.add_link_from(calc, "calc", LinkType.CREATE)
        export_cif(c, parameters=pd)

        values = export_values(c, parameters=pd)
        values = values['0']

        self.assertEquals(values['_tcod_computation_environment'],
                          ['PATH=/dev/null\nUSER=unknown'])
        self.assertEquals(values['_tcod_computation_command'],
                          ['cd 1; ./_aiidasubmit.sh'])

    def test_pw_translation(self):
        from aiida.tools.dbexporters.tcod \
            import translate_calculation_specific_values
        # from aiida.tools.dbexporters.tcod_plugins.pw \
        #     import PwTcodtranslator as PWT
        # from aiida.tools.dbexporters.tcod_plugins.cp \
        #     import CpTcodtranslator as CPT
        from aiida.orm.code import Code
        from aiida.orm.data.array import ArrayData
        from aiida.orm.data.array.kpoints import KpointsData
        from aiida.orm.data.parameter import ParameterData
        import numpy
        from aiida.common.pluginloader import get_plugin
        PWT = get_plugin('tools.dbexporters.tcod_plugins', 'quantumespresso.pw')
        CPT = get_plugin('tools.dbexporters.tcod_plugins', 'quantumespresso.cp')

        code = Code()
        code._set_attr('remote_exec_path', '/test')

        kpoints = KpointsData()
        kpoints.set_kpoints_mesh([2, 3, 4], offset=[0.25, 0.5, 0.75])

        def empty_list():
            return []

        calc = FakeObject({
            "inp": {"parameters": ParameterData(dict={}),
                    "kpoints": kpoints, "code": code},
            "out": {"output_parameters": ParameterData(dict={})},
            "get_inputs": empty_list
        })

        res = translate_calculation_specific_values(calc, PWT)
        self.assertEquals(res, {
            '_dft_BZ_integration_grid_X': 2,
            '_dft_BZ_integration_grid_Y': 3,
            '_dft_BZ_integration_grid_Z': 4,
            '_dft_BZ_integration_grid_shift_X': 0.25,
            '_dft_BZ_integration_grid_shift_Y': 0.5,
            '_dft_BZ_integration_grid_shift_Z': 0.75,
            '_dft_pseudopotential_atom_type': [],
            '_dft_pseudopotential_type': [],
            '_dft_pseudopotential_type_other_name': [],
            '_tcod_software_package': 'Quantum ESPRESSO',
            '_tcod_software_executable_path': '/test',
        })

        calc = FakeObject({
            "inp": {"parameters": ParameterData(dict={
                'SYSTEM': {'ecutwfc': 40, 'occupations': 'smearing'}
            })},
            "out": {"output_parameters": ParameterData(dict={
                'number_of_electrons': 10,
            })},
            "get_inputs": empty_list
        })
        res = translate_calculation_specific_values(calc, PWT)
        self.assertEquals(res, {
            '_dft_cell_valence_electrons': 10,
            '_tcod_software_package': 'Quantum ESPRESSO',
            '_dft_BZ_integration_smearing_method': 'Gaussian',
            '_dft_pseudopotential_atom_type': [],
            '_dft_pseudopotential_type': [],
            '_dft_pseudopotential_type_other_name': [],
            '_dft_kinetic_energy_cutoff_EEX': 2176.910676048,
            '_dft_kinetic_energy_cutoff_charge_density': 2176.910676048,
            '_dft_kinetic_energy_cutoff_wavefunctions': 544.227669012,
        })

        calc = FakeObject({
            "inp": {"parameters": ParameterData(dict={})},
            "out": {"output_parameters": ParameterData(dict={
                'energy_xc': 5,
            })},
            "get_inputs": empty_list
        })
        with self.assertRaises(ValueError):
            translate_calculation_specific_values(calc, PWT)

        calc = FakeObject({
            "inp": {"parameters": ParameterData(dict={})},
            "out": {"output_parameters": ParameterData(dict={
                'energy_xc': 5,
                'energy_xc_units': 'meV'
            })},
            "get_inputs": empty_list
        })
        with self.assertRaises(ValueError):
            translate_calculation_specific_values(calc, PWT)

        energies = {
            'energy': -3701.7004199449257,
            'energy_one_electron': -984.0078459766,
            'energy_xc': -706.6986753641559,
            'energy_ewald': -2822.6335103043157,
            'energy_hartree': 811.6396117001462,
            'fermi_energy': 10.25208617898623,
        }
        dct = energies
        for key in energies.keys():
            dct["{}_units".format(key)] = 'eV'
        calc = FakeObject({
            "inp": {"parameters": ParameterData(dict={
                'SYSTEM': {'smearing': 'mp'}
            })},
            "out": {"output_parameters": ParameterData(dict=dct)},
            "get_inputs": empty_list
        })
        res = translate_calculation_specific_values(calc, PWT)
        self.assertEquals(res, {
            '_tcod_total_energy': energies['energy'],
            '_dft_1e_energy': energies['energy_one_electron'],
            '_dft_correlation_energy': energies['energy_xc'],
            '_dft_ewald_energy': energies['energy_ewald'],
            '_dft_hartree_energy': energies['energy_hartree'],
            '_dft_fermi_energy': energies['fermi_energy'],
            '_tcod_software_package': 'Quantum ESPRESSO',
            '_dft_BZ_integration_smearing_method': 'Methfessel-Paxton',
            '_dft_BZ_integration_MP_order': 1,
            '_dft_pseudopotential_atom_type': [],
            '_dft_pseudopotential_type': [],
            '_dft_pseudopotential_type_other_name': [],
        })
        dct = energies
        dct['number_of_electrons'] = 10
        for key in energies.keys():
            dct["{}_units".format(key)] = 'eV'
        calc = FakeObject({
            "inp": {"parameters": ParameterData(dict={
                'SYSTEM': {'smearing': 'unknown-method'}
            })},
            "out": {"output_parameters": ParameterData(dict=dct)},
            "get_inputs": empty_list
        })
        res = translate_calculation_specific_values(calc, CPT)
        self.assertEquals(res, {'_dft_cell_valence_electrons': 10,
                                '_tcod_software_package':
                                    'Quantum ESPRESSO'})

        ad = ArrayData()
        ad.set_array("forces", numpy.array([[[1, 2, 3], [4, 5, 6]]]))
        calc = FakeObject({
            "inp": {"parameters": ParameterData(dict={
                'SYSTEM': {'smearing': 'unknown-method'}
            })},
            "out": {"output_parameters": ParameterData(dict={}),
                    "output_array": ad},
            "get_inputs": empty_list
        })
        res = translate_calculation_specific_values(calc, PWT)
        self.assertEquals(res, {
            '_tcod_software_package': 'Quantum ESPRESSO',
            '_dft_BZ_integration_smearing_method': 'other',
            '_dft_BZ_integration_smearing_method_other': 'unknown-method',
            '_dft_pseudopotential_atom_type': [],
            '_dft_pseudopotential_type': [],
            '_dft_pseudopotential_type_other_name': [],
            ## Residual forces are no longer produced, as they should
            ## be in the same CIF loop with coordinates -- to be
            ## implemented later, since it's not yet clear how.
            # '_tcod_atom_site_resid_force_Cartn_x': [1,4],
            # '_tcod_atom_site_resid_force_Cartn_y': [2,5],
            # '_tcod_atom_site_resid_force_Cartn_z': [3,6],
        })

    def test_nwcpymatgen_translation(self):
        from aiida.tools.dbexporters.tcod \
            import translate_calculation_specific_values
        # from aiida.tools.dbexporters.tcod_plugins.nwcpymatgen \
        #     import NwcpymatgenTcodtranslator as NPT
        from aiida.orm.data.parameter import ParameterData
        from tcodexporter import FakeObject
        from aiida.common.pluginloader import get_plugin
        NPT = get_plugin('tools.dbexporters.tcod_plugins', 'nwchem.nwcpymatgen')

        calc = FakeObject({
            "out": {"output":
                ParameterData(dict={
                    "basis_set": {
                        "H": {
                            "description": "6-31g",
                            "functions": "2",
                            "shells": "2",
                            "types": "2s"
                        },
                        "O": {
                            "description": "6-31g",
                            "functions": "9",
                            "shells": "5",
                            "types": "3s2p"
                        }
                    },
                    "corrections": {},
                    "energies": [
                        -2057.99011937535
                    ],
                    "errors": [],
                    "frequencies": None,
                    "has_error": False,
                    "job_type": "NWChem SCF Module"
                }),
                "job_info": ParameterData(dict={
                    "0 permanent": ".",
                    "0 scratch": ".",
                    "argument  1": "aiida.in",
                    "compiled": "Sun_Dec_22_04:02:59_2013",
                    "data base": "./aiida.db",
                    "date": "Mon May 11 17:10:07 2015",
                    "ga revision": "10379",
                    "global": "200.0 Mbytes (distinct from heap & stack)",
                    "hardfail": "no",
                    "heap": "100.0 Mbytes",
                    "hostname": "theospc11",
                    "input": "aiida.in",
                    "nproc": "6",
                    "nwchem branch": "6.3",
                    "nwchem revision": "24277",
                    "prefix": "aiida.",
                    "program": "/usr/bin/nwchem",
                    "source": "/build/buildd/nwchem-6.3+r1",
                    "stack": "100.0 Mbytes",
                    "status": "startup",
                    "time left": "-1s",
                    "total": "400.0 Mbytes",
                    "verify": "yes",
                })
            }})
        res = translate_calculation_specific_values(calc, NPT)
        self.assertEquals(res, {
            '_tcod_software_package': 'NWChem',
            '_tcod_software_package_version': '6.3',
            '_tcod_software_package_compilation_date': '2013-12-22T04:02:59',
            '_atom_type_symbol': ['H', 'O'],
            '_dft_atom_basisset': ['6-31g', '6-31g'],
            '_dft_atom_type_valence_configuration': ['2s', '3s2p'],
        })

    @unittest.skipIf(not has_ase(), "Unable to import ase")
    @unittest.skipIf(not has_spglib(), "Unable to import spglib")
    @unittest.skipIf(not has_pycifrw(), "Unable to import PyCifRW")
    def test_inline_export(self):
        from aiida.orm.data.cif import CifData
        from aiida.tools.dbexporters.tcod import export_values
        import tempfile

        with tempfile.NamedTemporaryFile() as f:
            f.write('''
                data_test
                _cell_length_a    10
                _cell_length_b    10
                _cell_length_c    10
                _cell_angle_alpha 90
                _cell_angle_beta  90
                _cell_angle_gamma 90
                loop_
                _atom_site_label
                _atom_site_fract_x
                _atom_site_fract_y
                _atom_site_fract_z
                C 0 0 0
                O 0.5 0.5 0.5
            ''')
            f.flush()
            a = CifData(file=f.name)

        s = a._get_aiida_structure(store=True)
        val = export_values(s)
        script = val.first_block()['_tcod_file_contents'][1]
        function = '_get_aiida_structure_ase_inline'
        self.assertNotEqual(script.find(function), script.rfind(function))

    @unittest.skipIf(not has_ase(), "Unable to import ase")
    @unittest.skipIf(not has_spglib(), "Unable to import spglib")
    @unittest.skipIf(not has_pycifrw(), "Unable to import PyCifRW")
    def test_symmetry_reduction(self):
        from aiida.orm.data.structure import StructureData
        from aiida.tools.dbexporters.tcod import export_values
        from ase import Atoms

        a = Atoms('BaTiO3', cell=(4., 4., 4.))
        a.set_scaled_positions(
            ((0.0, 0.0, 0.0),
             (0.5, 0.5, 0.5),
             (0.5, 0.5, 0.0),
             (0.5, 0.0, 0.5),
             (0.0, 0.5, 0.5),
             )
        )

        a.set_chemical_symbols(['Ba', 'Ti', 'O', 'O', 'O'])
        val = export_values(StructureData(ase=a), reduce_symmetry=True, store=True)['0']
        self.assertEqual(val['_atom_site_label'], ['Ba1', 'Ti1', 'O1'])
        self.assertEqual(val['_symmetry_space_group_name_H-M'], 'Pm-3m')
        self.assertEqual(val['_symmetry_space_group_name_Hall'], '-P 4 2 3')

    def test_cmdline_parameters(self):
        """
        Ensuring that neither extend_with_cmdline_parameters() nor
        deposition_cmdline_parameters() set default parameters.
        """
        from aiida.tools.dbexporters.tcod \
            import extend_with_cmdline_parameters, \
            deposition_cmdline_parameters
        import argparse

        parser = argparse.ArgumentParser()
        extend_with_cmdline_parameters(parser)
        options = vars(parser.parse_args(args=[]))

        for key in options.keys():
            if options[key] is None:
                options.pop(key)

        self.assertEqual(options, {})

        parser = argparse.ArgumentParser()
        deposition_cmdline_parameters(parser)
        options = vars(parser.parse_args(args=[]))

        for key in options.keys():
            if options[key] is None:
                options.pop(key)

        self.assertEqual(options, {})

    @unittest.skipIf(not has_ase(), "Unable to import ase")
    @unittest.skipIf(not has_spglib(), "Unable to import spglib")
    @unittest.skipIf(not has_pycifrw(), "Unable to import PyCifRW")
    def test_export_trajectory(self):
        from aiida.orm.data.structure import StructureData
        from aiida.orm.data.array.trajectory import TrajectoryData
        from aiida.tools.dbexporters.tcod import export_values

        cells = [
            [[2., 0., 0., ],
             [0., 2., 0., ],
             [0., 0., 2., ]],
            [[3., 0., 0., ],
             [0., 3., 0., ],
             [0., 0., 3., ]]
        ]
        symbols = [['H', 'O', 'C'], ['H', 'O', 'C']]
        positions = [
            [[0., 0., 0.],
             [0.5, 0.5, 0.5],
             [1.5, 1.5, 1.5]],
            [[0., 0., 0.],
             [0.75, 0.75, 0.75],
             [1.25, 1.25, 1.25]]
        ]
        structurelist = []
        for i in range(0, 2):
            struct = StructureData(cell=cells[i])
            for j, symbol in enumerate(symbols[i]):
                struct.append_atom(symbols=symbol, position=positions[i][j])
            structurelist.append(struct)

        td = TrajectoryData(structurelist=structurelist)

        with self.assertRaises(ValueError):
            # Trajectory index is not specified
            v = export_values(td)

        expected_tags = [
            '_atom_site_fract_x',
            '_atom_site_fract_y',
            '_atom_site_fract_z',
            '_atom_site_label',
            '_atom_site_type_symbol',
            '_audit_conform_dict_location',
            '_audit_conform_dict_name',
            '_audit_conform_dict_version',
            '_audit_creation_method',
            '_cell_angle_alpha',
            '_cell_angle_beta',
            '_cell_angle_gamma',
            '_cell_length_a',
            '_cell_length_b',
            '_cell_length_c',
            '_chemical_formula_sum',
            '_symmetry_Int_Tables_number',
            '_symmetry_equiv_pos_as_xyz',
            '_symmetry_space_group_name_H-M',
            '_symmetry_space_group_name_Hall'
        ]

        tcod_file_tags = [
            '_tcod_content_encoding_id',
            '_tcod_content_encoding_layer_id',
            '_tcod_content_encoding_layer_type',
            '_tcod_file_URI',
            '_tcod_file_content_encoding',
            '_tcod_file_contents',
            '_tcod_file_id',
            '_tcod_file_md5sum',
            '_tcod_file_name',
            '_tcod_file_role',
            '_tcod_file_sha1sum'
        ]

        # Not stored and not to be stored:
        v = export_values(td, trajectory_index=1)
        self.assertEqual(sorted(v['0'].keys()), expected_tags)

        # Stored, but not expected to be stored:
        td = TrajectoryData(structurelist=structurelist)
        td.store()
        v = export_values(td, trajectory_index=1)
        self.assertEqual(sorted(v['0'].keys()),
                         expected_tags + tcod_file_tags)

        # Not stored, but expected to be stored:
        td = TrajectoryData(structurelist=structurelist)
        v = export_values(td, trajectory_index=1, store=True)
        self.assertEqual(sorted(v['0'].keys()),
                         expected_tags + tcod_file_tags)

        # Both stored and expected to be stored:
        td = TrajectoryData(structurelist=structurelist)
        td.store()
        v = export_values(td, trajectory_index=1, store=True)
        self.assertEqual(sorted(v['0'].keys()),
                         expected_tags + tcod_file_tags)

        # Stored, but asked not to include DB dump:
        td = TrajectoryData(structurelist=structurelist)
        td.store()
        v = export_values(td, trajectory_index=1,
                          dump_aiida_database=False)
        self.assertEqual(sorted(v['0'].keys()),
                         expected_tags)

    def test_contents_encoding_2(self):
        """
        Testing the logic of choosing the encoding and the process of
        encoding contents.
        """
        from aiida.tools.dbexporters.tcod import decode_textfield

        def check_ncr(self, inp, out):
            from aiida.tools.dbexporters.tcod import (encode_textfield_ncr,
                                                      decode_textfield_ncr)
            encoded = encode_textfield_ncr(inp)
            decoded = decode_textfield_ncr(out)
            decoded_universal = decode_textfield(out, 'ncr')
            self.assertEquals(encoded, out)
            self.assertEquals(decoded, inp)
            self.assertEquals(decoded_universal, inp)

        def check_quoted_printable(self, inp, out):
            from aiida.tools.dbexporters.tcod import (encode_textfield_quoted_printable,
                                                      decode_textfield_quoted_printable)
            encoded = encode_textfield_quoted_printable(inp)
            decoded = decode_textfield_quoted_printable(out)
            decoded_universal = decode_textfield(out, 'quoted-printable')
            self.assertEquals(encoded, out)
            self.assertEquals(decoded, inp)
            self.assertEquals(decoded_universal, inp)

        def check_base64(self, inp, out):
            from aiida.tools.dbexporters.tcod import (encode_textfield_base64,
                                                      decode_textfield_base64)
            encoded = encode_textfield_base64(inp)
            decoded = decode_textfield_base64(out)
            decoded_universal = decode_textfield(out, 'base64')
            self.assertEquals(encoded, out)
            self.assertEquals(decoded, inp)
            self.assertEquals(decoded_universal, inp)

        def check_gzip_base64(self, text):
            from aiida.tools.dbexporters.tcod import (encode_textfield_gzip_base64,
                                                      decode_textfield_gzip_base64)
            encoded = encode_textfield_gzip_base64(text)
            decoded = decode_textfield_gzip_base64(encoded)
            decoded_universal = decode_textfield(encoded, 'gzip+base64')
            self.assertEquals(text, decoded)
            self.assertEquals(text, decoded_universal)

        check_ncr(self, '.', '&#46;')
        check_ncr(self, '?', '&#63;')
        check_ncr(self, ';\n', '&#59;\n')
        check_ncr(self, 'line\n;line', 'line\n&#59;line')
        check_ncr(self, 'tabbed\ttext', 'tabbed&#9;text')
        check_ncr(self, 'angstrom Å', 'angstrom &#195;&#133;')
        check_ncr(self, '<html>&#195;&#133;</html>',
                 '<html>&#38;#195;&#38;#133;</html>')

        check_quoted_printable(self, '.', '=2E')
        check_quoted_printable(self, '?', '=3F')
        check_quoted_printable(self, ';\n', '=3B\n')
        check_quoted_printable(self, 'line\n;line', 'line\n=3Bline')
        check_quoted_printable(self, 'tabbed\ttext', 'tabbed=09text')
        check_quoted_printable(self, 'angstrom Å', 'angstrom =C3=85')
        check_quoted_printable(self, 'line\rline\x00', 'line=0Dline=00')
        # This one is particularly tricky: a long line is folded by the QP
        # and the semicolon sign becomes the first character on a new line.
        check_quoted_printable(self,
                              "Å{};a".format("".join("a" for i in range(0, 69))),
                              '=C3=85aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
                              'aaaaaaaaaaaaaaaaaaaaaaaaaaaaa=\n=3Ba')

        check_base64(self, 'angstrom ÅÅÅ', 'YW5nc3Ryb20gw4XDhcOF')
        check_gzip_base64(self, 'angstrom ÅÅÅ')
