# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.backends.testbase import AiidaTestCase
from aiida.engine import CalcJob, WorkChain
from aiida.orm import Data
from aiida.parsers import Parser
from aiida.plugins import factories
from aiida.plugins.entry_point import get_entry_points
from aiida.schedulers import Scheduler
from aiida.transports import Transport
from aiida.tools.dbimporters import DbImporter


class TestExistingPlugins(AiidaTestCase):
    """
    Test the get_entry_points function and the plugin Factories.

    Will fail when:

        * If get_entry_points returns something other than a list
        * Any of the plugins, distributed with aiida or installed
          from external plugin repositories, fail to load
    """

    def test_existing_calculations(self):
        """Test listing all preinstalled calculations."""
        entry_points = get_entry_points('aiida.calculations')
        self.assertIsInstance(entry_points, list)

        for entry_point in entry_points:
            cls = factories.CalculationFactory(entry_point.name)
            self.assertTrue(issubclass(cls, CalcJob),
                'Calculation plugin class {} is not subclass of {}'.format(cls, CalcJob))

    def test_existing_data(self):
        """Test listing all preinstalled data classes."""
        entry_points = get_entry_points('aiida.data')
        self.assertIsInstance(entry_points, list)

        for entry_point in entry_points:
            cls = factories.DataFactory(entry_point.name)
            self.assertTrue(issubclass(cls, Data),
                'Data plugin class {} is not subclass of {}'.format(cls, Data))

    def test_existing_parsers(self):
        """Test listing all preinstalled parsers."""
        entry_points = get_entry_points('aiida.parsers')
        self.assertIsInstance(entry_points, list)

        for entry_point in entry_points:
            cls = factories.ParserFactory(entry_point.name)
            self.assertTrue(issubclass(cls, Parser),
                'Parser plugin class {} is not subclass of {}'.format(cls, Parser))

    def test_existing_schedulers(self):
        """Test listing all preinstalled schedulers."""
        entry_points = get_entry_points('aiida.schedulers')
        self.assertIsInstance(entry_points, list)

        for entry_point in entry_points:
            cls = factories.SchedulerFactory(entry_point.name)
            self.assertTrue(issubclass(cls, Scheduler),
                'Scheduler plugin class {} is not subclass of {}'.format(cls, Scheduler))

    def test_existing_transports(self):
        """Test listing all preinstalled transports."""
        entry_points = get_entry_points('aiida.transports')
        self.assertIsInstance(entry_points, list)

        for entry_point in entry_points:
            cls = factories.TransportFactory(entry_point.name)
            self.assertTrue(issubclass(cls, Transport),
                'Transport plugin class {} is not subclass of {}'.format(cls, Transport))

    def test_existing_workflows(self):
        """Test listing all preinstalled workflows."""
        entry_points = get_entry_points('aiida.workflows')
        self.assertIsInstance(entry_points, list)

        for entry_point in entry_points:
            cls = factories.WorkflowFactory(entry_point.name)
            self.assertTrue(issubclass(cls, WorkChain),
                'Workflow plugin class {} is not a subclass of {}'.format(cls, WorkChain))

    def test_existing_dbimporters(self):
        """Test listing all preinstalled dbimporter plugins."""
        entry_points = get_entry_points('aiida.tools.dbimporters')
        self.assertIsInstance(entry_points, list)

        for entry_point in entry_points:
            cls = factories.DbImporterFactory(entry_point.name)
            self.assertTrue(issubclass(cls, DbImporter),
                'DbImporter plugin class {} is not subclass of {}'.format(cls, DbImporter))
