# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module to test process runners."""
import plumpy

from aiida.backends.testbase import AiidaTestCase
from aiida.engine import Process
from aiida.manage.manager import get_manager
from aiida.orm import WorkflowNode


class Proc(Process):
    """Process class."""

    _node_class = WorkflowNode

    def run(self):
        pass


def the_hans_klok_comeback(loop):
    loop.stop()


class TestWorkchain(AiidaTestCase):
    """Test running work chains."""

    def setUp(self):
        super().setUp()
        self.runner = get_manager().get_runner()

    def test_call_on_calculation_finish(self):
        """Test call on calculation finish."""
        loop = self.runner.loop
        proc = Proc(runner=self.runner)
        future = plumpy.Future()

        def calc_done(pk):
            self.assertEqual(pk, proc.node.pk)
            loop.stop()
            future.set_result(True)

        self.runner.call_on_calculation_finish(proc.node.pk, calc_done)

        # Run the calculation
        self.runner.loop.add_callback(proc.step_until_terminated)
        self._run_loop_for(5.)

        self.assertTrue(future.result())

    def _run_loop_for(self, seconds):
        loop = self.runner.loop
        loop.call_later(seconds, the_hans_klok_comeback, self.runner.loop)
        loop.start()
