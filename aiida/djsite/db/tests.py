# -*- coding: utf-8 -*-
"""
This file contains tests for AiiDA.

This module checks that the module is properly loaded (i.e., if the
settings.aiida_test_list variable is set) and dynamically runs only the tests
specified in this list. See also the 'verdi test' function.
"""
import sys
import inspect
import importlib

from django.utils import unittest
from aiida.common.exceptions import InternalError
from aiida.djsite.settings import settings
from aiida.djsite.db.testbase import db_test_list

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.2.1"

tests_to_run = settings.__dict__.get('aiida_test_list', None)
if tests_to_run is None:
    # This is intended as a safety mechanism. This should help to ensure that tests are
    # run only after setting the flag in the djsite.settings.settings module, and
    # more importantly only after changing the DB and REPO to be test ones.
    raise InternalError("aiida_test_list is not set, but you are trying to run the tests...")

actually_run_tests = []
num_tests_expected = 0
for test in set(tests_to_run):
    try:
        modulename = db_test_list[test]
    except KeyError:
        print >> sys.stderr, "Unknown DB test {}... skipping".format(test)
        continue
    
    module = importlib.import_module(modulename)
    for objname, obj in module.__dict__.iteritems():
        if inspect.isclass(obj) and issubclass(obj, unittest.TestCase):
            # See if the object has test methods. 
            # Add only if there is at least one test_ method
            testmethods = [
                m for m in inspect.getmembers(obj, predicate=inspect.ismethod)
                if m[0].startswith("test_")]
            if testmethods: # at least a method starting with test_
                if objname in locals():
                    raise InternalError(
                        "Test class {} defined more than once".format(objname))
                locals()[objname] = obj
                num_tests_expected += len(testmethods)
                #for debug
                #print "{} ==> {} ({})".format(modulename, objname, len(testmethods))
    actually_run_tests.append(test)

obj = None # To avoid double runnings of the last test

print >> sys.stderr, "DB tests that will be run: {} (expecting {} tests)".format(
    ",".join(actually_run_tests), num_tests_expected)

