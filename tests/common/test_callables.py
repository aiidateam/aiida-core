###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :mod:`aiida.common._callables` module."""

import os
import subprocess
import sys
import textwrap
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest

from aiida.common import _callables as callables


def test_round_trip():
    """Test that :func:`~aiida.common._callables.dumps` carries the state a callable closes over."""
    offset = 10
    assert callables.loads(callables.dumps(lambda value: value + offset))(1) == 11


def load_elsewhere(payload: bytes, tmp_path: Path) -> str:
    """Load a payload in an interpreter that cannot import the module the callable was defined in.

    This stands in for the remote computer a calculation job uploads a callable to, which has aiida installed but
    nothing of the user's own code.
    """
    path = tmp_path / 'payload.pkl'
    path.write_bytes(payload)

    script = textwrap.dedent(f"""
        import pathlib, sys
        sys.path = [entry for entry in sys.path if entry != {str(tmp_path)!r}]
        try:
            import mylib
        except ImportError:
            pass
        else:
            msg = 'mylib is importable here, so this test proves nothing'
            raise SystemExit(msg)
        from aiida.common import _callables as callables
        print(callables.loads(pathlib.Path({str(path)!r}).read_bytes())(5))
    """)
    process = subprocess.run([sys.executable, '-c', script], capture_output=True, text=True, cwd=os.sep, check=False)

    return process.stdout.strip() if process.returncode == 0 else process.stderr.strip()


@pytest.fixture
def local_module(importable_module: Callable[..., ModuleType]):
    """A module that exists only here, as one a user writes does."""
    return importable_module('mylib', 'SCALE = 3\n\n\ndef compute(value):\n    return value * SCALE\n')


def test_dumps_refers_to_the_module(local_module: ModuleType, tmp_path: Path):
    """Test that the default payload refers to the defining module, so it cannot travel to where that is missing."""
    assert "No module named 'mylib'" in load_elsewhere(callables.dumps(local_module.compute), tmp_path)


def test_dumps_invalid():
    generator = (value for value in range(3))

    with pytest.raises(TypeError, match=r'.* could not be serialized: .*'):
        callables.dumps(lambda: generator)


def test_loads_invalid():
    with pytest.raises(ValueError, match=r'the serialized callable could not be deserialized: .*'):
        callables.loads(b'not-a-payload')
