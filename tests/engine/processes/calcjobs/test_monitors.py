"""Tests for the :mod:`aiida.engine.processes.calcjobs.monitors` module."""

from __future__ import annotations

import os
import tempfile
import time
from unittest.mock import MagicMock

import pytest

from aiida.calculations.arithmetic.add import ArithmeticAddCalculation
from aiida.calculations.monitors import base
from aiida.common.exceptions import EntryPointError
from aiida.engine import run_get_node
from aiida.engine.processes.calcjobs.monitors import (
    CalcJobMonitor,
    CalcJobMonitorAction,
    CalcJobMonitorResult,
    CalcJobMonitors,
)
from aiida.orm import Dict, Int, Str


class StoreMessageCalculation(ArithmeticAddCalculation):
    """Subclass of ``ArithmeticAddCalculation`` that just adds the ``messages`` output namespace."""

    @classmethod
    def define(cls, spec):
        """Define the process specification, including its inputs, outputs and known exit codes.

        :param spec: the calculation job process spec to define.
        """
        super().define(spec)
        spec.output_namespace('messages', valid_type=Str)


def monitor_store_message(node, transport, **kwargs):
    """Test monitor that returns an output node."""
    import datetime
    import secrets

    return CalcJobMonitorResult(
        action=CalcJobMonitorAction.DISABLE_ALL,
        outputs={
            'messages': {'datetime_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'): Str(secrets.token_hex(15))}
        },
    )


def test_calc_job_monitor_result_constructor_invalid():
    """Test :class:`aiida.engine.processes.calcjobs.monitors.CalcJobMonitorResult` constructor for invalid input."""
    with pytest.raises(TypeError, match=r'got an unexpected keyword argument .*'):
        CalcJobMonitorResult(invalid_key='test')

    with pytest.raises(TypeError, match=r'Got object of type .*'):
        CalcJobMonitorResult(key=[])

    with pytest.raises(TypeError, match=r'Got object of type .*'):
        CalcJobMonitorResult(message=[])

    with pytest.raises(TypeError, match=r'Got object of type .*'):
        CalcJobMonitorResult(message='message', action=[])

    with pytest.raises(TypeError, match=r'Got object of type .*'):
        CalcJobMonitorResult(message='message', parse='true')

    with pytest.raises(TypeError, match=r'Got object of type .*'):
        CalcJobMonitorResult(message='message', retrieve='true')

    with pytest.raises(ValueError, match=r'`parse` cannot be `True` if `retrieve` is `False`.'):
        CalcJobMonitorResult(message='message', retrieve=False, parse=True)

    with pytest.raises(TypeError, match=r'Got object of type .*'):
        CalcJobMonitorResult(message='message', override_exit_code='true')


def test_calc_job_monitor_result_constructor_valid():
    """Test the :class:`aiida.engine.processes.calcjobs.monitors.CalcJobMonitorResult` constructor for valid input."""
    key = 'some_monitor'
    message = 'some message'
    result = CalcJobMonitorResult(key=key, message=message)
    assert result.key == key
    assert result.message == message
    assert result.action == CalcJobMonitorAction.KILL
    assert result.retrieve is True
    assert result.parse is True
    assert result.override_exit_code is True


def test_calc_job_monitor_constructor_invalid():
    """Test :class:`aiida.engine.processes.calcjobs.monitors.CalcJobMonitor` constructor for invalid input."""
    with pytest.raises(TypeError, match=r'missing 1 required positional argument: .*'):
        CalcJobMonitor()

    with pytest.raises(TypeError, match=r'got an unexpected keyword argument .*'):
        CalcJobMonitor(invalid_key='test')

    with pytest.raises(TypeError, match=r'Got object of type .*'):
        CalcJobMonitor(entry_point=[])

    with pytest.raises(TypeError, match=r'Got object of type .*'):
        CalcJobMonitor(entry_point='core.always_kill', kwargs=[])

    with pytest.raises(TypeError, match=r'Got object of type .*'):
        CalcJobMonitor(entry_point='core.always_kill', priority='one')

    with pytest.raises(TypeError, match=r'Got object of type .*'):
        CalcJobMonitor(entry_point='core.always_kill', minimum_poll_interval='one')

    with pytest.raises(ValueError, match=r'The `minimum_poll_interval` must be a positive integer greater than zero.'):
        CalcJobMonitor(entry_point='core.always_kill', minimum_poll_interval=-1)

    with pytest.raises(ValueError, match=r'The monitor `core.always_kill` does not accept the keywords.*'):
        CalcJobMonitor(entry_point='core.always_kill', kwargs={'unsupported': 1})

    with pytest.raises(EntryPointError, match=r'Entry point \'core.non_existant\' not found in group.*'):
        CalcJobMonitor(entry_point='core.non_existant')


def test_calc_job_monitor_constructor_valid():
    """Test the :class:`aiida.engine.processes.calcjobs.monitors.CalcJobMonitor` constructor for valid input."""
    entry_point = 'core.always_kill'
    monitor = CalcJobMonitor(entry_point)
    assert monitor.entry_point == entry_point
    assert not monitor.kwargs
    assert monitor.priority == 0
    assert monitor.minimum_poll_interval is None
    assert monitor.call_timestamp is None


def test_calc_job_monitor_load_entry_point():
    """Test the :meth:`aiida.engine.processes.calcjobs.monitors.CalcJobMonitor.load_entry_point`."""
    entry_point = 'core.always_kill'
    monitor = CalcJobMonitor(entry_point)
    assert monitor.load_entry_point() == base.always_kill


@pytest.mark.parametrize(
    'monitors, expected',
    (
        ({'a': {}, 'b': {}}, ['a', 'b']),
        ({'a': {}, 'b': {'priority': 1}}, ['b', 'a']),
        ({'a': {'priority': 2}, 'b': {'priority': 1}}, ['a', 'b']),
        ({'b': {'priority': 3}, 'aab': {'priority': 2}, 'aaa': {'priority': 2}}, ['b', 'aaa', 'aab']),
    ),
)
def test_calc_job_monitors_monitors(monitors, expected):
    """Test the :meth:`aiida.engine.processes.calcjobs.monitors.CalcJobMonitors.monitors` property."""
    monitors_full = {}

    for key, value in monitors.items():
        monitors_full[key] = value
        monitors_full[key]['entry_point'] = 'core.always_kill'
        monitors_full[key] = Dict(monitors_full[key])

    assert list(CalcJobMonitors(monitors_full).monitors.keys()) == expected


def test_calc_job_monitors_process_poll_interval(monkeypatch):
    """Test the :meth:`aiida.engine.processes.calcjobs.monitors.CalcJobMonitors.process` method.

    Test that the ``minimum_poll_interval`` of the monitors is respected.
    """
    monitors = CalcJobMonitors({'always_kill': Dict({'entry_point': 'core.always_kill', 'minimum_poll_interval': 1})})

    def always_kill(*args, **kwargs):
        return 'always_kill called'

    monkeypatch.setattr(base, 'always_kill', always_kill)

    # First call should simple go through and so raise
    result = monitors.process(None, None)
    assert isinstance(result, CalcJobMonitorResult)
    assert result.message == 'always_kill called'

    # Calling again should skip it since the minimum poll interval has not yet passed
    assert monitors.process(None, None) is None

    time.sleep(1)

    # After the intervalhas passed, it should be called again
    result = monitors.process(None, None)
    assert isinstance(result, CalcJobMonitorResult)
    assert result.message == 'always_kill called'


def monitor_emit_warning(node, transport, **kwargs):
    """Test monitor that logs a warning when called."""
    from aiida.common.log import AIIDA_LOGGER

    AIIDA_LOGGER.warning('monitor_emit_warning monitor was called')


def test_calc_job_monitors_process_poll_interval_integrated(entry_points, aiida_code_installed, caplog):
    """Test the ``minimum_poll_interval`` input by actually running through the engine."""
    entry_points.add(monitor_emit_warning, 'aiida.calculations.monitors:core.emit_warning')

    code = aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash')
    builder = code.get_builder()
    builder.x = Int(1)
    builder.y = Int(1)
    builder.monitors = {'always_kill': Dict({'entry_point': 'core.emit_warning', 'minimum_poll_interval': 5})}
    builder.metadata = {'options': {'sleep': 1, 'resources': {'num_machines': 1}}}

    _, node = run_get_node(builder)
    assert node.is_finished_ok

    # Check that the number of log messages emitted by the monitor is just 1 as it should have been called just once.
    logs = [rec.message for rec in caplog.records if rec.message == 'monitor_emit_warning monitor was called']
    assert len(logs) == 1


def test_calc_job_monitors_outputs(entry_points, aiida_code_installed):
    """Test a monitor that returns outputs to be attached to the node."""
    entry_points.add(StoreMessageCalculation, 'aiida.calculations:core.store_message')
    entry_points.add(monitor_store_message, 'aiida.calculations.monitors:core.store_message')

    code = aiida_code_installed(default_calc_job_plugin='core.store_message', filepath_executable='/bin/bash')
    builder = code.get_builder()
    builder.x = Int(1)
    builder.y = Int(1)
    builder.monitors = {'store_message': Dict({'entry_point': 'core.store_message', 'minimum_poll_interval': 1})}
    builder.metadata = {'options': {'sleep': 3, 'resources': {'num_machines': 1}}}

    _, node = run_get_node(builder)
    assert node.is_finished_ok
    assert 'messages' in node.outputs
    assert len(node.outputs.messages)
    for message in node.outputs.messages.values():
        assert isinstance(message, Str)
        assert len(message.value) == 30, message.value


def test_always_kill_tempfile_cleanup(tmp_path, monkeypatch):
    """Test that the ``always_kill`` monitor properly cleans up temporary files."""
    # Create a mock node with a remote workdir
    mock_node = MagicMock()
    mock_node.get_remote_workdir.return_value = str(tmp_path)

    # Create a test submission script
    submit_script = tmp_path / '_aiidasubmit.sh'
    submit_script.write_text('#!/bin/bash\necho "test"')

    # Create a mock transport
    mock_transport = MagicMock()

    # Track created temp files
    created_files = []
    original_mkstemp = tempfile.mkstemp

    def tracking_mkstemp(*args, **kwargs):
        handle, path = original_mkstemp(*args, **kwargs)
        created_files.append(path)
        return handle, path

    monkeypatch.setattr(tempfile, 'mkstemp', tracking_mkstemp)

    # Mock getfile to copy the submit script to the temp file
    def mock_getfile(remote_path, local_path):
        with open(local_path, 'w', encoding='utf-8') as f:
            f.write(submit_script.read_text())

    mock_transport.getfile = mock_getfile

    # Call the monitor function
    result = base.always_kill(mock_node, mock_transport)

    # Verify the result
    assert result == 'Detected a non-empty submission script'

    # Verify that all temporary files were cleaned up
    for temp_file in created_files:
        assert not os.path.exists(temp_file), f'Temporary file {temp_file} was not cleaned up'
