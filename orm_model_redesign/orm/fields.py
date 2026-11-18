"""The one declaration a data plugin writes. Mirrors ``aiida.orm.field_spec``, narrowed.

This module is the public surface of the declaration layer, and it holds exactly one class. The
abstract base and the column kind are internals: a plugin cannot declare a column, so exporting
``ColumnField`` would promise a stability guarantee for something it has no business using.
"""

from __future__ import annotations

import typing as t

from poc.orm._core.fields import BaseField

__all__ = ('AttributeField',)


class AttributeField(BaseField):
    """A field the backend holds in the entity's open ``attributes``.

    This is what a data plugin declares, and the only kind it can: the attributes are the only
    part of the row a plugin may add to. It is therefore **the user-facing kind**, and it is kept
    to what a plugin author must state -- the type, and what the value means.

    It carries no default. There is no schema behind an attribute to supply one, so a default
    would be a decision about what to write, and writing is ``__init__``'s job (D4).
    """

    __slots__ = ()

    @property
    def is_attribute(self) -> bool:
        return True

    @property
    def backend_key(self) -> str:
        return f'attributes.{self._name}'

    def read(self, instance: t.Any) -> t.Any:
        """Return the stored value.

        :raises AttributeError: if the key is not set. There is no declared fallback: what an
            unset attribute should read as is the owning class's decision, made in ``__init__``.
        """
        return instance.base.attributes.get(self._name)
