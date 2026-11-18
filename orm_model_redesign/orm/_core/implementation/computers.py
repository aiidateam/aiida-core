"""Toy backend computer. Mirrors ``aiida.orm.implementation.computers``.

A computer has columns and no attributes blob, which is why every one of its declarations is a
``ColumnField`` and why it is the natural entity to test a projection against.
"""

from __future__ import annotations

import typing as t

__all__ = ('BackendComputer',)


class BackendComputer:
    """The row backing a computer."""

    COLUMNS: t.Final = (
        'uuid',
        'label',
        'description',
        'hostname',
        'transport_type',
        'scheduler_type',
        'mpirun_command',
    )

    def __init__(self, **columns: t.Any) -> None:
        unknown = set(columns) - set(self.COLUMNS)
        if unknown:
            msg = f'no such column(s): {sorted(unknown)}'
            raise ValueError(msg)
        self.uuid: str = columns.get('uuid', '')
        self.label: str = columns.get('label', '')
        self.description: str = columns.get('description', '')
        self.hostname: str = columns.get('hostname', '')
        self.transport_type: str = columns.get('transport_type', '')
        self.scheduler_type: str = columns.get('scheduler_type', '')
        self.mpirun_command: list[str] = columns.get('mpirun_command', [])
