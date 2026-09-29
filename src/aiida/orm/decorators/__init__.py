"""Decorators for AiiDA ORM classes."""

from aiida.orm.decorators.attributes import attribute
from aiida.orm.decorators.columns import column

__all__ = (
    'attribute',
    'column',
)
