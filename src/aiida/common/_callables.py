###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Internal callable serialization and source recording."""

from __future__ import annotations

import ast
import contextlib
import tokenize
import typing as t

if t.TYPE_CHECKING:
    from types import CodeType


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

    with contextlib.suppress(OSError, TypeError, tokenize.TokenError, SyntaxError, IndexError):
        return inspect.getsource(value)

    if not inspect.isclass(value):
        return None

    for member in vars(value).values():
        function: t.Any = getattr(member, '__func__', member)
        code: CodeType | None = getattr(function, '__code__', None)

        if code is None:
            continue

        if getattr(function, '__qualname__', '').rsplit('.', 1)[0] != value.__qualname__:
            continue
        lines: list[str] = linecache.getlines(filename=code.co_filename)
        try:
            tree: ast.Module = ast.parse(''.join(lines))
        except (SyntaxError, ValueError):
            continue
        candidates: list[ast.ClassDef] = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef)
            and node.name == value.__name__
            and node.end_lineno is not None
            and node.lineno <= code.co_firstlineno <= node.end_lineno
        ]
        if candidates:
            statement: ast.ClassDef = max(candidates, key=lambda node: node.lineno)
            start: int = min([statement.lineno, *(decorator.lineno for decorator in statement.decorator_list)])
            return ''.join(lines[start - 1 : statement.end_lineno])

    return None


def dumps(value: t.Any) -> bytes:
    """Serialize a callable, including any state it closes over, to bytes.

    `cloudpickle` records writer-importable callables by reference and dynamic definitions by value. Referenced
    modules must also be importable by the reader; serialization does not establish reader-side availability.

    :param value: The callable to serialize.
    :returns: The serialized callable.
    :raises TypeError: If the callable cannot be serialized.
    """
    import cloudpickle

    try:
        return t.cast(bytes, cloudpickle.dumps(value))
    except Exception as exception:
        msg: str = f'`{value}` could not be serialized: {exception}'
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
        msg: str = f'the serialized callable could not be deserialized: {exception}'
        raise ValueError(msg) from exception
