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
import inspect
import operator
import os
import subprocess
import sys
import textwrap
import types

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


@pytest.fixture
def local_package(tmp_path):
    """Yield a module that calls into a second one, which is the shape a single module cannot carry."""
    (tmp_path / 'myhelper.py').write_text('def triple(value):\n    return value * 3\n')
    (tmp_path / 'myfront.py').write_text(
        'import myhelper\n\n\ndef compute(value):\n    return myhelper.triple(value)\n'
    )
    sys.path.insert(0, str(tmp_path))

    try:
        import myfront

        yield myfront
    finally:
        sys.path.remove(str(tmp_path))
        for name in ('myfront', 'myhelper'):
            del sys.modules[name]


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


def test_dumps_carries_the_module(local_module, tmp_path):
    """Test that a carried module travels inside the payload, so a machine without it can run the callable."""
    payload = callables.dumps(local_module.compute, carry=[local_module])

    assert load_elsewhere(payload, tmp_path) == '15'
    assert len(payload) > len(callables.dumps(local_module.compute))


def test_dumps_carries_every_module_that_is_needed(local_package, tmp_path):
    """Test that a callable reaching a second local module needs that one carried too.

    Carrying only the defining module leaves the payload referring to the second one by name, which is exactly the
    reference that cannot be resolved where the module is missing.
    """
    only_its_own = callables.dumps(local_package.compute, carry=[local_package])
    assert "No module named 'myhelper'" in load_elsewhere(only_its_own, tmp_path)

    needed = callables.modules_missing_from(lambda name: name not in ('myfront', 'myhelper'))
    everything = callables.dumps(local_package.compute, carry=needed.values())
    assert load_elsewhere(everything, tmp_path) == '15'


def test_dumps_carrying_a_module_travels_for_a_closure(local_module, tmp_path):
    """Test that a closure reaching a local module needs it carried, which no property of the closure can supply.

    A closure has no name to replace with a reference, so it is written out whole either way. What breaks is the
    module it calls into, and only carrying that module fixes it.
    """

    def closure(value):
        return local_module.compute(value)

    assert "No module named 'mylib'" in load_elsewhere(callables.dumps(closure), tmp_path)
    assert load_elsewhere(callables.dumps(closure, carry=[local_module]), tmp_path) == '15'


def test_dumps_leaves_a_caller_registration_alone(local_module):
    """Test that serializing does not undo a by-value registration somebody else made.

    ``cloudpickle``'s registry is process global, so unregistering a module we did not register would silently change
    how another caller's callables serialize.
    """
    import cloudpickle

    cloudpickle.register_pickle_by_value(local_module)

    try:
        callables.dumps(local_module.compute, carry=[local_module])
        assert local_module.__name__ in cloudpickle.list_registry_pickle_by_value()
    finally:
        if local_module.__name__ in cloudpickle.list_registry_pickle_by_value():
            cloudpickle.unregister_pickle_by_value(local_module)


def test_dumps_carries_nothing_by_default():
    """Test that a callable no name refers to is carried whole, and nothing else rides along with it."""
    offset = 10

    def closure(value):
        return value + offset

    assert callables.dumps(closure) == callables.dumps(closure, carry=[])


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


def test_resolves_in_a_path_that_has_the_module(local_module, tmp_path):
    """Test that a module found under the given paths, at the very file it was imported from, resolves."""
    assert callables.resolves_in(local_module.compute, [str(tmp_path)]) is True


def test_resolves_in_walks_a_dotted_name():
    """Test that a name several packages deep resolves, since each part is searched under the previous one."""
    assert callables.resolves_in(callables.is_importable, sys.path) is True


def test_resolves_in_a_path_that_lacks_the_module(local_module, tmp_path):
    """Test that a module importable here and absent there does not resolve.

    This is what a directory added to ``sys.path`` after the daemon was started looks like from the daemon's side.
    """
    assert callables.is_importable(local_module.compute) is True
    assert callables.resolves_in(local_module.compute, [entry for entry in sys.path if entry != str(tmp_path)]) is False


def test_resolves_in_a_path_holding_a_different_file(local_module, tmp_path):
    """Test that a name finding a different file there does not resolve, which is the case that runs the wrong code."""
    other = tmp_path / 'other'
    other.mkdir()
    (other / 'mylib.py').write_text('def compute(value):\n    return 0\n')

    assert callables.resolves_in(local_module.compute, [str(other)]) is False


def test_resolves_in_needs_a_name_at_all():
    """Test that a callable no name identifies never resolves, whatever the paths are."""
    assert callables.resolves_in(lambda: None, sys.path) is False


def test_resolves_in_a_module_with_no_file():
    """Test that a builtin resolves, since it comes with the interpreter rather than from a path."""
    assert callables.resolves_in(sys.exit, []) is True


class SourceInAFilelessModule:
    """A class whose source `inspect.getsource` cannot reach through its module."""

    def method(self):
        return 'the cell this came from'


def test_source_of_a_class_whose_module_has_no_file(monkeypatch):
    """Test that a class is read from the file its own methods came from, when its module has none.

    ``inspect.getsource`` reaches a class through the file of the module that defines it, and a class defined in a
    notebook cell has no such file: the kernel's ``__main__`` is not one.
    """
    fileless = types.ModuleType('fileless')
    monkeypatch.setitem(sys.modules, 'fileless', fileless)
    monkeypatch.setattr(SourceInAFilelessModule, '__module__', 'fileless')

    # A module with no ``__file__`` makes ``inspect`` give up, as ``OSError`` in a kernel and ``TypeError`` here.
    with pytest.raises((OSError, TypeError)):
        inspect.getsource(SourceInAFilelessModule)

    source = callables.source_of(SourceInAFilelessModule)

    assert source is not None
    assert source.splitlines()[0] == 'class SourceInAFilelessModule:'
    assert 'the cell this came from' in source


def test_source_of_something_with_no_source():
    """Test that a callable with no source to read says so rather than raising."""
    assert callables.source_of(len) is None


def test_modules_missing_from_finds_what_the_reader_lacks(local_package):
    """Test that a module the reader cannot import is offered up, and one it has is not."""
    missing = callables.modules_missing_from(lambda name: name not in ('myfront', 'myhelper'))

    assert sorted(missing) == ['myfront', 'myhelper']
    assert 'sys' not in callables.modules_missing_from(lambda name: name != 'myfront')


def test_modules_missing_from_does_not_ask_the_callable(local_package):
    """Test that the answer does not depend on any callable, which is the point of asking it this way.

    Whether a particular callable reaches a module is not worth working out: ``cloudpickle`` writes only what the
    object it is given reaches, so carrying one it never touches produces the same bytes, and any answer derived by
    walking names misses what is reached at runtime.
    """
    import importlib

    reached_only_at_runtime = importlib.import_module('myhelper')

    missing = callables.modules_missing_from(lambda name: name not in ('myfront', 'myhelper'))

    assert reached_only_at_runtime.__name__ in missing


def test_modules_missing_from_skips_an_entry_that_is_not_a_module():
    """Test that a lazy stand-in or a failed import left in ``sys.modules`` is passed over.

    ``sys.modules`` holds whatever was put there, and registering a non-module by value would fail.
    """
    sys.modules['not-a-module'] = 'a string someone left behind'  # type: ignore[assignment]

    try:
        missing = callables.modules_missing_from(lambda name: False)
    finally:
        del sys.modules['not-a-module']

    assert 'not-a-module' not in missing


def test_modules_missing_from_skips_an_alias():
    """Test that a module reachable under a second name is carried under its own name only."""
    import json

    sys.modules['json_alias'] = json

    try:
        missing = callables.modules_missing_from(lambda name: False)
    finally:
        del sys.modules['json_alias']

    assert 'json_alias' not in missing
    assert 'json' in missing
