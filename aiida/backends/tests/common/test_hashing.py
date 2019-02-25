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
import math
from datetime import datetime

import numpy as np
import pytz

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from aiida.common.hashing import make_hash, create_unusable_pass, is_password_usable, truncate_float64
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


class TruncationTest(unittest.TestCase):
    """
    Tests for the truncate_* methods
    """

    def test_nan(self):
        self.assertTrue(math.isnan(truncate_float64(np.nan)))

    def test_inf(self):
        self.assertTrue(math.isinf(truncate_float64(np.inf)))
        self.assertTrue(math.isinf(truncate_float64(-np.inf)))

    def test_subnormal(self):
        self.assertTrue(np.isclose(truncate_float64(1.0e-308), 1.0e-308, atol=1.0e-309))


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
        self.assertEqual(make_hash((1, 2, 3)), '2827844e2fb5c034967dbc69e5b8039c39705272b9969f18f5e4c4e2345ca77d')
        self.assertEqual(make_hash([1, 2, 3]), '2827844e2fb5c034967dbc69e5b8039c39705272b9969f18f5e4c4e2345ca77d')

        for perm in itertools.permutations([1, 2, 3]):
            with self.subTest(orig=[1, 2, 3], perm=perm):
                self.assertNotEqual(make_hash(perm), make_hash({1, 2, 3}))

    def test_collisions_with_nested_objs(self):
        self.assertNotEqual(make_hash([[1, 2], 3]), make_hash([[1, 2, 3]]))
        self.assertNotEqual(make_hash({1, 2}), make_hash({1: 2}))

    def test_collection_with_unordered_sets(self):
        self.assertEqual(make_hash({1, 2, 3}), '4783567a68ed025ac3dc59346ded2328d56c975e31453e3823bdda480e64b139')
        self.assertEqual(make_hash({1, 2, 3}), make_hash({2, 1, 3}))

    def test_collection_with_dicts(self):
        self.assertEqual(
            make_hash({
                'a': 'b',
                'c': 'd'
            }), '656ef313d44684c44977b0c75f48f27a43686c63ae44c8778ea0fe05f629b3b9')

        # order changes in dictionaries should give the same hashes
        self.assertEqual(
            make_hash(collections.OrderedDict([('c', 'd'), ('a', 'b')]), odict_as_unordered=True),
            make_hash(collections.OrderedDict([('a', 'b'), ('c', 'd')]), odict_as_unordered=True))

    def test_collection_with_odicts(self):
        # ordered dicts should always give a different hash (because they are a different type), unless told otherwise:
        self.assertNotEqual(
            make_hash(collections.OrderedDict([('a', 'b'), ('c', 'd')])), make_hash(dict([('a', 'b'), ('c', 'd')])))
        self.assertEqual(
            make_hash(collections.OrderedDict([('a', 'b'), ('c', 'd')]), odict_as_unordered=True),
            make_hash(dict([('a', 'b'), ('c', 'd')])))

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

        obj_b = collections.OrderedDict([('c', set([2, 'b', 5, 'a', '5'])), ('b', 4),
                                         ('a', {
                                             2: 'goodbye',
                                             1: 'here',
                                             '1': 'hello',
                                         }), ('3', 4), (3, 4)])

        self.assertEqual(
            make_hash(obj_a, odict_as_unordered=True),
            'f05e75e0713d895b4858de62ee72e75fe3acb74d2e9754f149f87615eb6e826f')
        self.assertEqual(make_hash(obj_a, odict_as_unordered=True), make_hash(obj_b, odict_as_unordered=True))

    def test_bytes(self):
        self.assertEqual(make_hash(b'foo'), '459062c44082269b2d07f78c1b6e8c98b93448606bfb1cc1f48284cdfcea74e3')

    def test_uuid(self):
        some_uuid = uuid.UUID('62c42d58-56e8-4ade-9d5e-18de3a7baacd')

        self.assertEqual(make_hash(some_uuid), '3df6ae6dd5930e4cf8b22de123e5ac4f004f63ab396dff6225e656acc42dcf6f')
        self.assertNotEqual(make_hash(some_uuid), make_hash(str(some_uuid)))

    def test_datetime(self):
        # test for timezone-naive datetime:
        self.assertEqual(
            make_hash(datetime(2018, 8, 18, 8, 18)), 'c5ba00262f54deb718601b44dea01765ce009fd08f31967f2e65b7050b036426')
        self.assertEqual(
            make_hash(datetime.utcfromtimestamp(0)), 'a4de78590a7a290f0446f15c68639f5be3a4dde9140606cf6edcdcfc6bb8b5b0')

        # test with timezone-aware datetime:
        self.assertEqual(
            make_hash(datetime(2018, 8, 18, 8, 18).replace(tzinfo=pytz.timezone('US/Eastern'))),
            '2e7cb55d2a3982bd7a509aac0cb74c7dd485a9350d55eeb944bec3e1971d8dc0')
        self.assertEqual(
            make_hash(datetime(2018, 8, 18, 8, 18).replace(tzinfo=pytz.timezone('Europe/Amsterdam'))),
            'd28a58c7af872bab9f07d2610e313bbd14de8530e62245ebc52821708883188f')

    def test_numpy_types(self):
        self.assertEqual(
            make_hash(np.float64(3.141)), 'd00f2e88a088626f5db3eadb6d9d40c74b4b4d3f9f07c1ca2f76b247fe39530b')  # pylint: disable=no-member
        self.assertEqual(make_hash(np.int64(42)), '9498ab55b7c66c66b2d19f9dd8b668acf8e2facf44da0fb466f6986999bb8a56')  # pylint: disable=no-member

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

        class MadeupClass(object):  # pylint: disable=useless-object-inheritance
            pass

        with self.assertRaises(ValueError):
            make_hash(MadeupClass())

    def test_folder(self):
        # create directories for the Folder test
        with SandboxFolder(sandbox_in_repo=False) as folder:
            folder.open('file1', 'a').close()
            fhandle = folder.open('file2', 'w')
            fhandle.write(u"hello there!\n")
            fhandle.close()

            folder_hash = make_hash(folder)
            self.assertEqual(folder_hash, '47d9cdb2247e75eca492035f60f09fdd0daf87bbba40bb658d2d7e84f21f26c5')

            nested_obj = ['1.0.0a2', {u'array|a': [1001]}, folder, None]
            self.assertEqual(make_hash(nested_obj), '3a29176b16f7a4dfb78d9ef06f882cf228a2796b762f98dda80e7dda688af201')

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
