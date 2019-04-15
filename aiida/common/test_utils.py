# -*- coding: utf-8 -*-
import datetime
import unittest

from dateutil.parser import parse

from aiida.common import utils


__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.1.1"
__authors__ = "The AiiDA team."


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
        # original_raw_input = __builtins__.raw_input

        # Check the yes
        utils.raw_input = lambda _: "y"
        self.assertTrue(utils.query_yes_no("", "yes"))

        utils.raw_input = lambda _: "yes"
        self.assertTrue(utils.query_yes_no("", "yes"))

        # Check the no
        utils.raw_input = lambda _: "no"
        self.assertFalse(utils.query_yes_no("", "yes"))

        utils.raw_input = lambda _: "n"
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
        utils.raw_input = lambda _: answers[self.array_counter()]
        self.assertTrue(utils.query_yes_no("", None))
        self.assertEqual(self.seq, len(answers) - 1)

        # Check that the default answer is returned
        # when the user doesn't give an answer
        utils.raw_input = lambda _: ""
        self.assertTrue(utils.query_yes_no("", "yes"))

        utils.raw_input = lambda _: ""
        self.assertFalse(utils.query_yes_no("", "no"))

    def test_query_string(self):
        """
        This method tests that the query_string method behaves as expected.
        """
        # None should be returned when empty answer and empty default
        # answer is given
        utils.raw_input = lambda _: ""
        self.assertIsNone(utils.query_string("", ""))

        # If no answer is given then the default answer should be returned
        utils.raw_input = lambda _: ""
        self.assertEqual(
            utils.query_string("", "Def_answer"), "Def_answer")

        # The answer should be returned when the an answer is given by
        # the user
        utils.raw_input = lambda _: "Usr_answer"
        self.assertEqual(
            utils.query_string("", "Def_answer"), "Usr_answer")

    def test_ask_backup_question(self):
        """
        This method checks that the combined use of query_string and
        query_yes_no by the ask_backup_question is done as expected.
        """

        # Test that a question that asks for an integer is working
        # The given answers are in order:
        # - a non-accepted empty answer
        # - an answer that can not be parsed based on the given type
        # - the final expected answer
        self.seq = -1
        answers = ["", "3fd43", "1", "yes"]
        utils.raw_input = lambda _: answers[self.array_counter()]
        self.assertEqual(utils.ask_question("", int, False), int(answers[2]))

        # Test that a question that asks for a date is working correctly.
        # The behavior is similar to the above test.
        self.seq = -1
        answers = ["", "3fd43", "2015-07-28 20:48:53.197537+02:00", "yes"]
        utils.raw_input = lambda _: answers[self.array_counter()]
        self.assertEqual(utils.ask_question("", datetime.datetime, False),
                         parse(answers[2]))

        # Check that None is not allowed as answer
        question = ""
        answer = ""
        utils.raw_input = lambda x: answer if x == question else "y"
        self.assertEqual(utils.ask_question(question, int, True), None)
