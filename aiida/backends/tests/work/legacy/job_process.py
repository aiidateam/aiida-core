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
from aiida.orm.calculation.job.simpleplugins.templatereplacer import TemplatereplacerCalculation
from aiida.work import util
from aiida.work.class_loader import ClassLoader
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
        TemplatereplacerProcess = JobProcess.build(TemplatereplacerCalculation)

    def test_job_process_set_label_and_description(self):
        """
        Verify that calculation label and description get set when passed through inputs
        """
        label = 'test_label'
        description = 'test_description'
        inputs = {
            '_options': {
                    'computer': self.computer,
                    'resources': {
                        'num_machines': 1,
                        'num_mpiprocs_per_machine': 1
                    },
                    'max_wallclock_seconds': 10,
                },
            '_label': label,
            '_description': description
        }
        job_instance = self._run_inputs(inputs)

        self.assertEquals(job_instance.calc.label, label)
        self.assertEquals(job_instance.calc.description, description)

    def test_job_process_set_none(self):
        """
        Verify that calculation label and description can be set to ``None``.
        """
        inputs = {
            '_options': {
                    'computer': self.computer,
                    'resources': {
                        'num_machines': 1,
                        'num_mpiprocs_per_machine': 1
                    },
                    'max_wallclock_seconds': 10,
                },
            '_label': None,
            '_description': None
        }

        self._run_inputs(inputs)

    def _run_inputs(self, inputs):
        job_class = TemplatereplacerCalculation.process()
        job_instance = job_class.new_instance(inputs)

        job_instance.stop()
        job_instance.run_until_complete()

        return job_instance
