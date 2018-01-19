# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida import work
from aiida.backends.testbase import AiidaTestCase
from aiida.orm.calculation.job.simpleplugins.templatereplacer import TemplatereplacerCalculation
from aiida.work.class_loader import ClassLoader
from aiida.work.job_processes import JobProcess

from . import utils

Job = TemplatereplacerCalculation.process()


class TestJobProcess(AiidaTestCase):
    def setUp(self):
        super(TestJobProcess, self).setUp()
        self.assertEquals(len(work.ProcessStack.stack()), 0)
        self.runner = utils.create_test_runner()

    def tearDown(self):
        super(TestJobProcess, self).tearDown()
        self.assertEquals(len(work.ProcessStack.stack()), 0)
        self.runner.close()
        self.runner = None
        work.set_runner(None)

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
        job = Job(inputs)

        self.assertEquals(job.calc.label, label)
        self.assertEquals(job.calc.description, description)

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

        Job(inputs)
