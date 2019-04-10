# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the Profile class."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import uuid

from aiida.backends.testbase import AiidaTestCase
from aiida.backends.tests.utils.configuration import create_mock_profile
from aiida.manage.configuration import Profile


class TestProfile(AiidaTestCase):
    """Tests for the Profile class."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        """Setup a mock profile."""
        super(TestProfile, cls).setUpClass(*args, **kwargs)
        cls.profile_name = 'test_profile'
        cls.profile_dictionary = {
            'db_name': cls.profile_name,
            'db_host': 'localhost',
            'db_port': '5432',
            'db_user': 'user',
            'db_pass': 'pass',
            'email': 'dummy@localhost',
            'backend': 'django',
            'repo': os.path.join('/some/path', 'repository_' + cls.profile_name),
            Profile.KEY_PROFILE_UUID: Profile.generate_uuid(),
            Profile.KEY_DEFAULT_USER: 'dummy@localhost'
        }
        cls.profile = Profile(cls.profile_name, cls.profile_dictionary)

    def test_base_properties(self):
        """Test the basic properties of a Profile instance."""
        self.assertEqual(self.profile.name, self.profile_name)
        self.assertEqual(self.profile.dictionary, self.profile_dictionary)

        # Verify that the uuid property returns a valid UUID by attempting to construct an UUID instance from it
        uuid.UUID(self.profile.uuid)

        # Check that the default user email field is not None
        self.assertIsNotNone(self.profile.default_user_email)

        # The RabbitMQ prefix should contain the profile UUID
        self.assertIn(self.profile.uuid, self.profile.rmq_prefix)

    def test_is_test_profile(self):
        """Test that a profile whose name starts with `test_` is marked as a test profile."""
        profile_name = 'not_a_test_profile'
        profile = create_mock_profile(name=profile_name)

        # The one constructed in the setUpClass should be a test profile
        self.assertTrue(self.profile.is_test_profile)

        # The profile created here should *not* be a test profile
        self.assertFalse(profile.is_test_profile)
