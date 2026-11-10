"""What one layer does with one declaration.

A :class:`~poc.orm._core.fields.BaseField` says what the backend stores. A :class:`LayerField`
says what a consuming layer does with it: the name it publishes under, and whether it publishes it
at all.

There is a class per layer rather than one shared one. They have a common base because both
answer "publish this, under what name", but ``read_only`` is a question only a client-serving API
asks -- a CLI file a user edits has no notion of a field they may read but not write. Folding it
into one class meant the CLI carrying an option it ignores, and the next option either layer needs
would land in the other's vocabulary too.

Neither states any serialisation: every declared type is one pydantic already renders and parses,
and a field has to be database-serialisable anyway, which is the stricter requirement.

They live in ``common`` rather than in either layer so that an entity can declare its projection
without importing ``poc.cmdline`` or ``poc.restapi``.
"""

from __future__ import annotations

import typing as t

__all__ = ('CliField', 'LayerField', 'RestApiField')


class LayerField:
    """What every layer answers about a field: whether to publish it, and under what name."""

    __slots__ = ('_exclude', '_name')

    def __init__(self, *, name: str | None = None, exclude: bool = False) -> None:
        self._name = name
        self._exclude = exclude

    @property
    def name(self) -> str | None:
        """The name this layer publishes the field under, where it differs from the declared one."""
        return self._name

    @property
    def exclude(self) -> bool:
        """Whether this layer leaves the field out entirely."""
        return self._exclude

    def _options(self) -> dict[str, t.Any]:
        """Return the options this class was built from, so a copy can vary one of them."""
        return {'name': self._name, 'exclude': self._exclude}

    def replace(self, **changes: t.Any) -> t.Self:
        """Return a copy of this view with the given options changed."""
        return type(self)(**{**self._options(), **changes})

    def __repr__(self) -> str:
        stated = ', '.join(f'{key}={value!r}' for key, value in self._options().items() if value)
        return f'{type(self).__name__}({stated})'


class CliField(LayerField):
    """How the CLI publishes one declaration, in a file a user edits and re-imports.

    Only the setup entities need these -- ``Computer``, the code classes, ``Group``. A data node is
    exported and imported through a format converter specific to its type, so no data plugin
    declares one.
    """

    __slots__ = ()


class RestApiField(LayerField):
    """How the REST API publishes one declaration.

    Adds the one question only this layer asks: whether a client may write the field, or whether
    AiiDA sets it and a write should be refused.
    """

    __slots__ = ('_read_only',)

    def __init__(self, *, name: str | None = None, exclude: bool = False, read_only: bool = False) -> None:
        super().__init__(name=name, exclude=exclude)
        self._read_only = read_only

    @property
    def read_only(self) -> bool:
        """Whether a client may not write this field; AiiDA sets it."""
        return self._read_only

    def _options(self) -> dict[str, t.Any]:
        return {**super()._options(), 'read_only': self._read_only}
