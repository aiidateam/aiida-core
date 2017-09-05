# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.backends.testbase import AiidaTestCase

import plum.process_monitor
from aiida.orm.data.base import Int, Str
from aiida import work
from aiida.work import default_loop
from aiida.work.test_utils import DummyProcess


class TestRun(AiidaTestCase):
    def setUp(self):
        super(TestRun, self).setUp()
        self.assertEquals(len(plum.process_monitor.MONITOR.get_pids()), 0)

    def tearDown(self):
        super(TestRun, self).tearDown()
        self.assertEquals(len(plum.process_monitor.MONITOR.get_pids()), 0)

    def test_run_process_class(self):
        inputs = {'a': Int(2), 'b': Str('test')}

        # Queue up the process
        proc = default_loop.enqueue(DummyProcess, inputs)

        result = work.run(DummyProcess)

        # TODO: Use a process that actually outputs something and check
