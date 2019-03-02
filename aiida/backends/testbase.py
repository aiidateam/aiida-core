# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

import os
import sys
import unittest
import traceback

from tornado import ioloop

from aiida.backends import settings
from aiida.backends.tests import get_db_test_list
from aiida.common.exceptions import ConfigurationError, TestsNotAllowedError, InternalError
from aiida.common.lang import classproperty
from aiida.manage.manager import reset_manager


def check_if_tests_can_run():
    """
    Check if the tests can run (i.e., if we are in a test profile).
    Otherwise, raise TestsNotAllowedError.
    """
    from aiida import settings as settings2
    from aiida.common.setup import TEST_KEYWORD

    base_repo_path = os.path.basename(
        os.path.normpath(settings2.REPOSITORY_PATH))
    if (not settings.AIIDADB_PROFILE.startswith(TEST_KEYWORD) or
            TEST_KEYWORD not in base_repo_path or
            not settings2.DBNAME.startswith(TEST_KEYWORD)):
        msg = [
            "A non-test profile was given for tests. Please note "
            "that the test profile should have test specific "
            "database name and test specific repository name.",
            "Given profile: {}".format(settings.AIIDADB_PROFILE),
            "Related repository path: {}".format(base_repo_path),
            "Related database name: {}".format(settings2.DBNAME)]
        raise TestsNotAllowedError("\n".join(msg))


class AiidaTestCase(unittest.TestCase):
    """
    This is the base class for AiiDA tests, independent of the backend.

    Internally it loads the AiidaTestImplementation subclass according to the current backend
    """
    _class_was_setup = False
    __backend_instance = None
    backend = None  # type: aiida.orm.Backend

    @classmethod
    def get_backend_class(cls):
        from aiida.backends.testimplbase import AiidaTestImplementation

        from aiida.backends.profile import BACKEND_SQLA, BACKEND_DJANGO
        # Freeze the __impl_class after the first run
        if not hasattr(cls, '__impl_class'):
            if settings.BACKEND == BACKEND_SQLA:
                from aiida.backends.sqlalchemy.tests.testbase import (
                    SqlAlchemyTests)
                cls.__impl_class = SqlAlchemyTests
            elif settings.BACKEND == BACKEND_DJANGO:
                from aiida.backends.djsite.db.testbase import DjangoTests
                cls.__impl_class = DjangoTests
            else:
                raise ConfigurationError("Unknown backend type")

            # Check that it is of the right class
            if not issubclass(cls.__impl_class, AiidaTestImplementation):
                raise InternalError(
                    "The AiiDA test implementation is not of type "
                    "{}, that is not a subclass of AiidaTestImplementation".format(
                        cls.__impl_class.__name__
                    )
                )

        return cls.__impl_class

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        # Note: this will raise an exception, that will be seen as a test
        # failure. To be safe, you should do the same check also in the tearDownClass
        # to avoid that it is run
        check_if_tests_can_run()

        cls.__backend_instance = cls.get_backend_class()()
        cls.__backend_instance.setUpClass_method(*args, **kwargs)
        cls.backend = cls.__backend_instance.backend
        cls.insert_data()

        cls._class_was_setup = True

    def setUp(self):
        # Install a new IOLoop so that any messing up of the state of the loop is not propagated
        # to subsequent tests.
        # This call should come before the backend instance setup call just in case it uses the loop
        ioloop.IOLoop().make_current()
        self.__backend_instance.setUp_method()

    def tearDown(self):
        self.__backend_instance.tearDown_method()
        # Clean up the loop we created in set up.
        # Call this after the instance tear down just in case it uses the loop
        reset_manager()
        loop = ioloop.IOLoop.current()
        if not loop._closing:
            loop.close()

    def reset_database(self):
        """Reset the database to the default state deleting any content currently stored"""
        self.clean_db()
        self.insert_data()

    @classmethod
    def insert_data(cls):
        cls.__backend_instance.insert_data()

    @classmethod
    def clean_db(cls):
        """Clean up database and reset caches.

        Resets AiiDA manager cache, which could otherwise be left in an inconsistent state when cleaning the database.
        """
        from aiida.common.exceptions import InvalidOperation

        # Note: this will raise an exception, that will be seen as a test
        # failure. To be safe, you should do the same check also in the tearDownClass
        # to avoid that it is run
        check_if_tests_can_run()

        if not cls._class_was_setup:
            raise InvalidOperation("You cannot call clean_db before running the setUpClass")

        cls.__backend_instance.clean_db()

        # Reset AiiDA manager cache
        reset_manager()

    @classmethod
    def clean_repository(cls):
        """
        Cleans up file repository.
        """
        from aiida.settings import REPOSITORY_PATH
        from aiida.common.setup import TEST_KEYWORD
        from aiida.common.exceptions import InvalidOperation
        import shutil

        base_repo_path = os.path.basename(os.path.normpath(REPOSITORY_PATH))
        if TEST_KEYWORD not in base_repo_path:
            raise InvalidOperation("Warning: The repository folder {} does not "
                                   "seem to belong to a test profile and will therefore not be deleted.\n"
                                   "Full repository path: "
                                   "{}".format(base_repo_path, REPOSITORY_PATH))

        # Clean the test repository
        shutil.rmtree(REPOSITORY_PATH, ignore_errors=True)
        os.makedirs(REPOSITORY_PATH)

    @classproperty
    def computer(cls):
        """
        Get the default computer for this test

        :return: the test computer
        :rtype: :class:`aiida.orm.Computer`
        """
        return cls.__backend_instance.get_computer()

    @classproperty
    def user_email(cls):
        return cls.__backend_instance.get_user_email()

    @classmethod
    def tearDownClass(cls, *args, **kwargs):
        # Double check for double security to avoid to run the tearDown
        # if this is not a test profile
        check_if_tests_can_run()
        cls.clean_db()
        cls.clean_repository()
        cls.__backend_instance.tearDownClass_method(*args, **kwargs)

    def assertClickSuccess(self, cli_result):
        self.assertEqual(cli_result.exit_code, 0)
        self.assertClickResultNoException(cli_result)

    def assertClickResultNoException(self, cli_result):
        self.assertIsNone(cli_result.exception, ''.join(traceback.format_exception(*cli_result.exc_info)))


def run_aiida_db_tests(tests_to_run, verbose=False):
    """
    Run all tests specified in tests_to_run.
    Return the list of test results.
    """
    # Empty test suite that will be populated
    test_suite = unittest.TestSuite()

    actually_run_tests = []
    num_tests_expected = 0

    # To avoid adding more than once the same test
    # (e.g. if you type both db and db.xxx)
    found_modulenames = set()

    for test in set(tests_to_run):
        try:
            modulenames = get_db_test_list()[test]
        except KeyError:
            if verbose:
                print("Unknown DB test {}... skipping"
                      .format(test), file=sys.stderr)
            continue
        actually_run_tests.append(test)

        for modulename in modulenames:
            if modulename not in found_modulenames:
                try:
                    test_suite.addTest(unittest.defaultTestLoader.loadTestsFromName(modulename))
                except AttributeError as exception:
                    try:
                        import importlib
                        importlib.import_module(modulename)
                    except ImportError as exception:
                        print("[CRITICAL] The module '{}' has an import error and the tests cannot be run:\n{}"
                              .format(modulename, traceback.format_exc(exception)), file=sys.stderr)
                        sys.exit(1)
                found_modulenames.add(modulename)

        num_tests_expected = test_suite.countTestCases()

    if verbose:
        print("DB tests that will be run: {} (expecting {} tests)"
              .format(",".join(actually_run_tests), num_tests_expected), file=sys.stderr)
        results = unittest.TextTestRunner(failfast=False, verbosity=2).run(test_suite)
    else:
        results = unittest.TextTestRunner(failfast=False).run(test_suite)

    if verbose:
        print("Run tests: {}".format(results.testsRun))

    return results
