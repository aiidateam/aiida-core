# -*- coding: utf-8 -*-

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

        self.runner = work.create_runner(rmq_control_panel={'prefix': prefix})
        self.daemon_runner = work.create_daemon_runner(rmq_prefix=prefix)

    def tearDown(self):
        self.daemon_runner.close()
        self.runner.close()

    def test_launch_simple(self):
        # Launch the process
        self.runner.rmq.launch(test_utils.DummyProcess)

        # Tick the daemon runner a few times
        proc = None
        for _ in range(3):
            self.daemon_runner.tick()
            objs = self.daemon_runner.objects(obj_type=test_utils.DummyProcess)
            if len(objs) == 1:
                proc = objs[0]
                break

        self.assertIsNotNone(proc, "The process wasn't launched in the timeout")

    def test_launch_and_get_status(self):
        from plum.rmq.status import PROCS_KEY

        # Launch the process
        self.runner.rmq.launch(test_utils.WaitChain)

        # Tick the daemon runner a few times
        proc = None
        for _ in range(3):
            self.daemon_runner.tick()
            objs = self.daemon_runner.objects(obj_type=test_utils.WaitChain)
            if len(objs) == 1:
                proc = objs[0]
                break

        self.assertIsNotNone(proc, "The process wasn't launched in the timeout")

        responses = ~self.runner.rmq.status.send_request(timeout=2.)
        self.assertEqual(len(responses), 1)
        procs = responses[0][PROCS_KEY]
        self.assertIn(proc.process.pid, procs)
