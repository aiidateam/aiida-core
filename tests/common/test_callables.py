###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :mod:`aiida.common.callables` module."""

import functools
import operator
import os
import subprocess
import sys
import textwrap

import pytest

from aiida.common import callables


def module_level():
    """A function that a name reference resolves to, since this module can be imported."""


@pytest.mark.parametrize(
    'value, expected',
    (
        pytest.param(operator.add, True, id='library-function'),
        pytest.param(callables.is_importable, True, id='aiida-function'),
        pytest.param(functools.partial, True, id='class'),
        pytest.param(lambda: None, False, id='lambda'),
        pytest.param(functools.partial(operator.add, 1), False, id='partial'),
        pytest.param(operator.add.__call__, False, id='bound-method'),
    ),
)
def test_is_importable(value, expected):
    """Test :func:`~aiida.common.callables.is_importable`."""
    assert callables.is_importable(value) is expected


def test_is_importable_shadowed_name():
    """Test that a name resolving to a different object than the one asked about is not importable.

    A closure keeps the name of the function it was defined in, so the reference would silently load the wrong thing.
    """

    def factory():
        def module_level():
            """A different function that shares its qualified name up to the ``<locals>`` part."""

        return module_level

    assert callables.is_importable(factory()) is False


def test_round_trip():
    """Test that :func:`~aiida.common.callables.dumps` carries the state a callable closes over."""
    offset = 10
    assert callables.loads(callables.dumps(lambda value: value + offset))(1) == 11


@pytest.fixture
def local_module(tmp_path):
    """Yield a module that exists only here, as one a user writes does, importable for the duration of the test."""
    (tmp_path / 'mylib.py').write_text('SCALE = 3\n\n\ndef compute(value):\n    return value * SCALE\n')
    sys.path.insert(0, str(tmp_path))

    try:
        import mylib

        yield mylib
    finally:
        sys.path.remove(str(tmp_path))
        del sys.modules['mylib']


def load_elsewhere(payload: bytes, tmp_path) -> str:
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
            raise SystemExit('mylib is importable here, so this test proves nothing')
        from aiida.common import callables
        print(callables.loads(pathlib.Path({str(path)!r}).read_bytes())(5))
    """)
    process = subprocess.run([sys.executable, '-c', script], capture_output=True, text=True, cwd=os.sep, check=False)

    return process.stdout.strip() if process.returncode == 0 else process.stderr.strip()


def test_dumps_refers_to_the_module(local_module, tmp_path):
    """Test that the default payload refers to the defining module, so it cannot travel to where that is missing."""
    assert "No module named 'mylib'" in load_elsewhere(callables.dumps(local_module.compute), tmp_path)


def test_dumps_invalid():
    """Test that a callable that cannot be serialized is reported as such."""
    generator = (value for value in range(3))

    with pytest.raises(TypeError, match=r'.* could not be serialized: .*'):
        callables.dumps(lambda: generator)


def test_loads_invalid():
    """Test that a payload that cannot be deserialized is reported as such."""
    with pytest.raises(ValueError, match=r'the serialized callable could not be deserialized: .*'):
        callables.loads(b'not-a-payload')


def test_fingerprint_distinguishes_captured_state():
    """Test that the fingerprint separates callables that share everything but what they capture."""

    def factory(threshold):
        def parse():
            return threshold

        return parse

    assert callables.fingerprint(factory(10)) != callables.fingerprint(factory(20))
    assert callables.fingerprint(factory(10)) == callables.fingerprint(factory(10))


def test_source_of_something_with_no_source():
    """Test that a callable with no source to read says so rather than raising."""
    assert callables.source_of(len) is None
