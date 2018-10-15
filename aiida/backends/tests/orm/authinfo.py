# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Unit tests for the AuthInfo ORM class."""
from __future__ import absolute_import
from aiida.backends.testbase import AiidaTestCase
from aiida.control.computer import configure_computer


class TestAuthinfo(AiidaTestCase):
    """Unit tests for the AuthInfo ORM class."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super(TestAuthinfo, cls).setUpClass(*args, **kwargs)
        cls.auth_info = configure_computer(cls.computer)

    def test_set_auth_params(self):
        """Test the auth_params setter."""
        auth_params = {'safe_interval': 100}

        self.auth_info.set_auth_params(auth_params)
        self.assertEqual(self.auth_info.get_auth_params(), auth_params)
