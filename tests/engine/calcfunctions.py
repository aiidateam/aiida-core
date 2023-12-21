"""Definition of a calculation function used in ``test_calcfunctions.py``."""
from aiida.engine import calcfunction
from aiida.orm import Int


@calcfunction
def add_calcfunction(data):
    """Calcfunction mirroring a ``test_calcfunctions`` calcfunction but has a slightly different implementation."""
    return Int(data.value + 2)
