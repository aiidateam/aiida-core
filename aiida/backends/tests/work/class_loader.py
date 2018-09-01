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
import aiida
from aiida.work import Process
from aiida.backends.testbase import AiidaTestCase
from aiida.orm.calculation.job.simpleplugins.templatereplacer import TemplatereplacerCalculation


class TestJobProcess(AiidaTestCase):
    def setUp(self):
        super(TestJobProcess, self).setUp()
        self.assertIsNone(Process.current())

    def tearDown(self):
        super(TestJobProcess, self).tearDown()
        self.assertIsNone(Process.current())

    def test_class_loader(self):
        templatereplacer_process = aiida.work.JobProcess.build(TemplatereplacerCalculation)
        loader = aiida.work.get_object_loader()

        class_name = loader.identify_object(templatereplacer_process)
        loaded_class = loader.load_object(class_name)

        self.assertEqual(templatereplacer_process.__name__, loaded_class.__name__)
        self.assertEqual(class_name, loader.identify_object(loaded_class))
