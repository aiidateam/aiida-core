"""The base for data plugins. Mirrors ``aiida.orm.nodes.data.data``.

Everything a plugin adds is an :class:`AttributeField`, since the attributes are the only part of
the row it may add to. ``AttributeField`` is also the plugin's *only* option -- it cannot reach
for a column by accident, because the kind is the type.

Declarations go in ``_attribute_fields``, the protected subclass API for data plugins. This leaves
each declared name free for whatever accessor the class wants to expose.
"""

from __future__ import annotations

import typing as t
from collections.abc import Sequence

from poc.orm._core.fields import BaseField
from poc.orm._core.nodes.node import Node
from poc.orm.fields import AttributeField

__all__ = ('Data',)


class Data(Node):
    """A base for data plugins.

    Subclasses declare stored values through ``_attribute_fields``. This is a protected subclass
    API: it is supported for plugin classes to define, but ordinary users should use ``fields``
    for query introspection instead.
    """

    _attribute_fields: t.ClassVar[Sequence[BaseField]] = (
        AttributeField('source', dict | None, 'Where the data came from'),
    )

    def __init__(self, source: dict[str, t.Any] | None = None, **columns: t.Any) -> None:
        super().__init__(**columns)
        # The declaration states that a `source` is stored. What it starts out as is this
        # constructor's decision, which is why the declaration carries no default.
        self.base.attributes.set('source', source)

    @property
    def source(self) -> dict[str, t.Any] | None:
        return self.base.attributes.get('source')
