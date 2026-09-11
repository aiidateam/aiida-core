###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Data plugin to record the identity of a Python callable."""

from __future__ import annotations

import importlib
import importlib.metadata
import inspect
import typing as t
from collections import abc

from aiida.common import callables
from aiida.common.lang import type_check
from aiida.orm.nodes.data.data import Data

__all__ = ('CallableData',)


class CallableData(Data):
    """Data plugin that records what a Python callable is, without storing the callable itself.

    The record is inert: reading it executes nothing, where reading a stored pickle means running the code inside it.
    What it holds is the source text, where that source came from, and enough to tell two callables apart:

    * one that a plugin registers is recorded by its entry point, which is the most stable of the three since it
      survives the module being moved;
    * one that can be recovered by importing it is recorded by module and qualified name;
    * one that cannot, a lambda or a closure, is recorded by a fingerprint of its serialized form.

    The callable itself travels with the process that uses it, in its checkpoint, and is gone once that process
    terminates. So a stored record identifies a callable and shows its source, but only reconstructs it through
    :meth:`load` when it is importable.
    """

    KEY_ATTRIBUTES_NAME: str = 'name'
    """Attribute key that stores the qualified name of the callable."""

    KEY_ATTRIBUTES_MODULE: str = 'module'
    """Attribute key that stores the module the callable was defined in."""

    KEY_ATTRIBUTES_VERSION: str = 'version'
    """Attribute key that stores the version of the package that provides the callable, if it could be determined."""

    KEY_ATTRIBUTES_IMPORTABLE: str = 'importable'
    """Attribute key that stores whether the callable can be recovered by importing it under its recorded name."""

    KEY_ATTRIBUTES_ENTRY_POINT: str = 'callable_entry_point'
    """Attribute key that stores the entry point the callable is registered under, if it is registered at all."""

    KEY_ATTRIBUTES_FINGERPRINT: str = 'fingerprint'
    """Attribute key that stores the fingerprint that identifies a callable which cannot be recovered by name."""

    KEY_ATTRIBUTES_PARAMETERS: str = 'parameters'
    """Attribute key that stores the parameters the callable accepts, as ``[name, kind]`` pairs."""

    KEY_ATTRIBUTES_SOURCE_FILE: str = 'source_file'
    """Attribute key that stores the path of the file the callable was defined in."""

    KEY_ATTRIBUTES_SOURCE_LINE: str = 'source_line'
    """Attribute key that stores the line in ``source_file`` at which the definition of the callable starts."""

    FILENAME_SOURCE: str = 'source.py'
    """Name of the repository file that holds the source text of the callable."""

    _live_callable: t.Callable[..., t.Any] | None = None
    """The recorded callable, held only by the instance that recorded it. See :meth:`live_callable`."""

    def __init__(self, value: t.Callable[..., t.Any], *, entry_point: str | None = None, **kwargs: t.Any) -> None:
        """Construct a new instance recording the identity of the provided callable.

        :param value: The callable to record.
        :param entry_point: The full entry point string, ``group:name``, that ``value`` is registered under, if any.
        :param kwargs: Keyword arguments forwarded to :class:`~aiida.orm.nodes.data.data.Data`.
        :raises TypeError: If ``value`` is not callable, or cannot be recovered by name nor fingerprinted.
        :raises ValueError: If ``entry_point`` does not resolve to ``value``.
        """
        type_check(value, abc.Callable, msg=f'`value` should be a callable but got: {type(value)}')

        if entry_point is not None:
            self._validate_entry_point(entry_point, value)

        super().__init__(**kwargs)  # type: ignore[no-untyped-call]

        self._live_callable = value

        importable = callables.is_importable(value)
        module: str | None = getattr(value, '__module__', None)

        attributes: dict[str, t.Any] = {
            self.KEY_ATTRIBUTES_NAME: getattr(value, '__qualname__', None) or repr(value),
            self.KEY_ATTRIBUTES_MODULE: module,
            self.KEY_ATTRIBUTES_VERSION: self._get_version(module) if importable and module else None,
            self.KEY_ATTRIBUTES_IMPORTABLE: importable,
            # A name identifies an importable callable exactly, and hashing its serialized form instead would make the
            # record depend on the pickler that happened to be installed.
            self.KEY_ATTRIBUTES_FINGERPRINT: None if importable else callables.fingerprint(value),
            self.KEY_ATTRIBUTES_PARAMETERS: self._get_parameters(value),
            self.KEY_ATTRIBUTES_ENTRY_POINT: entry_point,
        }
        attributes.update(self._get_source_location(value))
        self.base.attributes.set_many(attributes)

        source = self._get_source(value)

        if source is not None:
            self.base.repository.put_object_from_bytes(source.encode('utf-8'), self.FILENAME_SOURCE)

    @staticmethod
    def _validate_entry_point(entry_point: str, value: t.Callable[..., t.Any]) -> None:
        """Check that ``entry_point`` is registered and resolves to ``value``.

        :raises ValueError: If it does not exist, cannot be loaded, or refers to something else.
        """
        from aiida.common.exceptions import EntryPointError
        from aiida.plugins.entry_point import load_entry_point_from_string

        try:
            loaded = load_entry_point_from_string(entry_point)
        except EntryPointError as exception:
            msg = f'the entry point `{entry_point}` could not be loaded: {exception}'
            raise ValueError(msg) from exception

        if loaded is not value:
            msg = f'the entry point `{entry_point}` refers to `{loaded}`, not to `{value}`.'
            raise ValueError(msg)

    @staticmethod
    def _get_version(module: str) -> str | None:
        """Return the version of the distribution that provides ``module``, or ``None`` if it cannot be determined."""
        try:
            return importlib.metadata.version(module.split('.', maxsplit=1)[0])
        except importlib.metadata.PackageNotFoundError:
            return None

    @staticmethod
    def _get_parameters(value: t.Callable[..., t.Any]) -> list[list[str]] | None:
        """Return the parameters ``value`` accepts as ``[name, kind]`` pairs, or ``None`` if it has no signature.

        The kind is kept because a name alone does not say how the parameter can be supplied: ``def hook(*, dirpath)``
        and ``def hook(dirpath)`` have the same names and only one of them can be called positionally.
        """
        try:
            signature = inspect.signature(value)
        except (TypeError, ValueError):
            return None

        return [[name, parameter.kind.name] for name, parameter in signature.parameters.items()]

    @staticmethod
    def _get_source(value: t.Callable[..., t.Any]) -> str | None:
        """Return the source text of ``value``, or ``None`` if it is not available."""
        return callables.source_of(value)

    @classmethod
    def _get_source_location(cls, value: t.Callable[..., t.Any]) -> dict[str, t.Any]:
        """Return the file and line at which ``value`` is defined, as far as they can be determined."""
        try:
            source_file = inspect.getsourcefile(value)
            _, source_line = inspect.getsourcelines(value)
        except (OSError, TypeError):
            source_file, source_line = None, None

        return {cls.KEY_ATTRIBUTES_SOURCE_FILE: source_file, cls.KEY_ATTRIBUTES_SOURCE_LINE: source_line}

    @property
    def live_callable(self) -> t.Callable[..., t.Any] | None:
        """Return the callable this record was made from, or ``None`` for a record that was loaded from the database.

        Only the instance that recorded the callable holds it, since what the node stores is a description of it.
        Whoever needs to call it has to take it from here while it is still available, and carry it themselves.
        For a process that means its checkpoint.
        """
        return self._live_callable

    @property
    def name(self) -> str:
        """Return the qualified name of the recorded callable."""
        return t.cast(str, self.base.attributes.get(self.KEY_ATTRIBUTES_NAME))

    @property
    def module(self) -> str | None:
        """Return the module the recorded callable was defined in."""
        return t.cast('str | None', self.base.attributes.get(self.KEY_ATTRIBUTES_MODULE))

    @property
    def version(self) -> str | None:
        """Return the version of the package that provides the recorded callable, if it could be determined."""
        return t.cast('str | None', self.base.attributes.get(self.KEY_ATTRIBUTES_VERSION))

    @property
    def callable_entry_point(self) -> str | None:
        """Return the entry point the recorded callable is registered under, if it is registered at all.

        Qualified, because :attr:`~aiida.orm.nodes.node.Node.entry_point` already means the entry point of the node
        class itself, which is a different thing that every node has.
        """
        return t.cast('str | None', self.base.attributes.get(self.KEY_ATTRIBUTES_ENTRY_POINT))

    @property
    def is_importable(self) -> bool:
        """Return whether the recorded callable can be recovered by importing it under its recorded name."""
        return t.cast(bool, self.base.attributes.get(self.KEY_ATTRIBUTES_IMPORTABLE))

    @property
    def fingerprint(self) -> str | None:
        """Return the fingerprint of the recorded callable, which is set only if it is not importable."""
        return t.cast('str | None', self.base.attributes.get(self.KEY_ATTRIBUTES_FINGERPRINT))

    @property
    def parameters(self) -> list[str] | None:
        """Return the names of the parameters the recorded callable accepts."""
        recorded = self._recorded_parameters

        return None if recorded is None else [name for name, _ in recorded]

    @property
    def positional_parameters(self) -> list[str] | None:
        """Return the names of the parameters that a positional call can supply.

        A caller that invokes the callable positionally, as a parser hook is invoked, has to check these rather than
        :meth:`parameters`, which includes those that can only be passed by keyword.
        """
        recorded = self._recorded_parameters
        positional = ('POSITIONAL_ONLY', 'POSITIONAL_OR_KEYWORD')

        return None if recorded is None else [name for name, kind in recorded if kind in positional]

    @property
    def _recorded_parameters(self) -> list[list[str]] | None:
        """Return the ``[name, kind]`` pairs recorded for the callable."""
        return t.cast('list[list[str]] | None', self.base.attributes.get(self.KEY_ATTRIBUTES_PARAMETERS))

    def get_source(self) -> str | None:
        """Return the source text of the recorded callable, or ``None`` if it was not available when it was recorded."""
        if self.FILENAME_SOURCE not in self.base.repository.list_object_names():
            return None

        return self.base.repository.get_object_content(self.FILENAME_SOURCE, mode='r')

    def load(self) -> t.Any:
        """Import and return the recorded callable.

        An entry point takes precedence over the module and name, since a plugin is free to move the callable and keep
        the entry point pointing at it.

        :returns: The recorded callable.
        :raises ValueError: If the callable cannot be reconstructed from this record.
        """
        if self.callable_entry_point is not None:
            from aiida.common.exceptions import EntryPointError
            from aiida.plugins.entry_point import load_entry_point_from_string

            try:
                return load_entry_point_from_string(self.callable_entry_point)
            except EntryPointError as exception:
                msg = f'`{self.callable_entry_point}` could not be loaded: {exception}'
                raise ValueError(msg) from exception

        if not self.is_importable:
            msg = (
                f'`{self.name}` was not importable when it was recorded, so it cannot be reconstructed from this node. '
                'Pass the callable itself to the process that needs it.'
            )
            raise ValueError(msg)

        try:
            loaded: t.Any = importlib.import_module(t.cast(str, self.module))
            for attribute in self.name.split('.'):
                loaded = getattr(loaded, attribute)
        except (ImportError, AttributeError) as exception:
            requirement = f'{self.module}=={self.version}' if self.version is not None else f'{self.module}'
            msg = f'`{self.name}` could not be imported from `{self.module}`. Install `{requirement}` and try again.'
            raise ValueError(msg) from exception

        return loaded
