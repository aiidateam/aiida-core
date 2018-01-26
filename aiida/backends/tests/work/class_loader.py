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
from plum.utils import class_name
from aiida import work


CLASS_LOADER = work.CLASS_LOADER

class TestJobProcess(AiidaTestCase):
    def setUp(self):
        super(TestJobProcess, self).setUp()
        self.assertEquals(len(util.ProcessStack.stack()), 0)

    def tearDown(self):
        super(TestJobProcess, self).tearDown()
        self.assertEquals(len(util.ProcessStack.stack()), 0)

    def test_class_loader(self):
        templatereplacer_process = work.JobProcess.build(TemplatereplacerCalculation)
        loaded_class = CLASS_LOADER.load_class(
            class_name(templatereplacer_process, class_loader=CLASS_LOADER))

        self.assertEqual(templatereplacer_process.__name__, loaded_class.__name__)
        self.assertEqual(
            class_name(templatereplacer_process, verify=False),
            class_name(loaded_class, verify=False))

