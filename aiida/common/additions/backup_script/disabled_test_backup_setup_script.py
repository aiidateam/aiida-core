# -*- coding: utf-8 -*-
import unittest
import backup_setup
import datetime

from backup import Backup
from dateutil.parser import parse
from aiida.common.utils import ask_question

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0.1"
__authors__ = "The AiiDA team."


class UnitTests(unittest.TestCase):

    def setUp(self):
        self._backup_setup_inst = backup_setup.BackupSetup()

    def tearDown(self):
        self._backup_setup_inst = None

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
        # Check the yes
        backup_setup.raw_input = lambda _: "y"
        self.assertTrue(self._backup_setup_inst.query_yes_no("", "yes"))
        
        backup_setup.raw_input = lambda _: "yes"
        self.assertTrue(self._backup_setup_inst.query_yes_no("", "yes"))
        
        # Check the no
        backup_setup.raw_input = lambda _: "no"
        self.assertFalse(self._backup_setup_inst.query_yes_no("", "yes"))
        
        backup_setup.raw_input = lambda _: "n"
        self.assertFalse(self._backup_setup_inst.query_yes_no("", "yes"))
        
        # Check the empty default value that should
        # lead to an error
        with self.assertRaises(ValueError):
            self._backup_setup_inst.query_yes_no("", "")
            
        # Check that a None default value and no answer from
        # the user should lead to the repetition of the query until
        # it is answered properly
        self.seq = -1
        answers  = ["", "", "", "yes"]
        backup_setup.raw_input = lambda _: answers[self.array_counter()]
        self.assertTrue(self._backup_setup_inst.query_yes_no("", None))
        self.assertEqual(self.seq, len(answers) - 1)
        
        # Check that the default answer is returned
        # when the user doesn't give an answer
        backup_setup.raw_input = lambda _: ""
        self.assertTrue(self._backup_setup_inst.query_yes_no("", "yes"))
        
        backup_setup.raw_input = lambda _: ""
        self.assertFalse(self._backup_setup_inst.query_yes_no("", "no"))

    def test_query_string(self):
        """
        This method tests that the query_string method behaves as expected.
        """
        # None should be returned when empty answer and empty default
        # answer is given
        backup_setup.raw_input = lambda _: ""
        self.assertIsNone(self._backup_setup_inst.query_string("", ""))
        
        # If no answer is given then the default answer should be returned
        backup_setup.raw_input = lambda _: ""
        self.assertEqual(
            self._backup_setup_inst.query_string("", "Def_answer"),
            "Def_answer")
        
        # The answer should be returned when the an answer is given by
        # the user
        backup_setup.raw_input = lambda _: "Usr_answer"
        self.assertEqual(
            self._backup_setup_inst.query_string("", "Def_answer"),
            "Usr_answer")
        
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
        backup_setup.raw_input = lambda _: answers[self.array_counter()]
        self.assertEqual(ask_question("", int, False), int(answers[2]))
    
        # Test that a question that asks for a date is working correctly.
        # The behavior is similar to the above test.
        self.seq = -1
        answers = ["", "3fd43", "2015-07-28 20:48:53.197537+02:00", "yes"]
        backup_setup.raw_input = lambda _: answers[self.array_counter()]
        self.assertEqual(("", datetime.datetime, False), parse(answers[2]))
    
        # Check that None is not allowed as answer
        question = ""
        answer = ""
        backup_setup.raw_input = lambda x: answer if x == question else "y"
        self.assertEqual(ask_question(question, int, True), None)
        
    def test_construct_backup_variables(self):
        """
        Test that checks that the backup variables are populated as it
        should by the construct_backup_variables by asking the needed
        questions. A lambda function is used to simulate the user input.
        """
        
        # Checking parsing of backup variables with many empty answers
        self.seq = -1
        answers = ["", "y", "", "y", "", "y", "1", "y", "2", "y"]
        backup_setup.raw_input = lambda _: answers[self.array_counter()]
        bk_vars = self._backup_setup_inst.construct_backup_variables("")
        # Check the parsed answers
        self.assertIsNone(bk_vars[Backup._oldest_object_bk_key])
        self.assertIsNone(bk_vars[Backup._days_to_backup_key])
        self.assertIsNone(bk_vars[Backup._end_date_of_backup_key])
        self.assertEqual(bk_vars[Backup._periodicity_key], 1)
        self.assertEqual(bk_vars[Backup._backup_length_threshold_key], 2)
        
        # Checking parsing of backup variables with all the answers given
        self.seq = -1
        answers = ["2013-07-28 20:48:53.197537+02:00", "y",
                    "2", "y", "2015-07-28 20:48:53.197537+02:00", "y",
                    "3", "y", "4", "y"]
        backup_setup.raw_input = lambda _: answers[self.array_counter()]
        bk_vars = self._backup_setup_inst.construct_backup_variables("")
        # Check the parsed answers
        self.assertEqual(bk_vars[Backup._oldest_object_bk_key], answers[0])
        self.assertEqual(bk_vars[Backup._days_to_backup_key], 2)
        self.assertEqual(bk_vars[Backup._end_date_of_backup_key], answers[4])
        self.assertEqual(bk_vars[Backup._periodicity_key], 3)
        self.assertEqual(bk_vars[Backup._backup_length_threshold_key], 4)
        
if __name__ == '__main__':
    unittest.main()
