# -*- coding: utf-8 -*-

import plum
import uuid
from aiida.backends.testbase import AiidaTestCase
import aiida.work.test_utils as test_utils
import aiida.work as work

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.0"


class TestProcess(AiidaTestCase):
    """
    Test AiiDA's RabbitMQ functionalities.
    """

    def setUp(self):
        super(TestProcess, self).setUp()
        prefix = "{}.{}".format(self.__class__.__name__, uuid.uuid4())

        self.loop = plum.new_event_loop()

        rmq_config = {
            'url': 'amqp://localhost',
            'prefix': prefix,
            'testing_mode': True
        }
        self.runner = work.Runner(
            rmq_config=rmq_config, rmq_submit=True, loop=self.loop, poll_interval=0.)
        self.daemon_runner = work.DaemonRunner(
            rmq_config=rmq_config, rmq_submit=True, loop=self.loop, poll_interval=0.)

    def tearDown(self):
        self.daemon_runner.close()
        self.runner.close()

    def test_launch_simple(self):
        # Launch the process
        calc_node = self.runner.submit(test_utils.DummyProcess)

        def stop(*args):
            self.loop.stop()

        self.runner.call_on_calculation_finish(calc_node.pk, stop)
        self.loop.call_later(5, stop)
        self.loop.start()

        self.assertTrue(calc_node.has_finished_ok())


        # def test_launch_and_get_status(self):
        #     from plum.rmq.status import PROCS_KEY
        #
        #     # Launch the process
        #     self.runner.submit(test_utils.WaitChain)
        #
        #     # Tick the daemon runner a few times
        #     proc = None
        #     for _ in range(3):
        #         self.daemon_runner.tick()
        #         objs = self.daemon_runner.objects(obj_type=test_utils.WaitChain)
        #         if len(objs) == 1:
        #             proc = objs[0]
        #             break
        #
        #     self.assertIsNotNone(proc, "The process wasn't launched in the timeout")
        #
        #     responses = ~self.runner.rmq.status.send_request(timeout=2.)
        #     self.assertEqual(len(responses), 1)
        #     procs = responses[0][PROCS_KEY]
        #     self.assertIn(proc.process.pid, procs)
