# -*- coding: utf-8 -*-
"""
Tests for TestTcodDbExporter
"""
from django.utils import unittest

from aiida.djsite.db.testbase import AiidaTestCase

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.4.1"
__contributors__ = "Andrea Cepellotti, Andrius Merkys, Giovanni Pizzi"

class TestTcodDbExporter(AiidaTestCase):
    """
    Tests for TcodDbExporter class.
    """
    from aiida.orm.data.structure import has_ase
    from aiida.orm.data.cif import has_pycifrw

    def test_contents_encoding(self):
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
            "Å{};a".format("".join("a" for i in range(0,69)))),
                         ('=C3=85aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
                          'aaaaaaaaaaaaaaaaaaaaaaaaaaaaa=\n=3Ba',
                          'quoted-printable'))
        self.assertEquals(cif_encode_contents('angstrom ÅÅÅ'),
                          ('YW5nc3Ryb20gw4XDhcOF', 'base64'))
        self.assertEquals(cif_encode_contents(
            "".join("a" for i in range(0,2048)))[1],
            None)
        self.assertEquals(cif_encode_contents(
            "".join("a" for i in range(0,2049)))[1],
            'quoted-printable')
        self.assertEquals(cif_encode_contents('datatest')[1],None)
        self.assertEquals(cif_encode_contents('data_test')[1],'base64')

    def test_collect_files(self):
        """
        Testing the collection of files from file tree.
        """
        from aiida.tools.dbexporters.tcod import _collect_files
        from aiida.common.folders import SandboxFolder
        import StringIO

        sf = SandboxFolder()
        sf.get_subfolder('out',create=True)
        sf.get_subfolder('pseudo',create=True)
        sf.get_subfolder('save',create=True)
        sf.get_subfolder('save/1',create=True)
        sf.get_subfolder('save/2',create=True)

        f = StringIO.StringIO("test")
        sf.create_file_from_filelike(f,'aiida.in')
        f = StringIO.StringIO("test")
        sf.create_file_from_filelike(f,'aiida.out')
        f = StringIO.StringIO("test")
        sf.create_file_from_filelike(f,'_aiidasubmit.sh')
        f = StringIO.StringIO("test")
        sf.create_file_from_filelike(f,'_.out')
        f = StringIO.StringIO("test")
        sf.create_file_from_filelike(f,'out/out')
        f = StringIO.StringIO("test")
        sf.create_file_from_filelike(f,'save/1/log.log')

        md5  = '098f6bcd4621d373cade4e832627b4f6'
        sha1 = 'a94a8fe5ccb19ba61c4c0873d391e987982fbbd3'
        self.assertEquals(
            _collect_files(sf.abspath),
            [{'name': 'aiida.in', 'contents': 'test', 'md5': md5,
                      'sha1': sha1, 'type': 'file'},
             {'name': 'save/', 'type': 'folder'},
             {'name': 'save/1/', 'type': 'folder'},
             {'name': 'save/1/log.log', 'contents': 'test', 'md5': md5,
                      'sha1': sha1, 'type': 'file'},
             {'name': 'save/2/', 'type': 'folder'},
             {'name': '_.out', 'contents': 'test', 'md5': md5,
                      'sha1': sha1, 'type': 'file'},
             {'name': 'out/', 'type': 'folder'},
             {'name': 'out/out', 'contents': 'test', 'md5': md5,
                      'sha1': sha1, 'type': 'file'},
             {'name': 'pseudo/', 'type': 'folder'},
             {'name': '_aiidasubmit.sh', 'contents': 'test', 'md5': md5,
                      'sha1': sha1, 'type': 'file'},
             {'name': 'aiida.out', 'contents': 'test', 'md5': md5,
                      'sha1': sha1, 'type': 'file'}])

    @unittest.skipIf(not has_ase(),"Unable to import ase")
    def test_cif_structure_roundtrip(self):
        from aiida.tools.dbexporters.tcod import export_cif,export_values
        from aiida.orm import Code
        from aiida.orm import JobCalculation
        from aiida.orm.data.cif import CifData
        from aiida.orm.data.parameter import ParameterData
        from aiida.orm.data.upf import UpfData
        from aiida.orm.data.folder import FolderData
        from aiida.common.folders import SandboxFolder
        from aiida.common.datastructures import calc_states
        import os
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
        calc.set_resources( {'num_machines': 1,
                          'num_mpiprocs_per_machine': 1} )
        calc._add_link_from(code, "code")
        calc.set_environment_variables({'PATH': '/dev/null', 'USER': 'unknown'})

        with tempfile.NamedTemporaryFile(prefix="Fe") as f:
            f.write("<UPF version=\"2.0.1\">\nelement=\"Fe\"\n")
            f.flush()
            upf = UpfData(file=f.name)
            upf.store()
            calc._add_link_from(upf, "upf")

        with tempfile.NamedTemporaryFile() as f:
            f.write("data_test")
            f.flush()
            cif = CifData(file=f.name)
            cif.store()
            calc._add_link_from(cif, "cif")

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
        fd._add_link_from(calc, calc._get_linkname_retrieved())

        pd._add_link_from(calc,"calc")
        pd.store()

        with self.assertRaises(ValueError):
            export_cif(c,parameters=pd)

        c._add_link_from(calc,"calc")
        export_cif(c,parameters=pd)

        values = export_values(c,parameters=pd)
        values = values['0']

        self.assertEquals(values['_tcod_computation_environment'],
                          ['PATH=/dev/null\nUSER=unknown'])
        self.assertEquals(values['_tcod_computation_command'],
                          ['cd 0; ./_aiidasubmit.sh'])

    def test_pw_translation(self):
        from aiida.tools.dbexporters.tcod \
             import translate_calculation_specific_values
        from aiida.tools.dbexporters.tcod_plugins.pw \
             import PwTcodtranslator as PWT
        from aiida.tools.dbexporters.tcod_plugins.cp \
             import CpTcodtranslator as CPT
        from aiida.orm.data.parameter import ParameterData

        pd = ParameterData(dict={})
        res = translate_calculation_specific_values(pd,PWT)
        self.assertEquals(res,{'_tcod_software_package':
                               'Quantum ESPRESSO'})

        pd = ParameterData(dict={'number_of_electrons': 10})
        res = translate_calculation_specific_values(pd,PWT)
        self.assertEquals(res,{'_dft_cell_valence_electrons': 10,
                               '_tcod_software_package':
                               'Quantum ESPRESSO'})

        pd = ParameterData(dict={'energy_xc': 5})
        with self.assertRaises(ValueError):
            translate_calculation_specific_values(pd,PWT)

        pd = ParameterData(dict={'energy_xc'      : 5,
                                 'energy_xc_units': 'meV'})
        with self.assertRaises(ValueError):
            translate_calculation_specific_values(pd,PWT)

        energies = {
            'energy'             : -3701.7004199449257,
            'energy_one_electron': -984.0078459766,
            'energy_xc'          : -706.6986753641559,
            'energy_ewald'       : -2822.6335103043157,
            'energy_hartree'     : 811.6396117001462,
            'fermi_energy'       : 10.25208617898623,
        }
        dct = energies
        for key in energies.keys():
            dct["{}_units".format(key)] = 'eV'
        pd = ParameterData(dict=dct)
        res = translate_calculation_specific_values(pd,PWT)
        self.assertEquals(res,{
            '_tcod_total_energy'     : energies['energy'],
            '_dft_1e_energy'         : energies['energy_one_electron'],
            '_dft_correlation_energy': energies['energy_xc'],
            '_dft_ewald_energy'      : energies['energy_ewald'],
            '_dft_hartree_energy'    : energies['energy_hartree'],
            '_dft_fermi_energy'      : energies['fermi_energy'],
            '_tcod_software_package' : 'Quantum ESPRESSO'
        })
        dct = energies
        dct['number_of_electrons'] = 10
        for key in energies.keys():
            dct["{}_units".format(key)] = 'eV'
        pd = ParameterData(dict=dct)
        res = translate_calculation_specific_values(pd,CPT)
        self.assertEquals(res,{'_dft_cell_valence_electrons': 10,
                               '_tcod_software_package':
                               'Quantum ESPRESSO'})

    def test_nwcpymatgen_translation(self):
        from aiida.tools.dbexporters.tcod \
             import translate_calculation_specific_values
        from aiida.tools.dbexporters.tcod_plugins.nwcpymatgen \
             import NwcpymatgenTcodtranslator as NPT
        from aiida.orm.data.parameter import ParameterData

        pd = ParameterData(dict={
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
        })
        res = translate_calculation_specific_values(pd,NPT)
        self.assertEquals(res,{
            '_tcod_software_package'              : 'NWChem',
            '_atom_type_symbol'                   : ['H', 'O'],
            '_dft_atom_basisset'                  : ['6-31g', '6-31g'],
            '_dft_atom_type_valence_configuration': ['2s', '3s2p'],
        })

    @unittest.skipIf(not has_ase() or not has_pycifrw(),
                     "Unable to import ase or pycifrw")
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
        self.assertNotEqual(script.find(function),script.rfind(function))

    @unittest.skipIf(not has_ase(),"Unable to import ase")
    def test_symmetry_reduction(self):
        from aiida.orm.data.structure import StructureData
        from aiida.tools.dbexporters.tcod import export_values
        from ase import Atoms

        a = Atoms('BaTiO3',cell=(4.,4.,4.))
        a.set_scaled_positions(
            ((0.0,0.0,0.0),
             (0.5,0.5,0.5),
             (0.5,0.5,0.0),
             (0.5,0.0,0.5),
             (0.0,0.5,0.5),
             )
            )

        a.set_chemical_symbols(['Ba','Ti','O','O','O'])
        val = export_values(StructureData(ase=a),reduce_symmetry=True,store=True)['0']
        self.assertEqual(val['_atom_site_label'],['Ba1','Ti1','O1'])
        self.assertEqual(val['_symmetry_space_group_name_H-M'],'Pm-3m')
        self.assertEqual(val['_symmetry_space_group_name_Hall'],'-P 4 2 3')

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

        self.assertEqual(options,{})

        parser = argparse.ArgumentParser()
        deposition_cmdline_parameters(parser)
        options = vars(parser.parse_args(args=[]))

        for key in options.keys():
            if options[key] is None:
                options.pop(key)

        self.assertEqual(options,{})

    @unittest.skipIf(not has_ase() or not has_pycifrw(),
                     "Unable to import ase or pycifrw")
    def test_export_trajectory(self):
        from aiida.orm.data.structure import StructureData
        from aiida.orm.data.array.trajectory import TrajectoryData
        from aiida.tools.dbexporters.tcod import export_values

        cells = [
            [[2.,0.,0.,],
             [0.,2.,0.,],
             [0.,0.,2.,]],
            [[3.,0.,0.,],
             [0.,3.,0.,],
             [0.,0.,3.,]]
        ]
        symbols = [['H', 'O', 'C'], ['H', 'O', 'C']]
        positions = [
            [[0.,0.,0.],
             [0.5,0.5,0.5],
             [1.5,1.5,1.5]],
            [[0.,0.,0.],
             [0.75,0.75,0.75],
             [1.25,1.25,1.25]]
        ]
        structurelist = []
        for i in range(0,2):
            struct = StructureData(cell=cells[i])
            for j,symbol in enumerate(symbols[i]):
                struct.append_atom(symbols=symbol,position=positions[i][j])
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
            '_cell_formula_units_Z',
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
        v = export_values(td,trajectory_index=1)
        self.assertEqual(sorted(v['0'].keys()),expected_tags)

        # Stored, but not expected to be stored:
        td = TrajectoryData(structurelist=structurelist)
        td.store()
        v = export_values(td,trajectory_index=1)
        self.assertEqual(sorted(v['0'].keys()),
                         expected_tags+tcod_file_tags)

        # Not stored, but expected to be stored:
        td = TrajectoryData(structurelist=structurelist)
        v = export_values(td,trajectory_index=1,store=True)
        self.assertEqual(sorted(v['0'].keys()),
                         expected_tags+tcod_file_tags)

        # Both stored and expected to be stored:
        td = TrajectoryData(structurelist=structurelist)
        td.store()
        v = export_values(td,trajectory_index=1,store=True)
        self.assertEqual(sorted(v['0'].keys()),
                         expected_tags+tcod_file_tags)

        # Stored, but asked not to include DB dump:
        td = TrajectoryData(structurelist=structurelist)
        td.store()
        v = export_values(td,trajectory_index=1,
                          dump_aiida_database=False)
        self.assertEqual(sorted(v['0'].keys()),
                         expected_tags)
