# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :py:mod:`~aiida.plugins.factories` module."""
from unittest.mock import patch

from aiida.backends.testbase import AiidaTestCase
from aiida.common.exceptions import InvalidEntryPointTypeError
from aiida.engine import calcfunction, workfunction, CalcJob, WorkChain
from aiida.orm import Data, Node, CalcFunctionNode, WorkFunctionNode
from aiida.parsers import Parser
from aiida.plugins import factories
from aiida.schedulers import Scheduler
from aiida.transports import Transport
from aiida.tools.data.orbital import Orbital
from aiida.tools.dbimporters import DbImporter


def custom_load_entry_point(group, name):
    """Function that mocks `aiida.plugins.entry_point.load_entry_point` that is called by factories."""

    @calcfunction
    def calc_function():
        pass

    @workfunction
    def work_function():
        pass

    entry_points = {
        'aiida.calculations': {
            'calc_job': CalcJob,
            'calc_function': calc_function,
            'work_function': work_function,
            'work_chain': WorkChain
        },
        'aiida.data': {
            'valid': Data,
            'invalid': Node,
        },
        'aiida.tools.dbimporters': {
            'valid': DbImporter,
            'invalid': Node,
        },
        'aiida.tools.data.orbitals': {
            'valid': Orbital,
            'invalid': Node,
        },
        'aiida.parsers': {
            'valid': Parser,
            'invalid': Node,
        },
        'aiida.schedulers': {
            'valid': Scheduler,
            'invalid': Node,
        },
        'aiida.transports': {
            'valid': Transport,
            'invalid': Node,
        },
        'aiida.workflows': {
            'calc_job': CalcJob,
            'calc_function': calc_function,
            'work_function': work_function,
            'work_chain': WorkChain
        }
    }
    return entry_points[group][name]


class TestFactories(AiidaTestCase):
    """Tests for the :py:mod:`~aiida.plugins.factories` factory classes."""

    @patch('aiida.plugins.entry_point.load_entry_point', custom_load_entry_point)
    def test_calculation_factory(self):
        """Test the `CalculationFactory`."""
        plugin = factories.CalculationFactory('calc_function')
        self.assertEqual(plugin.is_process_function, True)
        self.assertEqual(plugin.node_class, CalcFunctionNode)

        plugin = factories.CalculationFactory('calc_job')
        self.assertEqual(plugin, CalcJob)

        with self.assertRaises(InvalidEntryPointTypeError):
            factories.CalculationFactory('work_function')

        with self.assertRaises(InvalidEntryPointTypeError):
            factories.CalculationFactory('work_chain')

    @patch('aiida.plugins.entry_point.load_entry_point', custom_load_entry_point)
    def test_workflow_factory(self):
        """Test the `WorkflowFactory`."""
        plugin = factories.WorkflowFactory('work_function')
        self.assertEqual(plugin.is_process_function, True)
        self.assertEqual(plugin.node_class, WorkFunctionNode)

        plugin = factories.WorkflowFactory('work_chain')
        self.assertEqual(plugin, WorkChain)

        with self.assertRaises(InvalidEntryPointTypeError):
            factories.WorkflowFactory('calc_function')

        with self.assertRaises(InvalidEntryPointTypeError):
            factories.WorkflowFactory('calc_job')

    @patch('aiida.plugins.entry_point.load_entry_point', custom_load_entry_point)
    def test_data_factory(self):
        """Test the `DataFactory`."""
        plugin = factories.DataFactory('valid')
        self.assertEqual(plugin, Data)

        with self.assertRaises(InvalidEntryPointTypeError):
            factories.DataFactory('invalid')

    @patch('aiida.plugins.entry_point.load_entry_point', custom_load_entry_point)
    def test_db_importer_factory(self):
        """Test the `DbImporterFactory`."""
        plugin = factories.DbImporterFactory('valid')
        self.assertEqual(plugin, DbImporter)

        with self.assertRaises(InvalidEntryPointTypeError):
            factories.DbImporterFactory('invalid')

    @patch('aiida.plugins.entry_point.load_entry_point', custom_load_entry_point)
    def test_orbital_factory(self):
        """Test the `OrbitalFactory`."""
        plugin = factories.OrbitalFactory('valid')
        self.assertEqual(plugin, Orbital)

        with self.assertRaises(InvalidEntryPointTypeError):
            factories.OrbitalFactory('invalid')

    @patch('aiida.plugins.entry_point.load_entry_point', custom_load_entry_point)
    def test_parser_factory(self):
        """Test the `ParserFactory`."""
        plugin = factories.ParserFactory('valid')
        self.assertEqual(plugin, Parser)

        with self.assertRaises(InvalidEntryPointTypeError):
            factories.ParserFactory('invalid')

    @patch('aiida.plugins.entry_point.load_entry_point', custom_load_entry_point)
    def test_scheduler_factory(self):
        """Test the `SchedulerFactory`."""
        plugin = factories.SchedulerFactory('valid')
        self.assertEqual(plugin, Scheduler)

        with self.assertRaises(InvalidEntryPointTypeError):
            factories.SchedulerFactory('invalid')

    @patch('aiida.plugins.entry_point.load_entry_point', custom_load_entry_point)
    def test_transport_factory(self):
        """Test the `TransportFactory`."""
        plugin = factories.TransportFactory('valid')
        self.assertEqual(plugin, Transport)

        with self.assertRaises(InvalidEntryPointTypeError):
            factories.TransportFactory('invalid')
