"""Tests for the :mod:`aiida.calculations.importers.arithmetic.add` module."""

import os
import tempfile

from aiida.calculations.importers.arithmetic.add import ArithmeticAddCalculationImporter
from aiida.orm import Int, RemoteData


def test_parse_remote_data(tmp_path, aiida_localhost):
    """Test the ``ArithmeticAddCalculationImporter.parse_remote_data`` method."""
    with (tmp_path / 'aiida.in').open('w+') as handle:
        handle.write('echo $((4 + 12))')
        handle.flush()

        remote_data = RemoteData(tmp_path, computer=aiida_localhost)
        inputs = ArithmeticAddCalculationImporter.parse_remote_data(remote_data)

        assert list(inputs.keys()) == ['x', 'y']
        assert isinstance(inputs['x'], Int)
        assert isinstance(inputs['y'], Int)
        assert inputs['x'].value == 4
        assert inputs['y'].value == 12


def test_parse_remote_data_tempfile_cleanup(tmp_path, aiida_localhost, monkeypatch):
    """Test that ``parse_remote_data`` properly cleans up temporary files."""
    # Create the input file
    with (tmp_path / 'aiida.in').open('w+') as handle:
        handle.write('echo $((4 + 12))')

    # Track created temp files
    created_files = []
    original_mkstemp = tempfile.mkstemp

    def tracking_mkstemp(*args, **kwargs):
        handle, path = original_mkstemp(*args, **kwargs)
        created_files.append(path)
        return handle, path

    monkeypatch.setattr(tempfile, 'mkstemp', tracking_mkstemp)

    # Parse the remote data
    remote_data = RemoteData(tmp_path, computer=aiida_localhost)
    inputs = ArithmeticAddCalculationImporter.parse_remote_data(remote_data)

    # Verify the parsing worked
    assert inputs['x'].value == 4
    assert inputs['y'].value == 12

    # Verify that all temporary files were cleaned up
    for temp_file in created_files:
        assert not os.path.exists(temp_file), f'Temporary file {temp_file} was not cleaned up'
