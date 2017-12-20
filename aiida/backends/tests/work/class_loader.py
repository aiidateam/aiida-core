# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import aiida.work.utils as util
from aiida.backends.testbase import AiidaTestCase
from aiida.orm.calculation.job.simpleplugins.templatereplacer import TemplatereplacerCalculation
from aiida.work.globals import class_loader
from aiida.work.job_processes import JobProcess
from plum.utils import class_name


class TestJobProcess(AiidaTestCase):
    def setUp(self):
        super(TestJobProcess, self).setUp()
        self.assertEquals(len(util.ProcessStack.stack()), 0)

    def tearDown(self):
        super(TestJobProcess, self).tearDown()
        self.assertEquals(len(util.ProcessStack.stack()), 0)

    def test_class_loader(self):
        TemplatereplacerProcess = JobProcess.build(TemplatereplacerCalculation)
        LoadedClass = class_loader.load_class(class_name(TemplatereplacerProcess))

        self.assertEqual(TemplatereplacerProcess.__name__, LoadedClass.__name__)
        self.assertEqual(class_name(TemplatereplacerProcess), class_name(LoadedClass))

