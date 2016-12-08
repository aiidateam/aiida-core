import os
import sys
import unittest


from aiida.backends import settings
from aiida.common.utils import classproperty
from aiida.common.exceptions import ConfigurationError, TestsNotAllowedError
from aiida.backends.tests import get_db_test_list
from unittest import (
    TestSuite, TestResult,
    main as unittest_main, defaultTestLoader as test_loader)


def check_if_tests_can_run():
    """
    Check if the tests can run (i.e., if we are in a test profile.
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

    Each of them should contain two standard methods (i.e., *not* classmethods), called
    respectively ``setUpClass_method`` and ``tearDownClass_method``.
    They can set local properties (e.g. self.xxx = yyy) but xxx is not visible to this class.

    Moreover, it is required that they define in the setUpClass_method the two properties:

    - ``self.computer`` that must be a Computer object
    - ``self.user_email`` that must be a string

    These two are exposed to this test class.
    """
    @classmethod
    def get_backend_class(cls):
        from aiida.backends.profile import BACKEND_SQLA, BACKEND_DJANGO
        if not hasattr(cls, '__impl_class'):
            if settings.BACKEND == BACKEND_SQLA:
                from aiida.backends.sqlalchemy.tests.testbase import SqlAlchemyTests
                cls.__impl_class = SqlAlchemyTests
            elif settings.BACKEND == BACKEND_DJANGO:
                from aiida.backends.djsite.db.testbase import DjangoTests
                cls.__impl_class = DjangoTests
            else:
                raise ConfigurationError("Unknown backend type")

        return cls.__impl_class

    @classmethod
    def setUpClass(cls, *args, **kwargs):

        # Note: this will raise an exception, that will be seen as a test
        # failure. To be safe, you should do the same check also in the tearDownClass
        # to avoid that it is run
        check_if_tests_can_run()

        cls.__backend_instance = cls.get_backend_class()()
        cls.__backend_instance.setUpClass_method(*args, **kwargs)

    @classproperty
    def computer(cls):
        return cls.__backend_instance.computer

    @classproperty
    def user_email(cls):
        return cls.__backend_instance.user_email

    # @classmethod
    # def get_initialization_data(cls, dataname):
    #     """
    #     This function returns the object saved as self.dataname in the
    #     backend instance (function setUpClass_method of the backend_instance).
    #
    #     :param dataname: a string with the name of the object saved in the initialization (e.g., 'user')
    #     :return: the data value
    #     """
    #     return getattr(cls.__backend_instance, dataname)

    @classmethod
    def tearDownClass(cls, *args, **kwargs):

        # Double check for double security to avoid to run the tearDown
        # if this is not a test profile
        check_if_tests_can_run()

        cls.__backend_instance.tearDownClass_method(*args, **kwargs)

def run_aiida_db_tests(tests_to_run, verbose=True):
    """
    Run all sqlalchemy tests specified in tests_to_run.
    Return the list of test failures.
    """
    # Empty test suite that will be populated
    test_suite = TestSuite()

    actually_run_tests = []
    num_tests_expected = 0
    for test in set(tests_to_run):
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

    obj = None  # To avoid double runnings of the last test

    if verbose:
        print >> sys.stderr, (
            "DB tests that will be run: {} (expecting {} tests)".format(
                ",".join(actually_run_tests), num_tests_expected))

    results = unittest.TextTestRunner().run(test_suite)

    print "Run tests: {}".format(results.testsRun)

    return results.failures
