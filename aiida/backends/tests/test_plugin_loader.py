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
from aiida.backends.testbase import AiidaTestCase
from aiida.plugins.entry_point import get_entry_points
from aiida.orm import CalculationFactory, DataFactory, WorkflowFactory
from aiida.orm import Workflow
from aiida.parsers import Parser, ParserFactory
from aiida.orm.data import Data
from aiida.orm import Calculation
from aiida.scheduler import Scheduler, SchedulerFactory
from aiida.transport import Transport, TransportFactory
from aiida.tools.dbexporters.tcod_plugins import BaseTcodtranslator, TcodExporterFactory
from aiida.tools.dbimporters import DbImporter, DbImporterFactory
from aiida.work import WorkChain


class TestExistingPlugins(AiidaTestCase):
    """
    Test the get_entry_points function and the plugin Factories.
    Will fail when:

        * If get_entry_points returns something other than a list
        * Any of the plugins, distributed with aiida or installed
          from external plugin repositories, fail to load
    """

    def test_existing_calculations(self):
        """
        Test listing all preinstalled calculations
        """
        entry_points = get_entry_points('aiida.calculations')
        self.assertIsInstance(entry_points, list)

        for entry_point in entry_points:
            cls = CalculationFactory(entry_point.name)
            self.assertTrue(issubclass(cls, Calculation),
                'Calculation plugin class {} is not subclass of {}'.format(cls, Calculation))

    def test_existing_data(self):
        """
        Test listing all preinstalled data classes
        """
        entry_points = get_entry_points('aiida.data')
        self.assertIsInstance(entry_points, list)

        for entry_point in entry_points:
            cls = DataFactory(entry_point.name)
            self.assertTrue(issubclass(cls, Data),
                'Data plugin class {} is not subclass of {}'.format(cls, Data))

    def test_existing_parsers(self):
        """
        Test listing all preinstalled parsers
        """
        entry_points = get_entry_points('aiida.parsers')
        self.assertIsInstance(entry_points, list)

        for entry_point in entry_points:
            cls = ParserFactory(entry_point.name)
            self.assertTrue(issubclass(cls, Parser),
                'Parser plugin class {} is not subclass of {}'.format(cls, Parser))

    def test_existing_schedulers(self):
        """
        Test listing all preinstalled schedulers
        """
        entry_points = get_entry_points('aiida.schedulers')
        self.assertIsInstance(entry_points, list)

        for entry_point in entry_points:
            cls = SchedulerFactory(entry_point.name)
            self.assertTrue(issubclass(cls, Scheduler),
                'Scheduler plugin class {} is not subclass of {}'.format(cls, Scheduler))

    def test_existing_transports(self):
        """
        Test listing all preinstalled transports
        """
        entry_points = get_entry_points('aiida.transports')
        self.assertIsInstance(entry_points, list)

        for entry_point in entry_points:
            cls = TransportFactory(entry_point.name)
            self.assertTrue(issubclass(cls, Transport),
                'Transport plugin class {} is not subclass of {}'.format(cls, Transport))

    def test_existing_workflows(self):
        """
        Test listing all preinstalled workflows
        """
        entry_points = get_entry_points('aiida.workflows')
        self.assertIsInstance(entry_points, list)

        for entry_point in entry_points:
            cls = WorkflowFactory(entry_point.name)
            self.assertTrue(issubclass(cls, (Workflow, WorkChain)),
                'Workflow plugin class {} is neither a subclass of {} nor {}'.format(cls, Workflow, WorkChain))

    def test_existing_tcod_plugins(self):
        """
        Test listing all preinstalled tcod exporter plugins
        """
        entry_points = get_entry_points('aiida.tools.dbexporters.tcod_plugins')
        self.assertIsInstance(entry_points, list)

        for entry_point in entry_points:
            cls = TcodExporterFactory(entry_point.name)
            self.assertTrue(issubclass(cls, BaseTcodtranslator),
                'TcodExporter plugin class {} is not subclass of {}'.format(cls, BaseTcodtranslator))

    def test_existing_dbimporters(self):
        """
        Test listing all preinstalled dbimporter plugins
        """
        entry_points = get_entry_points('aiida.tools.dbimporters')
        self.assertIsInstance(entry_points, list)

        for entry_point in entry_points:
            cls = DbImporterFactory(entry_point.name)
            self.assertTrue(issubclass(cls, DbImporter),
                'DbImporter plugin class {} is not subclass of {}'.format(cls, BaseTcodtranslator))
