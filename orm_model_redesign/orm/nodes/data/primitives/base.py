"""A container for a single python value. Mirrors ``aiida.orm.nodes.data.base``."""

from __future__ import annotations

import typing as t

from poc.orm.nodes.data.data import Data

__all__ = ('BaseType',)


class BaseType(Data):
    """Holds a single value of ``_type``.

    Converting an incoming value to that type is **this class's** rule, applied once when the node
    is constructed. It is not a capability of the declaration: the declaration only records that
    an ``Int`` holds an ``int``, which is a fact about what is stored.
    """

    _type: t.ClassVar[type]

    def __init__(self, value: t.Any = None, **columns: t.Any) -> None:
        super().__init__(**columns)
        self.base.attributes.set('value', self._type() if value is None else self._type(value))

    @property
    def value(self) -> t.Any:
        """Return the stored value.

        A property rather than the declaration itself: the declaration lives in
        ``_attribute_fields``, so the name is the class's to spend as it likes.
        """
        return self.base.attributes.get('value')

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self.value!r})'
