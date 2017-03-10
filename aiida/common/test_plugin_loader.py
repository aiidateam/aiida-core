# -*- coding: utf-8 -*-
from aiida.common import pluginloader as pl
import unittest


class TestExistingPlugins(unittest.TestCase):
    """
    Test pluginloader's existing_plugins function.

    * will fail when any of the plugins distributede with aiida fail to load.
    * will fail when pluginloader gets broken.
    * will fail if pluginloader returns something else than a list
    """
    def setUp(self):
        from aiida import load_dbenv, is_dbenv_loaded
        if not is_dbenv_loaded():
            load_dbenv()

    def test_existing_calculations(self):
        """Test listing all preinstalled calculations """
        from aiida.orm.calculation.job import JobCalculation
        calcs = pl.existing_plugins(JobCalculation, 'aiida.orm.calculation.job', suffix='Calculation')
        self.assertIsInstance(calcs, list)

    def test_existing_parsers(self):
        """Test listing all preinstalled parsers"""
        from aiida.parsers import Parser
        pars = pl.existing_plugins(Parser, 'aiida.parsers.plugins')
        self.assertIsInstance(calcs, list)

    def test_existing_data(self):
        """Test listing all preinstalled data formats"""
        from aiida.orm.data import Data
        data = pl.existing_plugins(Data, 'aiida.orm.data')
        self.assertIsInstance(data, list)

    def test_existing_schedulers(self):
        """Test listing all preinstalled schedulers"""
        from aiida.scheduler import Scheduler
        sche = pl.existing_plugins(Scheduler, 'aiida.scheduler.plugins')
        self.assertIsInstance(sche, list)

    def test_existing_transports(self):
        """Test listing all preinstalled transports"""
        from aiida.transport import Transport
        tran = pl.existing_plugins(Transport, 'aiida.transport.plugins')
        self.assertIsInstance(tran, list)

    def test_existing_workflows(self):
        """Test listing all preinstalled workflows"""
        from aiida.orm import Workflow
        work = pl.existing_plugins(Workflow, 'aiida.workflows')
        self.assertIsInstance(work, list)

    def test_existing_tcod_plugins(self):
        """Test listing all preinstalled tcod exporter plugins"""
        from aiida.tools.dbexporters.tcod_plugins import BaseTcodtranslator
        tcpl = pl.existing_plugins(BaseTcodtranslator, 'aiida.tools.dbexporters.tcod_plugins')
        self.assertIsInstance(tcpl, list)
