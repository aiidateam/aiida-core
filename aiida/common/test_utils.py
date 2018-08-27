# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import absolute_import
import datetime
import unittest

from dateutil.parser import parse

from aiida.common import utils




class UniqueTest(unittest.TestCase):
    """
    Tests for the get_unique_filename function.
    """

    def test_unique_1(self):
        filename = "different.txt"
        filename_list = ["file1.txt", "file2.txt"]

        self.assertEqual(filename,
                         utils.get_unique_filename(filename, filename_list))

    def test_unique_2(self):
        filename = "file1.txt"
        filename_list = ["file1.txt", "file2.txt"]

        self.assertEqual("file1-1.txt",
                         utils.get_unique_filename(filename, filename_list))

    def test_unique_3(self):
        filename = "file1.txt"
        filename_list = ["file1.txt", "file1-1.txt"]

        self.assertEqual("file1-2.txt",
                         utils.get_unique_filename(filename, filename_list))

    def test_unique_4(self):
        filename = "file1.txt"
        filename_list = ["file1.txt", "file1-2.txt"]

        self.assertEqual("file1-1.txt",
                         utils.get_unique_filename(filename, filename_list))

    # The counter & the method that increments it and
    # returns its value. It is used in the tests
    seq = -1

    def array_counter(self):
        self.seq += 1
        return self.seq

    def test_query_yes_no(self):
        """
        This method tests the query_yes_no method behaves as expected. To
        perform this, a lambda function is used to simulate the user input.
        """
        from aiida.utils.capturing import Capturing

        # Capture the sysout for the following code
        with Capturing():
            # Check the yes
            utils.input = lambda _: "y"
            self.assertTrue(utils.query_yes_no("", "yes"))

            utils.input = lambda _: "yes"
            self.assertTrue(utils.query_yes_no("", "yes"))

            # Check the no
            utils.input = lambda _: "no"
            self.assertFalse(utils.query_yes_no("", "yes"))

            utils.input = lambda _: "n"
            self.assertFalse(utils.query_yes_no("", "yes"))

            # Check the empty default value that should
            # lead to an error
            with self.assertRaises(ValueError):
                utils.query_yes_no("", "")

            # Check that a None default value and no answer from
            # the user should lead to the repetition of the query until
            # it is answered properly
            self.seq = -1
            answers = ["", "", "", "yes"]
            utils.input = lambda _: answers[self.array_counter()]
            self.assertTrue(utils.query_yes_no("", None))
            self.assertEqual(self.seq, len(answers) - 1)

            # Check that the default answer is returned
            # when the user doesn't give an answer
            utils.input = lambda _: ""
            self.assertTrue(utils.query_yes_no("", "yes"))

            utils.input = lambda _: ""
            self.assertFalse(utils.query_yes_no("", "no"))

    def test_query_string(self):
        """
        This method tests that the query_string method behaves as expected.
        """
        # None should be returned when empty answer and empty default
        # answer is given
        utils.input = lambda _: ""
        self.assertIsNone(utils.query_string("", ""))

        # If no answer is given then the default answer should be returned
        utils.input = lambda _: ""
        self.assertEqual(
            utils.query_string("", "Def_answer"), "Def_answer")

        # The answer should be returned when the an answer is given by
        # the user
        utils.input = lambda _: "Usr_answer"
        self.assertEqual(
            utils.query_string("", "Def_answer"), "Usr_answer")

    def test_ask_backup_question(self):
        """
        This method checks that the combined use of query_string and
        query_yes_no by the ask_backup_question is done as expected.
        """
        from aiida.utils.capturing import Capturing

        # Capture the sysout for the following code
        with Capturing():
            # Test that a question that asks for an integer is working
            # The given answers are in order:
            # - a non-accepted empty answer
            # - an answer that can not be parsed based on the given type
            # - the final expected answer
            self.seq = -1
            answers = ["", "3fd43", "1", "yes"]
            utils.input = lambda _: answers[self.array_counter()]
            self.assertEqual(utils.ask_question("", int, False), int(answers[2]))

            # Test that a question that asks for a date is working correctly.
            # The behavior is similar to the above test.
            self.seq = -1
            answers = ["", "3fd43", "2015-07-28 20:48:53.197537+02:00", "yes"]
            utils.input = lambda _: answers[self.array_counter()]
            self.assertEqual(utils.ask_question("", datetime.datetime, False),
                             parse(answers[2]))

            # Check that None is not allowed as answer
            question = ""
            answer = ""
            utils.input = lambda x: answer if x == question else "y"
            self.assertEqual(utils.ask_question(question, int, True), None)


class FortranFormattingTest(unittest.TestCase):
    """
    Tests for the different Fortran formatting functions.
    """

    def test_fortfloat(self):
        """
        Check the `get_fortfloat` function.
        """

        floats_result = {
            "0.1d2": 10.,
             "0.D-3": 0.,
             ".2e1": 2.,
             "-0.23": -0.23,
             "23.": 23.,
             "232": 232.,
            }

        # the characters surrounding a float and the respective key:
        surroundings = {
            "charsbefore, abc = {}, charsafter": "abc",
            "    charsbefore\n    abc = {}\n    charsafter": "abc",
            "charsbefore, abc = {}\ncharsafter": "abc",
            }

        for surrounding, key in surroundings.items():
            for value, result in floats_result.items():
                # case sensitive
                self.assertAlmostEqual(utils.get_fortfloat(key, surrounding.format(value)), result)
                # check also the case insensitive case:
                self.assertAlmostEqual(utils.get_fortfloat(key.upper(), surrounding.format(value), False), result)
                # and the key not found case
                self.assertIsNone(utils.get_fortfloat(key.upper(), surrounding.format(value)))


class PrettifierTest(unittest.TestCase):
    """
    Tests for the Prettifier class methods.
    """

    def test_prettifier(self):
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
                'G': u'Γ',
                'bla3': r'bla_{3}',
                'bla33': r'bla_{33}',
                },
            'gnuplot_seekpath': {
                'SIGMA': u'Σ',
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

class ListFunctionsTest(unittest.TestCase):
    """
    Tests for the different list manipulation functions.
    """

    def test_flatten_list(self):
        self.assertEqual(utils.flatten_list([[[[[4],3]],[3],['a',[3]]]]), [4, 3, 3, 'a', 3])
