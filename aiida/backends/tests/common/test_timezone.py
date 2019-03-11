# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the timezone utility module."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import datetime
import unittest
import time

import aiida.common.timezone as timezone


class TimezoneTest(unittest.TestCase):
    """Tests for the timezone utility module."""

    def test_timezone_now(self):
        """Test timezone.now function."""
        delta = datetime.timedelta(minutes=1)
        ref = timezone.now()
        from_tz = timezone.make_aware(datetime.datetime.fromtimestamp(time.time()))
        self.assertLessEqual(from_tz, ref + delta)
        self.assertGreaterEqual(from_tz, ref - delta)
