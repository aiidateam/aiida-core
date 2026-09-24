###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utilities to identify Python callables and to move them between interpreters."""

from __future__ import annotations

import functools
import importlib
import sys
import typing as t
from types import ModuleType

if t.TYPE_CHECKING:
    from collections.abc import Callable, Collection, Sequence
    from importlib.machinery import ModuleSpec


def resolves_here(value: t.Any) -> bool:
    """Return whether this interpreter recovers ``value`` by importing it under its own name.

    Importability is a fact about one interpreter, and the result covers only the one running now. An object
    read back somewhere else depends on that interpreter instead.

    :param value: The object to check.
    :returns: ``True`` if importing ``__module__`` and following ``__qualname__`` yields ``value`` itself.
    """
    module_name: str | None = getattr(value, '__module__', None)
    qualname: str | None = getattr(value, '__qualname__', None)

    # ``__main__`` resolves to a different module in the interpreter that would have to do the importing, so a name
    # defined there resolves to nothing. This is why a function defined in a script cannot be recovered by name.
    if module_name is None or qualname is None or module_name == '__main__':
        return False

    try:
        resolved: t.Any = importlib.import_module(name=module_name)
        for attribute in qualname.split(sep='.'):
            resolved = getattr(resolved, attribute)
    except (ImportError, AttributeError):
        return False

    return resolved is value


@functools.lru_cache(maxsize=4096)
def _find_spec(module_name: str, search_paths: tuple[str, ...]) -> ModuleSpec | None:
    """Return the spec an interpreter searching ``search_paths`` would import ``module_name`` from.

    This walks the filesystem, and it runs on every state transition of every process, so it is cached. The paths
    passed in are those of a running daemon, which do not change while that daemon runs. The cache holds
    more entries than an interpreter has modules, since :func:`modules_unimportable_by` covers all of them in one
    pass and a smaller one would be evicted within that pass.

    :param module_name: The dotted name of the module to look for.
    :param search_paths: The ``sys.path`` of the interpreter that would do the importing.
    :returns: The spec of the module that would be found, or ``None`` if none would be.
    """
    from importlib.machinery import PathFinder

    finder: PathFinder = PathFinder()
    head, *rest = module_name.split(sep='.')
    spec: ModuleSpec | None = finder.find_spec(fullname=head, path=list(search_paths))

    for part in rest:
        # Only a package carries search locations, so a module with a name still to walk leads nowhere.
        if spec is None or spec.submodule_search_locations is None:
            return None

        spec = finder.find_spec(fullname=f'{spec.name}.{part}', path=list(spec.submodule_search_locations))

    return spec


def module_resolves_in(module_name: str, search_paths: Sequence[str]) -> bool:
    """Return whether an interpreter searching ``search_paths`` would import the very module of this name held here.

    A name that would find a *different* file counts as unresolvable, since that is the case where a reference
    silently runs the wrong code.

    :param module_name: The dotted name of the module to check.
    :param search_paths: The ``sys.path`` of the interpreter that would do the importing.
    :returns: ``True`` if that interpreter would find the same module this one has.
    """
    # ``__main__`` is the entry point of whichever interpreter is running, so the name never refers to this module.
    if module_name == '__main__':
        return False

    module: ModuleType | None = sys.modules.get(module_name)
    origin: str | None = getattr(getattr(module, '__spec__', None), 'origin', None)

    # A namespace package is a directory with no `__init__.py`, so it has no file of its own and its `__path__` is
    # what an importer has to find instead. A helper folder beside a notebook is one, which is why this cannot be
    # lumped in with the origin-less modules below.
    portions: tuple[str, ...] = tuple(getattr(module, '__path__', ()) or ())

    # A builtin or frozen module has no file to compare and comes with any interpreter running this same Python
    # binary, which a daemon worker does. Nor is there anything to compare for a module built in memory, which has
    # no spec at all, so it is taken as available, as it was before any of this.
    if origin in ('built-in', 'frozen') or (origin is None and not portions):
        return module is not None

    found: ModuleSpec | None = _find_spec(module_name=module_name, search_paths=tuple(search_paths))

    if found is None:
        return False

    if origin is not None:
        return found.origin == origin

    # Every directory this namespace package is made of has to be among the ones the worker would find. More there
    # than here is fine: it can import everything reachable from these.
    return set(found.submodule_search_locations or ()) >= set(portions)


def modules_unimportable_by(can_import: Callable[[str], bool]) -> dict[str, ModuleType]:
    """Return every loaded module an interpreter could not import, keyed by name.

    These are the modules a payload has to carry. Which of them a particular callable actually needs is not worth
    working out: ``cloudpickle`` writes only what the object it is given reaches, so registering a module that
    object never touches produces the same bytes. Walking the names a callable refers to would also miss
    whatever it reaches at runtime, through :func:`importlib.import_module` or an object built from data.

    :param can_import: Returns whether the interpreter that will read the payload can import a module of this name.
    :returns: The modules to carry, keyed by name.
    """
    missing: dict[str, ModuleType] = {}

    # Copied first, because iterating `sys.modules.items()` builds a tuple per module, and on CPython below
    # 3.12 those allocations can run a generation-0 collection whose finalizers import, changing the size of
    # `sys.modules` while the iteration is still going. `dict.copy` allocates once and calls back into no
    # Python, so nothing can mutate what it walks.
    for name, entry in sys.modules.copy().items():
        if _is_module_named(entry=entry, name=name) and not can_import(name):
            missing[name] = entry

    return missing


def _is_module_named(entry: object, name: str) -> bool:
    """Return whether ``entry`` is a module that lives in ``sys.modules`` under its own name.

    ``sys.modules`` holds lazy stand-ins, ``None`` left by a failed import, and aliases under a second name, none of
    which can be registered by value, since that goes by the module's own name.
    """
    return isinstance(entry, ModuleType) and getattr(entry, '__name__', None) == name


def dumps(value: t.Any, *, carry: Collection[ModuleType] = ()) -> bytes:
    """Serialize a callable, including any state it closes over, to bytes.

    :param value: The callable to serialize.
    :param carry: Modules to write into the payload by value, so that an interpreter which cannot import them
        still loads it. Needed when the payload leaves this machine, as it does for a calculation
        job that runs the callable on a remote computer. Leaving it empty keeps the payload small and keeps the
        callable in step with the code installed where it is read. :func:`modules_unimportable_by` derives the set.
    :returns: The serialized callable.
    :raises TypeError: If the callable cannot be serialized.
    """
    import cloudpickle

    # The registry is process global, so unregistering a module somebody else registered would silently change how
    # their callables serialize. Only undo the registrations this call made, and each of them once: unregistering
    # the same module twice raises out of the ``finally`` below.
    already: set[str] = set(cloudpickle.list_registry_pickle_by_value())
    registered: list[ModuleType] = list(
        {module.__name__: module for module in carry if module.__name__ not in already}.values()
    )

    for module in registered:
        cloudpickle.register_pickle_by_value(module)

    try:
        return t.cast(bytes, cloudpickle.dumps(value))
    except Exception as exception:
        msg: str = f'`{value}` could not be serialized: {exception}'
        raise TypeError(msg) from exception
    finally:
        for module in registered:
            cloudpickle.unregister_pickle_by_value(module)


def loads(payload: bytes) -> t.Any:
    """Deserialize a callable that was serialized with :func:`dumps`.

    :param payload: The serialized callable.
    :returns: The deserialized callable.
    :raises ValueError: If the payload cannot be deserialized.
    """
    import cloudpickle

    try:
        return cloudpickle.loads(payload)
    except Exception as exception:
        msg: str = f'the serialized callable could not be deserialized: {exception}'
        raise ValueError(msg) from exception
