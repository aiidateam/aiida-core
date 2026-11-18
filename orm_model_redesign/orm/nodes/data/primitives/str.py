"""A string value. Mirrors ``aiida.orm.nodes.data.str``."""

from __future__ import annotations

import typing as t
from collections.abc import Sequence

from poc.orm._core.fields import BaseField
from poc.orm.fields import AttributeField
from poc.orm.nodes.data.primitives.base import BaseType

__all__ = ('Str',)


class Str(BaseType):
    """Holds a ``str``."""

    _type = str

    _attribute_fields: t.ClassVar[Sequence[BaseField]] = (AttributeField('value', str, 'The value of the string'),)
