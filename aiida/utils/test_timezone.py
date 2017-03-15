# -*- coding: utf-8 -*-
import unittest
from aiida.utils.timezone import now, make_aware
from datetime import datetime, timedelta
import time
import pytz

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.1"
__authors__ = "The AiiDA team."


class TimezoneTest(unittest.TestCase):
    def test_timezone_now(self):
        DELTA = timedelta(minutes=1)
        for tz in pytz.all_timezones:
            ref = now()
            from_tz = datetime.fromtimestamp(time.time(), tz=pytz.timezone(tz))
            self.assertLessEqual(from_tz, ref + DELTA)
            self.assertGreaterEqual(from_tz, ref - DELTA)

