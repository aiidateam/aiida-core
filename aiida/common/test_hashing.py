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
import itertools
import collections
import uuid
from datetime import datetime

import numpy as np

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from aiida.common.hashing import make_hash, create_unusable_pass, is_password_usable
from aiida.common.folders import SandboxFolder


class PasswordFunctions(unittest.TestCase):
    """
    Tests for the password hashing functions.
    """

    def test_unusable_password(self):
        self.assertTrue(create_unusable_pass().startswith('!'))
        self.assertTrue(len(create_unusable_pass()) > 20)

    def test_is_usable(self):
        self.assertFalse(is_password_usable(None))
        self.assertFalse(is_password_usable('!foo'))
        self.assertFalse(is_password_usable('random string without hash identification'))


class MakeHashTest(unittest.TestCase):
    """
    Tests for the make_hash function.
    """

    # pylint: disable=missing-docstring,too-few-public-methods

    def test_builtin_types(self):
        test_data = {
            'something in ASCII': '06e87857590c91280d25e02f05637cd2381002bd1425dff3e36ca860bbb26a29',
            42: '9498ab55b7c66c66b2d19f9dd8b668acf8e2facf44da0fb466f6986999bb8a56',
            3.141: 'd00f2e88a088626f5db3eadb6d9d40c74b4b4d3f9f07c1ca2f76b247fe39530b',
            complex(1, 2): '31800fbabb47c8fbf60c848571ee25e7dcbdfc5dfb60c1e8421c1c363a80ea6a',
            True: '31ad5fa163a0c478d966c7f7568f3248f0c58d294372b2e8f7cb0560d8c8b12f',
            None: '1729486cc7e56a6383542b1ec73125ccb26093651a5da05e04657ac416a74b8f',
        }

        for val, digest in test_data.items():
            with self.subTest(val=val):
                self.assertEqual(make_hash(val), digest)

    def test_unicode_string(self):
        self.assertEqual(
            make_hash(u'something still in ASCII'), 'd55e492596cf214d877e165cdc3394f27e82e011838474f5ba5b9824074b9e91')

        self.assertEqual(
            make_hash(u"öpis mit Umluut wie ä, ö, ü und emene ß"),
            'c404bf9a62cba3518de5c2bae8c67010aff6e4051cce565fa247a7f1d71f1fc7')

    def test_collection_with_ordered_sets(self):
        self.assertEqual(make_hash((1, 2, 3)), '27e6598a3bd1c878ca09db22f4d93ebcb1a0e08db27e09c737e7f2e698dcce5b')
        self.assertEqual(make_hash([1, 2, 3]), '27e6598a3bd1c878ca09db22f4d93ebcb1a0e08db27e09c737e7f2e698dcce5b')

        for perm in itertools.permutations([1, 2, 3]):
            with self.subTest(orig=[1, 2, 3], perm=perm):
                self.assertNotEqual(make_hash(perm), make_hash({1, 2, 3}))

    def test_collection_with_unordered_sets(self):
        self.assertEqual(make_hash({1, 2, 3}), '2e096a4b81ab724c2250835fc2fef7d932a7a86deafe1fb584ff329adcc34e0f')
        self.assertEqual(make_hash({1, 2, 3}), make_hash({2, 1, 3}))

    def test_collection_with_dicts(self):
        self.assertEqual(
            make_hash({
                'a': 'b',
                'c': 'd'
            }), '1890162a70dbbcbef2d0cc40b9bd90463459f2e7e72573628e7f1c003ca25c95')

        # order changes in dictionaries should give the same hashes
        self.assertEqual(
            make_hash(collections.OrderedDict([('c', 'd'), ('a', 'b')])),
            make_hash(collections.OrderedDict([('a', 'b'), ('c', 'd')])))

    def test_nested_collections(self):
        obj_a = collections.OrderedDict([
            ('3', 4),
            (3, 4),
            ('a', {
                '1': 'hello',
                2: 'goodbye',
                1: 'here',
            }),
            ('b', 4),
            ('c', set([2, '5', 'a', 'b', 5])),
        ])

        obj_b = collections.OrderedDict([('c', set([2, 'b', 5, 'a', '5'])), ('b', 4), ('a', {
            2: 'goodbye',
            1: 'here',
            '1': 'hello',
        }), ('3', 4), (3, 4)])

        self.assertEqual(make_hash(obj_a), 'e6cd3e2e7f540793a91330776a16e8908d6fe4db0d7d01fd592195f92bffe2b9')
        self.assertEqual(make_hash(obj_a), make_hash(obj_b))

    def test_bytes(self):
        self.assertEqual(make_hash(b'foo'), '814a149f7569f1009b24670adfdc8a1edddb4759e2d7da85cd00386facfaebb2')

    def test_uuid(self):
        some_uuid = uuid.UUID('62c42d58-56e8-4ade-9d5e-18de3a7baacd')

        self.assertEqual(make_hash(some_uuid), '3df6ae6dd5930e4cf8b22de123e5ac4f004f63ab396dff6225e656acc42dcf6f')
        self.assertNotEqual(make_hash(some_uuid), make_hash(str(some_uuid)))

    def test_datetime(self):
        self.assertEqual(
            make_hash(datetime(2018, 8, 18, 8, 18)), 'c5ba00262f54deb718601b44dea01765ce009fd08f31967f2e65b7050b036426')
        self.assertEqual(
            make_hash(datetime.utcfromtimestamp(0)), 'a4de78590a7a290f0446f15c68639f5be3a4dde9140606cf6edcdcfc6bb8b5b0')

    def test_numpy_types(self):
        self.assertEqual(
            make_hash(np.float64(3.141)), 'd00f2e88a088626f5db3eadb6d9d40c74b4b4d3f9f07c1ca2f76b247fe39530b')  # pylint: disable=no-member
        self.assertEqual(make_hash(np.int64(42)), '3369413755ea6c01984a21d01fe231fab8dfde02787ba5d9c1527b08778acc12')  # pylint: disable=no-member

    def test_numpy_arrays(self):
        self.assertEqual(
            make_hash(np.array([1, 2, 3])), '8735e6439da0bd6949e97c7da08774fef2407dccef5e87bf569303e683c838ae')
        self.assertEqual(
            make_hash(np.array([np.float64(3.141)])),
            'e03f2b6485f7a6ba0a2767c69724a1f5a9f73b8c36f5413d660f85631b4b562d')  # pylint: disable=no-member
        self.assertEqual(
            make_hash(np.array([np.complex128(1 + 2j)])),
            'c8dab6e4d3f3904c90f2bb7a7f5ea84e36b6f0b8ad311e681dcd1863a7fdbb77')  # pylint: disable=no-member

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

            folder_hash = make_hash(folder)
            self.assertEqual(folder_hash, '5a4f4a762f6e6be02baca1922a4bb82fe8d9665c3ee356acbd141326adff0e0d')

            nested_obj = ['1.0.0a2', {u'array|a': [1001]}, folder, None]
            self.assertEqual(make_hash(nested_obj), '70a831e02a5d26985cab4a83e45bef439b2fbc771900f23362a91631d545d621')

            with folder.open('file3.npy', 'wb') as fhandle:
                np.save(fhandle, np.arange(10))

            # after adding a file, the folder hash should have changed
            self.assertNotEqual(make_hash(folder), folder_hash)
            # ... unless we explicitly tell it to ignore the new file
            self.assertEqual(make_hash(folder, ignored_folder_content='file3.npy'), folder_hash)

            subfolder = folder.get_subfolder("some_subdir", create=True)

            with subfolder.open('file4.npy', 'wb') as fhandle:
                np.save(fhandle, np.arange(5))

            self.assertNotEqual(make_hash(folder), folder_hash)
            self.assertEqual(make_hash(folder, ignored_folder_content=['file3.npy', 'some_subdir']), folder_hash)
