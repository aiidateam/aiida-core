"""Toy backend node. Mirrors ``aiida.orm.implementation.nodes``.

The shape that matters to the design: a **fixed set of columns**, owned by the schema and its
migrations, one of which holds an **open attributes blob** whose keys are whatever was put there.
That asymmetry is the whole reason there are two kinds of field declaration.

The columns are named attributes rather than a dictionary, because that is what they are in the
backend, and it is what makes ``ColumnField`` a plain ``getattr``.
"""

from __future__ import annotations

import datetime
import typing as t

__all__ = ('BackendNode',)


class BackendNode:
    """The row backing a node."""

    #: The columns this table has. A plugin cannot add to these; a migration would have to.
    COLUMNS: t.Final = ('uuid', 'label', 'ctime', 'attributes')

    def __init__(self, **columns: t.Any) -> None:
        unknown = set(columns) - set(self.COLUMNS)
        if unknown:
            msg = f'no such column(s): {sorted(unknown)}'
            raise ValueError(msg)
        self.uuid: str = columns.get('uuid', '')
        self.label: str = columns.get('label', '')
        # A real backend stamps this on insert, so the column is never null and the
        # declaration can say `datetime` rather than `datetime | None`.
        self.ctime: datetime.datetime = columns.get('ctime') or datetime.datetime.now(tz=datetime.timezone.utc)
        #: The open namespace. Its keys are whatever was stored, declared or not.
        self.attributes: dict[str, t.Any] = columns.get('attributes', {})
