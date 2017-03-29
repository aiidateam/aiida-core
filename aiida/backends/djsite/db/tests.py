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
from aiida.backends.djsite.settings import settings_profile
from aiida.backends.tests import get_db_test_list


tests_to_run = settings_profile.__dict__.get('aiida_test_list', None)
if tests_to_run is None:
    # This is intended as a safety mechanism. This should help to ensure that
    # tests are  run only after setting the flag in the djsite.settings.settings
    # module, and more importantly only after changing the DB and REPO to be
    # test ones.
    raise InternalError("aiida_test_list is not set, but you are trying to run the tests...")

actually_run_tests = []
num_tests_expected = 0
for test in set(tests_to_run):
    try:
        modulenames = get_db_test_list()[test]
    except KeyError:
        print >> sys.stderr, "Unknown DB test {}... skipping".format(test)
        continue

    for modulename in modulenames:
        module = importlib.import_module(modulename)
        for objname, obj in module.__dict__.iteritems():
            if inspect.isclass(obj) and issubclass(obj, unittest.TestCase):
                # See if the object has test methods.
                # Add only if there is at least one test_ method
                testmethods = [
                    m for m in inspect.getmembers(obj, predicate=inspect.ismethod)
                    if m[0].startswith("test_")]
                if testmethods:  # at least a method starting with test_
                    if objname in locals():
                        raise InternalError(
                            "Test class {} defined more than once".format(objname))
                    locals()[objname] = obj
                    num_tests_expected += len(testmethods)
                    # for debug
                    #print "{} ==> {} ({})".format(modulename, objname, len(testmethods))
        actually_run_tests.append(test)

obj = None  # To avoid double runnings of the last test

print >> sys.stderr, "DB tests that will be run: {} (expecting {} tests)".format(
    ",".join(actually_run_tests), num_tests_expected)

