# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Test classes and test runners for testing AiiDA plugins with unittest.
"""

import unittest

from aiida.manage.manager import get_manager
from . import _GLOBAL_TEST_MANAGER, test_manager, get_test_backend_name, get_test_profile_name

__all__ = ('PluginTestCase', 'TestRunner')


class PluginTestCase(unittest.TestCase):
    """
    Set up a complete temporary AiiDA environment for plugin tests.

    Note: This test class needs to be run through the :py:class:`~aiida.manage.tests.unittest_classes.TestRunner`
    and will **not** work simply with `python -m unittest discover`.

    Usage example::

        MyTestCase(aiida.manage.tests.unittest_classes.PluginTestCase):

            def setUp(self):
                # load my tests data

            # optionally extend setUpClass / tearDownClass / tearDown if needed

            def test_my_plugin(self):
                # execute tests
    """
    # Filled in during setUpClass
    backend = None  # type :class:`aiida.orm.implementation.Backend`

    @classmethod
    def setUpClass(cls):
        cls.test_manager = _GLOBAL_TEST_MANAGER
        if not cls.test_manager.has_profile_open():
            raise ValueError(
                'Fixture mananger has no open profile.' +
                'Please use aiida.manage.tests.unittest_classes.TestRunner to run these tests.'
            )

        cls.backend = get_manager().get_backend()

    def tearDown(self):
        self.test_manager.reset_db()


class TestRunner(unittest.runner.TextTestRunner):
    """
    Testrunner for unit tests using the fixture manager.

    Usage example::

        import unittest
        from aiida.manage.tests.unittest_classes import TestRunner

        tests = unittest.defaultTestLoader.discover('.')
        TestRunner().run(tests)

    """

    # pylint: disable=arguments-differ
    def run(self, suite, backend=None, profile_name=None):
        """
        Run tests using fixture manager for specified backend.

        :param suite: A suite of tests, as returned e.g. by :py:meth:`unittest.TestLoader.discover`
        :param backend: name of database backend to be used.
        :param profile_name: name of test profile to be used or None (will use temporary profile)
        """
        import warnings
        from aiida.common.warnings import AiidaDeprecationWarning
        warnings.warn(  # pylint: disable=no-member
            'Please use "pytest" for testing AiiDA plugins. Support for "unittest" will be removed in `v2.0.0`',
            AiidaDeprecationWarning
        )

        with test_manager(
            backend=backend or get_test_backend_name(), profile_name=profile_name or get_test_profile_name()
        ):
            return super().run(suite)
