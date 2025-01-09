###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :py:mod:`~aiida.plugins.factories` module."""

import pytest

from aiida.common.exceptions import InvalidEntryPointTypeError
from aiida.engine import CalcJob, CalcJobImporter, WorkChain, calcfunction, workfunction
from aiida.orm import CalcFunctionNode, Data, Node, WorkFunctionNode
from aiida.orm.implementation.storage_backend import StorageBackend
from aiida.parsers import Parser
from aiida.plugins import entry_point, factories
from aiida.schedulers import Scheduler
from aiida.tools.data.orbital import Orbital
from aiida.tools.dbimporters import DbImporter
from aiida.transports import AsyncTransport, BlockingTransport, Transport


def custom_load_entry_point(group, name):
    """Function that mocks :meth:`aiida.plugins.entry_point.load_entry_point` that is called by factories."""

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
            'work_chain': WorkChain,
        },
        'aiida.calculations.importers': {
            'importer': CalcJobImporter,
            'invalid': CalcJob,
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
        'aiida.storage': {
            'valid': StorageBackend,
            'invalid': Node,
        },
        'aiida.transports': {
            'valid_AsyncTransport': AsyncTransport,
            'valid_BlockingTransport': BlockingTransport,
            'valid_Transport': Transport,
            'invalid': Node,
        },
        'aiida.workflows': {
            'calc_job': CalcJob,
            'calc_function': calc_function,
            'work_function': work_function,
            'work_chain': WorkChain,
        },
    }
    return entry_points[group][name]


@pytest.fixture
def mock_load_entry_point(monkeypatch):
    """Monkeypatch the :meth:`aiida.plugins.entry_point.load_entry_point` method."""
    monkeypatch.setattr(entry_point, 'load_entry_point', custom_load_entry_point)
    yield


class TestFactories:
    """Tests for the :py:mod:`~aiida.plugins.factories` factory classes."""

    @pytest.mark.usefixtures('mock_load_entry_point')
    def test_calculation_factory(self):
        """Test the ```CalculationFactory```."""
        plugin = factories.CalculationFactory('calc_function')
        assert plugin.is_process_function
        assert plugin.node_class is CalcFunctionNode

        plugin = factories.CalculationFactory('calc_job')
        assert plugin is CalcJob

        with pytest.raises(InvalidEntryPointTypeError):
            factories.CalculationFactory('work_function')

        with pytest.raises(InvalidEntryPointTypeError):
            factories.CalculationFactory('work_chain')

    @pytest.mark.usefixtures('mock_load_entry_point')
    def test_calc_job_importer_factory(self):
        """Test the ``CalcJobImporterFactory``."""
        plugin = factories.CalcJobImporterFactory('importer')
        assert plugin is CalcJobImporter

        with pytest.raises(InvalidEntryPointTypeError):
            factories.CalcJobImporterFactory('invalid')

    @pytest.mark.usefixtures('mock_load_entry_point')
    def test_workflow_factory(self):
        """Test the ``WorkflowFactory``."""
        plugin = factories.WorkflowFactory('work_function')
        assert plugin.is_process_function
        assert plugin.node_class is WorkFunctionNode

        plugin = factories.WorkflowFactory('work_chain')
        assert plugin is WorkChain

        with pytest.raises(InvalidEntryPointTypeError):
            factories.WorkflowFactory('calc_function')

        with pytest.raises(InvalidEntryPointTypeError):
            factories.WorkflowFactory('calc_job')

    @pytest.mark.usefixtures('mock_load_entry_point')
    def test_data_factory(self):
        """Test the ``DataFactory``."""
        plugin = factories.DataFactory('valid')
        assert plugin is Data

        with pytest.raises(InvalidEntryPointTypeError):
            factories.DataFactory('invalid')

    @pytest.mark.usefixtures('mock_load_entry_point')
    def test_db_importer_factory(self):
        """Test the ``DbImporterFactory``."""
        plugin = factories.DbImporterFactory('valid')
        assert plugin is DbImporter

        with pytest.raises(InvalidEntryPointTypeError):
            factories.DbImporterFactory('invalid')

    @pytest.mark.usefixtures('mock_load_entry_point')
    def test_orbital_factory(self):
        """Test the ``OrbitalFactory``."""
        plugin = factories.OrbitalFactory('valid')
        assert plugin is Orbital

        with pytest.raises(InvalidEntryPointTypeError):
            factories.OrbitalFactory('invalid')

    @pytest.mark.usefixtures('mock_load_entry_point')
    def test_parser_factory(self):
        """Test the ``ParserFactory``."""
        plugin = factories.ParserFactory('valid')
        assert plugin is Parser

        with pytest.raises(InvalidEntryPointTypeError):
            factories.ParserFactory('invalid')

    @pytest.mark.usefixtures('mock_load_entry_point')
    def test_scheduler_factory(self):
        """Test the ``SchedulerFactory``."""
        plugin = factories.SchedulerFactory('valid')
        assert plugin is Scheduler

        with pytest.raises(InvalidEntryPointTypeError):
            factories.SchedulerFactory('invalid')

    @pytest.mark.usefixtures('mock_load_entry_point')
    def test_storage_factory(self):
        """Test the ``StorageFactory``."""
        plugin = factories.StorageFactory('valid')
        assert plugin is StorageBackend

        with pytest.raises(InvalidEntryPointTypeError):
            factories.StorageFactory('invalid')

    @pytest.mark.usefixtures('mock_load_entry_point')
    def test_transport_factory(self):
        """Test the ``TransportFactory``."""
        plugin = factories.TransportFactory('valid_Transport')
        assert plugin is Transport

        plugin = factories.TransportFactory('valid_AsyncTransport')
        assert plugin is AsyncTransport
        assert issubclass(plugin, Transport)

        plugin = factories.TransportFactory('valid_BlockingTransport')
        assert plugin is BlockingTransport
        assert issubclass(plugin, Transport)

        with pytest.raises(InvalidEntryPointTypeError):
            factories.TransportFactory('invalid')
