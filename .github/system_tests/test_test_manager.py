# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Unittests for TestManager"""
import sys
import unittest
import warnings

import pytest

from aiida.manage.tests import TestManager, get_test_backend_name


class TestManagerTestCase(unittest.TestCase):
    """Test the TestManager class"""

    def setUp(self):
        if sys.version_info[0] >= 3:
            # tell unittest not to warn about running processes
            warnings.simplefilter('ignore', ResourceWarning)  # pylint: disable=no-member,undefined-variable

        self.backend = get_test_backend_name()
        self.test_manager = TestManager()

    def tearDown(self):
        self.test_manager.destroy_all()

    @pytest.mark.filterwarnings('ignore:Creating AiiDA configuration folder')
    def test_pgtest_argument(self):
        """
        Create a temporary profile, passing the pgtest argument.
        """
        from pgtest.pgtest import which

        # this should fail
        pgtest = {'pg_ctl': 'notapath'}
        with self.assertRaises(AssertionError):
            self.test_manager.use_temporary_profile(backend=self.backend, pgtest=pgtest)

        # pg_ctl is what PGTest also looks for (although it might be more clever)
        pgtest = {'pg_ctl': which('pg_ctl')}
        self.test_manager.use_temporary_profile(backend=self.backend, pgtest=pgtest)


if __name__ == '__main__':
    unittest.main()
