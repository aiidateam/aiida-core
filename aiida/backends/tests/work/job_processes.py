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

import six

from aiida import work
from aiida.backends.testbase import AiidaTestCase
from aiida.common.utils import classproperty
from aiida.orm.data.int import Int
from aiida.orm.calculation.job.simpleplugins.templatereplacer import TemplatereplacerCalculation
from aiida.work.persistence import ObjectLoader
from aiida.work.job_processes import JobProcess
from aiida.work.process_builder import JobProcessBuilder
from aiida.work import Process

from . import utils


class AdditionalParameterCalculation(TemplatereplacerCalculation):
    """
    Subclass of TemplatereplacerCalculation that also defines a use method
    with an additional parameter
    """

    @classproperty
    def _use_methods(cls):
        retdict = TemplatereplacerCalculation._use_methods
        retdict.update({
            'pseudo': {
                'valid_types': Int,
                'additional_parameter': "kind",
                'linkname': cls._get_linkname_pseudo,
                'docstring': (''),
            },
        })
        return retdict

    @classmethod
    def _get_linkname_pseudo(cls, kind):
        """
        Create the linkname based on the additional parameter
        """
        if isinstance(kind, (tuple, list)):
            suffix_string = '_'.join(kind)
        elif isinstance(kind, six.string_types):
            suffix_string = kind
        else:
            raise TypeError('invalid additional parameter type')

        return '{}_{}'.format('pseudo', suffix_string)


class TestJobProcess(AiidaTestCase):

    def setUp(self):
        super(TestJobProcess, self).setUp()
        self.assertIsNone(Process.current())
        self.runner = utils.create_test_runner()

    def tearDown(self):
        super(TestJobProcess, self).tearDown()
        self.assertIsNone(Process.current())
        self.runner.close()
        self.runner = None
        work.set_runner(None)

    def test_job_calculation_process(self):
        """Verify that JobCalculation.process returns a sub class of JobProcess with correct calculation class."""
        process = TemplatereplacerCalculation.process()
        self.assertTrue(issubclass(process, JobProcess))
        self.assertEqual(process._calc_class, TemplatereplacerCalculation)

    def test_job_calculation_get_builder(self):
        """Verify that JobCalculation.get_builder() returns an instance of JobProcessBuilder."""
        process = TemplatereplacerCalculation.process()
        builder = TemplatereplacerCalculation.get_builder()
        self.assertTrue(isinstance(builder, JobProcessBuilder))

        # Class objects are actually different memory instances so can't use assertEqual on simply instances
        self.assertEqual(builder.process_class.__name__, process.__name__)

    def test_job_process_set_label_and_description(self):
        """
        Verify that calculation label and description get set when passed through inputs
        """
        label = 'test_label'
        description = 'test_description'
        inputs = {
            'options': {
                'computer': self.computer,
                'resources': {
                    'num_machines': 1,
                    'num_mpiprocs_per_machine': 1
                },
                'max_wallclock_seconds': 10,
            },
            'label': label,
            'description': description
        }
        process = TemplatereplacerCalculation.process()
        job = process(inputs)

        self.assertEquals(job.calc.label, label)
        self.assertEquals(job.calc.description, description)

    def test_job_process_label(self):
        """
        Verify that the process_label attribute is set equal to the class name of the calculation from which the
        JobProcess class was generated
        """
        inputs = {
            'options': {
                'computer': self.computer,
                'resources': {
                    'num_machines': 1,
                    'num_mpiprocs_per_machine': 1
                },
                'max_wallclock_seconds': 10,
            },
        }
        process = TemplatereplacerCalculation.process()
        job = process(inputs)

        self.assertEquals(job.calc.process_label, TemplatereplacerCalculation.__name__)

    def test_job_process_set_none(self):
        """
        Verify that calculation label and description can be not set.
        """
        inputs = {
            'options': {
                'computer': self.computer,
                'resources': {
                    'num_machines': 1,
                    'num_mpiprocs_per_machine': 1
                },
                'max_wallclock_seconds': 10,
            }
        }

        process = TemplatereplacerCalculation.process()
        job = process(inputs)


class TestAdditionalParameterJobProcess(AiidaTestCase):

    def setUp(self):
        super(TestAdditionalParameterJobProcess, self).setUp()
        self.assertIsNone(Process.current())
        self.runner = utils.create_test_runner()

    def tearDown(self):
        super(TestAdditionalParameterJobProcess, self).tearDown()
        self.assertIsNone(Process.current())
        self.runner.close()
        self.runner = None
        work.set_runner(None)

    def test_class_loader(self):
        cl = ObjectLoader()
        AdditionalParameterProcess = JobProcess.build(AdditionalParameterCalculation)

    def test_job_process_with_additional_parameter(self):
        """
        Verify that the additional parameter use_method 'pseudo' is supported
        """
        label = 'test_label'
        description = 'test_description'
        inputs = {
            'options': {
                'computer': self.computer,
                'resources': {
                    'num_machines': 1,
                    'num_mpiprocs_per_machine': 1
                },
                'max_wallclock_seconds': 10,
            },
            'pseudo': {
                'a': Int(1),
                'b': Int(2),
            },
            'label': label,
            'description': description
        }
        process = AdditionalParameterCalculation.process()
        job = process(inputs)
