"""Interface to a node's attributes. Mirrors ``aiida.orm.nodes.attributes``.

This is the manager an ``AttributeField`` reads through, reached as ``node.base.attributes``. It
is modelled here only so that :meth:`~poc.orm.fields.AttributeField._read` can be the same
line it is in ``aiida``.
"""

from __future__ import annotations

import typing as t

if t.TYPE_CHECKING:
    from poc.orm._core.nodes.node import Node

__all__ = ('NodeAttributes',)

_NO_DEFAULT: t.Final = object()


class NodeAttributes:
    """Interface to the attributes of a node instance."""

    def __init__(self, node: Node) -> None:
        self._node = node
        self._backend_node = node.backend_entity

    @property
    def all(self) -> dict[str, t.Any]:
        """Return the complete attributes dictionary, declared keys and undeclared alike."""
        return self._backend_node.attributes

    def get(self, key: str, default: t.Any = _NO_DEFAULT) -> t.Any:
        """Return the value of an attribute.

        :raises AttributeError: if the attribute is not set and no default is given.
        """
        try:
            return self._backend_node.attributes[key]
        except KeyError:
            if default is _NO_DEFAULT:
                raise AttributeError(key) from None
            return default

    def set(self, key: str, value: t.Any) -> None:
        """Set an attribute, running whatever its declaration states it must satisfy.

        The namespace is open, so any key is accepted -- an undeclared one simply has nothing to
        check against, which is C2 rather than an oversight.

        :raises ValueError: if the key is declared with a validator and the value does not pass.
        """
        declaration = type(self._node)._field_declarations.get(key)
        if declaration is not None and declaration.validator is not None:
            value = declaration.validator(value)
        self._backend_node.attributes[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self._backend_node.attributes
