# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import datetime

from tornado import gen

from aiida.backends.testbase import AiidaTestCase
from aiida import work
from aiida.manage.manager import AiiDAManager


class TestWf(AiidaTestCase):
    TIMEOUT = datetime.timedelta(seconds=5.0)

    def test_calculation_future_broadcasts(self):
        runner = AiiDAManager.get_runner()
        process = work.test_utils.DummyProcess()

        # No polling
        future = work.futures.CalculationFuture(
            pk=process.pid,
            poll_interval=None,
            communicator=AiiDAManager.get_communicator())

        work.run(process)
        calc_node = runner.run_until_complete(gen.with_timeout(self.TIMEOUT, future))

        self.assertEqual(process.calc.pk, calc_node.pk)

    def test_calculation_future_polling(self):
        runner = AiiDAManager.get_runner()
        process = work.test_utils.DummyProcess()

        # No communicator
        future = work.futures.CalculationFuture(
            pk=process.pid,
            loop=runner.loop,
            poll_interval=0)

        runner.run(process)
        calc_node = runner.run_until_complete(gen.with_timeout(self.TIMEOUT, future))

        self.assertEqual(process.calc.pk, calc_node.pk)
