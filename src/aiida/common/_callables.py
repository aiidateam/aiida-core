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
    """Return available source, recovering class definitions through their methods when inspection fails.

    :returns: Source text, or `None` when unavailable.
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
    """Serialize a callable and captured state with `cloudpickle`.

    Referenced modules must be importable when deserializing.

    :raises TypeError: If serialization fails.
    """
    import cloudpickle

    try:
        return t.cast(bytes, cloudpickle.dumps(value))
    except Exception as exception:
        msg: str = f'`{value}` could not be serialized: {exception}'
        raise TypeError(msg) from exception


def loads(payload: bytes) -> t.Any:
    """Deserialize a callable from a trusted :func:`dumps` payload.

    :raises ValueError: If deserialization fails.
    """
    import cloudpickle

    try:
        return cloudpickle.loads(payload)
    except Exception as exception:
        msg: str = f'the serialized callable could not be deserialized: {exception}'
        raise ValueError(msg) from exception
