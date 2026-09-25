###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :mod:`aiida.common.callables` module."""

import dataclasses
import functools
import inspect
import operator
import os
import subprocess
import sys
import textwrap
import typing as t
from collections.abc import Callable
from importlib import import_module
from pathlib import Path
from types import ModuleType

import pytest

from aiida.common import callables


def module_level():
    """A function that a name reference resolves to, since this module can be imported."""


@pytest.mark.parametrize(
    'value, expected',
    (
        pytest.param(operator.add, True, id='library-function'),
        pytest.param(callables.resolves_here, True, id='aiida-function'),
        pytest.param(functools.partial, True, id='class'),
        pytest.param(lambda: None, False, id='lambda'),
        pytest.param(functools.partial(operator.add, 1), False, id='partial'),
        pytest.param(operator.add.__call__, False, id='bound-method'),
    ),
)
def test_resolves_here(value: t.Any, expected):
    assert callables.resolves_here(value) is expected


def test_resolves_here_shadowed_name():
    """A closure keeps the name of the function it was defined in, so the reference would silently load the wrong
    thing.
    """

    def factory():
        def module_level():
            """A different function that shares its qualified name up to the ``<locals>`` part."""

        return module_level

    assert callables.resolves_here(factory()) is False


def test_resolves_here_a_name_that_finds_a_different_object():
    """The walk succeeding is not enough: it has to arrive back at the very object asked about. A name that lands on
    something else is the case that silently loads the wrong code.
    """

    def impostor():
        """Carries the module and qualified name of the module-level function defined above it."""

    impostor.__module__ = module_level.__module__
    impostor.__qualname__ = module_level.__qualname__

    assert callables.resolves_here(module_level) is True
    assert callables.resolves_here(impostor) is False


def test_resolves_here_rejects_main_even_when_the_name_is_found(monkeypatch: pytest.MonkeyPatch):
    """``__main__`` is a different module in the interpreter that would import it, so the name resolves to nothing
    there however well it resolves here. Under pytest ``__main__`` is the runner, in a notebook it is the kernel.
    """

    def defined_in_main():
        """Stands in for something a script or a cell defines."""

    monkeypatch.setitem(sys.modules, '__main__', sys.modules[__name__])
    monkeypatch.setattr(sys.modules['__main__'], 'defined_in_main', defined_in_main, raising=False)
    monkeypatch.setattr(defined_in_main, '__module__', '__main__')
    monkeypatch.setattr(defined_in_main, '__qualname__', 'defined_in_main')

    # The name is findable, so only the ``__main__`` rule keeps this from resolving.
    assert getattr(sys.modules['__main__'], 'defined_in_main') is defined_in_main
    assert callables.resolves_here(defined_in_main) is False


def test_round_trip():
    """Test that :func:`~aiida.common.callables.dumps` carries the state a callable closes over."""
    offset = 10
    assert callables.loads(callables.dumps(lambda value: value + offset))(1) == 11


@pytest.fixture
def local_module(importable_module: Callable[..., ModuleType]):
    """A module that exists only here, as one a user writes does."""
    return importable_module('mylib', 'SCALE = 3\n\n\ndef compute(value):\n    return value * SCALE\n')


@pytest.fixture
def local_package(importable_module: Callable[..., ModuleType]):
    """A module that calls into a second one, which is the shape a single module cannot carry."""
    return importable_module(
        'myfront',
        'import myhelper\n\n\ndef compute(value):\n    return myhelper.triple(value)\n',
        myhelper='def triple(value):\n    return value * 3\n',
    )


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
        from aiida.common import callables
        print(callables.loads(pathlib.Path({str(path)!r}).read_bytes())(5))
    """)
    process = subprocess.run([sys.executable, '-c', script], capture_output=True, text=True, cwd=os.sep, check=False)

    return process.stdout.strip() if process.returncode == 0 else process.stderr.strip()


def test_dumps_refers_to_the_module(local_module: ModuleType, tmp_path: Path):
    """Test that the default payload refers to the defining module, so it cannot travel to where that is missing."""
    assert "No module named 'mylib'" in load_elsewhere(callables.dumps(local_module.compute), tmp_path)


def test_dumps_carries_the_module(local_module: ModuleType, tmp_path: Path):
    """Test that a carried module travels inside the payload, so a machine without it can run the callable."""
    payload = callables.dumps(local_module.compute, carry=[local_module])

    assert load_elsewhere(payload, tmp_path) == '15'
    assert len(payload) > len(callables.dumps(local_module.compute))


def test_dumps_carries_every_module_that_is_needed(local_package: ModuleType, tmp_path: Path):
    """Carrying only the defining module leaves the payload referring to the second one by name, which is exactly the
    reference that cannot be resolved where the module is missing.
    """
    only_its_own = callables.dumps(local_package.compute, carry=[local_package])
    assert "No module named 'myhelper'" in load_elsewhere(only_its_own, tmp_path)

    needed = callables.modules_unimportable_by(lambda name: name not in ('myfront', 'myhelper'))
    everything = callables.dumps(local_package.compute, carry=needed.values())
    assert load_elsewhere(everything, tmp_path) == '15'


@pytest.fixture
def local_namespace_package(tmp_path: Path):
    """A module calling into a helper *directory* that has no ``__init__.py``, which makes it a namespace package.

    A folder of helpers beside a notebook is one of these, and it is the shape that has no file of its own: its spec
    carries no origin, exactly as a builtin's does not. Only its ``__path__`` tells the two apart.
    """
    (tmp_path / 'nshelper').mkdir()
    (tmp_path / 'nshelper' / 'tool.py').write_text('def triple(value):\n    return value * 3\n')
    (tmp_path / 'nsfront.py').write_text(
        'import nshelper.tool\n\n\ndef compute(value):\n    return nshelper.tool.triple(value)\n'
    )

    if str(tmp_path) not in sys.path:
        sys.path.insert(0, str(tmp_path))

    yield import_module('nsfront')

    if str(tmp_path) in sys.path:
        sys.path.remove(str(tmp_path))

    for name in ('nsfront', 'nshelper.tool', 'nshelper'):
        sys.modules.pop(name, None)


def test_dumps_carries_a_namespace_package(local_namespace_package: ModuleType, tmp_path: Path):
    """The package itself has to travel, not only the submodule under it.

    Having no origin, it read as a module that comes with any interpreter, so it was left out while its submodule was
    carried, and the reader got a submodule with no package to hang it on.
    """
    assert sys.modules['nshelper'].__spec__.origin is None, 'premise: a namespace package has no origin'

    # The real predicate against a reader holding everything this interpreter has except the helpers' own directory,
    # which is what a daemon worker looks like. A hand-written predicate naming `nshelper` would pass either way,
    # since it never reaches the origin test that was wrong.
    worker_without: tuple[str, ...] = tuple(entry for entry in sys.path if entry != str(tmp_path))
    needed = callables.modules_unimportable_by(
        can_import=functools.partial(callables.module_resolves_in, search_paths=worker_without)
    )

    assert 'nshelper' in needed
    assert len(needed) * 2 <= len(sys.modules), 'the ordinary result is a handful of modules'

    assert load_elsewhere(callables.dumps(local_namespace_package.compute, carry=needed.values()), tmp_path) == '15'


def test_module_resolves_in_accepts_a_namespace_package_the_reader_has(local_namespace_package: ModuleType):
    """The other direction: a reader searching the very directory it is made of needs no copy of it."""
    portions: list[str] = list(sys.modules['nshelper'].__path__)

    assert callables.module_resolves_in('nshelper', [str(Path(portions[0]).parent)])
    assert not callables.module_resolves_in('nshelper', ['/nowhere'])


def test_module_resolves_in_a_path_holding_a_different_namespace_package(
    local_namespace_package: ModuleType, tmp_path: Path
):
    """A reader whose own ``nshelper/`` is a different directory does not have this one.

    Only comparing the directories catches this. A reader with no such name at all is already refused by the
    lookup returning nothing, so without this case the comparison itself is never what decides.
    """
    other = tmp_path / 'elsewhere'
    (other / 'nshelper').mkdir(parents=True)
    (other / 'nshelper' / 'tool.py').write_text('def triple(value):\n    return value * 99\n')

    from importlib.machinery import PathFinder

    found = PathFinder.find_spec('nshelper', [str(other)])

    assert found is not None, 'premise: the reader does find a namespace package of that name'
    assert list(found.submodule_search_locations) == [str(other / 'nshelper')]

    assert callables.module_resolves_in('nshelper', [str(other)]) is False


def test_dumps_carrying_a_module_travels_for_a_closure(local_module: ModuleType, tmp_path: Path):
    """A closure has no name to replace with a reference, so it is written out whole either way. What breaks is the
    module it calls into, and only carrying that module fixes it.
    """

    def closure(value: t.Any):
        return local_module.compute(value)

    assert "No module named 'mylib'" in load_elsewhere(callables.dumps(closure), tmp_path)
    assert load_elsewhere(callables.dumps(closure, carry=[local_module]), tmp_path) == '15'


def test_dumps_leaves_a_caller_registration_alone(local_module: ModuleType):
    """``cloudpickle``'s registry is process global, so unregistering a module we did not register would silently
    change how another caller's callables serialize.
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
    offset = 10

    def closure(value: t.Any):
        return value + offset

    assert callables.dumps(closure) == callables.dumps(closure, carry=[])


def test_dumps_invalid():
    generator = (value for value in range(3))

    with pytest.raises(TypeError, match=r'.* could not be serialized: .*'):
        callables.dumps(lambda: generator)


def test_loads_invalid():
    with pytest.raises(ValueError, match=r'the serialized callable could not be deserialized: .*'):
        callables.loads(b'not-a-payload')


def test_module_resolves_in_a_path_that_has_it(local_module: ModuleType, tmp_path: Path):
    assert callables.module_resolves_in('mylib', [str(tmp_path)]) is True


def test_module_resolves_in_walks_a_dotted_name():
    """A name several packages deep resolves, since each part is searched under the previous one."""
    assert callables.module_resolves_in('aiida.common.callables', sys.path) is True


def test_module_resolves_in_a_path_that_lacks_it(local_module: ModuleType, tmp_path: Path):
    """A module importable here and absent there is what a directory added to ``sys.path`` after the daemon was
    started looks like from the daemon's side.
    """
    assert callables.module_resolves_in('mylib', [entry for entry in sys.path if entry != str(tmp_path)]) is False


def test_module_resolves_in_a_path_holding_a_different_file(local_module: ModuleType, tmp_path: Path):
    """A name finding a different file there does not resolve, which is the case that runs the wrong code."""
    other = tmp_path / 'elsewhere'
    other.mkdir()
    (other / 'mylib.py').write_text('SCALE = 99\n\n\ndef compute(value):\n    return value * SCALE\n')

    assert callables.module_resolves_in('mylib', [str(other)]) is False


def test_module_resolves_in_a_path_where_the_package_is_a_module(tmp_path: Path):
    """A dotted name stops where a part has nothing to descend into: a package here can be a plain module there, and
    the submodule then exists on neither side of the comparison.
    """
    here = tmp_path / 'here'
    (here / 'pkg').mkdir(parents=True)
    (here / 'pkg' / '__init__.py').write_text('')
    (here / 'pkg' / 'sub.py').write_text('value = 1\n')

    there = tmp_path / 'there'
    there.mkdir()
    (there / 'pkg.py').write_text('value = 1\n')

    sys.path.insert(0, str(here))

    try:
        import_module('pkg.sub')
        assert callables.module_resolves_in('pkg.sub', [str(here)]) is True
        assert callables.module_resolves_in('pkg.sub', [str(there)]) is False
    finally:
        sys.path.remove(str(here))
        sys.modules.pop('pkg.sub', None)
        sys.modules.pop('pkg', None)


def test_module_resolves_in_never_resolves_main():
    """``__main__`` is the entry point of whichever interpreter is running, so the name refers to a different module
    there however the paths line up. Everything defined in a script or a notebook cell lands here.
    """
    assert callables.module_resolves_in('__main__', sys.path) is False


def test_module_resolves_in_a_module_with_no_file():
    """A builtin resolves, since it comes with the interpreter rather than from a path."""
    assert callables.module_resolves_in('sys', []) is True


class SourceInAFilelessModule:
    """A class whose source `inspect.getsource` cannot reach through its module."""

    def method(self):
        return 'the cell this came from'


def test_source_of_a_class_whose_module_has_no_file(monkeypatch: pytest.MonkeyPatch):
    """``inspect.getsource`` reaches a class through the file of the module that defines it, and a class defined in a
    notebook cell has no such file: the kernel's ``__main__`` is not one.
    """
    fileless = ModuleType('fileless')
    monkeypatch.setitem(sys.modules, 'fileless', fileless)
    monkeypatch.setattr(SourceInAFilelessModule, '__module__', 'fileless')

    # A module with no ``__file__`` makes ``inspect`` give up, as ``OSError`` in a kernel and ``TypeError`` here.
    with pytest.raises((OSError, TypeError)):
        inspect.getsource(SourceInAFilelessModule)

    source = callables.source_of(SourceInAFilelessModule)

    assert source is not None
    assert source.splitlines()[0] == 'class SourceInAFilelessModule:'
    assert 'the cell this came from' in source


def test_source_of_skips_a_member_from_another_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """A class reached through its methods is searched member by member, and a method compiled elsewhere leads to a
    file the class statement is not in. The search has to carry on to the next member.

    The foreign member has to be the one met first, which means replacing a name the class body already declares:
    ``setattr`` of a new name appends to the class dictionary, landing behind every real method, where the search
    answers before ever reaching it.
    """
    decoy = tmp_path / 'decoy.py'
    decoy.write_text('def unrelated():\n    return 1\n')
    elsewhere: dict[str, t.Any] = {}
    exec(compile(decoy.read_text(), str(decoy), 'exec'), elsewhere)

    cell = tmp_path / 'cell.py'
    cell.write_text('class SourceBorrowing:\n    borrowed = None\n\n    def method(self):\n        return 1\n')
    namespace: dict[str, t.Any] = {}
    exec(compile(cell.read_text(), str(cell), 'exec'), namespace)
    wanted: type = namespace['SourceBorrowing']

    fileless = ModuleType('fileless_skip')
    monkeypatch.setitem(sys.modules, 'fileless_skip', fileless)
    monkeypatch.setattr(wanted, '__module__', 'fileless_skip')
    monkeypatch.setattr(wanted, 'borrowed', elsewhere['unrelated'])

    with_code = [name for name, member in vars(wanted).items() if getattr(member, '__code__', None) is not None]

    assert with_code[0] == 'borrowed', 'the member leading elsewhere has to be the one the search meets first'

    source = callables.source_of(wanted)

    assert source is not None
    assert source.splitlines()[0] == 'class SourceBorrowing:'


def test_source_of_a_class_no_member_leads_back_to(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Every member leading somewhere the class statement is not leaves nothing to return."""
    decoy = tmp_path / 'only_decoy.py'
    decoy.write_text('def unrelated():\n    return 1\n')
    namespace: dict[str, t.Any] = {}
    exec(compile(decoy.read_text(), str(decoy), 'exec'), namespace)

    fileless = ModuleType('fileless_none')
    monkeypatch.setitem(sys.modules, 'fileless_none', fileless)

    class NoSourceAnywhere:
        """Its only member with code was compiled from a file that holds no class statement."""

    monkeypatch.setattr(NoSourceAnywhere, '__module__', 'fileless_none')
    monkeypatch.setattr(NoSourceAnywhere, 'from_elsewhere', namespace['unrelated'], raising=False)

    assert callables.source_of(NoSourceAnywhere) is None


def test_source_of_a_class_whose_name_prefixes_a_sibling(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """A notebook cell defining ``MyCalcJob`` and ``MyCalcJobParser`` is the ordinary case, and a prefix match on
    ``class MyCalcJob`` reaches the parser first whenever it is written first.
    """
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
    monkeypatch.setitem(sys.modules, 'fileless_prefix', fileless)
    wanted: type = namespace['SourcePrefix']
    monkeypatch.setattr(wanted, '__module__', 'fileless_prefix')

    source: str | None = callables.source_of(wanted)

    assert source is not None
    assert source.splitlines()[0] == 'class SourcePrefix:'
    assert 'the body wanted' in source
    assert 'the extended body' not in source


def test_source_of_something_with_no_source():
    assert callables.source_of(len) is None


def test_source_of_something_unhashable():
    """A class that defines ``__eq__`` has no hash, which ``@dataclass`` does by default."""

    @dataclasses.dataclass
    class Unhashable:
        threshold: int = 10

        def __call__(self):
            return self.threshold

    assert callables.source_of(Unhashable()) is None


def test_modules_unimportable_by_finds_what_the_worker_lacks(local_package: ModuleType):
    missing = callables.modules_unimportable_by(lambda name: name not in ('myfront', 'myhelper'))

    assert sorted(missing) == ['myfront', 'myhelper']
    assert 'sys' not in callables.modules_unimportable_by(lambda name: name != 'myfront')


def test_modules_unimportable_by_ignores_what_the_callable_reaches(local_package: ModuleType):
    """Whether a particular callable reaches a module is not worth working out: ``cloudpickle`` writes only what the
    object it is given reaches, so carrying one it never touches produces the same bytes, and a set derived
    by walking names misses what is reached at runtime.
    """
    import importlib

    reached_only_at_runtime = importlib.import_module('myhelper')

    missing = callables.modules_unimportable_by(lambda name: name not in ('myfront', 'myhelper'))

    assert reached_only_at_runtime.__name__ in missing


def test_modules_unimportable_by_skips_an_entry_that_is_not_a_module():
    """A lazy stand-in or a failed import left in ``sys.modules`` is passed over: registering a non-module by value
    would fail.
    """
    sys.modules['not-a-module'] = 'a string someone left behind'  # type: ignore[assignment]

    try:
        missing = callables.modules_unimportable_by(lambda name: False)
    finally:
        del sys.modules['not-a-module']

    assert 'not-a-module' not in missing


def test_modules_unimportable_by_skips_an_alias():
    import json

    sys.modules['json_alias'] = json

    try:
        missing = callables.modules_unimportable_by(lambda name: False)
    finally:
        del sys.modules['json_alias']

    assert 'json_alias' not in missing
    assert 'json' in missing


def test_modules_unimportable_by_walks_a_snapshot(monkeypatch: pytest.MonkeyPatch):
    """The walk goes over a copy, so an import part-way through it cannot raise.

    Iterating ``sys.modules.items()`` builds a tuple per module, and on CPython below 3.12 those allocations can
    run a generation-0 collection whose finalizers import, which changes the size of the mapping mid-iteration and
    raises ``RuntimeError``. A worker doing that while it saved a checkpoint is what turned the 3.10 job red.

    The mapping here refuses to be iterated at all, which pins the copy on every version rather than only on the
    ones whose collector reaches into the allocation.
    """

    class RefusesToBeWalked(dict):
        def items(self):
            msg = 'dictionary changed size during iteration'
            raise RuntimeError(msg)

        def keys(self):
            msg = 'dictionary changed size during iteration'
            raise RuntimeError(msg)

    monkeypatch.setattr(sys, 'modules', RefusesToBeWalked(sys.modules))

    with pytest.raises(RuntimeError):
        sys.modules.items()

    assert 'json' in callables.modules_unimportable_by(lambda name: False)


def test_dumps_carrying_the_same_module_twice():
    """``unregister_pickle_by_value`` raises on a module that is not registered, so a duplicate would raise out of
    the ``finally`` that undoes the registrations.
    """
    carried = ModuleType('carried_twice')
    carried.__file__ = '/carried/twice.py'
    sys.modules['carried_twice'] = carried

    try:
        assert callables.loads(callables.dumps(len, carry=[carried, carried])) is len
    finally:
        del sys.modules['carried_twice']
