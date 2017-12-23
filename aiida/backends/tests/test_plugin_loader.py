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
from aiida.common.pluginloader import all_plugins
from aiida.orm import CalculationFactory, DataFactory, WorkflowFactory
from aiida.orm import Workflow
from aiida.parsers import Parser, ParserFactory
from aiida.orm.data import Data
from aiida.orm import JobCalculation
from aiida.scheduler import Scheduler, SchedulerFactory
from aiida.transport import Transport, TransportFactory
from aiida.tools.dbexporters.tcod_plugins import BaseTcodtranslator, TcodExporterFactory
from aiida.work import WorkChain


class TestExistingPlugins(AiidaTestCase):
    """
    Test pluginloader's all_plugins function.

    * will fail when any of the plugins distributed with aiida or installed
      from external plugin repositories, fails to load
    * will fail if pluginloader returns something else than a list
    """
    def test_existing_calculations(self):
        """
        Test listing all preinstalled calculations
        """
        calculations = all_plugins('calculations')
        self.assertIsInstance(calculations, list)
        for i in calculations:
            cls = CalculationFactory(i)
            self.assertTrue(issubclass(cls, JobCalculation),
                'Calculation plugin class {} is not subclass of {}'.format(cls, JobCalculation))

    def test_existing_data(self):
        """
        Test listing all preinstalled data classes
        """
        data = all_plugins('data')
        self.assertIsInstance(data, list)
        for i in data:
            cls = DataFactory(i)
            self.assertTrue(issubclass(cls, Data),
                'Data plugin class {} is not subclass of {}'.format(cls, Data))

    def test_existing_parsers(self):
        """
        Test listing all preinstalled parsers
        """
        parsers = all_plugins('parsers')
        self.assertIsInstance(parsers, list)
        for i in parsers:
            cls = ParserFactory(i)
            self.assertTrue(issubclass(cls, Parser),
                'Parser plugin class {} is not subclass of {}'.format(cls, Parser))

    def test_existing_schedulers(self):
        """
        Test listing all preinstalled schedulers
        """
        schedulers = all_plugins('schedulers')
        self.assertIsInstance(schedulers, list)
        for i in schedulers:
            cls = SchedulerFactory(i)
            self.assertTrue(issubclass(cls, Scheduler),
                'Scheduler plugin class {} is not subclass of {}'.format(cls, Scheduler))

    def test_existing_transports(self):
        """
        Test listing all preinstalled transports
        """
        transports = all_plugins('transports')
        self.assertIsInstance(transports, list)
        for i in transports:
            cls = TransportFactory(i)
            self.assertTrue(issubclass(cls, Transport),
                'Transport plugin class {} is not subclass of {}'.format(cls, Transport))

    def test_existing_workflows(self):
        """
        Test listing all preinstalled workflows
        """
        workflows = all_plugins('workflows')
        self.assertIsInstance(workflows, list)
        for i in workflows:
            cls = WorkflowFactory(i)
            self.assertTrue(issubclass(cls, (Workflow, WorkChain)),
                'Workflow plugin class {} is neither a subclass of {} nor {}'.format(cls, Workflow, WorkChain))

    def test_existing_tcod_plugins(self):
        """
        Test listing all preinstalled tcod exporter plugins
        """
        tcod_plugins = all_plugins('tools.dbexporters.tcod_plugins')
        self.assertIsInstance(tcod_plugins, list)
        for i in tcod_plugins:
            cls = TcodExporterFactory(i)
            self.assertTrue(issubclass(cls, BaseTcodtranslator),
                'TcodExporter plugin class {} is not subclass of {}'.format(cls, BaseTcodtranslator))
