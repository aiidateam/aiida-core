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
from aiida.scheduler import SchedulerFactory
from aiida.transport import TransportFactory
from aiida.orm import Workflow
from aiida.orm.data import Data
from aiida.orm import JobCalculation
from aiida.scheduler import Scheduler
from aiida.tools.dbexporters.tcod_plugins import BaseTcodtranslator
from aiida.transport import Transport


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
            self.assertTrue(
                issubclass(CalculationFactory(i), JobCalculation),
                'Calculation plugin class {} is not subclass of JobCalculation'.format(
                    CalculationFactory(i)))

    def test_existing_data(self):
        """
        Test listing all preinstalled data formats
        """
        data = all_plugins('data')
        self.assertIsInstance(data, list)
        for i in data:
            self.assertTrue(issubclass(DataFactory(i), Data))

    def test_existing_schedulers(self):
        """
        Test listing all preinstalled schedulers
        """
        schedulers = all_plugins('schedulers')
        self.assertIsInstance(schedulers, list)
        for i in schedulers:
            self.assertTrue(issubclass(SchedulerFactory(i), Scheduler))

    def test_existing_transports(self):
        """
        Test listing all preinstalled transports
        """
        transports = all_plugins('transports')
        self.assertIsInstance(transports, list)
        for i in transports:
            self.assertTrue(issubclass(TransportFactory(i), Transport))

    def test_existing_workflows(self):
        """
        Test listing all preinstalled workflows
        """
        workflows = all_plugins('workflows')
        self.assertIsInstance(workflows, list)
        for i in workflows:
            self.assertTrue(issubclass(WorkflowFactory(i), Workflow))

    def test_existing_tcod_plugins(self):
        """
        Test listing all preinstalled tcod exporter plugins
        """
        tcod_plugins = all_plugins('transports')
        self.assertIsInstance(tcod_plugins, list)
