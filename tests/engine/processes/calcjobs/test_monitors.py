# -*- coding: utf-8 -*-
"""Tests for the :mod:`aiida.engine.processes.calcjobs.monitors` module."""
import pytest

from aiida.calculations.monitors.base import always_kill
from aiida.common.exceptions import EntryPointError
from aiida.engine.processes.calcjobs.monitors import CalcJobMonitor


def test_calc_job_monitor_constructor_invalid():
    """Test :class:`aiida.engine.processes.calcjobs.monitors.CalcJobMonitor` constructor for invalid input."""
    with pytest.raises(TypeError, match=r'missing 1 required positional argument: .*'):
        CalcJobMonitor()  # pylint: disable=no-value-for-parameter

    with pytest.raises(TypeError, match=r'got an unexpected keyword argument .*'):
        CalcJobMonitor(invalid_key='test')  # pylint: disable=unexpected-keyword-arg,no-value-for-parameter

    with pytest.raises(TypeError, match=r'Got object of type .*'):
        CalcJobMonitor(entry_point=[])

    with pytest.raises(TypeError, match=r'Got object of type .*'):
        CalcJobMonitor(entry_point='core.always_kill', kwargs=[])

    with pytest.raises(ValueError, match=r'The monitor `core.always_kill` does not accept the keywords.*'):
        CalcJobMonitor(entry_point='core.always_kill', kwargs={'unsupported': 1})

    with pytest.raises(EntryPointError, match=r'Entry point \'core.non_existant\' not found in group.*'):
        CalcJobMonitor(entry_point='core.non_existant')


def test_calc_job_monitor_constructor_valid():
    """Test the :class:`aiida.engine.processes.calcjobs.monitors.CalcJobMonitor` constructor for valid input."""
    entry_point = 'core.always_kill'
    monitor = CalcJobMonitor(entry_point)
    assert monitor.entry_point == entry_point
    assert monitor.kwargs == {}


def test_calc_job_monitor_load_entry_point():
    """Test the :meth:`aiida.engine.processes.calcjobs.monitors.CalcJobMonitor.load_entry_point`."""
    entry_point = 'core.always_kill'
    monitor = CalcJobMonitor(entry_point)
    assert monitor.load_entry_point() == always_kill  # pylint: disable=comparison-with-callable
