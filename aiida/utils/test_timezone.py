# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import unittest
import aiida.utils.timezone as timezone
from aiida.utils.timezone import now, make_aware
from datetime import datetime, timedelta
import time
import pytz



class TimezoneTest(unittest.TestCase):
    def test_timezone_now(self):
        DELTA = timedelta(minutes=1)
        ref = timezone.now()
        from_tz = timezone.make_aware(datetime.fromtimestamp(time.time()))
        self.assertLessEqual(from_tz, ref + DELTA)
        self.assertGreaterEqual(from_tz, ref - DELTA)
