###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :mod:`aiida.common._callables` module."""

import dataclasses
import inspect
import os
import subprocess
import sys
import textwrap
import typing as t
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest

from aiida.common import _callables as callables


def test_closure_round_trip():
    """Serialization preserves captured state."""
    offset = 10
    assert callables.loads(callables.dumps(lambda value: value + offset))(1) == 11


def load_elsewhere(payload: bytes, tmp_path: Path) -> str:
    """Load and call the payload in a subprocess where `mylib` is unavailable.

    Return stripped stdout on success or stripped stderr on failure.
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
def local_module(importable_module: Callable[..., ModuleType]) -> ModuleType:
    """Return a temporary `mylib` module."""
    return importable_module(
        'mylib',
        textwrap.dedent("""
            SCALE = 3


            def compute(value):
                return value * SCALE
            """),
    )


def test_dumps_refers_to_the_module(local_module: ModuleType, tmp_path: Path):
    """Deserialization requires the referenced module."""
    assert "No module named 'mylib'" in load_elsewhere(callables.dumps(local_module.compute), tmp_path)


def test_dumps_invalid():
    """An unserializable capture raises `TypeError` naming the value."""
    generator = (value for value in range(3))

    with pytest.raises(TypeError, match=r'.* could not be serialized: .*'):
        callables.dumps(lambda: generator)


def test_loads_invalid():
    """A foreign payload raises `ValueError` instead of leaking the pickle error."""
    with pytest.raises(ValueError, match=r'the serialized callable could not be deserialized: .*'):
        callables.loads(b'not-a-payload')


class SourceInAFilelessModule:
    """A class whose source `inspect.getsource` cannot reach through its module."""

    def method(self):
        return 'the cell this came from'


def test_source_of_a_class_whose_module_has_no_file(monkeypatch: pytest.MonkeyPatch):
    """Recover class source when its defining module has no file."""
    fileless = ModuleType('fileless')
    monkeypatch.setitem(dic=sys.modules, name='fileless', value=fileless)
    monkeypatch.setattr(target=SourceInAFilelessModule, name='__module__', value='fileless')

    # A module with no ``__file__`` makes ``inspect`` give up, as ``OSError`` in a kernel and ``TypeError`` here.
    with pytest.raises((OSError, TypeError)):
        inspect.getsource(SourceInAFilelessModule)

    source = callables.source_of(SourceInAFilelessModule)

    assert source is not None
    assert source.splitlines()[0] == 'class SourceInAFilelessModule:'
    assert 'the cell this came from' in source


def test_source_of_a_decorated_class(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """The recorded source starts at the decorator of a decorated class."""
    cell = tmp_path / 'decorated.py'
    cell.write_text(
        textwrap.dedent("""
            def marker(cls):
                return cls


            @marker
            class Decorated:
                def method(self):
                    return 'marked'
            """)
    )
    namespace: dict[str, t.Any] = {}
    exec(compile(cell.read_text(), str(cell), 'exec'), namespace)

    fileless = ModuleType('fileless_decorated')
    monkeypatch.setitem(dic=sys.modules, name='fileless_decorated', value=fileless)
    wanted: type = namespace['Decorated']
    monkeypatch.setattr(target=wanted, name='__module__', value='fileless_decorated')

    source: str | None = callables.source_of(wanted)

    assert source is not None
    assert source.splitlines()[0] == '@marker'
    assert "return 'marked'" in source


def test_source_of_skips_a_member_from_another_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Recover class source after skipping its first code-bearing member from another file."""
    decoy = tmp_path / 'decoy.py'
    decoy.write_text(
        textwrap.dedent("""
            def unrelated():
                return 1
            """)
    )
    elsewhere: dict[str, t.Any] = {}
    exec(compile(decoy.read_text(), str(decoy), 'exec'), elsewhere)

    cell = tmp_path / 'cell.py'
    cell.write_text(
        textwrap.dedent("""
            class SourceBorrowing:
                borrowed = None

                def method(self):
                    return 1
            """)
    )
    namespace: dict[str, t.Any] = {}
    exec(compile(cell.read_text(), str(cell), 'exec'), namespace)
    wanted: type = namespace['SourceBorrowing']

    fileless = ModuleType('fileless_skip')
    monkeypatch.setitem(dic=sys.modules, name='fileless_skip', value=fileless)
    monkeypatch.setattr(target=wanted, name='__module__', value='fileless_skip')
    monkeypatch.setattr(target=wanted, name='borrowed', value=elsewhere['unrelated'])

    with_code = [name for name, member in vars(wanted).items() if getattr(member, '__code__', None) is not None]

    assert with_code[0] == 'borrowed', 'the member leading elsewhere has to be the one the search meets first'

    source = callables.source_of(wanted)

    assert source is not None
    assert source.splitlines()[0] == 'class SourceBorrowing:'


def test_source_of_a_class_with_only_foreign_members(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Return no source when every code-bearing member belongs to another definition."""
    decoy = tmp_path / 'only_decoy.py'
    decoy.write_text(
        textwrap.dedent("""
            def unrelated():
                return 1
            """)
    )
    namespace: dict[str, t.Any] = {}
    exec(compile(decoy.read_text(), str(decoy), 'exec'), namespace)

    fileless = ModuleType('fileless_none')
    monkeypatch.setitem(dic=sys.modules, name='fileless_none', value=fileless)

    class NoSourceAnywhere:
        """Source-recovery fixture with a foreign method."""

    monkeypatch.setattr(target=NoSourceAnywhere, name='__module__', value='fileless_none')
    monkeypatch.setattr(target=NoSourceAnywhere, name='from_elsewhere', value=namespace['unrelated'], raising=False)

    assert callables.source_of(NoSourceAnywhere) is None


def test_source_of_a_class_whose_name_prefixes_a_sibling(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Recover the exact class when an earlier sibling has the same name prefix."""
    cell = tmp_path / 'both.py'
    cell.write_text(
        textwrap.dedent("""
            class SourcePrefixExtended:
                def method(self):
                    return 'the extended body'


            class SourcePrefix:
                def method(self):
                    return 'the body wanted'
            """)
    )
    namespace: dict[str, t.Any] = {}
    exec(compile(cell.read_text(), str(cell), 'exec'), namespace)

    fileless = ModuleType('fileless_prefix')
    monkeypatch.setitem(dic=sys.modules, name='fileless_prefix', value=fileless)
    wanted: type = namespace['SourcePrefix']
    monkeypatch.setattr(target=wanted, name='__module__', value='fileless_prefix')

    source: str | None = callables.source_of(wanted)

    assert source is not None
    assert source.splitlines()[0] == 'class SourcePrefix:'
    assert 'the body wanted' in source
    assert 'the extended body' not in source


@pytest.mark.parametrize('file_backed', [pytest.param(False, id='cell'), pytest.param(True, id='module')])
def test_source_of_selects_the_redefined_class(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, file_backed: bool):
    """The inspected method identifies its owning definition among duplicate class names."""
    cell: Path = tmp_path / 'duplicates.py'
    cell.write_text(
        'class Probe:\n    def method(self):\n        return "old"\n\n'
        'class Probe:\n    def method(self):\n        return "new"\n'
    )
    module: ModuleType = ModuleType('duplicate_definitions')
    if file_backed:
        module.__file__ = str(cell)
    monkeypatch.setitem(dic=sys.modules, name=module.__name__, value=module)
    exec(compile(cell.read_text(), str(cell), 'exec'), module.__dict__)
    assert module.Probe().method() == 'new'
    source: str | None = callables.source_of(value=module.Probe)
    assert source is not None
    assert '"new"' in source
    assert '"old"' not in source


def test_source_of_selects_the_inner_duplicate_class(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """The inspected method identifies its owning definition among nested duplicate class names."""
    cell: Path = tmp_path / 'nested.py'
    cell.write_text(
        textwrap.dedent("""
            class Outer:
                class Outer:
                    def method(self):
                        return "inner"
            """)
    )
    module: ModuleType = ModuleType('nested_definitions')
    monkeypatch.setitem(dic=sys.modules, name=module.__name__, value=module)
    exec(compile(cell.read_text(), str(cell), 'exec'), module.__dict__)
    inner: type = module.Outer.Outer
    source: str | None = callables.source_of(value=inner)
    assert source is not None
    assert source.splitlines()[0] == '    class Outer:'
    assert '"inner"' in source


def test_source_of_incomplete_source_is_unavailable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Return no source when the file becomes syntactically incomplete after compilation."""
    cell: Path = tmp_path / 'incomplete.py'
    cell.write_text(
        textwrap.dedent("""
            class Probe:
                def method(self):
                    return 1
            """)
    )
    module: ModuleType = ModuleType('fileless_incomplete')
    monkeypatch.setitem(dic=sys.modules, name=module.__name__, value=module)
    exec(compile(cell.read_text(), str(cell), 'exec'), module.__dict__)
    cell.write_text(
        textwrap.dedent("""
            class Probe:
                def method(self):
                    return (
            """)
    )
    assert callables.source_of(value=module.Probe) is None


def test_source_of_a_builtin_returns_no_source():
    """A builtin has no retrievable source."""
    assert callables.source_of(len) is None


def test_source_of_an_unhashable_callable():
    """An unhashable callable instance returns no source."""

    @dataclasses.dataclass
    class Unhashable:
        threshold: int = 10

        def __call__(self):
            return self.threshold

    assert callables.source_of(Unhashable()) is None
