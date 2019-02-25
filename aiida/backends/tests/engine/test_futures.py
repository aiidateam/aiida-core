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
from aiida.backends.tests.utils import processes as test_processes
from aiida.engine import processes, run
from aiida.manage.manager import get_manager


class TestWf(AiidaTestCase):
    TIMEOUT = datetime.timedelta(seconds=5.0)

    def test_calculation_future_broadcasts(self):
        manager = get_manager()
        runner = manager.get_runner()
        process = test_processes.DummyProcess()

        # No polling
        future = processes.futures.CalculationFuture(
            pk=process.pid, poll_interval=None, communicator=manager.get_communicator())

        run(process)
        calc_node = runner.run_until_complete(gen.with_timeout(self.TIMEOUT, future))

        self.assertEqual(process.node.pk, calc_node.pk)

    def test_calculation_future_polling(self):
        runner = get_manager().get_runner()
        process = test_processes.DummyProcess()

        # No communicator
        future = processes.futures.CalculationFuture(pk=process.pid, loop=runner.loop, poll_interval=0)

        runner.run(process)
        calc_node = runner.run_until_complete(gen.with_timeout(self.TIMEOUT, future))

        self.assertEqual(process.node.pk, calc_node.pk)
