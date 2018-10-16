# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import absolute_import
from aiida.backends.testbase import AiidaTestCase
from aiida import work
import aiida.work.test_utils

from . import utils


class TestWf(AiidaTestCase):
    def test_calculation_future_broadcasts(self):
        runner = utils.create_test_runner(with_communicator=True)
        proc = work.test_utils.DummyProcess()
        # No polling
        future = work.CalculationFuture(
            pk=proc.pid,
            poll_interval=None,
            communicator=runner.communicator)
        work.run(proc)
        calc_node = runner.run_until_complete(future)
        self.assertEqual(proc.calc.pk, calc_node.pk)

    def test_calculation_future_polling(self):
        runner = utils.create_test_runner()
        proc = work.test_utils.DummyProcess()
        # No communicator
        future = work.CalculationFuture(
            pk=proc.pid,
            loop=runner.loop,
            poll_interval=0)
        work.run(proc)
        calc_node = runner.run_until_complete(future)
        self.assertEqual(proc.calc.pk, calc_node.pk)
