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

import contextlib
import functools
import hashlib
import importlib
import sys
import typing as t
from types import ModuleType

if t.TYPE_CHECKING:
    from collections.abc import Callable, Collection, Sequence

__all__ = ('dumps', 'fingerprint', 'is_importable', 'loads', 'modules_missing_from', 'resolves_in', 'source_of')


def is_importable(value: t.Any) -> bool:
    """Return whether ``value`` can be recovered in another interpreter by importing it under its own name.

    :param value: The object to check.
    :returns: ``True`` if importing ``__module__`` and following ``__qualname__`` yields ``value`` itself.
    """
    module_name = getattr(value, '__module__', None)
    qualname = getattr(value, '__qualname__', None)

    # ``__main__`` resolves to a different module in the interpreter that would have to do the importing, so a name
    # defined there identifies nothing. This is why a function defined in a script cannot be recovered by name.
    if module_name is None or qualname is None or module_name == '__main__':
        return False

    try:
        resolved: t.Any = importlib.import_module(module_name)
        for attribute in qualname.split('.'):
            resolved = getattr(resolved, attribute)
    except (ImportError, AttributeError):
        return False

    return resolved is value


@functools.lru_cache(maxsize=256)
def _find_origin(module_name: str, search_paths: tuple[str, ...]) -> str | None:
    """Return the file an interpreter searching ``search_paths`` would import ``module_name`` from.

    This walks the filesystem, and it is asked on every state transition of every process, so it is cached. The paths
    it is asked about are those of a running daemon, which do not change while that daemon runs.

    :param module_name: The dotted name of the module to look for.
    :param search_paths: The ``sys.path`` of the interpreter that would do the importing.
    :returns: The origin of the module that would be found, or ``None`` if none would be.
    """
    from importlib.machinery import PathFinder

    finder = PathFinder()
    parts = module_name.split('.')
    path: t.Any = list(search_paths)
    spec = None

    for depth in range(1, len(parts) + 1):
        if path is None:
            return None
        spec = finder.find_spec('.'.join(parts[:depth]), path=list(path))
        if spec is None:
            return None
        path = spec.submodule_search_locations

    return spec.origin if spec is not None else None


def module_resolves_in(module_name: str, search_paths: Sequence[str]) -> bool:
    """Return whether an interpreter searching ``search_paths`` would import the very module of this name held here.

    A name that would find a *different* file counts as unresolvable, since that is the case where a reference
    silently runs the wrong code.

    :param module_name: The dotted name of the module to check.
    :param search_paths: The ``sys.path`` of the interpreter that would do the importing.
    :returns: ``True`` if that interpreter would find the same module this one has.
    """
    # ``__main__`` is the entry point of whichever interpreter is asking, so the name never refers to this module.
    if module_name == '__main__':
        return False

    module = sys.modules.get(module_name)
    origin: str | None = getattr(getattr(module, '__spec__', None), 'origin', None)

    # A builtin, frozen or namespace module has no file to compare, and comes with any interpreter running this same
    # Python binary, which the daemon workers do.
    if origin is None or origin in ('built-in', 'frozen'):
        return module is not None

    return _find_origin(module_name, tuple(search_paths)) == origin


def resolves_in(value: t.Any, search_paths: Sequence[str]) -> bool:
    """Return whether ``value`` can be recovered by name in an interpreter whose ``sys.path`` is ``search_paths``.

    :func:`is_importable` answers the same question for *this* interpreter, which is the wrong one whenever the
    payload is read back somewhere else: a module in a directory added to ``sys.path`` after the daemon was started
    imports here and not there.

    :param value: The object to check.
    :param search_paths: The ``sys.path`` of the interpreter that would do the importing.
    :returns: ``True`` if that interpreter would find the very object this name refers to here.
    """
    return is_importable(value) and module_resolves_in(value.__module__, search_paths)


def source_of(value: t.Any) -> str | None:
    """Return the source text of ``value``, or ``None`` where it cannot be read.

    :func:`inspect.getsource` reaches a class through the file of the module that defines it, and a class defined in
    a notebook cell has no such file: the kernel's ``__main__`` is not one. Its own methods do carry the cell they
    were compiled from, and a class statement sits in the same cell as its methods, so that is where to look when
    the ordinary route fails.

    :param value: The object whose source to read.
    :returns: The source text, or ``None`` if it is not available.
    """
    import inspect
    import linecache

    with contextlib.suppress(OSError, TypeError):
        return inspect.getsource(value)

    if not inspect.isclass(value):
        return None

    for member in vars(value).values():
        function = getattr(member, '__func__', member)
        code = getattr(function, '__code__', None)

        if code is None:
            continue

        lines = linecache.getlines(code.co_filename)
        statement = f'class {value.__name__}'

        for index, line in enumerate(lines):
            if line.lstrip().startswith(statement):
                with contextlib.suppress(OSError, TypeError):
                    return ''.join(inspect.getblock(lines[index:]))

    return None


def modules_missing_from(available: Callable[[str], bool]) -> dict[str, ModuleType]:
    """Return every loaded module an interpreter could not import, keyed by name.

    These are the modules a payload has to carry. Which of them a particular callable actually needs is not worth
    working out: ``cloudpickle`` writes only what the object it is given reaches, so registering a module that
    object never touches produces the same bytes. Deciding by walking the names a callable mentions would also miss
    whatever it reaches at runtime, through :func:`importlib.import_module` or an object built from data.

    :param available: Answers whether the reader can import a module of this name.
    :returns: The modules to carry, keyed by name.
    """
    missing = {}

    for name, entry in list(sys.modules.items()):
        if _is_module_named(entry, name) and not available(name):
            missing[name] = entry

    return missing


def _is_module_named(entry: object, name: str) -> bool:
    """Return whether ``entry`` is a module that lives in ``sys.modules`` under its own name.

    ``sys.modules`` is not only modules: a package may put a lazy stand-in there, and a failed import can leave
    ``None`` behind. An entry aliasing a module under a second name is not ours to carry either, since registering
    it by value goes by the module's own name.
    """
    return isinstance(entry, ModuleType) and getattr(entry, '__name__', None) == name


def dumps(value: t.Any, *, carry: Collection[ModuleType] = ()) -> bytes:
    """Serialize a callable, including any state it closes over, to bytes.

    :param value: The callable to serialize.
    :param carry: Modules to write into the payload itself rather than refer to by name, so that an interpreter which
        cannot import them still loads it. Needed when the payload leaves this machine, as it does for a calculation
        job that runs the callable on a remote computer. Leaving it empty keeps the payload small and keeps the
        callable in step with the code installed where it is read. :func:`modules_missing_from` derives the set.
    :returns: The serialized callable.
    :raises TypeError: If the callable cannot be serialized.
    """
    import cloudpickle

    # The registry is process global, so unregistering a module somebody else registered would silently change how
    # their callables serialize. Only undo the registrations this call made.
    registered = [module for module in carry if module.__name__ not in cloudpickle.list_registry_pickle_by_value()]

    for module in registered:
        cloudpickle.register_pickle_by_value(module)

    try:
        return t.cast(bytes, cloudpickle.dumps(value))
    except Exception as exception:
        msg = f'`{value}` could not be serialized: {exception}'
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
        msg = f'the serialized callable could not be deserialized: {exception}'
        raise ValueError(msg) from exception


def fingerprint(value: t.Any) -> str:
    """Return a hash that distinguishes ``value`` from other callables, including the state it closes over.

    Two closures returned by the same factory share a name, a source text and a source location, so those cannot tell
    them apart. What they capture can, which is why this hashes the serialized form.

    The reference form is hashed, so a callable that can be imported is identified by its name rather than by bytes
    that would change with the pickler.

    :param value: The callable to fingerprint.
    :returns: The hex digest of the serialized callable.
    :raises TypeError: If the callable cannot be serialized.
    """
    return hashlib.sha256(dumps(value)).hexdigest()
