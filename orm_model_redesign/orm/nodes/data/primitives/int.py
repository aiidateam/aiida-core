"""An integer value. Mirrors ``aiida.orm.nodes.data.int``."""

from __future__ import annotations

import typing as t
from collections.abc import Sequence

from poc.orm._core.fields import BaseField
from poc.orm.fields import AttributeField
from poc.orm.nodes.data.primitives.base import BaseType

__all__ = ('Int',)


class Int(BaseType):
    """Holds an ``int``."""

    _type = int

    _attribute_fields: t.ClassVar[Sequence[BaseField]] = (AttributeField('value', int, 'The value of the integer'),)
