###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Unittests for aiida.common.hashing:make_hash with hardcoded hash values"""

import collections
import hashlib
import itertools
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import numpy as np
import pytest

from aiida.common.exceptions import HashingError
from aiida.common.folders import SandboxFolder
from aiida.common.hashing import chunked_file_hash, float_to_text, make_hash
from aiida.common.timezone import timezone_from_name
from aiida.common.utils import DatetimePrecision
from aiida.orm import Dict


class TestFloatToTextTest:
    """Tests for the float_to_text methods"""

    def test_subnormal(self):
        assert float_to_text(-0.00, sig=2) == '0'  # 0 is always printed as '0'
        assert float_to_text(3.555, sig=2) == '3.6'
        assert float_to_text(3.555, sig=3) == '3.56'
        assert float_to_text(3.141592653589793238462643383279502884197, sig=14) == '3.1415926535898'


@pytest.mark.parametrize(
    'value,digest',
    [
        ('something in ASCII', '06e87857590c91280d25e02f05637cd2381002bd1425dff3e36ca860bbb26a29'),
        (42, '9468692328de958d7a8039e8a2eb05cd6888b7911bbc3794d0dfebd8df3482cd'),
        (3.141, 'b3302aad550413e14fe44d5ead10b3aeda9884055fca77f9368c48517916d4be'),
        (complex(1, 2), '287c6bb18d4fb00fd5f3a6fb6931a85cd8ae4b1f43be4707a76964fbc322872e'),
        (True, '31ad5fa163a0c478d966c7f7568f3248f0c58d294372b2e8f7cb0560d8c8b12f'),
        (None, '1729486cc7e56a6383542b1ec73125ccb26093651a5da05e04657ac416a74b8f'),
    ],
)
def test_builtin_types(value, digest):
    assert make_hash(value) == digest


class TestMakeHashTest:
    """Tests for the make_hash function."""

    def test_unicode_string(self):
        assert (
            make_hash('something still in ASCII') == 'd55e492596cf214d877e165cdc3394f27e82e011838474f5ba5b9824074b9e91'
        )

        assert (
            make_hash('öpis mit Umluut wie ä, ö, ü und emene ß')
            == 'c404bf9a62cba3518de5c2bae8c67010aff6e4051cce565fa247a7f1d71f1fc7'
        )

    def test_collection_with_ordered_sets(self):
        assert make_hash((1, 2, 3)) == 'b6b13d50e3bee7e58371af2b303f629edf32d1be2f7717c9d14193b4b8b23e04'
        assert make_hash([1, 2, 3]) == 'b6b13d50e3bee7e58371af2b303f629edf32d1be2f7717c9d14193b4b8b23e04'

        for perm in itertools.permutations([1, 2, 3]):
            assert make_hash(perm) != make_hash({1, 2, 3})

    def test_collisions_with_nested_objs(self):
        assert make_hash([[1, 2], 3]) != make_hash([[1, 2, 3]])
        assert make_hash({1, 2}) != make_hash({1: 2})

    def test_collection_with_unordered_sets(self):
        assert make_hash({1, 2, 3}) == 'a11cff8e62b57e1aefb7de908bd50096816b66796eb7e11ad78edeaf2629f89c'
        assert make_hash({1, 2, 3}) == make_hash({2, 1, 3})

    def test_collection_with_dicts(self):
        assert make_hash({'a': 'b', 'c': 'd'}) == '656ef313d44684c44977b0c75f48f27a43686c63ae44c8778ea0fe05f629b3b9'

        # order changes in dictionaries should give the same hashes
        assert make_hash(collections.OrderedDict([('c', 'd'), ('a', 'b')]), odict_as_unordered=True) == make_hash(
            collections.OrderedDict([('a', 'b'), ('c', 'd')]), odict_as_unordered=True
        )

    def test_collection_with_odicts(self):
        # ordered dicts should always give a different hash (because they are a different type), unless told otherwise:
        assert make_hash(collections.OrderedDict([('a', 'b'), ('c', 'd')])) != make_hash(dict([('a', 'b'), ('c', 'd')]))
        assert make_hash(collections.OrderedDict([('a', 'b'), ('c', 'd')]), odict_as_unordered=True) == make_hash(
            dict([('a', 'b'), ('c', 'd')])
        )

    def test_nested_collections(self):
        obj_a = collections.OrderedDict(
            [
                ('3', 4),
                (3, 4),
                (
                    'a',
                    {
                        '1': 'hello',
                        2: 'goodbye',
                        1: 'here',
                    },
                ),
                ('b', 4),
                ('c', set([2, '5', 'a', 'b', 5])),
            ]
        )

        obj_b = collections.OrderedDict(
            [
                ('c', set([2, 'b', 5, 'a', '5'])),
                ('b', 4),
                (
                    'a',
                    {
                        2: 'goodbye',
                        1: 'here',
                        '1': 'hello',
                    },
                ),
                ('3', 4),
                (3, 4),
            ]
        )

        assert (
            make_hash(obj_a, odict_as_unordered=True)
            == 'e27bf6081c23afcb3db0ee3a24a64c73171c062c7f227fecc7f17189996add44'
        )
        assert make_hash(obj_a, odict_as_unordered=True) == make_hash(obj_b, odict_as_unordered=True)

    def test_bytes(self):
        assert make_hash(b'foo') == '459062c44082269b2d07f78c1b6e8c98b93448606bfb1cc1f48284cdfcea74e3'

    def test_uuid(self):
        some_uuid = uuid.UUID('62c42d58-56e8-4ade-9d5e-18de3a7baacd')

        assert make_hash(some_uuid) == '3df6ae6dd5930e4cf8b22de123e5ac4f004f63ab396dff6225e656acc42dcf6f'
        assert make_hash(some_uuid) != make_hash(str(some_uuid))

    def test_datetime(self):
        # test for timezone-naive datetime:
        assert (
            make_hash(datetime(2018, 8, 18, 8, 18))
            == '714138f1114daa5fdc74c3483260742952b71b568d634c6093bb838afad76646'
        )
        assert (
            make_hash(datetime.fromtimestamp(0, timezone.utc))
            == 'b4d97d9d486937775bcc25a5cba073f048348c3cd93d4460174a4f72a6feb285'
        )

        # test with timezone-aware datetime:
        assert (
            make_hash(datetime(2018, 8, 18, 8, 18).replace(tzinfo=timezone_from_name('US/Eastern')))
            == '194478834b3b8bd0518cf6ca6fefacc13bea15f9c0b8f5d585a0adf2ebbd562f'
        )
        assert (
            make_hash(datetime(2018, 8, 18, 8, 18).replace(tzinfo=timezone_from_name('Europe/Amsterdam')))
            == 'be7c7c7faaff07d796db4cbef4d3d07ed29fdfd4a38c9aded00a4c2da2b89b9c'
        )

    def test_datetime_precision_hashing(self):
        dt_prec = DatetimePrecision(datetime(2018, 8, 18, 8, 18), 10)
        assert make_hash(dt_prec) == '837ab70b3b7bd04c1718834a0394a2230d81242c442e4aa088abeab15622df37'
        dt_prec_utc = DatetimePrecision(datetime.fromtimestamp(0, timezone.utc), 0)
        assert make_hash(dt_prec_utc) == '8c756ee99eaf9655bb00166839b9d40aa44eac97684b28f6e3c07d4331ae644e'

    def test_numpy_types(self):
        assert make_hash(np.float64(3.141)) == 'b3302aad550413e14fe44d5ead10b3aeda9884055fca77f9368c48517916d4be'
        assert make_hash(np.int64(42)) == '9468692328de958d7a8039e8a2eb05cd6888b7911bbc3794d0dfebd8df3482cd'

    def test_decimal(self):
        assert make_hash(Decimal('3.141')) == 'b3302aad550413e14fe44d5ead10b3aeda9884055fca77f9368c48517916d4be'

        # make sure we get the same hashes as for corresponding float or int
        assert make_hash(Decimal('3.141')) == make_hash(3.141)

        assert make_hash(Decimal('3.')) == make_hash(3)

        assert make_hash(Decimal('3141')) == make_hash(3141)

        assert make_hash(Decimal('NaN')) == make_hash('NaN')
        assert make_hash(Decimal('Inf')) == make_hash('Infinity')
        assert make_hash(Decimal('-Inf')) == make_hash('-Infinity')

    def test_unhashable_type(self):
        class MadeupClass:
            pass

        with pytest.raises(HashingError):
            make_hash(MadeupClass())

    def test_folder(self):
        # create directories for the Folder test
        with SandboxFolder() as folder:
            with folder.open('file1', 'a') as handle:
                pass
            with folder.open('file2', 'w') as handle:
                handle.write('hello there!\n')

            folder_hash = make_hash(folder)
            assert folder_hash == '47d9cdb2247e75eca492035f60f09fdd0daf87bbba40bb658d2d7e84f21f26c5'

            nested_obj = ['1.0.0a2', {'array|a': [1001]}, folder, None]
            assert make_hash(nested_obj) == 'd3e7ff24708bc60b75a01571454ac0a664fa94ff2145848b584fb9ecc7e4fcbe'

            with folder.open('file3.npy', 'wb') as fhandle:
                np.save(fhandle, np.arange(10))

            # after adding a file, the folder hash should have changed
            assert make_hash(folder) != folder_hash
            # ... unless we explicitly tell it to ignore the new file
            assert make_hash(folder, ignored_folder_content='file3.npy') == folder_hash

            subfolder = folder.get_subfolder('some_subdir', create=True)

            with subfolder.open('file4.npy', 'wb') as fhandle:
                np.save(fhandle, np.arange(5))

            assert make_hash(folder) != folder_hash
            assert make_hash(folder, ignored_folder_content=['file3.npy', 'some_subdir']) == folder_hash


class TestCheckDBRoundTrip:
    """Check that the hash does not change after a roundtrip via the DB."""

    @staticmethod
    def test_attribute_storing():
        """I test that when storing different types of data as attributes (using a dict), the hash is the
        same before and after storing.
        """
        test_data = [
            'something in ASCII',
            42,
            3.14134253423433432343,
            7.53234432423942204222,
            7.27592016903727508353,
            -3.832844830976837684,
            -0.0046930852371537838,
            3.535434503274892738e-30,
            True,
            False,
            None,
            np.array([1.0, 2.0, 3.2]),  # This will be converted to a list internally by clean_value
            ['a', True, 4.322],
            {'a': 33, 'b': 6.433453},
        ]
        # This will run across the edge where floats become integer (see discussion in the clean_value function),
        # they should so something like:
        # 9.5e+13, 9.6e+13, 9.7e+13, 9.8e+13, 9.9e+13, 100000000000000, 101000000000000, 102000000000000,
        # 103000000000000, 104000000000000
        for i in range(10):
            test_data.append(9.5e13 + 1.0e12 * i)

        for val in test_data:
            node = Dict(dict={'data': val})
            node.store()
            first_hash = node.base.extras.get('_aiida_hash')
            recomputed_hash = node.base.caching.get_hash()

            assert first_hash == recomputed_hash


def test_chunked_file_hash(tmp_path):
    """Test the ``chunked_file_hash`` function."""
    (tmp_path / 'afile').write_bytes(b'content')
    with (tmp_path / 'afile').open('rb') as handle:
        key = chunked_file_hash(handle, hashlib.sha256)
    assert key == 'ed7002b439e9ac845f22357d822bac1444730fbdb6016d3ec9432297b9ec9f73'
