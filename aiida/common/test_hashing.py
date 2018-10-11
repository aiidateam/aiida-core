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

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import unittest
import itertools
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
        self.assertEqual(make_hash('something in ASCII'), u'7ada3e803dc6b66a8151c12985b0098d4f434da422bfd0740fcef562')
        self.assertEqual(make_hash(42), u'2ab4140f3a4686f65ed84a4524bc56156e23a9e37736e273d83e99f5')
        self.assertEqual(make_hash(3.141), u'e2f8e979916f99f6002239400f41949b94eecbaefdc064ecc51f8907')
        self.assertEqual(make_hash(complex(1, 2)), u'1d819b8d8f2ae0a2033471f556b6f4dee7fa7fd4ca7bd1c0d0d2c70a')
        self.assertEqual(make_hash(True), u'40f09510111ae311ce3f2406b547adcc222f8276dfe93e9f4dfc5098')
        self.assertEqual(make_hash(None), u'2d4ca80c884a9f6dfedc579cd8072fce7918ed390bf71c1fa9fea081')

    def test_unicode_string(self):
        self.assertEqual(
            make_hash(u'something still in ASCII'), u'7cbae2b37638c56d5fe98429d5582edc3aad061e83fa1e45d754b2d6')

        self.assertEqual(
            make_hash(u"öpis mit Umluut wie ä, ö, ü und emene ß"),
            "524b0fb4e50f855046796751f9045d581f5758b0b91d59a6803c2535")

    def test_collection_with_builtin_types(self):
        self.assertEqual(make_hash((1, 2, 3)), '44d5ef36d5ae47a6e9aee5d910d148f1b63b6cdf073d11750159518f')
        self.assertEqual(make_hash([1, 2, 3]), '44d5ef36d5ae47a6e9aee5d910d148f1b63b6cdf073d11750159518f')
        self.assertEqual(make_hash([3, 1, 2]), '26e80d9e69085eca985309695732d132696c3dad6953b785e8faa963')
        self.assertEqual(make_hash({1, 2, 3}), 'd1b190427d67bc95366a44c987e34fd68aa80716c4f45500db2bc635')
        for perm in itertools.permutations([1, 2, 3]):
            self.assertNotEqual(make_hash(perm), make_hash({1, 2, 3}))
        self.assertEqual(make_hash({'a': 'b', 'c': 'd'}), 'f5a57db4d625848dba7dade0a1b64c612779bc536e3008453eb442d2')
        self.assertEqual(make_hash({'c': 'd', 'a': 'b'}), 'f5a57db4d625848dba7dade0a1b64c612779bc536e3008453eb442d2')

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

        self.assertEqual(make_hash(obj_a), '28dd36897f1fcd153c71330f843e0fb28566f6b752fcdcb7fc7e0cfe')
        self.assertEqual(make_hash(obj_b), '28dd36897f1fcd153c71330f843e0fb28566f6b752fcdcb7fc7e0cfe')

    def test_datetime(self):
        self.assertEqual(
            make_hash(datetime(2018, 8, 18, 8, 18)), 'b71d8e8cd775cc6bb61ba545e4674005515f9db212d8dcb9c779e915')
        self.assertEqual(
            make_hash(datetime.utcfromtimestamp(0)), 'b932cff36ce23f7d3a43757d34fe935d03a083134e987c022973a35e')

    def test_numpy_types(self):
        self.assertEqual(make_hash(np.float64(3.141)), 'e2f8e979916f99f6002239400f41949b94eecbaefdc064ecc51f8907')  # pylint: disable=no-member
        self.assertEqual(make_hash(np.int64(42)), '2ab4140f3a4686f65ed84a4524bc56156e23a9e37736e273d83e99f5')  # pylint: disable=no-member

    def test_numpy_arrays(self):
        self.assertEqual(make_hash(np.array([1, 2, 3])), '9b2bec0622bc5bedcb3d02c0b5b9d19bdbde36eec41be423715285df')
        self.assertEqual(
            make_hash(np.array([np.float64(3.141)])), 'e437b69603b2189abaf2fd8f2cc3d3f9fbebc537052ba3dad75e22a8')  # pylint: disable=no-member
        self.assertEqual(
            make_hash(np.array([np.complex128(1 + 2j)])), '37451dd77b55202142b5367f26830dfa751c208b4bb15da66d46200d')  # pylint: disable=no-member

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

            self.assertEqual(make_hash(folder), '6e5ddd16e397aa0a0154abde43d1f262c8b0f7ae388508221bbdd155')

            nested_obj = ['1.0.0a2', {u'array|a': [1001]}, folder, None]
            self.assertEqual(make_hash(nested_obj), '80d1905172f136615cbe1dded3131527d54dff7fd2d643adf63f3b49')

            fhandle = folder.open('file3.npy', 'wb')
            np.save(fhandle, np.arange(10))
            fhandle.close()
            self.assertEqual(make_hash(folder), '4ed5bec24a050386812e6666bfab96ffee04795ca29561e115d16bcc')
