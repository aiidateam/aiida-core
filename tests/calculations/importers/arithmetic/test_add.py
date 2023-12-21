"""Tests for the :mod:`aiida.calculations.importers.arithmetic.add` module."""
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
