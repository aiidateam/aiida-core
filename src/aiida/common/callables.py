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
import typing as t

if t.TYPE_CHECKING:
    pass

__all__ = ('dumps', 'fingerprint', 'is_importable', 'loads', 'source_of')


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
def source_of(value: t.Any) -> str | None:
    """Return the source text of ``value``, or ``None`` where it cannot be read.

    :param value: The object whose source to read.
    :returns: The source text, or ``None`` if it is not available.
    """
    import inspect

    with contextlib.suppress(OSError, TypeError):
        return inspect.getsource(value)

    return None


def dumps(value: t.Any) -> bytes:
    """Serialize a callable, including any state it closes over, to bytes.

    :param value: The callable to serialize.
    :returns: The serialized callable.
    :raises TypeError: If the callable cannot be serialized.
    """
    import cloudpickle

    try:
        return t.cast(bytes, cloudpickle.dumps(value))
    except Exception as exception:
        msg = f'`{value}` could not be serialized: {exception}'
        raise TypeError(msg) from exception


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
