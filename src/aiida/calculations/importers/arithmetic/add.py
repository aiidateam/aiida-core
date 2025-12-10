"""Importer for the :class:`aiida.calculations.arithmetic.add.ArithmeticAddCalculation` plugin."""

from pathlib import Path
from re import match
from tempfile import NamedTemporaryFile
from typing import Dict, Union

from aiida.engine import CalcJobImporter
from aiida.orm import Int, Node, RemoteData


class ArithmeticAddCalculationImporter(CalcJobImporter):
    """Importer for the :class:`aiida.calculations.arithmetic.add.ArithmeticAddCalculation` plugin."""

    @staticmethod
    def parse_remote_data(remote_data: RemoteData, **kwargs) -> Dict[str, Union[Node, Dict]]:
        """Parse the input nodes from the files in the provided ``RemoteData``.

        :param remote_data: the remote data node containing the raw input files.
        :param kwargs: additional keyword arguments to control the parsing process.
        :returns: a dictionary with the parsed inputs nodes that match the input spec of the associated ``CalcJob``.
        """
        import os

        with NamedTemporaryFile('w+', delete=False) as handle:
            temp_path = handle.name

        try:
            with remote_data.get_authinfo().get_transport() as transport:
                filepath = Path(remote_data.get_remote_path()) / 'aiida.in'
                transport.getfile(filepath, temp_path)

            with open(temp_path, 'r') as handle:
                data = handle.read()

            matches = match(r'echo \$\(\(([0-9]+) \+ ([0-9]+)\)\).*', data.strip())

            if matches is None:
                raise ValueError(f'failed to parse the integers `x` and `y` from the input content: {data}')

            return {
                'x': Int(matches.group(1)),
                'y': Int(matches.group(2)),
            }
        finally:
            try:
                os.remove(temp_path)
            except OSError:
                pass
