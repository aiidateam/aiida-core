"""A boolean value. Mirrors ``aiida.orm.nodes.data.bool``."""

from __future__ import annotations

import typing as t
from collections.abc import Sequence

from poc.orm._core.fields import BaseField
from poc.orm.fields import AttributeField
from poc.orm.nodes.data.primitives.base import BaseType

__all__ = ('Bool',)


class Bool(BaseType):
    """Holds a ``bool``.

    The one type whose query field admits the boolean operators, so ``Bool.fields.value`` can turn
    itself into a filter through ``as_filter()``, ``&`` or ``~``.
    """

    _type = bool

    _attribute_fields: t.ClassVar[Sequence[BaseField]] = (AttributeField('value', bool, 'The value of the boolean'),)
