"""Interface to a node's columns, reached as ``node.base.columns``.

The counterpart to ``node.base.attributes``, and new: in ``aiida`` the columns are reached only
through hand-written properties on ``Node``, so there is no single point a write passes through.
Giving them a namespace gives writes one, which is where a declared ``validator`` runs.

The public accessors do not go away -- ``node.label`` stays a property, and delegates here. What
changes is that the property is a *spelling* rather than the only path, so a value cannot reach
the backend without being checked.
"""

from __future__ import annotations

import typing as t

if t.TYPE_CHECKING:
    from poc.orm._core.entities import Entity

__all__ = ('EntityColumns',)


class EntityColumns:
    """Interface to the fixed columns of an entity."""

    def __init__(self, entity: Entity) -> None:
        self._entity = entity
        self._backend_entity = entity.backend_entity

    def get(self, key: str) -> t.Any:
        """Return the stored value of a column."""
        return getattr(self._backend_entity, key)

    def set(self, key: str, value: t.Any) -> None:
        """Set a column, running whatever its declaration states it must satisfy.

        :raises ValueError: if the declaration has a validator and the value does not pass it.
        """
        declaration = type(self._entity)._field_declarations.get(key)
        if declaration is not None and declaration.validator is not None:
            value = declaration.validator(value)
        setattr(self._backend_entity, key, value)

    def __contains__(self, key: str) -> bool:
        return key in type(self._entity)._field_declarations
