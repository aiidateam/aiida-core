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
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.backends.testbase import AiidaTestCase
from aiida.common import exceptions
from aiida.orm import authinfos


class TestAuthinfo(AiidaTestCase):
    """Unit tests for the AuthInfo ORM class."""

    def setUp(self):
        super(TestAuthinfo, self).setUp()
        for auth_info in authinfos.AuthInfo.objects.all():
            authinfos.AuthInfo.objects.delete(auth_info.pk)

        self.auth_info = self.computer.configure()  # pylint: disable=no-member

    def test_set_auth_params(self):
        """Test the auth_params setter."""
        auth_params = {'safe_interval': 100}

        self.auth_info.set_auth_params(auth_params)
        self.assertEqual(self.auth_info.get_auth_params(), auth_params)

    def test_delete(self):
        """Test deleting a single AuthInfo."""
        pk = self.auth_info.pk

        self.assertEqual(len(authinfos.AuthInfo.objects.all()), 1)
        authinfos.AuthInfo.objects.delete(pk)
        self.assertEqual(len(authinfos.AuthInfo.objects.all()), 0)

        with self.assertRaises(exceptions.NotExistent):
            authinfos.AuthInfo.objects.delete(pk)
