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
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import unittest

from six.moves import range

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.common.links import LinkType


class TestTcodDbExporter(AiidaTestCase):
    """Tests for TcodDbExporter class."""
    from aiida.orm.nodes.data.structure import has_ase, has_spglib
    from aiida.orm.nodes.data.cif import has_pycifrw

    def test_contents_encoding_1(self):
        """
        Testing the logic of choosing the encoding and the process of
        encoding contents.
        """
        from aiida.tools.dbexporters.tcod import cif_encode_contents
        self.assertEquals(cif_encode_contents(b'simple line')[1],
                          None)
        self.assertEquals(cif_encode_contents(b' ;\n ;')[1],
                          None)
        self.assertEquals(cif_encode_contents(b';\n'),
                          (b'=3B\n', 'quoted-printable'))
        self.assertEquals(cif_encode_contents(b'line\n;line'),
                          (b'line\n=3Bline', 'quoted-printable'))
        self.assertEquals(cif_encode_contents(b'tabbed\ttext'),
                          (b'tabbed=09text', 'quoted-printable'))

        # Angstrom symbol 'Å' will be encoded as two bytes, thus encoding it
        # for CIF will produce two quoted-printable entities, '=C3' and '=85',
        # one for each byte.

        self.assertEquals(cif_encode_contents(u'angstrom Å'.encode('utf-8')),
                          (b'angstrom =C3=85', 'quoted-printable'))
        self.assertEquals(cif_encode_contents(b'.'),
                          (b'=2E', 'quoted-printable'))
        self.assertEquals(cif_encode_contents(b'?'),
                          (b'=3F', 'quoted-printable'))
        self.assertEquals(cif_encode_contents(b'.?'), (b'.?', None))
        # This one is particularly tricky: a long line is folded by the QP
        # and the semicolon sign becomes the first character on a new line.
        self.assertEquals(cif_encode_contents(
            u"Å{};a".format("".join("a" for i in range(0, 69))).encode('utf-8')),
            (b'=C3=85aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
             b'aaaaaaaaaaaaaaaaaaaaaaaaaaaaa=\n=3Ba',
             'quoted-printable'))
        self.assertEquals(cif_encode_contents(u'angstrom ÅÅÅ'.encode('utf-8')),
                          (b'YW5nc3Ryb20gw4XDhcOF', 'base64'))
        self.assertEquals(cif_encode_contents(
            "".join("a" for i in range(0, 2048)).encode('utf-8'))[1], None)
        self.assertEquals(cif_encode_contents(
            "".join("a" for i in range(0, 2049)).encode('utf-8'))[1], 'quoted-printable')
        self.assertEquals(cif_encode_contents(b'datatest')[1], None)
        self.assertEquals(cif_encode_contents(b'data_test')[1], 'base64')

    def test_collect_files(self):
        """Testing the collection of files from file tree."""
        from aiida.tools.dbexporters.tcod import _collect_files
        from aiida.common.folders import SandboxFolder
        from six.moves import StringIO as StringIO

        sf = SandboxFolder()
        sf.get_subfolder('out', create=True)
        sf.get_subfolder('pseudo', create=True)
        sf.get_subfolder('save', create=True)
        sf.get_subfolder('save/1', create=True)
        sf.get_subfolder('save/2', create=True)

        f = StringIO(u"test")
        sf.create_file_from_filelike(f, 'aiida.in', mode='w')
        f = StringIO(u"test")
        sf.create_file_from_filelike(f, 'aiida.out', mode='w')
        f = StringIO(u"test")
        sf.create_file_from_filelike(f, '_aiidasubmit.sh', mode='w')
        f = StringIO(u"test")
        sf.create_file_from_filelike(f, '_.out', mode='w')
        f = StringIO(u"test")
        sf.create_file_from_filelike(f, 'out/out', mode='w')
        f = StringIO(u"test")
        sf.create_file_from_filelike(f, 'save/1/log.log', mode='w')

        md5 = '098f6bcd4621d373cade4e832627b4f6'
        sha1 = 'a94a8fe5ccb19ba61c4c0873d391e987982fbbd3'
        self.assertEquals(
            _collect_files(sf.abspath),
            [{'name': '_.out', 'contents': b'test', 'md5': md5,
              'sha1': sha1, 'type': 'file'},
             {'name': '_aiidasubmit.sh', 'contents': b'test', 'md5': md5,
              'sha1': sha1, 'type': 'file'},
             {'name': 'aiida.in', 'contents': b'test', 'md5': md5,
              'sha1': sha1, 'type': 'file'},
             {'name': 'aiida.out', 'contents': b'test', 'md5': md5,
              'sha1': sha1, 'type': 'file'},
             {'name': 'out/', 'type': 'folder'},
             {'name': 'out/out', 'contents': b'test', 'md5': md5,
              'sha1': sha1, 'type': 'file'},
             {'name': 'pseudo/', 'type': 'folder'},
             {'name': 'save/', 'type': 'folder'},
             {'name': 'save/1/', 'type': 'folder'},
             {'name': 'save/1/log.log', 'contents': b'test', 'md5': md5,
              'sha1': sha1, 'type': 'file'},
             {'name': 'save/2/', 'type': 'folder'}])

    @unittest.skipIf(not has_ase(), "Unable to import ase")
    @unittest.skipIf(not has_spglib(), "Unable to import spglib")
    @unittest.skipIf(not has_pycifrw(), "Unable to import PyCifRW")
    def test_cif_structure_roundtrip(self):
        from aiida.tools.dbexporters.tcod import export_cif, export_values
        from aiida.common.folders import SandboxFolder
        import tempfile

        with tempfile.NamedTemporaryFile(mode='w+') as tmpf:
            tmpf.write('''
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
            tmpf.flush()
            a = orm.CifData(filepath=tmpf.name)

        c = a.get_structure()
        c.store()
        pd = orm.Dict()

        code = orm.Code(local_executable='test.sh')
        with tempfile.NamedTemporaryFile(mode='w+') as tmpf:
            tmpf.write("#/bin/bash\n\necho test run\n")
            tmpf.flush()
            code.put_object_from_filelike(tmpf, 'test.sh')

        code.store()

        calc = orm.CalcJobNode(computer=self.computer)
        calc.set_option('resources', {'num_machines': 1,
                            'num_mpiprocs_per_machine': 1})
        calc.add_incoming(code, LinkType.INPUT_CALC, "code")
        calc.set_option('environment_variables', {'PATH': '/dev/null', 'USER': 'unknown'})

        with tempfile.NamedTemporaryFile(mode='w+', prefix="Fe") as tmpf:
            tmpf.write("<UPF version=\"2.0.1\">\nelement=\"Fe\"\n")
            tmpf.flush()
            upf = orm.UpfData(filepath=tmpf.name)
            upf.store()
            calc.add_incoming(upf, LinkType.INPUT_CALC, "upf")

        with tempfile.NamedTemporaryFile(mode='w+') as tmpf:
            tmpf.write("data_test")
            tmpf.flush()
            cif = orm.CifData(filepath=tmpf.name)
            cif.store()
            calc.add_incoming(cif, LinkType.INPUT_CALC, "cif")

        with SandboxFolder() as fhandle:
            calc.put_object_from_tree(fhandle.abspath)
        calc.store()

        fd = orm.FolderData()
        with fd.open('_scheduler-stdout.txt', 'w') as fhandle:
            fhandle.write(u"standard output")

        with fd.open('_scheduler-stderr.txt', 'w') as fhandle:
            fhandle.write(u"standard error")

        fd.store()
        fd.add_incoming(calc, LinkType.CREATE, calc.link_label_retrieved)

        pd.add_incoming(calc, LinkType.CREATE, "create1")
        pd.store()

        with self.assertRaises(ValueError):
            export_cif(c, parameters=pd)

        c.add_incoming(calc, LinkType.CREATE, "create2")
        export_cif(c, parameters=pd)

        values = export_values(c, parameters=pd)
        values = values['0']

        self.assertEquals(values['_tcod_computation_environment'],
                          ['PATH=/dev/null\nUSER=unknown'])
        self.assertEquals(values['_tcod_computation_command'],
                          ['cd 1; ./_aiidasubmit.sh'])

    @unittest.skipIf(not has_ase(), "Unable to import ase")
    @unittest.skipIf(not has_spglib(), "Unable to import spglib")
    @unittest.skipIf(not has_pycifrw(), "Unable to import PyCifRW")
    def test_inline_export(self):
        from aiida.tools.dbexporters.tcod import export_values
        import tempfile

        with tempfile.NamedTemporaryFile(mode='w+') as tmpf:
            tmpf.write('''
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
            tmpf.flush()
            a = orm.CifData(filepath=tmpf.name)

        s = a.get_structure(store=True)
        val = export_values(s)
        script = val.first_block()['_tcod_file_contents'][1]
        function = '_get_aiida_structure_pymatgen_inline'
        self.assertNotEqual(script.find(function), script.rfind(function))

    @unittest.skipIf(not has_ase(), "Unable to import ase")
    @unittest.skipIf(not has_spglib(), "Unable to import spglib")
    @unittest.skipIf(not has_pycifrw(), "Unable to import PyCifRW")
    def test_symmetry_reduction(self):
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
        val = export_values(orm.StructureData(ase=a), reduce_symmetry=True, store=True)['0']
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

        options = {k: v for k, v in options.items() if v is not None}

        self.assertEqual(options, {})

        parser = argparse.ArgumentParser()
        deposition_cmdline_parameters(parser)
        options = vars(parser.parse_args(args=[]))

        options = {k: v for k, v in options.items() if v is not None}

        self.assertEqual(options, {})

    @unittest.skipIf(not has_ase(), "Unable to import ase")
    @unittest.skipIf(not has_spglib(), "Unable to import spglib")
    @unittest.skipIf(not has_pycifrw(), "Unable to import PyCifRW")
    def test_export_trajectory(self):
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
            struct = orm.StructureData(cell=cells[i])
            for j, symbol in enumerate(symbols[i]):
                struct.append_atom(symbols=symbol, position=positions[i][j])
            structurelist.append(struct)

        td = orm.TrajectoryData(structurelist=structurelist)

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
            '_symmetry_equiv_pos_as_xyz',
            '_symmetry_int_tables_number',
            '_symmetry_space_group_name_h-m',
            '_symmetry_space_group_name_hall'
        ]

        tcod_file_tags = [
            '_tcod_content_encoding_id',
            '_tcod_content_encoding_layer_id',
            '_tcod_content_encoding_layer_type',
            '_tcod_file_content_encoding',
            '_tcod_file_contents',
            '_tcod_file_id',
            '_tcod_file_md5sum',
            '_tcod_file_name',
            '_tcod_file_role',
            '_tcod_file_sha1sum',
            '_tcod_file_uri',
        ]

        # Not stored and not to be stored:
        v = export_values(td, trajectory_index=1)
        self.assertEqual(sorted(v['0'].keys()), expected_tags)

        # Stored, but not expected to be stored:
        td = orm.TrajectoryData(structurelist=structurelist)
        td.store()
        v = export_values(td, trajectory_index=1)
        self.assertEqual(sorted(v['0'].keys()),
                         expected_tags + tcod_file_tags)

        # Not stored, but expected to be stored:
        td = orm.TrajectoryData(structurelist=structurelist)
        v = export_values(td, trajectory_index=1, store=True)
        self.assertEqual(sorted(v['0'].keys()),
                         expected_tags + tcod_file_tags)

        # Both stored and expected to be stored:
        td = orm.TrajectoryData(structurelist=structurelist)
        td.store()
        v = export_values(td, trajectory_index=1, store=True)
        self.assertEqual(sorted(v['0'].keys()),
                         expected_tags + tcod_file_tags)

        # Stored, but asked not to include DB dump:
        td = orm.TrajectoryData(structurelist=structurelist)
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

        check_ncr(self, b'.', b'&#46;')
        check_ncr(self, b'?', b'&#63;')
        check_ncr(self, b';\n', b'&#59;\n')
        check_ncr(self, b'line\n;line', b'line\n&#59;line')
        check_ncr(self, b'tabbed\ttext', b'tabbed&#9;text')
        # Angstrom symbol 'Å' will be encoded as two bytes, thus encoding it
        # for CIF will produce two NCR entities, '&#195;' and '&#133;', one for
        # each byte.
        check_ncr(self, u'angstrom Å'.encode('utf-8'), b'angstrom &#195;&#133;')
        check_ncr(self, b'<html>&#195;&#133;</html>',
                 b'<html>&#38;#195;&#38;#133;</html>')

        check_quoted_printable(self, b'.', b'=2E')
        check_quoted_printable(self, b'?', b'=3F')
        check_quoted_printable(self, b';\n', b'=3B\n')
        check_quoted_printable(self, b'line\n;line', b'line\n=3Bline')
        check_quoted_printable(self, b'tabbed\ttext', b'tabbed=09text')
        # Angstrom symbol 'Å' will be encoded as two bytes, thus encoding it
        # for CIF will produce two quoted-printable entities, '=C3' and '=85',
        # one for each byte.
        check_quoted_printable(self, u'angstrom Å'.encode('utf-8'), b'angstrom =C3=85')
        check_quoted_printable(self, b'line\rline\x00', b'line=0Dline=00')
        # This one is particularly tricky: a long line is folded by the QP
        # and the semicolon sign becomes the first character on a new line.
        check_quoted_printable(self,
                              u"Å{};a".format("".join("a" for i in range(0, 69))).encode('utf-8'),
                              b'=C3=85aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
                              b'aaaaaaaaaaaaaaaaaaaaaaaaaaaaa=\n=3Ba')

        check_base64(self, u'angstrom ÅÅÅ'.encode('utf-8'), b'YW5nc3Ryb20gw4XDhcOF')
        check_gzip_base64(self, u'angstrom ÅÅÅ'.encode('utf-8'))
