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
Unittests for aiida.common.hashing:make_hash with hardcoded hash values
"""

from __future__ import absolute_import
import unittest
from datetime import datetime

import six
import numpy as np

from aiida.common.hashing import make_hash
from aiida.common.folders import SandboxFolder


class MakeHashTest(unittest.TestCase):
    """
    Tests for the make_hash function.
    """

    # pylint: disable=missing-docstring,too-few-public-methods

    def test_builtin_types(self):
        self.assertEqual(make_hash('something in ASCII'), '82c78710eebc41c0f0684e817944d6f08e54be54a279f9fc263f8403')
        self.assertEqual(make_hash(42), 'f7d4da96058de015a3a6f6b98cff45a80a2852fe721b0d06a2627944')
        self.assertEqual(make_hash(3.141), '2086094b3fbadc66b71c38281fc079d7c3978e74eb28ca7f3b966371')
        self.assertEqual(make_hash(complex(1, 2)), '59975775040ab3a41ca969fc360f0ff1b1663d64046005a6ee68bf7b')
        self.assertEqual(make_hash(True), '15ca7d7468e8aa86ea3db945ae856d783e2f92056550a50cb96fe7fd')
        self.assertEqual(make_hash(None), '9a5b682a9a6a99a1d2ce4353d52062d511d418af058679d1b9b97570')

    def test_unicode_string(self):
        self.assertEqual(
            make_hash(u'something still in ASCII'), '753df9fb179504652f66dd15877d393a743cbfe31d6bf6a9faed7e37')
        # current implementation fails with real unicode:
        # self.assertEqual(make_hash(u'öpis mit Umluut wie ä, ö, ü und emene ß 😊'), '')

    def test_collection_with_builtin_types(self):
        self.assertEqual(make_hash((1, 2, 3)), 'ccbd4c0c83df304a4d8fa1cb4d556f370d8d09c03b49cd069fd72598')
        self.assertEqual(make_hash([1, 2, 3]), 'ccbd4c0c83df304a4d8fa1cb4d556f370d8d09c03b49cd069fd72598')
        self.assertEqual(make_hash([3, 1, 2]), '401c29a918e635ab4b384e7a0ac1d189eb857bfc3e8085fe3aaa17c2')
        self.assertEqual(make_hash({1, 2, 3}), '95467151c8099d6bef0e52588f0e651d6276fa4cad0866c710447a58')
        self.assertEqual(make_hash({'a': 'b', 'c': 'd'}), 'ee137be5e9397e30612b6628df24be4e4913c6cc4a6be5bf85509ef3')
        self.assertEqual(make_hash({'c': 'd', 'a': 'b'}), 'ee137be5e9397e30612b6628df24be4e4913c6cc4a6be5bf85509ef3')

    @unittest.skipIf(six.PY3, "Broken on Python 3")
    def test_nested_collections(self):
        obj_a = {
            '3': 4,
            3: 4,
            'a': {
                '1': 'hello',
                2: 'goodbye',
                1: 'here',
            },
            'b': 4,
            'c': set([2, '5', 'a', 'b', 5]),
        }

        obj_b = {
            'c': set([2, 'b', 5, 'a', '5']),
            'b': 4,
            'a': {
                2: 'goodbye',
                1: 'here',
                '1': 'hello',
            },
            '3': 4,
            3: 4
        }

        self.assertEqual(make_hash(obj_a), '41f1b6de377112ea0068416c00c6bb6cd2abf0133fe852fa4bb9dfbb')
        self.assertEqual(make_hash(obj_b), '41f1b6de377112ea0068416c00c6bb6cd2abf0133fe852fa4bb9dfbb')

    def test_datetime(self):
        self.assertEqual(
            make_hash(datetime(2018, 8, 18, 8, 18)), 'bc10b5f4152733191369a40dd96cb8992ac40ece6f0e59e77518f46f')
        self.assertEqual(
            make_hash(datetime.utcfromtimestamp(0)), 'aaff3b5717365f5fbf4d415ae893cda13fef1b1a28cb66f381fddea2')

    def test_numpy_types(self):
        self.assertEqual(make_hash(np.float64(3.141)), '2086094b3fbadc66b71c38281fc079d7c3978e74eb28ca7f3b966371')  # pylint: disable=no-member
        self.assertEqual(make_hash(np.int64(42)), 'f7d4da96058de015a3a6f6b98cff45a80a2852fe721b0d06a2627944')  # pylint: disable=no-member

    def test_numpy_arrays(self):
        self.assertEqual(make_hash(np.array([1, 2, 3])), '88348823a5582f72b20b9bc51221dbbf2e52adedfa949b537f41d0f3')
        self.assertEqual(
            make_hash(np.array([np.float64(3.141)])), '57a640be101799c6b70ced7aa688af6dd76f0ed75007c05a97d0af6c')  # pylint: disable=no-member
        self.assertEqual(
            make_hash(np.array([np.complex128(1 + 2j)])), 'eddf5fbcd94f8caf2b821ddd03c6bca1593d7029914c928c29ba25f4')  # pylint: disable=no-member

    def test_unhashable_type(self):

        class MadeupClass(object):
            pass

        with self.assertRaises(ValueError):
            make_hash(MadeupClass())

    def test_folder(self):
        # create directories for the Folder test
        with SandboxFolder(sandbox_in_repo=False) as folder:
            folder.open('file1', 'a').close()
            fhandle = folder.open('file2', 'w')
            fhandle.write("hello there!\n")
            fhandle.close()

            self.assertEqual(make_hash(folder), '7e09b5bc4fec5b85ef85ff1679efea2c11fa1fd9212f8cb70550627b')

            nested_obj = ['1.0.0a2', {u'array|a': [1001]}, folder, None]
            self.assertEqual(make_hash(nested_obj), 'd7e6914da5cf7bf3c1c98cab90192362d440e2c13bd4fe04cdd71bde')

            fhandle = folder.open('file3.npy', 'wb')
            np.save(fhandle, np.arange(10))
            fhandle.close()
            self.assertEqual(make_hash(folder), '18e28635210ec949097222567d0c8ecfbcd918af8721766e4aaecf73')
