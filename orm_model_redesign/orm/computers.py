"""The computer entity. Mirrors ``aiida.orm.computers``.

Here to give the projection layers something with no attributes at all: every declaration is a
``ColumnField``, and two of them are published by the CLI under a different name than the one the
schema uses, which is what makes it a real test of whether a name map is enough.
"""

from __future__ import annotations

import typing as t
from collections.abc import Sequence

from poc.orm._core.entities import Entity
from poc.orm._core.fields import BaseField, ColumnField
from poc.orm._core.implementation.computers import BackendComputer

__all__ = ('Computer',)


def _no_whitespace(value: str) -> str:
    """Reject a hostname that could not be dialled.

    On the declaration rather than in ``__init__`` because a REST ``PUT`` replaces the stored
    value without constructing anything, so a check written there would never run.
    """
    if value != value.strip() or ' ' in value:
        msg = f'a hostname may not contain whitespace, got {value!r}'
        raise ValueError(msg)
    return value


class Computer(Entity):
    """A computer AiiDA can run calculations on."""

    _column_fields: t.ClassVar[Sequence[BaseField]] = (
        ColumnField('uuid', str, 'The UUID of the computer', cli_exclude=True, rest_api_read_only=True),
        ColumnField('label', str, 'The computer label'),
        ColumnField('description', str, 'What the computer is', default=''),
        ColumnField('hostname', str, 'The hostname to connect to', validator=_no_whitespace),
        ColumnField('transport_type', str, 'Entry point name of the transport'),
        ColumnField('scheduler_type', str, 'Entry point name of the scheduler'),
        ColumnField('mpirun_command', list[str], 'The command to run in parallel', default_factory=list),
    )

    def __init__(self, **columns: t.Any) -> None:
        self.backend_entity = BackendComputer(**columns)

    @property
    def label(self) -> str:
        return self.backend_entity.label

    @classmethod
    def from_cli_model(cls, model: t.Any) -> Computer:
        """Return a computer built from what ``verdi computer import`` read.

        Only the setup entities need this: ``Computer``, the code classes, ``Group``. A data node
        is exported and imported through a format converter (``_prepare_<fmt>`` and its parsers),
        which is specific to the data type and does not generalise -- so no data plugin has to
        implement anything here.
        """
        computer = cls.from_model(model)
        # A freshly imported computer is a new one, so it does not carry the exporter's identity.
        computer.backend_entity.uuid = ''
        return computer
