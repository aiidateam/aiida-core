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

from aiida.orm.calculation.job.quantumespresso.pw import PwCalculation
from aiida.work.class_loader import ClassLoader
import aiida.work.util as util
from aiida.work.legacy.job_process import JobProcess


class TestJobProcess(AiidaTestCase):
    def setUp(self):
        super(TestJobProcess, self).setUp()
        self.assertEquals(len(util.ProcessStack.stack()), 0)

    def tearDown(self):
        super(TestJobProcess, self).tearDown()
        self.assertEquals(len(util.ProcessStack.stack()), 0)

    def test_class_loader(self):
        cl = ClassLoader()
        PwProcess = JobProcess.build(PwCalculation)