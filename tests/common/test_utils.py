# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the aiida.common.utils functionality."""
import unittest

from aiida.common import escaping
from aiida.common import utils


class UniqueTest(unittest.TestCase):
    """
    Tests for the get_unique_filename function.
    """

    def test_unique_1(self):
        filename = 'different.txt'
        filename_list = ['file1.txt', 'file2.txt']

        self.assertEqual(filename, utils.get_unique_filename(filename, filename_list))

    def test_unique_2(self):
        filename = 'file1.txt'
        filename_list = ['file1.txt', 'file2.txt']

        self.assertEqual('file1-1.txt', utils.get_unique_filename(filename, filename_list))

    def test_unique_3(self):
        filename = 'file1.txt'
        filename_list = ['file1.txt', 'file1-1.txt']

        self.assertEqual('file1-2.txt', utils.get_unique_filename(filename, filename_list))

    def test_unique_4(self):
        filename = 'file1.txt'
        filename_list = ['file1.txt', 'file1-2.txt']

        self.assertEqual('file1-1.txt', utils.get_unique_filename(filename, filename_list))

    # The counter & the method that increments it and
    # returns its value. It is used in the tests
    seq = -1

    def array_counter(self):
        self.seq += 1
        return self.seq


class PrettifierTest(unittest.TestCase):
    """
    Tests for the Prettifier class methods.
    """

    def test_prettifier(self):
        """
        Check that the prettified strings work as expected for
        a number of different labels and different codes that should
        show them
        """
        prettifier_data = {
            'agr_seekpath': {
                'DELTA_5': r'\xD\f{}\s5\N',
            },
            'agr_simple': {
                'G': r'\xG',
                'Boo3': r'Boo\s3\N',
                'Boo99': r'Boo\s99\N',
            },
            'latex_simple': {
                'G': r'$\Gamma$',
                'Delta9': r'Delta$_{9}$',
                'Delta90': r'Delta$_{90}$',
            },
            'latex_seekpath': {
                'LAMBDA': r'$\Lambda$',
                'something_2': r'something$_{2}$',
            },
            'gnuplot_simple': {
                'G': 'Γ',
                'bla3': r'bla_{3}',
                'bla33': r'bla_{33}',
            },
            'gnuplot_seekpath': {
                'SIGMA': 'Σ',
                'bla_3': r'bla_{3}',
            },
            'pass': {
                'foo': 'foo',
            },
        }

        for prettifier_id in utils.Prettifier.get_prettifiers():
            prettifier = utils.Prettifier(prettifier_id)

            for label, prettified in prettifier_data[prettifier_id].items():
                self.assertEqual(prettifier.prettify(label), prettified)


class SqlStringMatchTest(unittest.TestCase):
    """"
    Test the functions to convert SQL to regex patterns
    """

    def test_patterns(self):
        """"
        Test complex patterns to see if the logic of conversion is correct
        """
        for pattern, match_true, match_false in [
            (r'aa\_a%a_b', ['aa_abbbaab', 'aa_aa_b', 'aa_abaa_b', 'aa_aaxb', 'aa_abaaxb'], ['aaaba_b', 'aa_abab_b']),
            (r'^aa[\_%]b', ['^aa[_aaa]b', '^aa[_]b', '^aa[_1]b'], ['^aa[]b', 'aa[1]b', '^aa_b']),
            (
                r'z^aa^a\sd[\__%]*sa$dfa&s\%d$a', [r'z^aa^a\sd[_d]*sa$dfa&s%d$a', r'z^aa^a\sd[_aaa]*sa$dfa&s%d$a'],
                [r'z^aa^a\sd[_]*sa$dfa&s%d$a', 'zaa^asd[_aa]*sa$a']
            )
        ]:
            for sample in match_true:
                self.assertTrue(
                    escaping.sql_string_match(string=sample, pattern=pattern),
                    f"String '{sample}' should have matched pattern '{pattern}'"
                )
            for sample in match_false:
                self.assertFalse(
                    escaping.sql_string_match(string=sample, pattern=pattern),
                    f"String '{sample}' should not have matched pattern '{pattern}'"
                )
