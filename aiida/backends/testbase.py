import os
import sys
import unittest


from aiida.backends import settings
from aiida.common.utils import classproperty
from aiida.common.exceptions import ConfigurationError, TestsNotAllowedError, InternalError
from aiida.backends.tests import get_db_test_list
from unittest import (
    TestSuite, TestResult,
    main as unittest_main, defaultTestLoader as test_loader)


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

    @classmethod
    def get_backend_class(cls):
        from aiida.backends.testimplbase import AiidaTestImplementation

        from aiida.backends.profile import BACKEND_SQLA, BACKEND_DJANGO
        # Freeze the __impl_class after the first run
        if not hasattr(cls, '__impl_class'):
            if settings.BACKEND == BACKEND_SQLA:
                from aiida.backends.sqlalchemy.tests.testbase import SqlAlchemyTests
                cls.__impl_class = SqlAlchemyTests
            elif settings.BACKEND == BACKEND_DJANGO:
                from aiida.backends.djsite.db.testbase import DjangoTests
                cls.__impl_class = DjangoTests
            else:
                raise ConfigurationError("Unknown backend type")


            # Check that it is of the right class
            if not issubclass(cls.__impl_class, AiidaTestImplementation):
                raise InternalError("The AiiDA test implementation is not of type "
                    "{}, that is not a subclass of AiidaTestImplementation".format(
                    cls.__impl_class.__name__
                ))

        return cls.__impl_class

    @classmethod
    def setUpClass(cls, *args, **kwargs):

        # Note: this will raise an exception, that will be seen as a test
        # failure. To be safe, you should do the same check also in the tearDownClass
        # to avoid that it is run
        check_if_tests_can_run()

        cls.__backend_instance = cls.get_backend_class()()
        cls.__backend_instance.setUpClass_method(*args, **kwargs)

        cls._class_was_setup = True

    def setUp(self):
        self.__backend_instance.setUp_method()
        # from plum.process_monitor import MONITOR
        # from aiida.work.util import ProcessStack
        # print "BEFORE:", self.id(), self._testMethodName, ProcessStack.pids()

    def tearDown(self):
        self.__backend_instance.tearDown_method()
        # SPHUBER
        # from plum.process_monitor import MONITOR
        # from aiida.work.util import ProcessStack
        # print "AFTER:", self.id(), self._testMethodName, ProcessStack.pids()
        # print "MONITOR BEFORE:", self.id(), self._testMethodName, MONITOR.get_pids()
        # print "STACK BEFORE:", self.id(), self._testMethodName, ProcessStack.stack()
        # for pid in list(ProcessStack.pids()):
        #     ProcessStack.pop(pid=pid)
        # MONITOR._reset()
        # print "MONITOR AFTER:", self.id(), self._testMethodName, MONITOR.get_pids()
        # print "STACK AFTER:", self.id(), self._testMethodName, ProcessStack.stack()

    @classmethod
    def insert_data(cls):
        cls.__backend_instance.insert_data()

    @classmethod
    def clean_db(cls):

        # Note: this will raise an exception, that will be seen as a test
        # failure. To be safe, you should do the same check also in the tearDownClass
        # to avoid that it is run
        check_if_tests_can_run()

        from aiida.common.exceptions import InvalidOperation

        if not cls._class_was_setup:
            raise InvalidOperation("You cannot call clean_db before running the setUpClass")

        cls.__backend_instance.clean_db()

    @classproperty
    def computer(cls):
        return cls.__backend_instance.get_computer()

    @classproperty
    def user_email(cls):
        return cls.__backend_instance.get_user_email()

    @classmethod
    def tearDownClass(cls, *args, **kwargs):

        # Double check for double security to avoid to run the tearDown
        # if this is not a test profile
        check_if_tests_can_run()

        cls.__backend_instance.tearDownClass_method(*args, **kwargs)


def run_aiida_db_tests(tests_to_run, verbose=False):
    """
    Run all tests specified in tests_to_run.
    Return the list of test results.
    """
    # Empty test suite that will be populated
    test_suite = TestSuite()

    actually_run_tests = []
    num_tests_expected = 0
    for test in set(tests_to_run):
        from plum.process_monitor import MONITOR
        try:
            modulenames = get_db_test_list()[test]
        except KeyError:
            if verbose:
                print >> sys.stderr, "Unknown DB test {}... skipping".format(
                    test)
            continue
        actually_run_tests.append(test)

        for modulename in modulenames:
            test_suite.addTest(test_loader.loadTestsFromName(modulename))

        num_tests_expected = test_suite.countTestCases()

    if verbose:
        print >> sys.stderr, (
            "DB tests that will be run: {} (expecting {} tests)".format(
                ",".join(actually_run_tests), num_tests_expected))

    results = unittest.TextTestRunner().run(test_suite)

    if verbose:
        print "Run tests: {}".format(results.testsRun)

    return results
